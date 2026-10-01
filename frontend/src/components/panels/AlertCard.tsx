import { useEffect } from 'react'
import { GlassPanel, PanelTitle } from '../ui/GlassPanel'
import { LANGUAGES, alertText, languagesFor, type LangCode } from '../../lib/alerts'
import { CATEGORY_LABELS, LEVEL_STYLES, formatPeople } from '../../lib/format'
import type { SpeechFallback } from '../../hooks/useSpeech'
import type { Threat } from '../../types/forecast'

interface AlertCardProps {
  threat: Threat
  date: string
  lang: LangCode
  onLang: (lang: LangCode) => void
  speaking: boolean
  canSpeak: (speechLang: string) => boolean
  speechSupported: boolean
  onSpeak: (text: string, speechLang: string, fallback?: SpeechFallback) => void
  onPrefetch: (text: string, speechLang: string) => void
  onStop: () => void
  onDispatch: () => void
  onClose: () => void
}

export function AlertCard(props: AlertCardProps) {
  const { threat, date, lang, speaking } = props
  const options = languagesFor(threat.state)
  const active = options.includes(lang) ? lang : options[0]
  const pack = LANGUAGES[active]
  const text = alertText(threat, date, active)
  const voiceAvailable = props.canSpeak(pack.speech)
  // No voice for the regional language: read the English warning instead of staying silent
  const fallback: SpeechFallback = { text: alertText(threat, date, 'en'), lang: LANGUAGES.en.speech }
  const listenLabel = voiceAvailable || active === 'en' ? '🔊 Listen' : '🔊 Listen (English)'
  const listenTitle = !props.speechSupported
    ? 'Speech is not supported in this browser'
    : voiceAvailable
      ? undefined
      : `No ${pack.label} voice installed in this browser; reading the English warning`

  // Generate audio for every language tab as soon as the warning opens (active tab first),
  // so "Listen" plays immediately instead of waiting for the backend
  const { onPrefetch } = props
  useEffect(() => {
    for (const code of [active, ...options.filter((c) => c !== active)]) {
      onPrefetch(alertText(threat, date, code), LANGUAGES[code].speech)
    }
    // options derive from threat.state
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [threat, date, active, onPrefetch])

  return (
    <GlassPanel as="section" label="Public warning" strong className="p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <PanelTitle>Public warning · Impact-based</PanelTitle>
          <p className="mt-1 truncate text-sm font-semibold text-white">
            {threat.district}, {threat.state}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <span className={`rounded-md px-1.5 py-0.5 text-[10px] font-semibold uppercase ring-1 ${LEVEL_STYLES[threat.level]}`}>
            {CATEGORY_LABELS[threat.category]}
          </span>
          <button
            type="button"
            onClick={props.onClose}
            aria-label="Close warning"
            className="rounded-md px-1.5 text-lg leading-none text-slate-400 hover:text-white"
          >
            ×
          </button>
        </div>
      </div>

      <div role="tablist" aria-label="Warning language" className="mt-3 flex flex-wrap gap-1.5">
        {options.map((code) => (
          <button
            key={code}
            type="button"
            role="tab"
            aria-selected={code === active}
            onClick={() => props.onLang(code)}
            className={`rounded-lg px-2.5 py-1 text-xs ring-1 transition-colors ${
              code === active ? 'bg-cyan-400/15 text-cyan-100 ring-cyan-400/40' : 'text-slate-400 ring-white/10 hover:text-white'
            }`}
          >
            {LANGUAGES[code].label}
          </button>
        ))}
      </div>

      <p lang={pack.speech} className="scrollbar-thin mt-3 max-h-32 overflow-y-auto text-[13px] leading-relaxed text-slate-200">
        {text}
      </p>

      <div className="mt-3 flex items-center justify-between gap-3 border-t border-white/10 pt-3">
        <span className="text-xs text-slate-400">
          <span className="font-semibold text-slate-200">{formatPeople(threat.population_exposed)}</span> people in affected area
        </span>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={!props.speechSupported}
            title={listenTitle}
            onClick={() => (speaking ? props.onStop() : props.onSpeak(text, pack.speech, fallback))}
            className="rounded-lg bg-white/5 px-3 py-1.5 text-xs font-medium text-slate-100 ring-1 ring-white/15 hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {speaking ? '■ Stop' : listenLabel}
          </button>
          <button
            type="button"
            onClick={props.onDispatch}
            className="rounded-lg bg-red-500/90 px-3 py-1.5 text-xs font-semibold text-white shadow-lg shadow-red-900/40 hover:bg-red-500"
          >
            Dispatch alert
          </button>
        </div>
      </div>
    </GlassPanel>
  )
}
