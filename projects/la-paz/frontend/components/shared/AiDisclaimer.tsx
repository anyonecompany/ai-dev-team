import { cn } from "@/lib/utils";

interface AiDisclaimerProps {
  className?: string;
  variant?: "label" | "disclaimer";
}

export default function AiDisclaimer({ className, variant = "label" }: AiDisclaimerProps) {
  if (variant === "disclaimer") {
    return (
      <p className={cn("text-xs text-muted-foreground", className)}>
        AI 응답은 부정확할 수 있습니다. 중요한 결정에는 공식 자료를 확인하세요.
      </p>
    );
  }

  return (
    <div className={cn("flex items-center gap-1.5 text-xs text-muted-foreground", className)} role="status">
      <span className="inline-block h-1.5 w-1.5 rounded-full bg-primary" />
      AI가 생성한 답변입니다
    </div>
  );
}
