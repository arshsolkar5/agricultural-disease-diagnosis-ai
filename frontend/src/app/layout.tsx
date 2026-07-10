import type { Metadata } from 'next'
import { Providers } from '@/components/providers'
import { Navbar } from '@/components/layout/navbar'
import './globals.css'

export const metadata: Metadata = {
  title: 'AgriSense AI',
  description: 'Agricultural disease diagnosis',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head />
      <body className="antialiased" suppressHydrationWarning>
        <Providers>
          <Navbar />
          <main className="min-h-screen bg-white">
            {children}
          </main>
        </Providers>
      </body>
    </html>
  )
}
