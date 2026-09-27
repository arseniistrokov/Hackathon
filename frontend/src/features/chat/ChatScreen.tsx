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
    <div className="nexa-orb-container" role="img" aria-label="NEXA AI Core">
      {/* Мягкое фоновое рассеянное свечение */}
      <div className="nexa-orb-halo" aria-hidden="true" />

      {/* Живая квантовая 3D сфера по референсу Figma */}
      <div className="nexa-orb-body">
        <svg
          className="nexa-orb-svg"
          viewBox="0 0 400 400"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
        >
          <defs>
            <radialGradient id="nexaCoreGradient" cx="38%" cy="32%" r="68%">
              <stop offset="0%" stopColor="var(--c-orb-cyan)" />
              <stop offset="30%" stopColor="var(--c-orb-blue)" />
              <stop offset="70%" stopColor="var(--c-nexa-purple)" />
              <stop offset="100%" stopColor="var(--c-nexa-orb-deep)" />
            </radialGradient>

            <radialGradient id="nexaWave1" cx="30%" cy="30%" r="50%">
              <stop offset="0%" stopColor="var(--c-orb-light-cyan)" stopOpacity="0.9" />
              <stop offset="50%" stopColor="var(--c-nexa-cyan)" stopOpacity="0.5" />
              <stop offset="100%" stopColor="var(--c-nexa-blue)" stopOpacity="0" />
            </radialGradient>

            <radialGradient id="nexaWave2" cx="70%" cy="70%" r="55%">
              <stop offset="0%" stopColor="var(--c-orb-pink)" stopOpacity="0.75" />
              <stop offset="45%" stopColor="var(--c-orb-purple)" stopOpacity="0.45" />
              <stop offset="100%" stopColor="var(--c-nexa-orb-deep)" stopOpacity="0" />
            </radialGradient>

            <linearGradient id="nexaSheenGrad" x1="10%" y1="10%" x2="90%" y2="90%">
              <stop offset="0%" stopColor="var(--c-surface)" stopOpacity="0.6" />
              <stop offset="35%" stopColor="var(--c-surface)" stopOpacity="0.1" />
              <stop offset="100%" stopColor="var(--c-surface)" stopOpacity="0" />
            </linearGradient>

            <linearGradient id="nexaEnergyWave" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="var(--c-nexa-turquoise)" stopOpacity="0.8" />
              <stop offset="50%" stopColor="var(--c-orb-pink)" stopOpacity="0.6" />
              <stop offset="100%" stopColor="var(--c-nexa-cyan)" stopOpacity="0.7" />
            </linearGradient>

            <filter id="nexaBlurSoft" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="6" />
            </filter>
            <filter id="nexaBlurMedium" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="16" />
            </filter>

            <clipPath id="nexaSphereClip">
              <circle cx="200" cy="200" r="140" />
            </clipPath>
          </defs>

          <g clipPath="url(#nexaSphereClip)">
            <circle cx="200" cy="200" r="140" fill="url(#nexaCoreGradient)" />

            <circle
              className="nexa-blob-anim nexa-blob-anim--1"
              cx="160"
              cy="150"
              r="105"
              fill="url(#nexaWave1)"
              filter="url(#nexaBlurMedium)"
            />
            <circle
              className="nexa-blob-anim nexa-blob-anim--2"
              cx="240"
              cy="230"
              r="110"
              fill="url(#nexaWave2)"
              filter="url(#nexaBlurMedium)"
            />
            <ellipse
              className="nexa-blob-anim nexa-blob-anim--3"
              cx="200"
              cy="200"
              rx="120"
              ry="75"
              transform="rotate(25 200 200)"
              fill="var(--c-orb-cyan)"
              opacity="0.55"
              filter="url(#nexaBlurMedium)"
            />

            <path
              className="nexa-wave-anim nexa-wave-anim--a"
              d="M 80 180 Q 150 120 200 180 T 320 180"
              stroke="url(#nexaEnergyWave)"
              strokeWidth="4"
              strokeLinecap="round"
              fill="none"
              opacity="0.8"
              filter="url(#nexaBlurSoft)"
            />
            <path
              className="nexa-wave-anim nexa-wave-anim--b"
              d="M 90 220 Q 160 270 210 210 T 310 220"
              stroke="url(#nexaEnergyWave)"
              strokeWidth="3.5"
              strokeLinecap="round"
              fill="none"
              opacity="0.75"
              filter="url(#nexaBlurSoft)"
            />

            <circle cx="200" cy="200" r="140" fill="url(#nexaSheenGrad)" />
            <ellipse
              cx="175"
              cy="135"
              rx="65"
              ry="32"
              transform="rotate(-20 175 135)"
              fill="var(--c-surface)"
              opacity="0.4"
              filter="url(#nexaBlurSoft)"
            />
          </g>

          <circle
            cx="200"
            cy="200"
            r="139.5"
            fill="none"
            stroke="var(--c-white-translucent)"
            strokeWidth="1.2"
          />
        </svg>
      </div>
    </div>
  )
}

export const NexaOrb = NexaMascot

const MIN_QUESTION_LENGTH = 2

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
  showHeader = false,
  onQueryAsked,
  onResetRegistered,
}: ChatScreenProps = {}) {
  const [lang, setLang] = useState<Lang>(currentLang || "ro")
  const [draft, setDraft] = useState("")
  const [turns, setTurns] = useState<Turn[]>([])
  const [pending, setPending] = useState(false)
  const [failed, setFailed] = useState(false)
  const [lastQuestion, setLastQuestion] = useState("")
  const [showAttachPill, setShowAttachPill] = useState(false)
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
        setShowAttachPill(false)
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
    setShowAttachPill(false)
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
    <div className="nexa-chat-screen">
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

      <main className="nexa-chat-screen__thread">
        {showEmpty && (
          <section className="nexa-welcome" aria-label="NEXA Welcome">
            <NexaOrb />
            <h1 className="nexa-welcome__title">{lang === "ru" ? "Привет, я NEXA" : "Hi, I'm NEXA"}</h1>
            <h2 className="nexa-welcome__subtitle">{lang === "ru" ? "Чем я могу помочь?" : "How can I help you?"}</h2>

            {/* Карточки готовых вопросов по референсу Figma */}
            <div className="nexa-hero-cards" role="region" aria-label="Suggested prompts">
              <button
                type="button"
                className="nexa-hero-card"
                onClick={() => void run(lang === "ru" ? "Тарифы на проезд в троллейбусе" : "Tarife călătorie troleibuz RTEC")}
              >
                <div className="nexa-hero-card__header">
                  <span className="nexa-hero-card__title">
                    {lang === "ru" ? "Тарифы и проезд RTEC .." : "Tarife transport public și RTEC .."}
                  </span>
                  <svg className="nexa-hero-card__chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </div>
                <p className="nexa-hero-card__desc">
                  {lang === "ru"
                    ? "Тарифы RTEC и автобусов, маршруты, проездные абонементы и правила оплаты проезда в муниципии Кишинёв."
                    : "Tarife RTEC și autobuze, rute, abonamente de călătorie și orare de circulație în municipiul Chișinău."}
                </p>
              </button>

              <button
                type="button"
                className="nexa-hero-card"
                onClick={() => void run(lang === "ru" ? "В какой срок рассматривается петиция в примэрии?" : "Care este termenul de examinare a unei petiții?")}
              >
                <div className="nexa-hero-card__header">
                  <span className="nexa-hero-card__title">
                    {lang === "ru" ? "Сроки рассмотрения петиций .." : "Termenul de examinare a petițiilor .."}
                  </span>
                  <svg className="nexa-hero-card__chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </div>
                <p className="nexa-hero-card__desc">
                  {lang === "ru"
                    ? "Процедура и установленные законодательством сроки рассмотрения петиций и обращений граждан в примэрии."
                    : "Procedura și termenele legale de examinare a petițiilor și cererilor cetățenilor adresate primăriei."}
                </p>
              </button>
            </div>
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

      <div className="nexa-composer-container">
        {/* Всплывающая плашка добавления файлов (Figma black pill) */}
        {showAttachPill && (
          <div className="nexa-attach-pill">
            <button
              type="button"
              className="nexa-attach-pill__btn"
              onClick={() => setShowAttachPill(false)}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
              </svg>
              <span className="nexa-attach-pill__bold">Add photos & files</span>
              <span className="nexa-attach-pill__muted">Upload from computer</span>
            </button>
          </div>
        )}

        {/* Форма ввода (Figma pill composer) */}
        <form className="nexa-composer-pill" onSubmit={onSubmit}>
          <button
            type="button"
            className="nexa-composer-plus-btn"
            onClick={() => setShowAttachPill((prev) => !prev)}
            title="Attach file"
            aria-label="Attach file"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
          </button>

          <div className="nexa-composer-input-wrapper">
            <input
              id="question"
              className="nexa-composer-input"
              type="text"
              value={draft}
              placeholder={lang === "ru" ? "Спросите NEXA о чём угодно..." : "Ask NEXA anything.."}
              maxLength={1000}
              autoComplete="off"
              onChange={(event) => setDraft(event.target.value)}
            />
          </div>

          <div className="nexa-composer-actions">
            <MicButton
              lang={lang}
              onTranscript={(text) => setDraft(text)}
              recognitionFactory={getFallbackRecognitionFactory(lang)}
            />
            <button
              type="submit"
              className={`nexa-composer-submit-btn ${pending ? "nexa-composer-submit-btn--pending" : ""}`}
              disabled={!canSend}
              aria-label={pending ? s.sending : s.send}
              title={pending ? s.sending : s.send}
            >
              {pending ? (
                <svg className="composer__spinner" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" aria-hidden="true">
                  <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
                </svg>
              ) : (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <line x1="12" y1="19" x2="12" y2="5" />
                  <polyline points="5 12 12 5 19 12" />
                </svg>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
