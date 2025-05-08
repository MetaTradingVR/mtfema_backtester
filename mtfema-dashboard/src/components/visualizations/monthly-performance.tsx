"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useState } from "react";

interface MonthlyPerformanceProps {
  monthlyReturns: {
    year: number;
    month: number;
    return: number;
  }[];
  title?: string;
}

export function MonthlyPerformance({
  monthlyReturns,
  title = "Monthly Performance"
}: MonthlyPerformanceProps) {
  const availableYears = getAvailableYears(monthlyReturns);
  const [selectedYear, setSelectedYear] = useState<number>(
    availableYears.length > 0 ? Math.max(...availableYears) : new Date().getFullYear()
  );

  const prevYear = () => {
    const prevIndex = availableYears.indexOf(selectedYear) - 1;
    if (prevIndex >= 0) {
      setSelectedYear(availableYears[prevIndex]);
    }
  };

  const nextYear = () => {
    const nextIndex = availableYears.indexOf(selectedYear) + 1;
    if (nextIndex < availableYears.length) {
      setSelectedYear(availableYears[nextIndex]);
    }
  };

  const monthsData = generateMonthsData(monthlyReturns, selectedYear);
  const yearReturn = calculateYearReturn(monthsData);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>{title}</CardTitle>
            <CardDescription>Monthly returns breakdown</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="icon"
              className="h-7 w-7"
              onClick={prevYear}
              disabled={availableYears.indexOf(selectedYear) <= 0}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="text-sm font-medium">{selectedYear}</span>
            <Button
              variant="outline"
              size="icon"
              className="h-7 w-7"
              onClick={nextYear}
              disabled={availableYears.indexOf(selectedYear) >= availableYears.length - 1}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-4 gap-2">
          {monthsData.map((month) => (
            <div
              key={month.month}
              className={`p-3 rounded ${
                getReturnColorClass(month.return)
              }`}
            >
              <div className="text-xs font-medium mb-1">
                {getMonthName(month.month)}
              </div>
              <div className="text-lg font-bold">
                {month.return !== null ? formatReturn(month.return) : "-"}
              </div>
            </div>
          ))}
        </div>
        
        <div className="mt-4 p-3 rounded bg-muted">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium">Year Total</span>
            <span className={`text-lg font-bold ${yearReturn > 0 ? 'text-green-600' : yearReturn < 0 ? 'text-red-600' : ''}`}>
              {formatReturn(yearReturn)}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function getAvailableYears(monthlyReturns: MonthlyPerformanceProps["monthlyReturns"]): number[] {
  const years = monthlyReturns.map(item => item.year);
  return [...new Set(years)].sort((a, b) => a - b);
}

function generateMonthsData(
  monthlyReturns: MonthlyPerformanceProps["monthlyReturns"],
  year: number
): { month: number; return: number | null }[] {
  const months = Array.from({ length: 12 }, (_, i) => ({ 
    month: i + 1, 
    return: null as number | null 
  }));

  monthlyReturns
    .filter(item => item.year === year)
    .forEach(item => {
      if (item.month >= 1 && item.month <= 12) {
        months[item.month - 1].return = item.return;
      }
    });

  return months;
}

function calculateYearReturn(monthsData: { month: number; return: number | null }[]): number {
  // Calculate compound return for the year
  let yearReturn = 1;
  let hasData = false;

  monthsData.forEach(month => {
    if (month.return !== null) {
      yearReturn *= (1 + month.return / 100);
      hasData = true;
    }
  });

  return hasData ? (yearReturn - 1) * 100 : 0;
}

function getMonthName(month: number): string {
  const months = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun", 
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
  ];
  return months[month - 1] || "";
}

function formatReturn(value: number): string {
  return `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function getReturnColorClass(value: number | null): string {
  if (value === null) return "bg-muted";
  if (value > 3) return "bg-green-500/20 text-green-700";
  if (value > 1) return "bg-green-400/20 text-green-600";
  if (value > 0) return "bg-green-300/20 text-green-600";
  if (value === 0) return "bg-muted";
  if (value > -1) return "bg-red-300/20 text-red-600";
  if (value > -3) return "bg-red-400/20 text-red-600";
  return "bg-red-500/20 text-red-700";
} 