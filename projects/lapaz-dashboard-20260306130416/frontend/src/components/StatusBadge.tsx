interface StatusBadgeProps {
  status: "draft" | "published" | "archived" | string;
}

const config: Record<string, { bg: string; text: string; dot: string; label: string }> = {
  draft: { bg: "bg-amber-500/10", text: "text-amber-400", dot: "bg-amber-400", label: "Draft" },
  published: { bg: "bg-emerald-500/10", text: "text-emerald-400", dot: "bg-emerald-400", label: "Published" },
  archived: { bg: "bg-gray-500/10", text: "text-gray-500", dot: "bg-gray-500", label: "Archived" },
};

export default function StatusBadge({ status }: StatusBadgeProps) {
  const c = config[status] ?? config.archived;
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full ${c.bg} px-2.5 py-0.5`}>
      <span className={`h-1.5 w-1.5 rounded-full ${c.dot}`} />
      <span className={`text-[10px] font-semibold uppercase tracking-wider ${c.text}`}>
        {c.label}
      </span>
    </span>
  );
}
