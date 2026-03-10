"use client";

interface StatusBadgeProps {
  status: "draft" | "published" | "archived" | string;
}

const config: Record<string, { bg: string; text: string; label: string }> = {
  draft: {
    bg: "border border-[#2A2A2A]",
    text: "text-[#6B6B6B]",
    label: "Draft",
  },
  published: {
    bg: "bg-[#00E5A0] text-[#0A0A0A]",
    text: "text-[#0A0A0A]",
    label: "Published",
  },
  archived: {
    bg: "bg-[#1E1E1E]",
    text: "text-[#6B6B6B]",
    label: "Archived",
  },
};

export default function StatusBadge({ status }: StatusBadgeProps) {
  const c = config[status] ?? config.archived;
  return (
    <span
      className={`inline-flex items-center rounded-[2px] px-2.5 py-0.5 text-[12px] font-semibold uppercase tracking-[0.05em] ${c.bg} ${c.text}`}
    >
      {c.label}
    </span>
  );
}
