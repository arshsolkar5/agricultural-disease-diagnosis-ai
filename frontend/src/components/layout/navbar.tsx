'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/cn'

const routes = [
  { href: '/', label: 'Home' },
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/diagnosis', label: 'Diagnosis' },
]

export function Navbar() {
  const pathname = usePathname()

  return (
    <nav className="border-b border-gray-200 bg-white sticky top-0 z-50">
      <div className="grid-container flex items-center justify-between py-4">
        <Link href="/" className="text-xl font-bold text-emerald-600">
          AgriSense
        </Link>
        <div className="flex space-x-6 overflow-x-auto">
          {routes.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={cn(
                'text-gray-600 hover:text-gray-900 transition-colors whitespace-nowrap',
                pathname === href && 'font-semibold text-emerald-600'
              )}
            >
              {label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  )
}
