import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface StatsCardProps {
  title: string;
  value: string | number;
  change?: {
    value: string;
    positive: boolean;
  };
  icon?: LucideIcon;
  variant?: "default" | "excellent" | "good" | "poor" | "very-poor";
  description?: string;
  trend?: "up" | "down" | "neutral";
}

const variantStyles = {
  default: "border-border/50",
  excellent: "border-l-4 border-l-excellent border-t-border/50 border-r-border/50 border-b-border/50",
  good: "border-l-4 border-l-good border-t-border/50 border-r-border/50 border-b-border/50", 
  poor: "border-l-4 border-l-poor border-t-border/50 border-r-border/50 border-b-border/50",
  "very-poor": "border-l-4 border-l-very-poor border-t-border/50 border-r-border/50 border-b-border/50",
};

const iconStyles = {
  default: "text-muted-foreground",
  excellent: "text-excellent",
  good: "text-good",
  poor: "text-poor", 
  "very-poor": "text-very-poor",
};

const backgroundStyles = {
  default: "bg-card",
  excellent: "bg-card",
  good: "bg-card",
  poor: "bg-card",
  "very-poor": "bg-card",
};

export function StatsCard({ 
  title, 
  value, 
  change, 
  icon: Icon, 
  variant = "default",
  description,
  trend = "neutral"
}: StatsCardProps) {
  return (
    <Card className={cn(
      "transition-all duration-200 hover:shadow-md relative overflow-hidden",
      variantStyles[variant],
      backgroundStyles[variant]
    )}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <p className="metric-label">{title}</p>
          {Icon && (
            <div className={cn(
              "p-2 rounded-lg bg-muted/30",
              iconStyles[variant]
            )}>
              <Icon className="h-4 w-4" />
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-2">
          <div className="stat-value">{value}</div>
          
          {change && (
            <div className="flex items-center space-x-2">
              <div className={cn(
                "text-xs font-medium px-2 py-1 rounded-full",
                change.positive 
                  ? "text-excellent bg-excellent/10" 
                  : "text-very-poor bg-very-poor/10"
              )}>
                {change.positive ? "+" : ""}{change.value}
              </div>
            </div>
          )}
          
          {description && (
            <p className="text-caption leading-relaxed">
              {description}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}