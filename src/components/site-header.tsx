"use client"

import React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Home, BarChart3, LineChart, Activity } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ThemeToggle } from "@/components/ui/theme-toggle"

export function SiteHeader() {
  const pathname = usePathname()

  const navItems = [
    {
      name: "Dashboard",
      href: "/",
      icon: <Home className="h-4 w-4 mr-2" />
    },
    {
      name: "Backtest",
      href: "/backtest",
      icon: <LineChart className="h-4 w-4 mr-2" />
    },
    {
      name: "Optimization",
      href: "/optimization",
      icon: <BarChart3 className="h-4 w-4 mr-2" />
    },
    {
      name: "Live Trading",
      href: "/live-trading",
      icon: <Activity className="h-4 w-4 mr-2" />
    }
  ]

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        <div className="mr-4 flex">
          <Link href="/" className="flex items-center space-x-2">
            <span className="font-bold">MT 9 EMA Backtester</span>
          </Link>
        </div>
        <nav className="flex items-center space-x-2 lg:space-x-4">
          {navItems.map((item) => (
            <Button
              key={item.href}
              variant={pathname === item.href ? "default" : "ghost"}
              asChild
              size="sm"
              className="transition-all duration-100"
            >
              <Link href={item.href}>
                {item.icon}
                {item.name}
              </Link>
            </Button>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-2">
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
} 