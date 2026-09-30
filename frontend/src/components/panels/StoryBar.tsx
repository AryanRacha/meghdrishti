import type { StoryCaption } from '../../hooks/useStoryMode'
import { GlassPanel } from '../ui/GlassPanel'

export function StoryBar({
  caption,
  onNext,
  onStop,
}: {
  caption: StoryCaption
  onNext: () => void
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
            onClick={onNext}
            title="Next step (Enter)"
            className="flex items-center gap-1 rounded-md bg-cyan-500/20 px-2.5 py-1 text-xs font-medium text-cyan-200 ring-1 ring-cyan-400/40 hover:bg-cyan-500/30"
          >
            <span>{caption.index === caption.total - 1 ? 'Finish' : 'Next'}</span>
            <kbd className="font-mono text-[10px] text-cyan-300">↵</kbd>
          </button>
          <button
            type="button"
            onClick={onStop}
            aria-label="Stop guided tour"
            className="rounded-md px-2 py-1 text-xs text-slate-400 ring-1 ring-white/10 hover:text-white"
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
