import type { ReactNode } from 'react'

interface GlassPanelProps {
  children: ReactNode
  className?: string
  as?: 'div' | 'section' | 'aside' | 'header'
  label?: string
  strong?: boolean
}

export function GlassPanel({ children, className = '', as: Tag = 'div', label, strong = false }: GlassPanelProps) {
  return (
    <Tag aria-label={label} className={`${strong ? 'glass-strong' : 'glass'} pointer-events-auto rounded-2xl ${className}`}>
      {children}
    </Tag>
  )
}

export function PanelTitle({ children }: { children: ReactNode }) {
  return <h2 className="text-[11px] font-semibold tracking-[0.14em] text-slate-400 uppercase">{children}</h2>
}
