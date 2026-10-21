'use client'

import { createContext, useContext, useEffect, useRef, useState, ReactNode, MouseEvent, KeyboardEvent } from 'react'
import { cn } from '@/lib/utils'
import { ChevronDown, Check } from 'lucide-react'

interface DropdownMenuContextType {
  open: boolean
  setOpen: (open: boolean) => void
  triggerRef: React.RefObject<HTMLButtonElement | null>
  contentRef: React.RefObject<HTMLDivElement | null>
}

const DropdownMenuContext = createContext<DropdownMenuContextType | null>(null)

function useDropdownMenu() {
  const context = useContext(DropdownMenuContext)
  if (!context) {
    throw new Error('DropdownMenu components must be used within DropdownMenu')
  }
  return context
}

export function DropdownMenu({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const contentRef = useRef<HTMLDivElement>(null)

  return (
    <DropdownMenuContext.Provider value={{ open, setOpen, triggerRef, contentRef }}>
      <div className="relative inline-block">{children}</div>
    </DropdownMenuContext.Provider>
  )
}

export function DropdownMenuTrigger({ children, className, ...props }: { children: ReactNode; className?: string } & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const { open, setOpen, triggerRef } = useDropdownMenu()

  const handleClick = (e: MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation()
    setOpen(!open)
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLButtonElement>) => {
    if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown') {
      e.preventDefault()
      setOpen(true)
    }
  }

  return (
    <button
      ref={triggerRef}
      type="button"
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      aria-haspopup="true"
      aria-expanded={open}
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-md bg-background px-3 py-2 text-sm font-medium ring-offset-background transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
        className
      )}
      {...props}
    >
      {children}
      <ChevronDown className={cn('h-4 w-4 transition-transform', open && 'rotate-180')} />
    </button>
  )
}

export function DropdownMenuContent({ children, className, ...props }: { children: ReactNode; className?: string } & React.HTMLAttributes<HTMLDivElement>) {
  const { open, setOpen, contentRef } = useDropdownMenu()

  useEffect(() => {
    if (!open) return
    const handleClickOutside = (event: globalThis.MouseEvent) => {
      if (contentRef.current && !contentRef.current.contains(event.target as Node)) setOpen(false)
    }
    const handleKeyDown = (event: globalThis.KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [open, setOpen, contentRef])

  if (!open) return null

  return (
    <div
      ref={contentRef}
      className={cn(
        'z-50 min-w-[8rem] origin-top-right rounded-md bg-popover p-1 text-popover-foreground shadow-lg border animate-in fade-in-0 zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

export function DropdownMenuItem({ children, className, onClick, disabled, ...props }: { children: ReactNode; className?: string; onClick?: () => void; disabled?: boolean } & React.HTMLAttributes<HTMLDivElement>) {
  const { setOpen } = useDropdownMenu()

  const handleClick = () => {
    if (!disabled && onClick) {
      onClick()
    }
    setOpen(false)
  }

  return (
    <div
      onClick={handleClick}
      role="menuitem"
      tabIndex={-1}
      aria-disabled={disabled}
      className={cn(
        'relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

export function DropdownMenuLabel({ children, className, ...props }: { children: ReactNode; className?: string } & React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('px-2 py-1.5 text-sm font-semibold', className)} {...props}>
      {children}
    </div>
  )
}

export function DropdownMenuSeparator({ className, ...props }: { className?: string } & React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('-mx-1 my-1 h-px bg-border', className)} {...props} />
}

export function DropdownMenuCheckboxItem({ children, className, checked, onCheckedChange, ...props }: { children: ReactNode; className?: string; checked: boolean; onCheckedChange: (checked: boolean) => void } & React.HTMLAttributes<HTMLDivElement>) {
  const { setOpen } = useDropdownMenu()

  const handleClick = () => {
    onCheckedChange(!checked)
    setOpen(false)
  }

  return (
    <div
      onClick={handleClick}
      role="menuitemcheckbox"
      aria-checked={checked}
      tabIndex={-1}
      className={cn(
        'relative flex cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none transition-colors focus:bg-accent focus:text-accent-foreground',
        className
      )}
      {...props}
    >
      <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
        {checked && <Check className="h-4 w-4" />}
      </span>
      {children}
    </div>
  )
}
