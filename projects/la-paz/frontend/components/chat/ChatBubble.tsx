import { Newspaper, BarChart2, Activity, Paperclip } from "lucide-react";
import { cn } from "@/lib/utils";
import AiDisclaimer from "@/components/shared/AiDisclaimer";
import type { ChatSource } from "@/lib/types/api";

interface ChatBubbleProps {
  role: "user" | "assistant";
  content: string;
  sources?: ChatSource[];
  isStreaming?: boolean;
  timestamp: string;
}

function SourceIcon({ docType }: { docType: string }) {
  switch (docType) {
    case "match_report":
      return <Activity className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />;
    case "player_profile":
    case "team_profile":
    case "league_standing":
      return <BarChart2 className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />;
    case "article":
    case "transfer_news":
      return <Newspaper className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />;
    default:
      return <Paperclip className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />;
  }
}

export default function ChatBubble({
  role,
  content,
  sources,
  isStreaming,
}: ChatBubbleProps) {
  const isUser = role === "user";

  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[85%] rounded-lg p-4 md:max-w-[70%] lg:max-w-[60%]",
          isUser ? "bg-primary text-primary-foreground" : "bg-card border border-border"
        )}
      >
        {!isUser && <AiDisclaimer className="mb-2" />}
        <div className="whitespace-pre-wrap text-sm leading-relaxed">{content}</div>
        {isStreaming && (
          <span
            className="mt-1 inline-block text-muted-foreground"
            aria-label="AI가 답변을 생성 중입니다"
          >
            <span className="animate-typing">...</span>
          </span>
        )}
        {sources && sources.length > 0 && (
          <div className="mt-3 space-y-1.5">
            <p className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
              <Paperclip className="h-3 w-3" aria-hidden="true" />
              Sources:
            </p>
            {sources.slice(0, 5).map((source, i) => (
              <div key={i} className="flex items-center gap-1.5 rounded-sm bg-muted p-1.5 text-xs">
                <SourceIcon docType={source.doc_type} />
                <span className="truncate">{source.title}</span>
              </div>
            ))}
          </div>
        )}
        {!isUser && !isStreaming && (
          <AiDisclaimer variant="disclaimer" className="mt-3" />
        )}
      </div>
    </div>
  );
}
