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
        viewBox="0 0 600 600"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <defs>
          {/* Базовый 3D сферический градиент света и тени */}
          <radialGradient id="nexaSphere3D" cx="35%" cy="28%" r="72%">
            <stop offset="0%" stopColor="var(--c-orb-cyan)" />
            <stop offset="35%" stopColor="var(--c-orb-blue)" />
            <stop offset="70%" stopColor="var(--c-orb-dark-blue)" />
            <stop offset="100%" stopColor="var(--c-nexa-orb-deep)" />
          </radialGradient>

          {/* Неоновые градиенты для колец */}
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

          {/* Изогнутая световая волна по центру */}
          <linearGradient id="orbWaveGrad" x1="0%" y1="100%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="var(--c-surface)" stopOpacity="0" />
            <stop offset="30%" stopColor="var(--c-surface)" stopOpacity="0.85" />
            <stop offset="70%" stopColor="var(--c-orb-cyan)" stopOpacity="0.75" />
            <stop offset="100%" stopColor="var(--c-nexa-turquoise)" stopOpacity="0" />
          </linearGradient>

          {/* Glass Sheen под углом 135° */}
          <linearGradient id="orbGlassSheen" x1="15%" y1="15%" x2="85%" y2="85%">
            <stop offset="0%" stopColor="var(--c-surface)" stopOpacity="0.32" />
            <stop offset="40%" stopColor="var(--c-surface)" stopOpacity="0.08" />
            <stop offset="80%" stopColor="var(--c-surface)" stopOpacity="0" />
          </linearGradient>

          {/* Мягкие размытия для слоев сферы */}
          <filter id="orbBlurSoft" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="8" />
          </filter>
          <filter id="orbBlurMed" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="22" />
          </filter>
          <filter id="orbBlurLarge" x="-40%" y="-40%" width="180%" height="180%">
            <feGaussianBlur stdDeviation="35" />
          </filter>

          {/* Свечение колец */}
          <filter id="orbRingGlow" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
          <filter id="orbRingSoft" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="4.5" />
          </filter>

          {/* Маска сферы */}
          <clipPath id="orbSphereMask">
            <circle cx="300" cy="300" r="180" />
          </clipPath>
        </defs>

        {/* 3D Орбитальные кольца - задние дуги (за сферой, математически точные эллипсы) */}
        <g className="nexa-mascot__rings-back">
          {/* Задняя дуга кольца 1 (наклон -24°) */}
          <g transform="rotate(-24 300 300)">
            <path
              d="M 45 300 A 255 70 0 0 1 555 300"
              stroke="url(#orbRingGradBlue)"
              strokeWidth="12"
              strokeLinecap="round"
              opacity="0.45"
              filter="url(#orbRingSoft)"
            />
            <path
              d="M 45 300 A 255 70 0 0 1 555 300"
              stroke="var(--c-orb-cyan)"
              strokeWidth="2.5"
              strokeLinecap="round"
              opacity="0.6"
            />
          </g>

          {/* Задняя дуга кольца 2 (наклон +36°) */}
          <g transform="rotate(36 300 300)">
            <path
              d="M 55 300 A 245 62 0 0 1 545 300"
              stroke="url(#orbRingGradBlue)"
              strokeWidth="11"
              strokeLinecap="round"
              opacity="0.4"
              filter="url(#orbRingSoft)"
            />
            <path
              d="M 55 300 A 245 62 0 0 1 545 300"
              stroke="var(--c-orb-blue)"
              strokeWidth="2"
              strokeLinecap="round"
              opacity="0.55"
            />
          </g>
        </g>

        {/* 3D Сфера маскота с переливающимися слоями */}
        <g className="nexa-mascot__sphere">
          <g clipPath="url(#orbSphereMask)">
            {/* Базовая 3D глубина */}
            <circle cx="300" cy="300" r="180" fill="url(#nexaSphere3D)" />

            {/* Внутренние цветные облака по рецепту Figma с живым движением */}
            <ellipse
              className="orb-blob orb-blob--blue"
              cx="240"
              cy="225"
              rx="115"
              ry="95"
              fill="var(--c-orb-blue)"
              opacity="0.75"
              filter="url(#orbBlurMed)"
            />
            <ellipse
              className="orb-blob orb-blob--cyan"
              cx="300"
              cy="230"
              rx="125"
              ry="110"
              fill="var(--c-orb-cyan)"
              opacity="0.7"
              filter="url(#orbBlurLarge)"
            />
            <ellipse
              className="orb-blob orb-blob--purple"
              cx="235"
              cy="295"
              rx="115"
              ry="115"
              fill="var(--c-orb-purple)"
              opacity="0.55"
              filter="url(#orbBlurLarge)"
            />
            <ellipse
              className="orb-blob orb-blob--pink"
              cx="305"
              cy="300"
              rx="125"
              ry="110"
              fill="var(--c-orb-pink)"
              opacity="0.55"
              filter="url(#orbBlurLarge)"
            />
            <ellipse
              className="orb-blob orb-blob--light-cyan"
              cx="365"
              cy="290"
              rx="125"
              ry="110"
              fill="var(--c-orb-light-cyan)"
              opacity="0.65"
              filter="url(#orbBlurLarge)"
            />
            <ellipse
              className="orb-blob orb-blob--yellow"
              cx="365"
              cy="375"
              rx="95"
              ry="85"
              fill="var(--c-orb-yellow)"
              opacity="0.45"
              filter="url(#orbBlurLarge)"
            />
            <ellipse
              className="orb-blob orb-blob--dark-blue"
              cx="300"
              cy="385"
              rx="115"
              ry="95"
              fill="var(--c-orb-dark-blue)"
              opacity="0.65"
              filter="url(#orbBlurMed)"
            />

            {/* Световые рефлексы и глубина */}
            <ellipse
              className="orb-blob orb-blob--top-light"
              cx="300"
              cy="210"
              rx="135"
              ry="65"
              fill="var(--c-surface)"
              opacity="0.22"
              filter="url(#orbBlurMed)"
            />
            <ellipse
              className="orb-blob orb-blob--bottom-glow"
              cx="300"
              cy="400"
              rx="135"
              ry="55"
              fill="var(--c-orb-glow-blue)"
              opacity="0.35"
              filter="url(#orbBlurMed)"
            />

            {/* Изогнутая световая волна небулы */}
            <ellipse
              className="orb-blob orb-blob--wave"
              cx="300"
              cy="320"
              rx="130"
              ry="38"
              transform="rotate(-15 300 320)"
              fill="url(#orbWaveGrad)"
              opacity="0.75"
              filter="url(#orbBlurSoft)"
            />

            {/* Glass sheen 135° */}
            <circle cx="300" cy="300" r="180" fill="url(#orbGlassSheen)" />

            {/* Верхне-левый стеклянный блик */}
            <ellipse
              cx="270"
              cy="200"
              rx="100"
              ry="35"
              transform="rotate(-30 270 200)"
              fill="var(--c-surface)"
              opacity="0.28"
              filter="url(#orbBlurSoft)"
            />

            {/* Неоновый шеврон снизу */}
            <polygon
              className="nexa-mascot__chevron"
              points="292,415 300,428 308,415 305,415 300,423 295,415"
              fill="var(--c-nexa-turquoise)"
              opacity="0.95"
              filter="url(#orbRingSoft)"
            />
          </g>

          {/* Тонкий стеклянный ободок */}
          <circle
            cx="300"
            cy="300"
            r="179.5"
            fill="none"
            stroke="var(--c-orb-white-stroke)"
            strokeWidth="1"
          />
        </g>

        {/* 3D Орбитальные кольца - передние дуги (перед сферой, математически точные эллипсы) */}
        <g className="nexa-mascot__rings-front">
          {/* Передняя дуга кольца 1 (наклон -24°) */}
          <g transform="rotate(-24 300 300)">
            <path
              className="nexa-mascot__ring-glow-1"
              d="M 45 300 A 255 70 0 0 0 555 300"
              stroke="url(#orbRingGradCyan)"
              strokeWidth="12"
              strokeLinecap="round"
              opacity="0.7"
              filter="url(#orbRingGlow)"
            />
            <path
              className="nexa-mascot__ring-loop-1"
              d="M 45 300 A 255 70 0 0 0 555 300"
              stroke="var(--c-nexa-turquoise)"
              strokeWidth="3.6"
              strokeLinecap="round"
              opacity="0.95"
            />
          </g>

          {/* Передняя дуга кольца 2 (наклон +36°) */}
          <g transform="rotate(36 300 300)">
            <path
              className="nexa-mascot__ring-glow-2"
              d="M 55 300 A 245 62 0 0 0 545 300"
              stroke="url(#orbRingGradCyan)"
              strokeWidth="10"
              strokeLinecap="round"
              opacity="0.65"
              filter="url(#orbRingGlow)"
            />
            <path
              className="nexa-mascot__ring-loop-2"
              d="M 55 300 A 245 62 0 0 0 545 300"
              stroke="var(--c-orb-cyan)"
              strokeWidth="3.2"
              strokeLinecap="round"
              opacity="0.9"
            />
          </g>
        </g>

        {/* Квантовые искры */}
        <g className="nexa-mascot__sparks">
          <circle cx="65" cy="205" r="3.5" fill="var(--c-nexa-turquoise)" className="spark-1" filter="url(#orbRingSoft)" />
          <circle cx="535" cy="395" r="3.2" fill="var(--c-orb-cyan)" className="spark-2" filter="url(#orbRingSoft)" />
          <circle cx="495" cy="155" r="2.8" fill="var(--c-surface)" className="spark-3" filter="url(#orbRingSoft)" />
          <circle cx="105" cy="445" r="3" fill="var(--c-orb-blue)" className="spark-4" filter="url(#orbRingSoft)" />
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
