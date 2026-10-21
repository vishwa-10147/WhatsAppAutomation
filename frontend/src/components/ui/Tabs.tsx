'use client'

import { createContext, useContext, useState, ReactNode, useId } from 'react'
import { cn } from '@/lib/utils'

interface TabsContextType {
  value: string
  onValueChange: (value: string) => void
  baseId: string
}

const TabsContext = createContext<TabsContextType | null>(null)

function useTabs() {
  const context = useContext(TabsContext)
  if (!context) {
    throw new Error('Tabs components must be used within Tabs')
  }
  return context
}

export function Tabs({ children, value, onValueChange, defaultValue }: { children: ReactNode; value?: string; onValueChange?: (value: string) => void; defaultValue?: string }) {
  const [internalValue, setInternalValue] = useState(value || defaultValue || '')
  const baseId = useId()

  const handleValueChange = (newValue: string) => {
    setInternalValue(newValue)
    onValueChange?.(newValue)
  }

  return (
    <TabsContext.Provider value={{ value: internalValue, onValueChange: handleValueChange, baseId }}>
      <div data-tabs>{children}</div>
    </TabsContext.Provider>
  )
}

export function TabsList({ children, className, ...props }: { children: ReactNode; className?: string } & React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      role="tablist"
      aria-orientation="horizontal"
      className={cn('inline-flex h-10 items-center justify-center bg-muted p-1 rounded-md', className)}
      {...props}
    >
      {children}
    </div>
  )
}

export function TabsTrigger({ children, value, className, disabled, ...props }: { children: ReactNode; value: string; className?: string; disabled?: boolean } & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const { value: currentValue, onValueChange, baseId } = useTabs()
  const isActive = currentValue === value

  return (
    <button
      role="tab"
      aria-selected={isActive}
      aria-controls={`${baseId}-panel-${value}`}
      id={`${baseId}-trigger-${value}`}
      data-state={isActive ? 'active' : 'inactive'}
      disabled={disabled}
      onClick={() => !disabled && onValueChange(value)}
      className={cn(
        'inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm',
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
}

export function TabsContent({ children, value, className, forceMount, ...props }: { children: ReactNode; value: string; className?: string; forceMount?: boolean } & React.HTMLAttributes<HTMLDivElement>) {
  const { value: currentValue, baseId } = useTabs()
  const isActive = currentValue === value

  if (!forceMount && !isActive) {
    return null
  }

  return (
    <div
      role="tabpanel"
      aria-labelledby={`${baseId}-trigger-${value}`}
      id={`${baseId}-panel-${value}`}
      data-state={isActive ? 'active' : 'inactive'}
      data-orientation="horizontal"
      className={cn('mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2', className)}
      {...props}
    >
      {isActive && children}
    </div>
  )
}