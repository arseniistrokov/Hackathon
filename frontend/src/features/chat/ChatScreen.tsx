// Экран чата: ввод, переключатель ro/ru, история вопросов, загрузка и ошибка.
// Уровень L0/L1 переключает только api/client.ts — здесь про моки ничего не известно.
import { useState } from "react"
import { ask } from "@/api/client"
import type { AskResponse, Lang } from "@/api/types"
import { t } from "@/i18n"
import { AnswerCard } from "./AnswerCard"
import "./chat.css"

const MIN_QUESTION_LENGTH = 2 // AskRequest.question: min_length=2

interface Turn {
  id: number
  question: string
  response: AskResponse
}

export function ChatScreen() {
  const [lang, setLang] = useState<Lang>("ro")
  const [draft, setDraft] = useState("")
  const [turns, setTurns] = useState<Turn[]>([])
  const [pending, setPending] = useState(false)
  const [failed, setFailed] = useState(false)
  const [lastQuestion, setLastQuestion] = useState("")
  const s = t(lang)

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
                onClick={() => setLang(code)}
              >
                {code.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
      </header>

      <main className="chat__thread">
        {showEmpty && (
          <section className="chat__empty">
            <h2>{s.emptyTitle}</h2>
            <p>{s.emptyBody}</p>
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
          <button type="submit" className="composer__submit" disabled={!canSend}>
            {pending ? s.sending : s.send}
          </button>
        </div>
      </form>
    </div>
  )
}
