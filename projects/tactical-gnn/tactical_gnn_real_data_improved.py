from __future__ import annotations

import argparse
import gc
import json
import random
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from scipy.spatial.distance import cdist
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split
from torch.amp import GradScaler, autocast
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader
from torch_geometric.nn import GATv2Conv, global_max_pool, global_mean_pool
from tqdm import tqdm


TACTIC_CLASSES = {
    "빌드업-크로스형": 0,
    "빌드업-중앙침투형": 1,
    "빌드업-중앙 침투형": 1,
    "빌드업-측면침투형": 2,
    "빌드업-측면 침투형": 2,
    "빌드업-롱볼형": 3,
    "빌드업-롱볼 형": 3,
    "세트피스-코너킥": 4,
    "세트피스-프리킥": 5,
    "세트피스-스로인": 6,
    "세트피스-골킥": 7,
    "수비-고위압박": 8,
    "수비-중위압박": 9,
    "수비-저위블록": 10,
    "공격전환": 11,
    "수비전환": 12,
}

NUM_TACTIC_CLASSES = 13
IDX_TO_TACTIC = {v: k for k, v in TACTIC_CLASSES.items()}

TACTIC_TO_FAMILY = {
    0: 0, 1: 0, 2: 0, 3: 0,
    4: 1, 5: 1, 6: 1, 7: 1,
    8: 2, 9: 2, 10: 2,
    11: 3, 12: 3,
}
IDX_TO_FAMILY = {
    0: "빌드업",
    1: "세트피스",
    2: "수비",
    3: "전환",
}

POSITION_NAMES = ["GK", "DF", "MF", "FW", "FP"]
POS_TO_IDX = {name: idx for idx, name in enumerate(POSITION_NAMES)}
POS_TO_ONEHOT = {
    name: [1.0 if i == j else 0.0 for j in range(len(POSITION_NAMES))]
    for i, name in enumerate(POSITION_NAMES)
}

COMPLEMENTARITY_INIT = np.array(
    [
        [0.1, 0.8, 0.4, 0.2, 0.5],
        [0.8, 0.6, 0.9, 0.5, 0.7],
        [0.4, 0.9, 0.5, 0.9, 0.7],
        [0.2, 0.5, 0.9, 0.3, 0.6],
        [0.5, 0.7, 0.7, 0.6, 0.5],
    ],
    dtype=np.float32,
)

NODE_IN_DIM = 11
EDGE_IN_DIM = 5


@dataclass
class MatchMeta:
    match_id: str
    track_path: Path
    fps: int
    n_frames: int
    player_map: dict[int, dict[str, str]]
    team_to_id: dict[str, int]
    tactics: list[dict[str, int | str]]
    dominant_class: int
    tactic_hist: Counter


class TacticalData(Data):
    def __inc__(self, key, value, *args, **kwargs):
        if key == "link_pairs":
            return self.x.size(0)
        if key == "prev_edge_index":
            return self.prev_x.size(0) if hasattr(self, "prev_x") else 0
        if key == "prev2_edge_index":
            return self.prev2_x.size(0) if hasattr(self, "prev2_x") else 0
        return super().__inc__(key, value, *args, **kwargs)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Improved Tactical GNN training on AIHub real data.")
    parser.add_argument(
        "--aihub-dir",
        type=Path,
        default=Path("/content/drive/MyDrive/tactical-gnn/data/aihub/training_labels/1.동영상분석"),
        help="Root directory containing AIHub match folders.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("/content/drive/MyDrive/tactical-gnn/models/improved_real"),
        help="Directory to save checkpoints and reports.",
    )
    parser.add_argument("--max-matches", type=int, default=0, help="0 means all matches.")
    parser.add_argument("--sample-rate", type=int, default=90, help="Frame stride. 90 ~= 3 seconds at 30fps.")
    parser.add_argument("--batch-size", type=int, default=48)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--hidden-dim", type=int, default=96)
    parser.add_argument("--gat-heads", type=int, default=4)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--dropout", type=float, default=0.25)
    parser.add_argument("--label-smoothing", type=float, default=0.05)
    parser.add_argument("--link-weight", type=float, default=0.0)
    parser.add_argument("--change-weight", type=float, default=0.0)
    parser.add_argument("--min-change-positives", type=int, default=20)
    parser.add_argument("--test-size", type=float, default=0.15)
    parser.add_argument("--val-size", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--grad-clip", type=float, default=1.0)
    parser.add_argument("--patience", type=int, default=12)
    parser.add_argument("--coarse-weight", type=float, default=0.4)
    return parser.parse_args()


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def choose_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def summarize_distribution(name: str, labels: list[int]) -> str:
    if not labels:
        return f"{name}: empty"
    counts = Counter(labels)
    parts = [f"{IDX_TO_TACTIC.get(label, str(label))}={count}" for label, count in sorted(counts.items())]
    return f"{name}: " + ", ".join(parts)


def load_match_meta(match_dir: Path) -> MatchMeta | None:
    track_path = match_dir / "03" / "track1.json"
    strategy_path = match_dir / "06" / "strategy.json"
    if not track_path.exists() or not strategy_path.exists():
        return None

    try:
        with open(strategy_path, encoding="utf-8-sig") as handle:
            strategy = json.load(handle)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return None

    try:
        with open(track_path, encoding="utf-8-sig") as handle:
            track = json.load(handle)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return None

    fps = int(track.get("fps", 30))
    n_frames = len(track.get("tag", []))
    player_info_raw = track.get("playerInfo", [])
    del track
    gc.collect()

    player_map: dict[int, dict[str, str]] = {}
    for player in player_info_raw:
        sid = player.get("player_sid")
        if sid is None:
            continue
        position = player.get("player_position", "FP")
        if position not in POSITION_NAMES:
            position = "FP"
        player_map[sid] = {"team": player.get("team", ""), "position": position}

    team_names = sorted({info["team"] for info in player_map.values() if info["team"] and info["team"] != "심판"})
    if len(team_names) < 2 or n_frames == 0:
        return None

    tactics: list[dict[str, int | str]] = []
    tactic_hist: Counter = Counter()
    for entry in strategy.get("strategyArray", []):
        offense = entry.get("offense_strategy", {})
        tactic_name = offense.get("depth1", "")
        tactic_class = TACTIC_CLASSES.get(tactic_name, -1)
        if tactic_class < 0:
            continue
        tactics.append(
            {
                "start": int(entry["start"]),
                "end": int(entry["end"]),
                "tactic_class": tactic_class,
                "tactic_name": tactic_name,
            }
        )
        tactic_hist[tactic_class] += 1

    if not tactics:
        return None

    dominant_class = tactic_hist.most_common(1)[0][0]
    return MatchMeta(
        match_id=match_dir.name,
        track_path=track_path,
        fps=fps,
        n_frames=n_frames,
        player_map=player_map,
        team_to_id={team_names[0]: 0, team_names[1]: 1},
        tactics=tactics,
        dominant_class=dominant_class,
        tactic_hist=tactic_hist,
    )


def safe_split(matches: list[MatchMeta], test_size: float, seed: int) -> tuple[list[MatchMeta], list[MatchMeta]]:
    if not matches:
        return [], []
    labels = [match.dominant_class for match in matches]
    label_counts = Counter(labels)
    stratify = labels if len(label_counts) > 1 and min(label_counts.values()) >= 2 else None
    left, right = train_test_split(matches, test_size=test_size, random_state=seed, stratify=stratify)
    return list(left), list(right)


def extract_frame(
    tag_entry: dict,
    player_map: dict[int, dict[str, str]],
    team_to_id: dict[str, int],
    img_w: float = 1920.0,
    img_h: float = 1080.0,
) -> dict[str, np.ndarray | list[str]] | None:
    positions: list[list[float]] = []
    team_ids: list[int] = []
    roles: list[str] = []

    for obj in tag_entry.get("data", []):
        sid = obj.get("id")
        bbox = obj.get("tag", [])
        if sid is None or len(bbox) < 4:
            continue
        info = player_map.get(sid)
        if info is None or info["team"] == "심판":
            continue
        team_id = team_to_id.get(info["team"])
        if team_id is None:
            continue

        cx = max(0.0, min(1.0, (bbox[0] + bbox[2] / 2) / img_w))
        cy = max(0.0, min(1.0, (bbox[1] + bbox[3] / 2) / img_h))
        positions.append([cx, cy])
        team_ids.append(team_id)
        roles.append(info["position"])

    if len(positions) < 10:
        return None

    return {
        "positions": np.array(positions, dtype=np.float32),
        "team_ids": np.array(team_ids, dtype=np.int64),
        "roles": roles,
    }


def get_tactic_for_frame(frame_num: int, tactics: list[dict[str, int | str]]) -> int:
    for tactic in tactics:
        if int(tactic["start"]) <= frame_num <= int(tactic["end"]):
            return int(tactic["tactic_class"])
    return -1


def frame_to_graph(
    positions: np.ndarray,
    team_ids: np.ndarray,
    prev_positions: np.ndarray | None = None,
    roles: list[str] | None = None,
    k_neighbors: int = 5,
) -> TacticalData:
    n_nodes = len(positions)
    k_neighbors = min(k_neighbors, n_nodes - 1)
    if prev_positions is not None and len(prev_positions) == n_nodes:
        velocity = positions - prev_positions
    else:
        velocity = np.zeros_like(positions)

    boundary_distance = np.full((n_nodes, 1), -1.0, dtype=np.float32)
    role_source = roles or ["FP"] * n_nodes
    pos_onehot = np.array([POS_TO_ONEHOT.get(role, POS_TO_ONEHOT["FP"]) for role in role_source], dtype=np.float32)
    x = np.hstack([positions, velocity, team_ids.reshape(-1, 1), boundary_distance, pos_onehot]).astype(np.float32)

    distance_matrix = cdist(positions, positions)
    src, dst, edge_features = [], [], []
    for i in range(n_nodes):
        neighbors = np.argsort(distance_matrix[i])[1 : k_neighbors + 1]
        for j in neighbors:
            src.append(i)
            dst.append(j)
            edge_features.append(
                [
                    distance_matrix[i, j],
                    np.linalg.norm(velocity[i] - velocity[j]),
                    float(team_ids[i] == team_ids[j]),
                    positions[j, 0] - positions[i, 0],
                    positions[j, 1] - positions[i, 1],
                ]
            )

    return TacticalData(
        x=torch.tensor(x, dtype=torch.float32),
        edge_index=torch.tensor([src, dst], dtype=torch.long),
        edge_attr=torch.tensor(edge_features, dtype=torch.float32),
    )


def compute_synergy_targets(
    positions: np.ndarray,
    team_ids: np.ndarray,
    roles: list[str],
    n_samples: int = 20,
    seed: int = 0,
) -> tuple[torch.Tensor, torch.Tensor]:
    n_nodes = len(positions)
    distance_matrix = cdist(positions, positions)
    max_distance = float(distance_matrix.max() + 1e-8)
    rng = np.random.default_rng(seed)

    same_team = [(a, b) for a in range(n_nodes) for b in range(a + 1, n_nodes) if team_ids[a] == team_ids[b]]
    diff_team = [(a, b) for a in range(n_nodes) for b in range(a + 1, n_nodes) if team_ids[a] != team_ids[b]]
    n_pairs = min(len(same_team), len(diff_team), n_samples)
    if n_pairs == 0:
        return torch.zeros((0, 2), dtype=torch.long), torch.zeros(0, dtype=torch.float32)

    pairs: list[list[int]] = []
    labels: list[float] = []

    for idx in rng.choice(len(same_team), n_pairs, replace=False):
        a, b = same_team[idx]
        comp = COMPLEMENTARITY_INIT[POS_TO_IDX.get(roles[a], 4), POS_TO_IDX.get(roles[b], 4)]
        proximity = max(0.0, 1.0 - float(distance_matrix[a, b] / max_distance))
        pairs.append([a, b])
        labels.append(float(comp * proximity))

    for idx in rng.choice(len(diff_team), n_pairs, replace=False):
        a, b = diff_team[idx]
        pairs.append([a, b])
        labels.append(0.0)

    return torch.tensor(pairs, dtype=torch.long), torch.tensor(labels, dtype=torch.float32)


def build_graphs(
    matches: list[MatchMeta],
    sample_rate: int,
    labeled_only: bool = True,
) -> tuple[list[TacticalData], dict[str, int]]:
    graphs: list[TacticalData] = []
    stats = defaultdict(int)

    for match_idx, match in enumerate(tqdm(matches, desc="Building graphs")):
        try:
            with open(match.track_path, encoding="utf-8-sig") as handle:
                tags = json.load(handle).get("tag", [])
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            stats["skipped_matches"] += 1
            continue

        prev_graph: TacticalData | None = None
        prev2_graph: TacticalData | None = None
        prev_positions: np.ndarray | None = None
        prev_kept_graph: TacticalData | None = None

        for idx in range(0, len(tags), sample_rate):
            tag_entry = tags[idx]
            frame_num = int(tag_entry.get("frame", idx))

            frame = extract_frame(tag_entry, match.player_map, match.team_to_id)
            if frame is None:
                prev_graph = None
                prev2_graph = None
                prev_positions = None
                continue

            positions = frame["positions"]
            team_ids = frame["team_ids"]
            roles = frame["roles"]
            tactic_class = get_tactic_for_frame(frame_num, match.tactics)

            graph = frame_to_graph(positions, team_ids, prev_positions, roles)
            graph.match_idx = torch.tensor([match_idx], dtype=torch.long)
            graph.frame_num = torch.tensor([frame_num], dtype=torch.long)
            graph.y = torch.tensor([max(tactic_class, 0)], dtype=torch.long)
            graph.coarse_y = torch.tensor([TACTIC_TO_FAMILY.get(max(tactic_class, 0), 0)], dtype=torch.long)
            graph.y_mask = torch.tensor([1.0 if tactic_class >= 0 else 0.0], dtype=torch.float32)
            graph.change_label = torch.tensor([0.0], dtype=torch.float32)

            link_pairs, link_labels = compute_synergy_targets(positions, team_ids, roles, seed=frame_num)
            graph.link_pairs = link_pairs
            graph.link_labels = link_labels

            if prev_graph is not None:
                graph.prev_x = prev_graph.x.clone()
                graph.prev_edge_index = prev_graph.edge_index.clone()
                graph.prev_edge_attr = prev_graph.edge_attr.clone()
                graph.prev_num_nodes = torch.tensor([prev_graph.num_nodes], dtype=torch.long)
                graph.has_prev = torch.tensor([1.0], dtype=torch.float32)
            else:
                graph.prev_x = graph.x.clone()
                graph.prev_edge_index = graph.edge_index.clone()
                graph.prev_edge_attr = graph.edge_attr.clone()
                graph.prev_num_nodes = torch.tensor([graph.num_nodes], dtype=torch.long)
                graph.has_prev = torch.tensor([0.0], dtype=torch.float32)

            if prev2_graph is not None:
                graph.prev2_x = prev2_graph.x.clone()
                graph.prev2_edge_index = prev2_graph.edge_index.clone()
                graph.prev2_edge_attr = prev2_graph.edge_attr.clone()
                graph.prev2_num_nodes = torch.tensor([prev2_graph.num_nodes], dtype=torch.long)
                graph.has_prev2 = torch.tensor([1.0], dtype=torch.float32)
            else:
                graph.prev2_x = graph.prev_x.clone()
                graph.prev2_edge_index = graph.prev_edge_index.clone()
                graph.prev2_edge_attr = graph.prev_edge_attr.clone()
                graph.prev2_num_nodes = graph.prev_num_nodes.clone()
                graph.has_prev2 = torch.tensor([0.0], dtype=torch.float32)

            prev2_graph = prev_graph
            prev_graph = graph
            prev_positions = positions

            if tactic_class < 0 and labeled_only:
                stats["unlabeled_skipped"] += 1
                continue

            if tactic_class >= 0:
                stats["labeled"] += 1
                stats[f"class_{tactic_class}"] += 1
                if prev_kept_graph is not None and int(prev_kept_graph.y.item()) != tactic_class:
                    graph.change_label = torch.tensor([1.0], dtype=torch.float32)
                    stats["change_positive"] += 1
            else:
                stats["unlabeled_kept"] += 1

            prev_kept_graph = graph
            graphs.append(graph)

        del tags
        gc.collect()

    stats["graphs"] = len(graphs)
    return graphs, dict(stats)


def make_class_weights(labels: list[int], n_classes: int) -> torch.Tensor:
    counts = Counter(labels)
    total = max(sum(counts.values()), 1)
    weights = torch.ones(n_classes, dtype=torch.float32)
    for class_idx in range(n_classes):
        count = counts.get(class_idx, 0)
        if count > 0:
            weights[class_idx] = total / (len(counts) * count)
    return weights


def make_sampler(labels: list[int]) -> torch.utils.data.WeightedRandomSampler:
    counts = Counter(labels)
    sample_weights = [1.0 / counts[label] for label in labels]
    return torch.utils.data.WeightedRandomSampler(
        weights=torch.tensor(sample_weights, dtype=torch.double),
        num_samples=len(sample_weights),
        replacement=True,
    )


class SharedGATBackbone(nn.Module):
    def __init__(self, in_dim: int, hidden_dim: int, heads: int = 4, edge_dim: int = EDGE_IN_DIM, dropout: float = 0.25):
        super().__init__()
        self.input_norm = nn.BatchNorm1d(in_dim)
        self.conv1 = GATv2Conv(in_dim, hidden_dim, heads=heads, edge_dim=edge_dim, concat=True, dropout=dropout)
        self.norm1 = nn.LayerNorm(hidden_dim * heads)
        self.conv2 = GATv2Conv(hidden_dim * heads, hidden_dim, heads=1, edge_dim=edge_dim, concat=False, dropout=dropout)
        self.norm2 = nn.LayerNorm(hidden_dim)
        self.res_proj = nn.Linear(in_dim, hidden_dim)
        self.dropout = dropout

    def forward(self, x, edge_index, edge_attr, batch):
        x0 = self.input_norm(x)
        h = self.conv1(x0, edge_index, edge_attr)
        h = F.dropout(F.elu(self.norm1(h)), p=self.dropout, training=self.training)
        h = self.conv2(h, edge_index, edge_attr)
        h = F.dropout(F.elu(self.norm2(h)), p=self.dropout, training=self.training)
        node_emb = h + self.res_proj(x0)
        graph_emb = torch.cat([global_mean_pool(node_emb, batch), global_max_pool(node_emb, batch)], dim=-1)
        return node_emb, graph_emb


class TaskAdapter(nn.Module):
    def __init__(self, in_dim: int, out_dim: int):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(in_dim, out_dim), nn.GELU(), nn.LayerNorm(out_dim))

    def forward(self, x):
        return self.net(x)


class LearnableComplementarity(nn.Module):
    def __init__(self, init_matrix: np.ndarray):
        super().__init__()
        init_tensor = torch.tensor(init_matrix, dtype=torch.float32).clamp(0.01, 0.99)
        self.logits = nn.Parameter(torch.log(init_tensor / (1.0 - init_tensor)))

    def forward(self, pos_i: torch.Tensor, pos_j: torch.Tensor, distance: torch.Tensor) -> torch.Tensor:
        return torch.sigmoid(self.logits)[pos_i, pos_j] * torch.exp(-distance)


class LinkPredictionHead(nn.Module):
    def __init__(self, emb_dim: int, dropout: float = 0.25):
        super().__init__()
        self.complementarity = LearnableComplementarity(COMPLEMENTARITY_INIT)
        self.adapter = TaskAdapter(emb_dim, emb_dim)
        self.mlp = nn.Sequential(
            nn.Linear(emb_dim * 2, emb_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(emb_dim, emb_dim // 2),
            nn.GELU(),
            nn.Linear(emb_dim // 2, 1),
        )

    def forward(
        self,
        node_emb: torch.Tensor,
        pairs: torch.Tensor,
        pos_indices: torch.Tensor | None = None,
        distances: torch.Tensor | None = None,
    ) -> torch.Tensor:
        if pairs.numel() == 0:
            return torch.zeros(0, device=node_emb.device)
        adapted = self.adapter(node_emb)
        emb_score = torch.sigmoid(self.mlp(torch.cat([adapted[pairs[:, 0]], adapted[pairs[:, 1]]], dim=-1))).squeeze(-1)
        if pos_indices is None or distances is None:
            return emb_score
        comp_score = self.complementarity(pos_indices[pairs[:, 0]], pos_indices[pairs[:, 1]], distances)
        return 0.7 * emb_score + 0.3 * comp_score


class TacticClassificationHead(nn.Module):
    def __init__(self, graph_dim: int, num_classes: int, dropout: float = 0.25):
        super().__init__()
        hidden = graph_dim // 2
        self.adapter = TaskAdapter(graph_dim, hidden)
        self.mlp = nn.Sequential(
            nn.Linear(hidden, hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, num_classes),
        )

    def forward(self, graph_emb: torch.Tensor) -> torch.Tensor:
        return self.mlp(self.adapter(graph_emb))


class ChangeDetectionHead(nn.Module):
    def __init__(self, graph_dim: int, dropout: float = 0.25):
        super().__init__()
        self.adapter = TaskAdapter(graph_dim * 3, graph_dim)
        self.mlp = nn.Sequential(
            nn.Linear(graph_dim, graph_dim // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(graph_dim // 2, 1),
        )

    def forward(self, current_graph_emb: torch.Tensor, prev_graph_emb: torch.Tensor) -> torch.Tensor:
        fused = torch.cat([current_graph_emb, prev_graph_emb, current_graph_emb - prev_graph_emb], dim=-1)
        return self.mlp(self.adapter(fused))


class TacticalGNN(nn.Module):
    def __init__(
        self,
        node_in_dim: int = NODE_IN_DIM,
        hidden_dim: int = 96,
        num_classes: int = NUM_TACTIC_CLASSES,
        num_families: int = 4,
        gat_heads: int = 4,
        edge_dim: int = EDGE_IN_DIM,
        dropout: float = 0.25,
    ):
        super().__init__()
        graph_dim = hidden_dim * 2
        self.backbone = SharedGATBackbone(node_in_dim, hidden_dim, heads=gat_heads, edge_dim=edge_dim, dropout=dropout)
        self.temporal_gru = nn.GRU(graph_dim, graph_dim, batch_first=True)
        self.temporal_norm = nn.LayerNorm(graph_dim)
        self.link_head = LinkPredictionHead(hidden_dim, dropout=dropout)
        self.tactic_head = TacticClassificationHead(graph_dim, num_classes, dropout=dropout)
        self.coarse_head = TacticClassificationHead(graph_dim, num_families, dropout=dropout)
        self.change_head = ChangeDetectionHead(graph_dim, dropout=dropout)

    @staticmethod
    def _prev_batch(prev_num_nodes: torch.Tensor) -> torch.Tensor:
        counts = prev_num_nodes.view(-1).to(torch.long)
        return torch.repeat_interleave(torch.arange(counts.size(0), device=counts.device), counts)

    def forward(self, data: TacticalData) -> dict[str, torch.Tensor]:
        node_emb, graph_emb = self.backbone(data.x, data.edge_index, data.edge_attr, data.batch)
        prev_batch = self._prev_batch(data.prev_num_nodes)
        _, prev_graph_emb = self.backbone(data.prev_x, data.prev_edge_index, data.prev_edge_attr, prev_batch)
        prev2_batch = self._prev_batch(data.prev2_num_nodes)
        _, prev2_graph_emb = self.backbone(data.prev2_x, data.prev2_edge_index, data.prev2_edge_attr, prev2_batch)

        temporal_seq = torch.stack([prev2_graph_emb, prev_graph_emb, graph_emb], dim=1)
        _, hidden = self.temporal_gru(temporal_seq)
        temporal_graph_emb = self.temporal_norm(hidden[-1] + graph_emb)

        tactic_logits = self.tactic_head(temporal_graph_emb)
        coarse_logits = self.coarse_head(temporal_graph_emb)
        change_logits = self.change_head(graph_emb, prev_graph_emb)
        link_scores = torch.zeros(0, device=node_emb.device)
        if hasattr(data, "link_pairs") and data.link_pairs.numel() > 0:
            pos_indices = data.x[:, 6:11].argmax(dim=1)
            pairs = data.link_pairs
            distances = torch.norm(data.x[pairs[:, 0], :2] - data.x[pairs[:, 1], :2], dim=1)
            link_scores = self.link_head(node_emb, pairs, pos_indices, distances)

        return {
            "tactic_logits": tactic_logits,
            "coarse_logits": coarse_logits,
            "change_logits": change_logits,
            "link_scores": link_scores,
        }


@dataclass
class EpochMetrics:
    loss: float
    acc: float
    macro_f1: float
    weighted_f1: float
    link_mse: float
    report: str
    labels: list[int]
    preds: list[int]


def run_epoch(
    model: TacticalGNN,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer | None,
    scaler: GradScaler,
    device: torch.device,
    ce_loss: nn.Module,
    coarse_loss_fn: nn.Module,
    coarse_weight: float,
    link_weight: float,
    change_weight: float,
    change_loss: nn.Module,
    grad_clip: float,
    idx_to_tactic: dict[int, str],
    fine_to_coarse: dict[int, int],
) -> EpochMetrics:
    is_train = optimizer is not None
    model.train(mode=is_train)

    total_loss = 0.0
    total_graphs = 0
    total_link_loss = 0.0
    total_link_count = 0
    all_labels: list[int] = []
    all_preds: list[int] = []

    for batch in loader:
        batch = batch.to(device)
        if is_train:
            optimizer.zero_grad(set_to_none=True)

        with autocast(device_type=device.type, enabled=device.type == "cuda"):
            outputs = model(batch)
            tactic_targets = batch.y.view(-1)
            coarse_targets = batch.coarse_y.view(-1)
            tactic_loss = ce_loss(outputs["tactic_logits"], tactic_targets)
            coarse_loss = coarse_loss_fn(outputs["coarse_logits"], coarse_targets)

            link_loss = torch.tensor(0.0, device=device)
            if outputs["link_scores"].numel() > 0:
                link_loss = F.smooth_l1_loss(outputs["link_scores"], batch.link_labels.to(device))

            current_change_weight = change_weight
            change_term = torch.tensor(0.0, device=device)
            if change_weight > 0.0 and batch.has_prev.view(-1).sum().item() > 0:
                mask = batch.has_prev.view(-1) > 0
                change_logits = outputs["change_logits"].view(-1)[mask]
                change_targets = batch.change_label.view(-1)[mask]
                if change_targets.numel() > 0:
                    change_term = change_loss(change_logits, change_targets)
                else:
                    current_change_weight = 0.0

            loss = tactic_loss + coarse_weight * coarse_loss + link_weight * link_loss + current_change_weight * change_term

        if is_train:
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
            scaler.step(optimizer)
            scaler.update()

        combined_logits = outputs["tactic_logits"].clone()
        coarse_log_probs = F.log_softmax(outputs["coarse_logits"], dim=-1)
        for fine_idx, coarse_idx in fine_to_coarse.items():
            combined_logits[:, fine_idx] += 0.35 * coarse_log_probs[:, coarse_idx]
        preds = combined_logits.argmax(dim=1)
        all_labels.extend(tactic_targets.detach().cpu().tolist())
        all_preds.extend(preds.detach().cpu().tolist())

        batch_graphs = batch.num_graphs
        total_loss += float(loss.detach().cpu()) * batch_graphs
        total_graphs += batch_graphs

        if outputs["link_scores"].numel() > 0:
            batch_link_mse = F.mse_loss(outputs["link_scores"], batch.link_labels.to(device))
            total_link_loss += float(batch_link_mse.detach().cpu()) * int(outputs["link_scores"].numel())
            total_link_count += int(outputs["link_scores"].numel())

    label_space = sorted(set(all_labels) | set(all_preds))
    report = classification_report(
        all_labels,
        all_preds,
        labels=label_space,
        target_names=[idx_to_tactic.get(idx, f"class_{idx}") for idx in label_space],
        zero_division=0,
    )
    return EpochMetrics(
        loss=total_loss / max(total_graphs, 1),
        acc=float(np.mean(np.array(all_preds) == np.array(all_labels))) if all_labels else 0.0,
        macro_f1=f1_score(all_labels, all_preds, average="macro", zero_division=0) if all_labels else 0.0,
        weighted_f1=f1_score(all_labels, all_preds, average="weighted", zero_division=0) if all_labels else 0.0,
        link_mse=total_link_loss / max(total_link_count, 1),
        report=report,
        labels=all_labels,
        preds=all_preds,
    )


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def serialize_config(config) -> dict:
    payload = {}
    for key, value in vars(config).items():
        payload[key] = str(value) if isinstance(value, Path) else value
    return payload


def summarize_compact_distribution(name: str, labels: list[int], idx_to_tactic: dict[int, str]) -> str:
    if not labels:
        return f"{name}: empty"
    counts = Counter(labels)
    parts = [f"{idx_to_tactic.get(label, str(label))}={count}" for label, count in sorted(counts.items())]
    return f"{name}: " + ", ".join(parts)


def remap_labels(
    graph_groups: list[list[TacticalData]],
) -> tuple[dict[int, int], dict[int, str], dict[int, str], dict[int, int]]:
    active_labels = sorted(
        {
            int(graph.y.item())
            for graphs in graph_groups
            for graph in graphs
        }
    )
    original_to_compact = {original: compact for compact, original in enumerate(active_labels)}
    compact_to_name = {compact: IDX_TO_TACTIC.get(original, f"class_{original}") for original, compact in original_to_compact.items()}
    active_families = sorted(
        {
            int(graph.coarse_y.item())
            for graphs in graph_groups
            for graph in graphs
        }
    )
    family_to_compact = {original: compact for compact, original in enumerate(active_families)}
    compact_to_family = {compact: IDX_TO_FAMILY.get(original, f"family_{original}") for original, compact in family_to_compact.items()}
    fine_to_coarse: dict[int, int] = {}

    for graphs in graph_groups:
        for graph in graphs:
            original = int(graph.y.item())
            original_family = int(graph.coarse_y.item())
            graph.y = torch.tensor([original_to_compact[original]], dtype=torch.long)
            graph.coarse_y = torch.tensor([family_to_compact[original_family]], dtype=torch.long)
            fine_to_coarse[original_to_compact[original]] = family_to_compact[original_family]

    return original_to_compact, compact_to_name, compact_to_family, fine_to_coarse


def make_tempered_class_weights(labels: list[int]) -> torch.Tensor:
    counts = Counter(labels)
    n_classes = max(max(labels, default=-1) + 1, 1)
    total = max(sum(counts.values()), 1)
    weights = torch.ones(n_classes, dtype=torch.float32)

    for class_idx, count in counts.items():
        raw = np.sqrt(total / max(count, 1))
        weights[class_idx] = float(min(max(raw, 1.0), 3.0))

    weights = weights / weights.mean().clamp(min=1e-8)
    return weights


def main() -> None:
    args = parse_args()
    set_seed(args.seed)

    device = choose_device()
    use_amp = device.type == "cuda"
    scaler = GradScaler(device="cuda", enabled=use_amp)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    match_dirs = sorted([path for path in args.aihub_dir.iterdir() if path.is_dir()])
    if args.max_matches > 0:
        match_dirs = match_dirs[: args.max_matches]

    print(f"Device: {device}")
    print(f"Match directories: {len(match_dirs)}")

    matches = []
    for match_dir in tqdm(match_dirs, desc="Loading metadata"):
        meta = load_match_meta(match_dir)
        if meta is not None:
            matches.append(meta)

    if len(matches) < 10:
        raise RuntimeError(f"Not enough valid matches to train: {len(matches)}")

    train_matches, test_matches = safe_split(matches, args.test_size, args.seed)
    train_matches, val_matches = safe_split(train_matches, args.val_size, args.seed)

    print(f"Train matches: {len(train_matches)}, Val matches: {len(val_matches)}, Test matches: {len(test_matches)}")
    print(summarize_distribution("Train dominant tactics", [m.dominant_class for m in train_matches]))
    print(summarize_distribution("Val dominant tactics", [m.dominant_class for m in val_matches]))
    print(summarize_distribution("Test dominant tactics", [m.dominant_class for m in test_matches]))

    train_graphs, train_stats = build_graphs(train_matches, sample_rate=args.sample_rate, labeled_only=True)
    val_graphs, val_stats = build_graphs(val_matches, sample_rate=args.sample_rate, labeled_only=True)
    test_graphs, test_stats = build_graphs(test_matches, sample_rate=args.sample_rate, labeled_only=True)

    if not train_graphs or not val_graphs or not test_graphs:
        raise RuntimeError("One of the splits is empty after graph construction.")

    print(f"Train graphs: {len(train_graphs)}, Val graphs: {len(val_graphs)}, Test graphs: {len(test_graphs)}")
    print(f"Train stats: {train_stats}")
    print(f"Val stats: {val_stats}")
    print(f"Test stats: {test_stats}")

    _, compact_idx_to_tactic, compact_idx_to_family, fine_to_coarse = remap_labels([train_graphs, val_graphs, test_graphs])

    train_labels = [int(graph.y.item()) for graph in train_graphs]
    val_labels = [int(graph.y.item()) for graph in val_graphs]
    test_labels = [int(graph.y.item()) for graph in test_graphs]

    print("Compact label space:", compact_idx_to_tactic)
    print("Compact family space:", compact_idx_to_family)
    print(summarize_compact_distribution("Train labels", train_labels, compact_idx_to_tactic))
    print(summarize_compact_distribution("Val labels", val_labels, compact_idx_to_tactic))
    print(summarize_compact_distribution("Test labels", test_labels, compact_idx_to_tactic))

    class_weights = make_tempered_class_weights(train_labels).to(device)

    train_loader = DataLoader(
        train_graphs,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=use_amp,
    )
    val_loader = DataLoader(
        val_graphs,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=use_amp,
    )
    test_loader = DataLoader(
        test_graphs,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=use_amp,
    )

    train_change_positives = sum(int(graph.change_label.item()) for graph in train_graphs)
    effective_change_weight = args.change_weight
    if train_change_positives < args.min_change_positives:
        effective_change_weight = 0.0

    model = TacticalGNN(
        hidden_dim=args.hidden_dim,
        gat_heads=args.gat_heads,
        dropout=args.dropout,
        num_classes=len(compact_idx_to_tactic),
        num_families=len(compact_idx_to_family),
    ).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(optimizer, T_0=10, T_mult=2)

    ce_loss = nn.CrossEntropyLoss(weight=class_weights, label_smoothing=args.label_smoothing)
    coarse_loss = nn.CrossEntropyLoss(label_smoothing=min(args.label_smoothing, 0.02))
    if train_change_positives > 0:
        neg = max(len(train_graphs) - train_change_positives, 1)
        pos_weight = torch.tensor([neg / max(train_change_positives, 1)], dtype=torch.float32, device=device)
    else:
        pos_weight = torch.tensor([1.0], dtype=torch.float32, device=device)
    change_loss = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    history: list[dict[str, float]] = []
    best_metric = -1.0
    best_epoch = 0
    patience_left = args.patience
    checkpoint_path = args.output_dir / "best_tactical_gnn_real_improved.pt"

    print(f"Model parameters: {sum(parameter.numel() for parameter in model.parameters()):,}")
    print(f"Change positives in train: {train_change_positives}, change_weight={effective_change_weight:.3f}")

    start_time = time.time()
    for epoch in range(1, args.epochs + 1):
        train_metrics = run_epoch(
            model=model,
            loader=train_loader,
            optimizer=optimizer,
            scaler=scaler,
            device=device,
            ce_loss=ce_loss,
            coarse_loss_fn=coarse_loss,
            coarse_weight=args.coarse_weight,
            link_weight=args.link_weight,
            change_weight=effective_change_weight,
            change_loss=change_loss,
            grad_clip=args.grad_clip,
            idx_to_tactic=compact_idx_to_tactic,
            fine_to_coarse=fine_to_coarse,
        )
        val_metrics = run_epoch(
            model=model,
            loader=val_loader,
            optimizer=None,
            scaler=scaler,
            device=device,
            ce_loss=ce_loss,
            coarse_loss_fn=coarse_loss,
            coarse_weight=args.coarse_weight,
            link_weight=args.link_weight,
            change_weight=effective_change_weight,
            change_loss=change_loss,
            grad_clip=args.grad_clip,
            idx_to_tactic=compact_idx_to_tactic,
            fine_to_coarse=fine_to_coarse,
        )
        scheduler.step()

        history.append(
            {
                "epoch": epoch,
                "train_loss": train_metrics.loss,
                "train_acc": train_metrics.acc,
                "train_macro_f1": train_metrics.macro_f1,
                "val_loss": val_metrics.loss,
                "val_acc": val_metrics.acc,
                "val_macro_f1": val_metrics.macro_f1,
                "val_weighted_f1": val_metrics.weighted_f1,
                "train_link_mse": train_metrics.link_mse,
                "val_link_mse": val_metrics.link_mse,
            }
        )

        selection_score = 0.5 * (val_metrics.macro_f1 + val_metrics.weighted_f1)
        improved = selection_score > best_metric + 1e-4
        if improved:
            best_metric = selection_score
            best_epoch = epoch
            patience_left = args.patience
            torch.save(
                {
                    "model_state": model.state_dict(),
                    "args": serialize_config(args),
                    "best_epoch": best_epoch,
                    "best_val_score": best_metric,
                    "class_weights": class_weights.detach().cpu(),
                    "idx_to_tactic": compact_idx_to_tactic,
                    "idx_to_family": compact_idx_to_family,
                    "fine_to_coarse": fine_to_coarse,
                },
                checkpoint_path,
            )
        else:
            patience_left -= 1

        print(
            f"Epoch {epoch:03d} | "
            f"train acc/f1 {train_metrics.acc:.3f}/{train_metrics.macro_f1:.3f} | "
            f"val acc/f1/wf1 {val_metrics.acc:.3f}/{val_metrics.macro_f1:.3f}/{val_metrics.weighted_f1:.3f} | "
            f"val link {val_metrics.link_mse:.4f} | "
            f"best {best_metric:.3f} (epoch {best_epoch}) | "
            f"patience {patience_left}"
        )

        if patience_left <= 0:
            print(f"Early stopping at epoch {epoch}")
            break

    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
    model.load_state_dict(checkpoint["model_state"])

    test_metrics = run_epoch(
        model=model,
        loader=test_loader,
        optimizer=None,
        scaler=scaler,
        device=device,
        ce_loss=ce_loss,
        coarse_loss_fn=coarse_loss,
        coarse_weight=args.coarse_weight,
        link_weight=args.link_weight,
        change_weight=effective_change_weight,
        change_loss=change_loss,
        grad_clip=args.grad_clip,
        idx_to_tactic=compact_idx_to_tactic,
        fine_to_coarse=fine_to_coarse,
    )

    elapsed = time.time() - start_time
    print("\n=== Final Test ===")
    print(f"Accuracy: {test_metrics.acc:.4f}")
    print(f"Macro F1: {test_metrics.macro_f1:.4f}")
    print(f"Weighted F1: {test_metrics.weighted_f1:.4f}")
    print(f"Link MSE: {test_metrics.link_mse:.4f}")
    print("\n=== Classification Report ===")
    print(test_metrics.report)

    save_json(
        args.output_dir / "training_summary.json",
        {
            "device": str(device),
            "used_amp": use_amp,
            "elapsed_sec": elapsed,
            "best_epoch": best_epoch,
            "best_val_score": best_metric,
            "test_accuracy": test_metrics.acc,
            "test_macro_f1": test_metrics.macro_f1,
            "test_weighted_f1": test_metrics.weighted_f1,
            "test_link_mse": test_metrics.link_mse,
            "train_stats": train_stats,
            "val_stats": val_stats,
            "test_stats": test_stats,
            "train_distribution": Counter(train_labels),
            "val_distribution": Counter(val_labels),
            "test_distribution": Counter(test_labels),
            "history": history,
            "classification_report": test_metrics.report,
        },
    )
    print(f"Saved checkpoint to: {checkpoint_path}")
    print(f"Saved summary to: {args.output_dir / 'training_summary.json'}")


if __name__ == "__main__":
    main()
