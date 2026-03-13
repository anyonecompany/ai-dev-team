import { cn } from "@/lib/utils";
import { getConfidenceColor, getConfidenceLabel } from "@/lib/utils/formatters";

interface ConfidenceGaugeProps {
  value: number;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
  showPercentage?: boolean;
}

const sizeConfig = {
  sm: { height: "h-1.5", width: "w-[60px]", font: "text-xs" },
  md: { height: "h-2", width: "w-[100px]", font: "text-sm" },
  lg: { height: "h-3", width: "w-[160px]", font: "text-base" },
};

const colorMap = {
  destructive: "bg-destructive",
  warning: "bg-warning",
  success: "bg-success",
};

export default function ConfidenceGauge({
  value,
  size = "md",
  showLabel = true,
  showPercentage = true,
}: ConfidenceGaugeProps) {
  const color = getConfidenceColor(value);
  const label = getConfidenceLabel(value);
  const config = sizeConfig[size];

  return (
    <div className="flex items-center gap-2">
      <div
        className={cn("rounded-full bg-muted", config.height, config.width)}
        role="meter"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`신뢰도 ${value}%`}
      >
        <div
          className={cn("rounded-full transition-all", config.height, colorMap[color])}
          style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
        />
      </div>
      {showPercentage && (
        <span className={cn("stat-number", config.font)}>{value}%</span>
      )}
      {showLabel && (
        <span className={cn("text-muted-foreground", config.font)}>{label}</span>
      )}
    </div>
  );
}
