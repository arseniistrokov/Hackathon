// Образец: switch по status, опциональные поля условно, строки из i18n, цвета только токенами.
import type { AskResponse } from "@/api/types"
import { t } from "@/i18n"

export function AnswerCardExample({ r }: { r: AskResponse }) {
  const s = t(r.language)
  if (r.status === "NOT_FOUND") {
    return (
      <section className="answer answer--not-found">
        <h3>{s.notFoundTitle}</h3>
        <p>{s.notFoundBody(r.meta.corpus_documents, r.meta.passages_used)}</p>
      </section>
    )
  }
  if (r.status === "CONFLICT" && r.conflict) {
    return (
      <section className="answer answer--conflict">
        <p>{r.answer}</p>
        <div className="conflict-grid">
          {[r.conflict.a, r.conflict.b].map((side, i) => (
            <article key={i}>
              <strong>{side.value}</strong>
              {side.date && <time>{side.date}</time>}
              <blockquote>{side.citation.passage}</blockquote>
              <a href={side.citation.url} target="_blank" rel="noreferrer">{s.openDocument}</a>
            </article>
          ))}
        </div>
      </section>
    )
  }
  return (
    <section className="answer answer--answered">
      {r.warning && <div className="banner">{r.warning}</div>}
      <p>{r.answer}</p>
      {r.citations.map((c) => (
        <article key={c.chunk_id} className="citation">
          <header>{c.title}{c.section && <> · {c.section}</>}{c.page != null && <> · p. {c.page}</>}</header>
          <blockquote>{c.passage}</blockquote>
          <a href={c.url} target="_blank" rel="noreferrer">{s.openDocument}</a>
        </article>
      ))}
      {r.navigation && <a href={r.navigation.url}>{r.navigation.label}</a>}
    </section>
  )
}
