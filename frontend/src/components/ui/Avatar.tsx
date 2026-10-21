import { forwardRef, ImgHTMLAttributes, HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

interface AvatarProps extends HTMLAttributes<HTMLDivElement> {}

export const Avatar = forwardRef<HTMLDivElement, AvatarProps>(
  ({ className, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full', className)}
      {...props}
    >
      {children}
    </div>
  )
)
Avatar.displayName = 'Avatar'

export const AvatarImage = forwardRef<HTMLImageElement, ImgHTMLAttributes<HTMLImageElement>>(
  ({ className, ...props }, ref) => (
    <img
      ref={ref}
      className={cn('aspect-square h-full w-full', className)}
      {...props}
    />
  )
)
AvatarImage.displayName = 'AvatarImage'

export const AvatarFallback = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex h-full w-full items-center justify-center rounded-full bg-muted', className)}
      {...props}
    />
  )
)
AvatarFallback.displayName = 'AvatarFallback'