interface SegmentedProps<T extends string> {
  label: string
  options: readonly T[]
  value: T
  onChange: (value: T) => void
  renderLabel: (value: T) => string
}

export function Segmented<T extends string>({ label, options, value, onChange, renderLabel }: SegmentedProps<T>) {
  return (
    <div role="group" aria-label={label} className="flex rounded-xl bg-white/5 p-1 ring-1 ring-white/10">
      {options.map((opt) => {
        const active = opt === value
        return (
          <button
            key={opt}
            type="button"
            aria-pressed={active}
            onClick={() => onChange(opt)}
            className={`flex-1 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors focus-visible:outline-2 focus-visible:outline-accent ${
              active ? 'bg-cyan-400/15 text-cyan-200 ring-1 ring-cyan-400/40' : 'text-slate-400 hover:text-slate-100'
            }`}
          >
            {renderLabel(opt)}
          </button>
        )
      })}
    </div>
  )
}
