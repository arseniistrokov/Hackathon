import { useState, useEffect } from "react"
import { ask } from "@/api/client"
import type { AskResponse, Lang } from "@/api/types"
import { t } from "@/i18n"
import { AnswerCard } from "./AnswerCard"
import { MicButton, isSpeechRecognitionSupported } from "../voice/MicButton"
import { StatsFooter } from "../stats/StatsFooter"
import { NexaOrb } from "../portal/NexaOrb"
import "./chat.css"

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

  useEffect(() => {
    if (onResetRegistered) {
      onResetRegistered(() => {
        setTurns([])
        setDraft("")
        setPending(false)
        setFailed(false)
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
        if (question.trim().length >= MIN_QUESTION_LENGTH) {
          void run(question.trim())
        }
      })
    }
  }, [onQuickAsk, lang])

  useEffect(() => {
    const q = initialQuestion || quickQuestion
    if (q && q.trim().length >= MIN_QUESTION_LENGTH) {
      void run(q.trim())
    }
  }, [initialQuestion, quickQuestion])

  async function run(question: string): Promise<void> {
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
            <h2 className="welcome__title">
              {lang === "ru" ? "Привет, я NEXA" : "Salut, sunt NEXA"}
            </h2>
            <p className="welcome__subtitle">
              {lang === "ru" ? "Чем я могу помочь?" : "Cum te pot ajuta?"}
            </p>
            <p className="welcome__desc">{s.welcomeDescription}</p>
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
      </main>

      {chipsSlot}

      <form className="composer" onSubmit={onSubmit}>
        <div className="composer__input-wrapper">
          <input
            id="question"
            className="composer__input"
            type="text"
            value={draft}
            placeholder={
              lang === "ru"
                ? "Задайте вопрос NEXA..."
                : "Ask NEXA anything..."
            }
            maxLength={1000}
            autoComplete="off"
            onChange={(event) => setDraft(event.target.value)}
          />
        </div>
        <div className="composer__toolbar">
          <div className="composer__meta-tag" title="Surse oficiale Primăria Chișinău">
            <span className="composer__meta-icon" aria-hidden="true">📎</span>
            <span>{lang === "ru" ? "Официальные источники" : "Surse oficiale"}</span>
          </div>
          <div className="composer__actions">
            <MicButton
              lang={lang}
              onTranscript={(text) => setDraft(text)}
              recognitionFactory={getFallbackRecognitionFactory(lang)}
            />
            <button
              type="submit"
              className="composer__submit"
              disabled={!canSend}
              aria-label={s.send}
              title={s.send}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <line x1="12" y1="19" x2="12" y2="5" />
                <polyline points="5 12 12 5 19 12" />
              </svg>
            </button>
          </div>
        </div>
      </form>

      <StatsFooter />
    </div>
  )
}
