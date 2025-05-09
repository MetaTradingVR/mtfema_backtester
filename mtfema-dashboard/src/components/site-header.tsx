"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChartBar, GitBranch, Home, Settings, BarChart3 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ui/theme-toggle";

export function SiteHeader() {
  const pathname = usePathname();
  
  const navItems = [
    {
      title: "Dashboard",
      href: "/",
      icon: <Home className="mr-2 h-4 w-4" />,
    },
    {
      title: "Backtest",
      href: "/backtest",
      icon: <ChartBar className="mr-2 h-4 w-4" />,
    },
    {
      title: "Indicators",
      href: "/indicators",
      icon: <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2 h-4 w-4"><path d="M2 12h10"></path><path d="M9 4v16"></path><path d="M3 9l2 2"></path><path d="M3 15l2-2"></path><path d="M14 12h8"></path><path d="M18 16v-8"></path><path d="M21 9l-2 2"></path><path d="M21 15l-2-2"></path></svg>,
    },
    {
      title: "Optimization",
      href: "/optimization",
      icon: <GitBranch className="mr-2 h-4 w-4" />,
    },
    {
      title: "Live Trading",
      href: "/live",
      icon: <BarChart3 className="mr-2 h-4 w-4" />,
    },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        <div className="mr-4 hidden md:flex">
          <Link href="/" className="mr-6 flex items-center space-x-2">
            <span className="hidden font-bold sm:inline-block">
              MT 9 EMA Backtester
            </span>
          </Link>
          <nav className="flex items-center space-x-2 text-sm font-medium">
            {navItems.map((item, index) => (
              <Button
                key={index}
                asChild
                variant={pathname === item.href ? "default" : "ghost"}
                size="sm"
              >
                <Link href={item.href}>
                  {item.icon}
                  {item.title}
                </Link>
              </Button>
            ))}
          </nav>
        </div>
        
        <div className="flex flex-1 items-center justify-between space-x-2 md:justify-end">
          <div className="w-full flex-1 md:w-auto md:flex-none">
            <button className="md:hidden inline-flex h-9 items-center justify-center rounded-md px-3 text-sm font-medium bg-background transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none">
              <Home className="h-4 w-4 mr-2" />
              <span className="sr-only">Menu</span>
            </button>
            <div className="hidden items-center md:flex">
              {/* Add any additional top-right elements here */}
            </div>
          </div>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
} 