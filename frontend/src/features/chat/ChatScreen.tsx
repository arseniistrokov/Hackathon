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
        viewBox="0 0 320 280"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <defs>
          <radialGradient
            id="nexaSphereGrad"
            cx="35%"
            cy="28%"
            r="68%"
            fx="35%"
            fy="28%"
          >
            <stop offset="0%" stopColor="var(--c-nexa-orb-light)" />
            <stop offset="30%" stopColor="var(--c-nexa-cyan)" />
            <stop offset="68%" stopColor="var(--c-nexa-blue)" />
            <stop offset="100%" stopColor="var(--c-nexa-orb-deep)" />
          </radialGradient>

          <linearGradient id="nexaHighlightGrad" x1="0%" y1="100%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="var(--c-surface)" stopOpacity="0" />
            <stop offset="25%" stopColor="var(--c-surface)" stopOpacity="0.95" />
            <stop offset="65%" stopColor="var(--c-nexa-highlight-soft)" stopOpacity="0.85" />
            <stop offset="100%" stopColor="var(--c-nexa-cyan)" stopOpacity="0" />
          </linearGradient>

          <linearGradient id="nexaUpperGlow" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="var(--c-surface)" stopOpacity="0.8" />
            <stop offset="100%" stopColor="var(--c-surface)" stopOpacity="0" />
          </linearGradient>

          <linearGradient id="nexaRingGradBlue" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="var(--c-nexa-blue)" />
            <stop offset="50%" stopColor="var(--c-nexa-cyan)" />
            <stop offset="100%" stopColor="var(--c-nexa-orb-light)" />
          </linearGradient>

          <linearGradient id="nexaRingGradCyan" x1="100%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="var(--c-nexa-turquoise)" />
            <stop offset="45%" stopColor="var(--c-nexa-cyan)" />
            <stop offset="100%" stopColor="var(--c-nexa-blue)" />
          </linearGradient>

          <filter id="nexaMascotBloom" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>

          <filter id="nexaSoftNebula" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="4.5" />
          </filter>
        </defs>

        {/* Задние дуги орбитальных колец (Layer_1 за сферой) */}
        <g className="nexa-mascot__rings-back">
          <path
            d="M 58 116 C 54 94 85 74 146 68 C 176 65 206 68 234 78"
            stroke="url(#nexaRingGradBlue)"
            strokeWidth="9"
            strokeLinecap="round"
            opacity="0.48"
            filter="url(#nexaSoftNebula)"
          />
          <path
            d="M 90 76 C 120 68 165 66 210 74 C 246 80 268 96 264 116"
            stroke="url(#nexaRingGradCyan)"
            strokeWidth="9"
            strokeLinecap="round"
            opacity="0.52"
            filter="url(#nexaSoftNebula)"
          />
        </g>

        {/* 3D Сфера маскота (Frame 88 / Frame 91) */}
        <g className="nexa-mascot__sphere">
          <circle cx="160" cy="140" r="78" fill="var(--c-nexa-orb-deep)" />
          <circle cx="160" cy="140" r="78" fill="url(#nexaSphereGrad)" />

          {/* Глубокая тень справа снизу */}
          <path
            d="M 160 62 A 78 78 0 0 1 238 140 A 78 78 0 0 1 185 215 C 220 185 225 125 185 85 C 175 75 167 67 160 62 Z"
            fill="var(--c-nexa-orb-deep)"
            opacity="0.65"
          />

          {/* Изогнутая световая полоса/небула (Frame 88) */}
          <path
            className="nexa-mascot__highlight"
            d="M 102 165 Q 155 210 218 148 Q 165 180 102 165 Z"
            fill="url(#nexaHighlightGrad)"
            filter="url(#nexaSoftNebula)"
          />

          {/* Верхний мягкий блик */}
          <ellipse
            cx="145"
            cy="100"
            rx="46"
            ry="20"
            transform="rotate(-15 145 100)"
            fill="url(#nexaUpperGlow)"
            opacity="0.65"
            filter="url(#nexaSoftNebula)"
          />

          {/* Неоновый шеврон снизу (Frame 91) */}
          <polygon
            className="nexa-mascot__chevron"
            points="154,195 160,206 166,195 162,195 160,201 158,195"
            fill="var(--c-nexa-turquoise)"
            opacity="0.9"
            filter="url(#nexaSoftNebula)"
          />
        </g>

        {/* Передние дуги орбитальных колец (Layer_1 перед сферой) */}
        <g className="nexa-mascot__rings-front">
          {/* Левая синяя петля */}
          <path
            className="nexa-mascot__ring-loop-1"
            d="M 52 112 C 30 135 25 168 55 190 C 85 212 145 208 215 178 C 248 164 268 145 264 130 C 260 118 245 110 225 105"
            stroke="url(#nexaRingGradBlue)"
            strokeWidth="11"
            strokeLinecap="round"
            filter="url(#nexaMascotBloom)"
          />

          {/* Правая бирюзовая петля */}
          <path
            className="nexa-mascot__ring-loop-2"
            d="M 268 112 C 290 135 292 168 262 188 C 230 208 170 198 105 168 C 72 154 50 138 55 125 C 60 114 78 106 100 102"
            stroke="url(#nexaRingGradCyan)"
            strokeWidth="10.5"
            strokeLinecap="round"
            filter="url(#nexaMascotBloom)"
          />
        </g>

        {/* Живые квантовые искры вокруг орбиты */}
        <g className="nexa-mascot__sparks">
          <circle cx="56" cy="132" r="3.2" fill="var(--c-nexa-orb-light)" className="spark-1" />
          <circle cx="266" cy="144" r="2.8" fill="var(--c-nexa-turquoise)" className="spark-2" />
          <circle cx="204" cy="64" r="2.2" fill="var(--c-surface)" className="spark-3" />
          <circle cx="114" cy="216" r="3" fill="var(--c-nexa-cyan)" className="spark-4" />
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
