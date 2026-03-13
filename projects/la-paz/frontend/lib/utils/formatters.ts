export function formatDate(iso: string, locale: string = "ko"): string {
  return new Date(iso).toLocaleDateString(locale === "ko" ? "ko-KR" : "en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatDateTime(iso: string, locale: string = "ko"): string {
  return new Date(iso).toLocaleDateString(locale === "ko" ? "ko-KR" : "en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatRelativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "방금 전";
  if (minutes < 60) return `${minutes}분 전`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}시간 전`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}일 전`;
  return formatDate(iso);
}

export function formatScore(score: number | null): string {
  return score !== null && score !== undefined ? String(score) : "-";
}

export function getConfidenceColor(value: number): "destructive" | "warning" | "success" {
  if (value <= 30) return "destructive";
  if (value <= 60) return "warning";
  return "success";
}

export function getConfidenceLabel(value: number): string {
  if (value <= 30) return "낮음";
  if (value <= 60) return "보통";
  return "높음";
}
