import { cn } from '@/lib/cn'

interface SpinnerProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'md' | 'lg'
}

export function Spinner({ size = 'md', className, ...props }: SpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4 border-2',
    md: 'h-8 w-8 border-2',
    lg: 'h-12 w-12 border-3',
  }

  return (
    <div
      className={cn(
        'animate-spin rounded-full border-gray-300 border-t-emerald-600',
        sizeClasses[size],
        className
      )}
      {...props}
    />
  )
}
