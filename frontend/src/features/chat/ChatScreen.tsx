import { useState, useEffect, useRef } from "react"
import { ask } from "@/api/client"
import type { AskResponse, Lang } from "@/api/types"
import { t } from "@/i18n"
import { AnswerCard } from "./AnswerCard"
import { MicButton, isSpeechRecognitionSupported } from "../voice/MicButton"
import { StatsFooter } from "../stats/StatsFooter"
import "./chat.css"

export function NexaMascot() {
  return (
    <div className="nexa-mascot" role="img" aria-label="NEXA AI Mascot">
      <div className="nexa-mascot__halo" aria-hidden="true" />
      <svg
        className="nexa-mascot__svg"
        viewBox="-120 -90 840 780"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <defs>
          <linearGradient id="orbRingGradBlue" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="var(--c-orb-blue)" />
            <stop offset="50%" stopColor="var(--c-orb-cyan)" />
            <stop offset="100%" stopColor="var(--c-nexa-turquoise)" />
          </linearGradient>

          <linearGradient id="orbRingGradCyan" x1="100%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="var(--c-nexa-turquoise)" />
            <stop offset="45%" stopColor="var(--c-orb-cyan)" />
            <stop offset="100%" stopColor="var(--c-orb-blue)" />
          </linearGradient>

          {/* Figma Glass Effect: Light angle 135°, intensity 35% */}
          <linearGradient id="orbGlassSheen" x1="15%" y1="15%" x2="85%" y2="85%">
            <stop offset="0%" stopColor="var(--c-surface)" stopOpacity="0.35" />
            <stop offset="40%" stopColor="var(--c-surface)" stopOpacity="0.10" />
            <stop offset="75%" stopColor="var(--c-surface)" stopOpacity="0" />
          </linearGradient>

          {/* Figma recipe blur filters */}
          <filter id="orbBlur70" x="-40%" y="-40%" width="180%" height="180%">
            <feGaussianBlur stdDeviation="35" />
          </filter>
          <filter id="orbBlur90" x="-40%" y="-40%" width="180%" height="180%">
            <feGaussianBlur stdDeviation="45" />
          </filter>
          <filter id="orbBlur100" x="-40%" y="-40%" width="180%" height="180%">
            <feGaussianBlur stdDeviation="50" />
          </filter>
          <filter id="orbBlur110" x="-40%" y="-40%" width="180%" height="180%">
            <feGaussianBlur stdDeviation="55" />
          </filter>
          <filter id="orbBlur80" x="-40%" y="-40%" width="180%" height="180%">
            <feGaussianBlur stdDeviation="40" />
          </filter>
          <filter id="orbBlur60" x="-40%" y="-40%" width="180%" height="180%">
            <feGaussianBlur stdDeviation="30" />
          </filter>

          <filter id="orbRingGlow" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="7" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>

          <filter id="orbRingSoft" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="5" />
          </filter>

          {/* Layer 1: Cercul de bază (mască 600 x 600 px) */}
          <clipPath id="orbSphereMask">
            <circle cx="300" cy="300" r="300" />
          </clipPath>
        </defs>

        {/* 3D Орбитальные кольца - задние дуги (за сферой) */}
        <g className="nexa-mascot__rings-back">
          {/* Задняя дуга кольца 1 */}
          <path
            d="M -70 185 C 30 70, 480 320, 670 415"
            stroke="url(#orbRingGradBlue)"
            strokeWidth="22"
            strokeLinecap="round"
            opacity="0.5"
            filter="url(#orbRingSoft)"
          />
          {/* Задняя дуга кольца 2 */}
          <path
            d="M 0 490 C 130 620, 520 220, 600 110"
            stroke="url(#orbRingGradBlue)"
            strokeWidth="20"
            strokeLinecap="round"
            opacity="0.45"
            filter="url(#orbRingSoft)"
          />
        </g>

        {/* 12-слойная переливающаяся сфера по рецепту Figma (Pașii pentru recreare în Figma) */}
        <g className="nexa-mascot__sphere">
          <g clipPath="url(#orbSphereMask)">
            {/* Базовая полупрозрачная основа */}
            <circle cx="300" cy="300" r="300" fill="var(--c-orb-blue)" opacity="0.32" />

            {/* Layer 2: Albastru (75%, Blur: 70px, 380x320 px, sus-stânga) */}
            <ellipse
              className="orb-blob orb-blob--blue"
              cx="220"
              cy="180"
              rx="190"
              ry="160"
              fill="var(--c-orb-blue)"
              opacity="0.75"
              filter="url(#orbBlur70)"
            />

            {/* Layer 3: Cyan (70%, Blur: 90px, 420x360 px, sus-centru) */}
            <ellipse
              className="orb-blob orb-blob--cyan"
              cx="300"
              cy="190"
              rx="210"
              ry="180"
              fill="var(--c-orb-cyan)"
              opacity="0.70"
              filter="url(#orbBlur90)"
            />

            {/* Layer 4: Mov (55%, Blur: 100px, 380x380 px, stânga) */}
            <ellipse
              className="orb-blob orb-blob--purple"
              cx="190"
              cy="290"
              rx="190"
              ry="190"
              fill="var(--c-orb-purple)"
              opacity="0.55"
              filter="url(#orbBlur100)"
            />

            {/* Layer 5: Roz (55%, Blur: 110px, 420x360 px, centru) */}
            <ellipse
              className="orb-blob orb-blob--pink"
              cx="310"
              cy="300"
              rx="210"
              ry="180"
              fill="var(--c-orb-pink)"
              opacity="0.55"
              filter="url(#orbBlur110)"
            />

            {/* Layer 6: Cyan deschis (65%, Blur: 100px, 420x360 px, dreapta) */}
            <ellipse
              className="orb-blob orb-blob--light-cyan"
              cx="410"
              cy="290"
              rx="210"
              ry="180"
              fill="var(--c-orb-light-cyan)"
              opacity="0.65"
              filter="url(#orbBlur100)"
            />

            {/* Layer 7: Galben (45%, Blur: 100px, 320x280 px, dreapta-jos) */}
            <ellipse
              className="orb-blob orb-blob--yellow"
              cx="410"
              cy="420"
              rx="160"
              ry="140"
              fill="var(--c-orb-yellow)"
              opacity="0.45"
              filter="url(#orbBlur100)"
            />

            {/* Layer 8: Albastru închis (65%, Blur: 80px, 380x320 px, jos) */}
            <ellipse
              className="orb-blob orb-blob--dark-blue"
              cx="300"
              cy="440"
              rx="190"
              ry="160"
              fill="var(--c-orb-dark-blue)"
              opacity="0.65"
              filter="url(#orbBlur80)"
            />

            {/* Layer 10: Lumina de sus (reflexie) (18%, Blur: 60px, 450x220 px, sus) */}
            <ellipse
              className="orb-blob orb-blob--top-light"
              cx="300"
              cy="150"
              rx="225"
              ry="110"
              fill="var(--c-surface)"
              opacity="0.18"
              filter="url(#orbBlur60)"
            />

            {/* Layer 11: Umbra de jos (glow) (32%, Blur: 80px, 450x180 px, jos) */}
            <ellipse
              className="orb-blob orb-blob--bottom-glow"
              cx="300"
              cy="460"
              rx="225"
              ry="90"
              fill="var(--c-orb-glow-blue)"
              opacity="0.32"
              filter="url(#orbBlur80)"
            />

            {/* Layer 12: Glass sheen (Figma Glass effect 135°) */}
            <circle cx="300" cy="300" r="300" fill="url(#orbGlassSheen)" />

            {/* Спекулярный рефракционный блик по верхне-левому краю */}
            <path
              d="M 80 220 A 300 300 0 0 1 420 80 A 285 285 0 0 0 110 260 Z"
              fill="var(--c-surface)"
              opacity="0.25"
              filter="url(#orbBlur60)"
            />

            {/* Неоновый шеврон снизу (символ навигации NEXA) */}
            <polygon
              className="nexa-mascot__chevron"
              points="284,480 300,504 316,480 309,480 300,494 291,480"
              fill="var(--c-nexa-turquoise)"
              opacity="0.95"
              filter="url(#orbRingSoft)"
            />
          </g>

          {/* Layer 9: Stroke (contur subtil 25%, 1px, 600x600 px) */}
          <circle
            cx="300"
            cy="300"
            r="299.5"
            fill="none"
            stroke="var(--c-orb-white-stroke)"
            strokeWidth="1"
          />
        </g>

        {/* 3D Орбитальные кольца - передние дуги (перед сферой) */}
        <g className="nexa-mascot__rings-front">
          {/* Переднее кольцо 1: мягкое свечение и четкое неоновое ядро */}
          <path
            className="nexa-mascot__ring-loop-1-glow"
            d="M -70 185 C 100 320, 460 550, 670 415"
            stroke="url(#orbRingGradCyan)"
            strokeWidth="20"
            strokeLinecap="round"
            opacity="0.75"
            filter="url(#orbRingGlow)"
          />
          <path
            className="nexa-mascot__ring-loop-1"
            d="M -70 185 C 100 320, 460 550, 670 415"
            stroke="var(--c-nexa-turquoise)"
            strokeWidth="5.5"
            strokeLinecap="round"
            opacity="0.95"
          />

          {/* Переднее кольцо 2: мягкое свечение и четкое неоновое ядро */}
          <path
            className="nexa-mascot__ring-loop-2-glow"
            d="M 600 110 C 465 -10, 90 340, 0 490"
            stroke="url(#orbRingGradCyan)"
            strokeWidth="18"
            strokeLinecap="round"
            opacity="0.7"
            filter="url(#orbRingGlow)"
          />
          <path
            className="nexa-mascot__ring-loop-2"
            d="M 600 110 C 465 -10, 90 340, 0 490"
            stroke="var(--c-orb-cyan)"
            strokeWidth="5"
            strokeLinecap="round"
            opacity="0.9"
          />
        </g>

        {/* Живые квантовые искры вокруг орбиты */}
        <g className="nexa-mascot__sparks">
          <circle cx="-40" cy="180" r="4.5" fill="var(--c-nexa-turquoise)" className="spark-1" filter="url(#orbRingSoft)" />
          <circle cx="640" cy="420" r="4" fill="var(--c-orb-cyan)" className="spark-2" filter="url(#orbRingSoft)" />
          <circle cx="580" cy="120" r="3.5" fill="var(--c-surface)" className="spark-3" filter="url(#orbRingSoft)" />
          <circle cx="20" cy="470" r="4" fill="var(--c-orb-blue)" className="spark-4" filter="url(#orbRingSoft)" />
        </g>
      </svg>
    </div>
  )
}

export const NexaOrb = NexaMascot

const MIN_QUESTION_LENGTH = 2 // AskRequest.question: min_length=2

interface Turn {
  id: number
  question: string
  response: AskResponse
}

export interface ChatScreenProps {
  initialQuestion?: string
  quickQuestion?: string
  chipsSlot?: React.ReactNode
  onQuickAsk?: (askFn: (question: string) => void) => void
  currentLang?: Lang
  onLangChange?: (lang: Lang) => void
  showHeader?: boolean
  onQueryAsked?: (question: string) => void
  onResetRegistered?: (resetFn: () => void) => void
}

function getFallbackRecognitionFactory(lang: Lang) {
  if (typeof window === "undefined" || isSpeechRecognitionSupported()) {
    return undefined
  }
  return () => {
    return class FallbackSpeechRecognition {
      lang = lang === "ru" ? "ru-RU" : "ro-RO"
      interimResults = false
      onresult: ((event: any) => void) | null = null
      onerror: (() => void) | null = null
      onend: (() => void) | null = null
      private timer: any = null

      start() {
        this.timer = setTimeout(() => {
          if (this.onresult) {
            const sample =
              lang === "ru"
                ? "В какой срок рассматривается петиция в примэрии?"
                : "Care este termenul de examinare a unei petiții?"
            this.onresult({
              results: [[{ transcript: sample }]],
            })
          }
        }, 2200)
      }

      stop() {
        if (this.timer) clearTimeout(this.timer)
        this.onend?.()
      }

      abort() {
        if (this.timer) clearTimeout(this.timer)
      }
    }
  }
}

export function ChatScreen({
  initialQuestion,
  quickQuestion,
  chipsSlot,
  onQuickAsk,
  currentLang,
  onLangChange,
  showHeader = !currentLang,
  onQueryAsked,
  onResetRegistered,
}: ChatScreenProps = {}) {
  const [lang, setLang] = useState<Lang>(currentLang || "ro")
  const [draft, setDraft] = useState("")
  const [turns, setTurns] = useState<Turn[]>([])
  const [pending, setPending] = useState(false)
  const [failed, setFailed] = useState(false)
  const [lastQuestion, setLastQuestion] = useState("")
  const s = t(lang)

  const lastRunRef = useRef<{ q: string; time: number } | null>(null)
  const lastInitialRef = useRef<string | undefined>(undefined)

  useEffect(() => {
    if (onResetRegistered) {
      onResetRegistered(() => {
        setTurns([])
        setDraft("")
        setPending(false)
        setFailed(false)
        lastRunRef.current = null
        lastInitialRef.current = undefined
      })
    }
  }, [onResetRegistered])

  useEffect(() => {
    if (currentLang && currentLang !== lang) {
      setLang(currentLang)
    }
  }, [currentLang])

  useEffect(() => {
    if (onQuickAsk) {
      onQuickAsk((question: string) => {
        const trimmed = question.trim()
        if (trimmed.length >= MIN_QUESTION_LENGTH) {
          void run(trimmed)
        }
      })
    }
  }, [onQuickAsk, lang])

  useEffect(() => {
    const q = (initialQuestion || quickQuestion)?.trim()
    if (q && q.length >= MIN_QUESTION_LENGTH && q !== lastInitialRef.current) {
      lastInitialRef.current = q
      void run(q)
    }
  }, [initialQuestion, quickQuestion])

  async function run(question: string): Promise<void> {
    const now = Date.now()
    if (pending) return
    if (lastRunRef.current && lastRunRef.current.q === question && now - lastRunRef.current.time < 800) {
      return
    }
    lastRunRef.current = { q: question, time: now }

    setPending(true)
    setFailed(false)
    setLastQuestion(question)
    onQueryAsked?.(question)
    try {
      const response = await ask(question, lang)
      setTurns((previous) => [...previous, { id: previous.length + 1, question, response }])
      setDraft("")
    } catch {
      setFailed(true)
    } finally {
      setPending(false)
    }
  }

  function onSubmit(event: React.FormEvent<HTMLFormElement>): void {
    event.preventDefault()
    const question = draft.trim()
    if (question.length < MIN_QUESTION_LENGTH || pending) return
    void run(question)
  }

  const canSend = draft.trim().length >= MIN_QUESTION_LENGTH && !pending
  const showEmpty = turns.length === 0 && !pending && !failed

  return (
    <div className="chat">
      {showHeader && (
        <header className="chat__header">
          <div>
            <h1 className="chat__title">{s.appTitle}</h1>
            <p className="chat__tagline">{s.appTagline}</p>
          </div>
          <div className="lang">
            <span className="lang__label">{s.langLabel}</span>
            <div className="lang__group">
              {(["ro", "ru"] as const).map((code) => (
                <button
                  key={code}
                  type="button"
                  className="lang__button"
                  aria-pressed={lang === code}
                  onClick={() => {
                    setLang(code)
                    onLangChange?.(code)
                  }}
                >
                  {code.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        </header>
      )}

      <main className="chat__thread">
        {showEmpty && (
          <section className="welcome" aria-label="NEXA Welcome">
            <NexaOrb />
            <h1 className="welcome__title">{lang === "ru" ? "Привет, я NEXA" : "HI, Im NEXA"}</h1>
            <h2 className="welcome__subtitle">{lang === "ru" ? "Чем я могу помочь?" : "How can i help you?"}</h2>
          </section>
        )}

        {turns.map((turn) => (
          <section className="turn" key={turn.id}>
            <p className="turn__question">{turn.question}</p>
            <AnswerCard response={turn.response} />
          </section>
        ))}

        {pending && (
          <section className="skeleton" aria-busy="true">
            <p className="skeleton__caption">{s.loading}</p>
            <div className="skeleton__bar" />
            <div className="skeleton__bar" />
            <div className="skeleton__bar skeleton__bar--short" />
          </section>
        )}

        {failed && (
          <section className="error" role="alert">
            <h3 className="error__title">{s.errorTitle}</h3>
            <p className="error__body">{s.errorBody}</p>
            <button type="button" className="error__retry" onClick={() => void run(lastQuestion)}>
              {s.retry}
            </button>
          </section>
        )}

        {!showEmpty && <StatsFooter />}
      </main>

      {!showEmpty && chipsSlot}

      <form className="composer" onSubmit={onSubmit}>
        <div className="composer__input-wrapper">
          <input
            id="question"
            className="composer__input"
            type="text"
            value={draft}
            placeholder={lang === "ru" ? "Спросите NEXA о чём угодно..." : "Ask NEXA anything .."}
            maxLength={1000}
            autoComplete="off"
            onChange={(event) => setDraft(event.target.value)}
          />
        </div>
        <div className="composer__bottom-bar">
          <button type="button" className="composer__attach-btn" onClick={() => {}} title="Attach">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
            </svg>
            <span>{s.attachLabel}</span>
          </button>
          <div className="composer__actions">
            <MicButton
              lang={lang}
              onTranscript={(text) => setDraft(text)}
              recognitionFactory={getFallbackRecognitionFactory(lang)}
            />
            <button
              type="submit"
              className={`composer__submit ${pending ? "composer__submit--pending" : ""}`}
              disabled={!canSend}
              aria-label={pending ? s.sending : s.send}
              title={pending ? s.sending : s.send}
            >
              {pending ? (
                <svg className="composer__spinner" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" aria-hidden="true">
                  <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
                </svg>
              ) : (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <line x1="12" y1="19" x2="12" y2="5" />
                  <polyline points="5 12 12 5 19 12" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}
