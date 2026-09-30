import type { StoryCaption } from '../../hooks/useStoryMode'
import { GlassPanel } from '../ui/GlassPanel'

export function StoryBar({
  caption,
  onNext,
  onPrev,
  onStop,
}: {
  caption: StoryCaption
  onNext: () => void
  onPrev: () => void
  onStop: () => void
}) {
  return (
    <GlassPanel as="section" label="Guided tour" strong className="overflow-hidden">
      <div key={caption.index} className="appear flex items-start gap-4 px-5 py-3.5">
        <span className="mt-0.5 font-mono text-xs text-cyan-300 tabular-nums">
          {String(caption.index + 1).padStart(2, '0')}/{String(caption.total).padStart(2, '0')}
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-base font-semibold text-white">{caption.title}</p>
          {caption.text && <p className="mt-0.5 text-sm text-slate-300">{caption.text}</p>}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={onPrev}
            disabled={caption.index === 0}
            title="Previous step (Left Arrow ←)"
            className="flex items-center gap-1 rounded-md bg-white/5 px-2.5 py-1 text-xs font-medium text-slate-300 ring-1 ring-white/10 transition-colors hover:bg-white/10 hover:text-white disabled:pointer-events-none disabled:opacity-30 cursor-pointer"
          >
            <span aria-hidden>‹</span>
            <span>Back</span>
          </button>
          <button
            type="button"
            onClick={onNext}
            title="Next step (Right Arrow → or Enter ↵)"
            className="flex items-center gap-1 rounded-md bg-cyan-500/20 px-3 py-1 text-xs font-medium text-cyan-200 ring-1 ring-cyan-400/40 transition-colors hover:bg-cyan-500/30 cursor-pointer"
          >
            <span>{caption.index === caption.total - 1 ? 'Finish' : 'Next'}</span>
            <span aria-hidden>›</span>
          </button>
          <button
            type="button"
            onClick={onStop}
            aria-label="Stop guided tour (Esc)"
            title="Stop tour (Esc)"
            className="rounded-md px-2.5 py-1 text-xs text-slate-400 ring-1 ring-white/10 transition-colors hover:text-white cursor-pointer"
          >
            Esc
          </button>
        </div>
      </div>
      <div className="h-0.5 bg-white/5">
        <div
          key={`bar-${caption.index}`}
          className="h-full bg-cyan-400"
          style={{ animation: `story-progress ${caption.durationMs}ms linear forwards` }}
        />
      </div>
    </GlassPanel>
  )
}
