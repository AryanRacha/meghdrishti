# 14. State Emblem & Read-Aloud Fixes

## Context & Objectives
1. **Incorrect State Emblem**: The bulletin letterhead used a hand-drawn SVG approximation (ellipses for the bull/horse, simplified lions) that did not resemble the State Emblem of India.
2. **Listen button disabled**: `AlertCard` disabled "Listen" whenever the browser had no voice for the exact warning language. Chrome on Windows ships few or no Indian-language voices, so the button was greyed out for most regional warnings.
3. **Read-aloud silent / not multilingual**: `useSpeech.speak()` resolved immediately with no voice, so the guided tour's "Last-mile warning" step said nothing. Long warnings were also cut off by Chrome.

---

## Technical Implementation

### 1. State Emblem (`frontend/public/emblem-of-india.svg`, `BulletinModal.tsx`)
- Source: Wikimedia Commons `Emblem_of_India.svg` (single-colour vector, includes "सत्यमेव जयते").
- On screen, `StateEmblem` renders it as a CSS `mask` over `bg-current`, so it inherits the letterhead colour (amber).
- In print, `PrintEmblem` renders a plain `<img>`. Masks are background graphics and are dropped when the print dialog's "Background graphics" option is off.

### 2. Backend TTS (`backend/app/services/tts_engine.py`, `backend/app/api/tts.py`)
Brave (and Firefox) expose no Indian-language browser voices, so audio is generated server-side.
- `POST /api/v1/tts` `{text, lang}` → `audio/mpeg` or `audio/wav`. `lang` is one of the 12 `LangCode`s; text is 1–2000 chars.
- **edge-tts** (Microsoft neural voices, online): en, hi, mr, bn, ta, te, kn, ml, gu.
- **Meta MMS-TTS** (`facebook/mms-tts-{asm,pan,ory}`, local VITS on CPU): Assamese, Punjabi, Odia. These have no edge voice.
  - MMS vocabularies have no digits or `.`, so `normalize_for_mms` reads numbers digit by digit, writes "24 hours" as a word, and expands `mm` abbreviations.
  - Models (~145 MB each, Hugging Face cache) are loaded at startup from the local cache only. Uncached models download on first use.
  - Loading and inference share one lock: `transformers` patches torch tensor creation while loading, so overlapping use fails with `narrow(): length must be non-negative`.
- Results are LRU-cached (64 entries). Failures return `503`.
- Dependencies: `edge-tts`, `transformers` (added to `requirements.txt` and `pyproject.toml`; run `uv lock` to refresh `uv.lock`).

### 3. Speech Hook (`frontend/src/hooks/useSpeech.ts`, `frontend/src/api/client.ts`)
- `speak()` fetches backend audio (`fetchSpeech`) and plays it via `HTMLAudioElement`.
- If the backend is unreachable or playback fails, it falls back to browser `speechSynthesis`.
- **Browser voice fallback chain**: exact language → same-script sibling (`mr → hi`, `as → bn`) → caller-supplied `fallback` (the English warning, `en-IN`).
- Stopping or superseding a request aborts its fetch, pauses audio, and resolves its promise, so the guided tour never hangs.
- **Sentence chunking**: text is split on `. ! ? ।` and queued as separate utterances. This avoids Chrome's ~15 s utterance cutoff.
- **GC-safe queue**: utterances are kept in a ref, because Chrome drops `onend` for garbage-collected utterances.
- **Cancel race**: `speak()` is deferred 60 ms after `cancel()`. A request owns the queue, so a stale `onerror` from a cancelled request cannot reset a newer one.
- Exposes `supported` (Web Speech API present) alongside `canSpeak(lang)`.

### 4. Alert Card (`frontend/src/components/panels/AlertCard.tsx`)
- "Listen" is disabled only when the browser has no Web Speech API.
- Without a regional voice, the label shows **"Listen (English)"** and a tooltip explains the fallback.

### 5. Guided Tour (`frontend/src/lib/storyScript.ts`)
- The "Last-mile warning" step passes the English headline as the fallback, so the tour always speaks.

---

## Notes
- Nine languages need internet (edge-tts uses Microsoft's unofficial Read Aloud endpoint). Offline, those languages fall back to browser voices.
- Assamese, Punjabi and Odia work offline once their models are cached.
- Use of the State Emblem is governed by the State Emblem of India (Prohibition of Improper Use) Act, 2005. Here it appears only in a prototype mock-up of an IMD bulletin.
