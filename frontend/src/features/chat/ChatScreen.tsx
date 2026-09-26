// Экран чата: ввод, переключатель ro/ru, история вопросов, загрузка и ошибка.
// Уровень L0/L1 переключает только api/client.ts — здесь про моки ничего не известно.
import { useState, useEffect } from "react"
import { ask } from "@/api/client"
import type { AskResponse, Lang } from "@/api/types"
import { t } from "@/i18n"
import { AnswerCard } from "./AnswerCard"
import { MicButton } from "../voice/MicButton"
import { StatsFooter } from "../stats/StatsFooter"
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
}

export function ChatScreen({
  initialQuestion,
  quickQuestion,
  chipsSlot,
  onQuickAsk,
  currentLang,
  onLangChange,
}: ChatScreenProps = {}) {
  const [lang, setLang] = useState<Lang>(currentLang || "ro")
  const [draft, setDraft] = useState("")
  const [turns, setTurns] = useState<Turn[]>([])
  const [pending, setPending] = useState(false)
  const [failed, setFailed] = useState(false)
  const [lastQuestion, setLastQuestion] = useState("")
  const s = t(lang)

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

      <main className="chat__thread">
        {showEmpty && (
          <section className="welcome" aria-label={s.welcomeGreeting}>
            <div className="welcome__icon" aria-hidden="true">
              🏛️
            </div>
            <h2 className="welcome__title">{s.welcomeGreeting}</h2>
            <p className="welcome__subtitle">{s.welcomeSubtitle}</p>
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
        <label className="composer__label" htmlFor="question">
          {s.questionLabel}
        </label>
        <div className="composer__row">
          <input
            id="question"
            className="composer__input"
            type="text"
            value={draft}
            placeholder={s.questionPlaceholder}
            maxLength={1000}
            autoComplete="off"
            onChange={(event) => setDraft(event.target.value)}
          />
          <MicButton lang={lang} onTranscript={(text) => setDraft(text)} />
          <button type="submit" className="composer__submit" disabled={!canSend}>
            {pending ? s.sending : s.send}
          </button>
        </div>
      </form>

      <StatsFooter />
    </div>
  )
}
