import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Redthread Investigation',
  description: 'Institutional memory engine for investigations',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0a0a0a] text-gray-100 h-screen w-screen overflow-hidden font-sans">
        {children}
      </body>
    </html>
  )
}
