"use client";

import { useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ChevronDown, Filter, ArrowUpDown, Search, Eye } from "lucide-react";
import { OptimizationResult } from "@/lib/api";

interface ResultsListProps {
  results: OptimizationResult[];
  onSelectResult: (id: string) => void;
}

export function ResultsList({ results, onSelectResult }: ResultsListProps) {
  const [sortField, setSortField] = useState<keyof OptimizationResult["metrics"]>("total_return");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");
  const [searchTerm, setSearchTerm] = useState("");

  // Sort results
  const sortedResults = [...results].sort((a, b) => {
    const aValue = a.metrics[sortField] || 0;
    const bValue = b.metrics[sortField] || 0;
    return sortDirection === "asc" ? aValue - bValue : bValue - aValue;
  });

  // Filter results
  const filteredResults = sortedResults.filter((result) => {
    const searchFields = [
      ...Object.entries(result.params).map(([key, value]) => `${key}:${value}`),
      ...Object.entries(result.metrics).map(([key, value]) => `${key}:${value}`),
    ];
    
    const searchString = searchFields.join(" ").toLowerCase();
    return searchString.includes(searchTerm.toLowerCase());
  });

  // Toggle sort direction
  const toggleSort = (field: keyof OptimizationResult["metrics"]) => {
    if (field === sortField) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("desc"); // Default to descending for new field
    }
  };

  // Get sort icon
  const getSortIcon = (field: keyof OptimizationResult["metrics"]) => {
    if (field !== sortField) return <ArrowUpDown className="h-4 w-4 ml-1" />;
    return (
      <ArrowUpDown 
        className={`h-4 w-4 ml-1 ${sortDirection === "asc" ? "rotate-180" : ""}`} 
      />
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search parameters or metrics..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-8 w-full"
          />
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm">
              <Filter className="h-4 w-4 mr-2" />
              Sort By
              <ChevronDown className="h-4 w-4 ml-2" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Sort By</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => toggleSort("total_return")}>
              Total Return {sortField === "total_return" && (sortDirection === "asc" ? "↑" : "↓")}
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => toggleSort("sharpe_ratio")}>
              Sharpe Ratio {sortField === "sharpe_ratio" && (sortDirection === "asc" ? "↑" : "↓")}
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => toggleSort("win_rate")}>
              Win Rate {sortField === "win_rate" && (sortDirection === "asc" ? "↑" : "↓")}
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => toggleSort("max_drawdown")}>
              Max Drawdown {sortField === "max_drawdown" && (sortDirection === "asc" ? "↑" : "↓")}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <div className="rounded-md border overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[100px]">Rank</TableHead>
              <TableHead>Parameters</TableHead>
              <TableHead className="w-[120px] cursor-pointer" onClick={() => toggleSort("total_return")}>
                Return {getSortIcon("total_return")}
              </TableHead>
              <TableHead className="w-[120px] cursor-pointer" onClick={() => toggleSort("sharpe_ratio")}>
                Sharpe {getSortIcon("sharpe_ratio")}
              </TableHead>
              <TableHead className="w-[120px] cursor-pointer" onClick={() => toggleSort("win_rate")}>
                Win Rate {getSortIcon("win_rate")}
              </TableHead>
              <TableHead className="w-[120px] cursor-pointer" onClick={() => toggleSort("max_drawdown")}>
                Drawdown {getSortIcon("max_drawdown")}
              </TableHead>
              <TableHead className="w-[80px]">View</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredResults.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-4">
                  No results found
                </TableCell>
              </TableRow>
            ) : (
              filteredResults.map((result, index) => (
                <TableRow key={index}>
                  <TableCell className="font-medium">#{index + 1}</TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {Object.entries(result.params).map(([key, value]) => (
                        <Badge key={key} variant="outline">
                          {key}: {value}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell className={result.metrics.total_return > 0 ? "text-green-600" : "text-red-600"}>
                    {result.metrics.total_return.toFixed(2)}%
                  </TableCell>
                  <TableCell>{result.metrics.sharpe_ratio.toFixed(2)}</TableCell>
                  <TableCell>{result.metrics.win_rate.toFixed(1)}%</TableCell>
                  <TableCell className="text-red-600">
                    {result.metrics.max_drawdown.toFixed(2)}%
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onSelectResult(index.toString())}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
      
      <div className="text-sm text-muted-foreground">
        Showing {filteredResults.length} of {results.length} results
      </div>
    </div>
  );
} 