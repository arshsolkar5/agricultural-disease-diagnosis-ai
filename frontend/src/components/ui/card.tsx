import { cn } from '@/lib/cn'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'outlined'
}

export function Card({ variant = 'default', className, ...props }: CardProps) {
  return (
    <div
      className={cn(
        'rounded-lg bg-white transition-all duration-200',
        variant === 'default' && 'border border-gray-200 shadow-sm',
        variant === 'outlined' && 'border border-gray-300',
        className
      )}
      {...props}
    />
  )
}
