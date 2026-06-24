'use client'

import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'

import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
  {
    variants: {
      variant: {
        default:
          'border-transparent bg-primary text-primary-foreground shadow hover:bg-primary/80',
        secondary:
          'border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80',
        destructive:
          'border-transparent bg-destructive text-destructive-foreground shadow hover:bg-destructive/80',
        outline: 'text-foreground',
        success:
          'border-transparent bg-green-500/10 text-green-700 hover:bg-green-500/20',
        warning:
          'border-transparent bg-amber-500/10 text-amber-700 hover:bg-amber-500/20',
        error:
          'border-transparent bg-red-500/10 text-red-700 hover:bg-red-500/20',
        info:
          'border-transparent bg-blue-500/10 text-blue-700 hover:bg-blue-500/20',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
)

export interface StatusBadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {
  icon?: React.ReactNode
  withBorder?: boolean
  children?: React.ReactNode
}

const StatusBadge = React.forwardRef<HTMLDivElement, StatusBadgeProps>(
  ({ className, variant = 'default', icon, withBorder = false, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          badgeVariants({ variant }),
          withBorder && 'border',
          className,
        )}
        {...props}
      >
        {icon && <span className="mr-1.5">{icon}</span>}
        {children}
      </div>
    )
  },
)
StatusBadge.displayName = 'StatusBadge'

export { badgeVariants, StatusBadge }
