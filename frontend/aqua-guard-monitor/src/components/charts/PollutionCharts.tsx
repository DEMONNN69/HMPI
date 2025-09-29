import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  LineChart,
  Line,
  ResponsiveContainer,
} from "recharts";

const POLLUTION_COLORS = {
  excellent: "hsl(var(--excellent))",
  good: "hsl(var(--good))",
  poor: "hsl(var(--poor))",
  "very-poor": "hsl(var(--very-poor))",
};

interface QualityData {
  name: string;
  value: number;
  color: string;
  [key: string]: any;
}

interface TrendData {
  date: string;
  average_hpi: number;
  sample_count: number;
}

const chartConfig = {
  excellent: {
    label: "Excellent",
    color: POLLUTION_COLORS.excellent,
  },
  good: {
    label: "Good", 
    color: POLLUTION_COLORS.good,
  },
  poor: {
    label: "Fair",
    color: POLLUTION_COLORS.poor,
  },
  "very-poor": {
    label: "Poor",
    color: POLLUTION_COLORS["very-poor"],
  },
  average_hpi: {
    label: "HPI Index",
    color: "hsl(var(--primary))",
  },
};

export function QualityDistributionChart({ data }: { data: QualityData[] }) {
  const total = data.reduce((sum, item) => sum + item.value, 0);
  
  return (
    <Card className="shadow-professional">
      <CardHeader className="pb-4">
        <CardTitle className="text-heading">Water Quality Distribution</CardTitle>
        <p className="text-caption">Classification of {total.toLocaleString()} monitoring points</p>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig} className="h-[280px]">
          <PieChart>
            <ChartTooltip 
              content={<ChartTooltipContent />}
              formatter={(value: any, name: any) => [
                `${value} sites (${((value / total) * 100).toFixed(1)}%)`,
                name
              ]}
            />
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={90}
              innerRadius={45}
              paddingAngle={2}
            >
              {data.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={entry.color}
                  stroke="hsl(var(--background))"
                  strokeWidth={2}
                />
              ))}
            </Pie>
          </PieChart>
        </ChartContainer>
        
        {/* Legend */}
        <div className="grid grid-cols-2 gap-3 mt-4">
          {data.map((item, index) => (
            <div key={index} className="flex items-center space-x-2">
              <div 
                className="w-3 h-3 rounded-full" 
                style={{ backgroundColor: item.color }}
              />
              <span className="text-body">{item.name}</span>
              <span className="text-caption ml-auto">{item.value}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export function HPIBarChart({ data }: { data: QualityData[] }) {
  return (
    <Card className="shadow-professional">
      <CardHeader className="pb-4">
        <CardTitle className="text-heading">Site Classification Overview</CardTitle>
        <p className="text-caption">Distribution by water quality category</p>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig} className="h-[280px]">
          <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.5} />
            <XAxis 
              dataKey="name" 
              tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
              axisLine={{ stroke: "hsl(var(--border))" }}
            />
            <YAxis 
              tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
              axisLine={{ stroke: "hsl(var(--border))" }}
            />
            <ChartTooltip 
              content={<ChartTooltipContent />}
              formatter={(value: any, name: any) => [`${value} sites`, "Count"]}
            />
            <Bar dataKey="value" radius={[6, 6, 0, 0]} strokeWidth={0}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}

export function HPITrendChart({ data }: { data: TrendData[] }) {
  return (
    <Card className="shadow-professional">
      <CardHeader className="pb-4">
        <CardTitle className="text-heading">Heavy Metal Pollution Trend</CardTitle>
        <p className="text-caption">8-day moving average across monitoring network</p>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig} className="h-[320px]">
          <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
            <XAxis 
              dataKey="date" 
              tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
              axisLine={{ stroke: "hsl(var(--border))" }}
            />
            <YAxis 
              domain={[25, 45]}
              tick={{ fontSize: 12, fill: "hsl(var(--muted-foreground))" }}
              axisLine={{ stroke: "hsl(var(--border))" }}
              label={{ value: 'HPI Index', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle', fontSize: 12, fill: "hsl(var(--muted-foreground))" } }}
            />
            <ChartTooltip 
              content={<ChartTooltipContent />}
              formatter={(value: any, name: any) => [
                `${value} HPI`,
                "Average Index"
              ]}
              labelFormatter={(label) => `Date: ${label}`}
            />
            <Line
              type="monotone"
              dataKey="average_hpi"
              stroke="hsl(var(--primary))"
              strokeWidth={3}
              dot={{ 
                fill: "hsl(var(--primary))", 
                strokeWidth: 2, 
                stroke: "hsl(var(--background))",
                r: 5 
              }}
              activeDot={{ 
                r: 7, 
                stroke: "hsl(var(--primary))", 
                strokeWidth: 2,
                fill: "hsl(var(--primary))"
              }}
            />
          </LineChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}