"use client";

import * as React from "react";
import { useTheme, getActiveTheme } from "@/lib/theme";

interface ThemeProviderProps {
  children: React.ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const { theme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  // Update the theme when the component is mounted
  React.useEffect(() => {
    setMounted(true);
  }, []);

  // Apply the theme class to the document
  React.useEffect(() => {
    if (!mounted) return;
    
    const activeTheme = getActiveTheme(theme);
    
    if (activeTheme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [theme, mounted]);

  return <>{children}</>;
} 