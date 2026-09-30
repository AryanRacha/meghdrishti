import { useCallback, useEffect, useState } from 'react'

const synth: SpeechSynthesis | undefined = typeof window !== 'undefined' ? window.speechSynthesis : undefined

/** Prefer natural/online (neural) voices, e.g. Edge's "Microsoft Swara Online (Natural)". */
function pickVoice(voices: SpeechSynthesisVoice[], lang: string): SpeechSynthesisVoice | undefined {
  const base = lang.split('-')[0]
  const matches = voices.filter((v) => v.lang.replace('_', '-') === lang || v.lang.startsWith(`${base}-`))
  return matches.find((v) => /natural|online|neural/i.test(v.name)) ?? matches[0]
}

export function useSpeech() {
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>(() => synth?.getVoices() ?? [])
  const [speaking, setSpeaking] = useState(false)

  useEffect(() => {
    if (!synth) return
    const load = () => setVoices(synth.getVoices())
    synth.addEventListener('voiceschanged', load)
    return () => {
      synth.removeEventListener('voiceschanged', load)
      synth.cancel()
    }
  }, [])

  const canSpeak = useCallback((lang: string) => pickVoice(voices, lang) !== undefined, [voices])

  const stop = useCallback(() => {
    synth?.cancel()
    setSpeaking(false)
  }, [])

  /** Resolves when speech ends (or immediately if no voice exists for the language). */
  const speak = useCallback(
    (text: string, lang: string): Promise<void> =>
      new Promise((resolve) => {
        const voice = pickVoice(voices, lang)
        if (!synth || !voice) return resolve()
        synth.cancel()
        const utterance = new SpeechSynthesisUtterance(text)
        utterance.voice = voice
        utterance.lang = voice.lang
        utterance.rate = 0.95
        utterance.onend = utterance.onerror = () => {
          setSpeaking(false)
          resolve()
        }
        setSpeaking(true)
        synth.speak(utterance)
      }),
    [voices],
  )

  return { speak, stop, speaking, canSpeak }
}
