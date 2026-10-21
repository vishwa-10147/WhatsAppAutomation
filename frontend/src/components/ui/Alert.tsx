import { HTMLAttributes, forwardRef } from 'react'
import { cn } from '@/lib/utils'
import { AlertCircle, CheckCircle, Info, AlertTriangle } from 'lucide-react'

interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'destructive' | 'success' | 'info'
}

export const Alert = forwardRef<HTMLDivElement, AlertProps>(
  ({ className, variant = 'default', children, ...props }, ref) => {
    const icons = {
      default: <AlertCircle className="h-4 w-4" />,
      destructive: <AlertTriangle className="h-4 w-4" />,
      success: <CheckCircle className="h-4 w-4" />,
      info: <Info className="h-4 w-4" />,
    }

    const variants = {
      default: 'bg-muted text-foreground border border-border',
      destructive: 'bg-destructive/10 text-destructive border border-destructive/20',
      success: 'bg-green-500/10 text-green-600 dark:text-green-400 border border-green-500/20',
      info: 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20',
    }

    return (
      <div
        ref={ref}
        role="alert"
        className={cn('relative w-full rounded-lg border p-4 [&>svg~*]:pl-7 [&>svg+div]:translate-y-[-3px] [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4', variants[variant], className)}
        {...props}
      >
        {icons[variant]}
        <div className="grid gap-1 [&>p]:leading-normal">
          {children}
        </div>
      </div>
    )
  }
)
Alert.displayName = 'Alert'

export const AlertTitle = forwardRef<HTMLHeadingElement, HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h5 ref={ref} className={cn('mb-1 font-medium leading-none tracking-tight', className)} {...props} />
  )
)
AlertTitle.displayName = 'AlertTitle'

export const AlertDescription = forwardRef<HTMLParagraphElement, HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('text-sm [&_p]:leading-relaxed', className)} {...props} />
  )
)
AlertDescription.displayName = 'AlertDescription'
