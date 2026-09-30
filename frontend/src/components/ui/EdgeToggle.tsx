interface EdgeToggleProps {
  side: 'left' | 'right'
  open: boolean
  onToggle: () => void
  label: string
  shortcut: string
}

/** Slim tab on the screen edge that slides with its panel. */
export function EdgeToggle({ side, open, onToggle, label, shortcut }: EdgeToggleProps) {
  const position =
    side === 'left' ? (open ? 'left-[21.25rem]' : 'left-2') : open ? 'right-[25.25rem]' : 'right-2'
  const chevron = side === 'left' ? (open ? '‹' : '›') : open ? '›' : '‹'

  return (
    <button
      type="button"
      onClick={onToggle}
      aria-expanded={open}
      aria-label={`${open ? 'Hide' : 'Show'} ${label}`}
      title={`${open ? 'Hide' : 'Show'} ${label} (${shortcut})`}
      className={`glass pointer-events-auto absolute top-1/2 hidden h-16 w-6 -translate-y-1/2 place-items-center rounded-full text-lg text-slate-300 transition-all duration-500 hover:text-white lg:grid ${position}`}
    >
      <span aria-hidden>{chevron}</span>
    </button>
  )
}
