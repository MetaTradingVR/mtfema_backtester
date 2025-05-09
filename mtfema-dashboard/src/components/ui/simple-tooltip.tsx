"use client"

/**
 * Simple Tooltip Component
 * 
 * A lightweight tooltip implementation that doesn't rely on external dependencies.
 */

import React, { useState, useRef, useEffect } from 'react'
import { cn } from '@/lib/utils'

interface SimpleTooltipProps {
  children: React.ReactNode
  content: React.ReactNode
  side?: 'top' | 'right' | 'bottom' | 'left'
  align?: 'start' | 'center' | 'end'
  className?: string
}

export function SimpleTooltip({
  children,
  content,
  side = 'top',
  align = 'center',
  className
}: SimpleTooltipProps) {
  const [isVisible, setIsVisible] = useState(false)
  const tooltipRef = useRef<HTMLDivElement>(null)
  const triggerRef = useRef<HTMLDivElement>(null)

  // Position calculations
  useEffect(() => {
    if (isVisible && tooltipRef.current && triggerRef.current) {
      const triggerRect = triggerRef.current.getBoundingClientRect()
      const tooltipRect = tooltipRef.current.getBoundingClientRect()
      
      let top = 0
      let left = 0
      
      // Calculate position based on side
      switch (side) {
        case 'top':
          top = triggerRect.top - tooltipRect.height - 8
          break
        case 'bottom':
          top = triggerRect.bottom + 8
          break
        case 'left':
          left = triggerRect.left - tooltipRect.width - 8
          top = triggerRect.top + (triggerRect.height / 2) - (tooltipRect.height / 2)
          break
        case 'right':
          left = triggerRect.right + 8
          top = triggerRect.top + (triggerRect.height / 2) - (tooltipRect.height / 2)
          break
      }
      
      // Adjust horizontal alignment for top/bottom
      if (side === 'top' || side === 'bottom') {
        switch (align) {
          case 'start':
            left = triggerRect.left
            break
          case 'center':
            left = triggerRect.left + (triggerRect.width / 2) - (tooltipRect.width / 2)
            break
          case 'end':
            left = triggerRect.right - tooltipRect.width
            break
        }
      }
      
      // Adjust vertical alignment for left/right
      if (side === 'left' || side === 'right') {
        switch (align) {
          case 'start':
            top = triggerRect.top
            break
          case 'center':
            top = triggerRect.top + (triggerRect.height / 2) - (tooltipRect.height / 2)
            break
          case 'end':
            top = triggerRect.bottom - tooltipRect.height
            break
        }
      }
      
      // Apply position
      tooltipRef.current.style.top = `${top}px`
      tooltipRef.current.style.left = `${left}px`
    }
  }, [isVisible, side, align])

  return (
    <div className="relative inline-block">
      <div
        ref={triggerRef}
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        onClick={() => setIsVisible(!isVisible)}
      >
        {children}
      </div>
      
      {isVisible && (
        <div
          ref={tooltipRef}
          className={cn(
            "absolute z-50 px-3 py-2 text-sm bg-white dark:bg-gray-800 rounded shadow-md border border-gray-200 dark:border-gray-700",
            "animate-in fade-in-0 zoom-in-95",
            className
          )}
          style={{ position: 'fixed' }}
          onMouseEnter={() => setIsVisible(true)}
          onMouseLeave={() => setIsVisible(false)}
        >
          {content}
        </div>
      )}
    </div>
  )
}

export default SimpleTooltip
