// Три состояния ответа: ANSWERED · NOT_FOUND · CONFLICT. Строки — из i18n по языку ОТВЕТА.
// Опциональные поля (warning, navigation, conflict, section, page, date) рисуются условно:
// и null от бэкенда, и отсутствующее поле не должны ронять экран.
import type { AskResponse, Citation, ConflictSide, Lang, Meta, Navigation } from "@/api/types"
import { t } from "@/i18n"
import { CitationCard } from "./CitationCard"
import { FeedbackBar } from "../feedback/FeedbackBar"

function MetaRow({ meta, lang }: { meta: Meta; lang: Lang }) {
  const s = t(lang)
  return (
    <p className="meta">
      <span>{s.metaCorpus(meta.corpus_documents, meta.corpus_chunks)}</span>
      <span>{s.metaPassages(meta.passages_retrieved, meta.passages_used)}</span>
      <span>
        {s.metaModel}: {meta.model}
      </span>
      <span>{s.metaLatency(meta.latency_ms)}</span>
    </p>
  )
}

function NavigationRow({ navigation, lang }: { navigation: Navigation; lang: Lang }) {
  const s = t(lang)
  return (
    <div className="navigation">
      <span className="navigation__label">{s.navigationLabel}</span>
      <a className="navigation__link" href={navigation.url} target="_blank" rel="noreferrer">
        {navigation.label}
      </a>
    </div>
  )
}

function ConflictColumn({
  side,
  index,
  lang,
  onOpenDocument,
}: {
  side: ConflictSide
  index: number
  lang: Lang
  onOpenDocument?: (citation: Citation) => void
}) {
  const s = t(lang)
  const date = side.date ?? side.citation.date
  return (
    <div className="conflict-side">
      <span className="conflict-side__label">{s.conflictSide(index)}</span>
      <strong className="conflict-side__value">{side.value}</strong>
      <span className="conflict-side__date">
        {date ? <time dateTime={date}>{date}</time> : s.undatedLabel}
      </span>
      <CitationCard citation={side.citation} lang={lang} onOpenDocument={onOpenDocument} />
    </div>
  )
}

export function AnswerCard({
  response,
  onOpenDocument,
}: {
  response: AskResponse
  onOpenDocument?: (citation: Citation) => void
}) {
  const lang = response.language
  const s = t(lang)

  if (response.status === "NOT_FOUND") {
    return (
      <section className="answer answer--not-found" aria-live="polite">
        <span className="answer__status">{s.notFoundLabel}</span>
        <h3 className="answer__heading">{s.notFoundTitle}</h3>
        <p className="answer__text">{s.notFoundBody(response.meta.corpus_documents, response.meta.passages_used)}</p>
        {response.navigation && <NavigationRow navigation={response.navigation} lang={lang} />}
        <FeedbackBar queryId={response.meta.query_id} lang={lang} />
        <MetaRow meta={response.meta} lang={lang} />
      </section>
    )
  }

  // status === CONFLICT без объекта conflict быть не должно, но если пришёл — показываем ответ
  // и обе цитаты обычным списком, а не падаем.
  if (response.status === "CONFLICT" && response.conflict) {
    const conflict = response.conflict
    return (
      <section className="answer answer--conflict" aria-live="polite">
        <span className="answer__status">{s.conflictLabel}</span>
        <h3 className="answer__heading">{s.conflictTitle}</h3>
        <p className="answer__text">{response.answer}</p>
        <dl className="conflict__entity">
          <dt>{s.conflictEntity}</dt>
          <dd>{conflict.entity}</dd>
        </dl>
        <div className="conflict-grid">
          <ConflictColumn side={conflict.a} index={1} lang={lang} onOpenDocument={onOpenDocument} />
          <ConflictColumn side={conflict.b} index={2} lang={lang} onOpenDocument={onOpenDocument} />
        </div>
        {response.navigation && <NavigationRow navigation={response.navigation} lang={lang} />}
        <FeedbackBar queryId={response.meta.query_id} lang={lang} />
        <MetaRow meta={response.meta} lang={lang} />
      </section>
    )
  }

  const statusClass = response.status === "CONFLICT" ? "answer--conflict" : "answer--answered"
  const statusLabel = response.status === "CONFLICT" ? s.conflictLabel : s.answeredLabel
  return (
    <section className={`answer ${statusClass}`} aria-live="polite">
      <span className="answer__status">{statusLabel}</span>
      {response.warning && (
        <div className="banner">
          <span className="banner__label">{s.warningLabel}</span>
          <span>{response.warning}</span>
        </div>
      )}
      <p className="answer__text">{response.answer}</p>
      {response.citations.length > 0 && (
        <>
          <h4 className="section-label">{s.sourcesLabel}</h4>
          {response.citations.map((citation) => (
            <CitationCard
              key={citation.chunk_id}
              citation={citation}
              lang={lang}
              onOpenDocument={onOpenDocument}
            />
          ))}
        </>
      )}
      {response.navigation && <NavigationRow navigation={response.navigation} lang={lang} />}
      <FeedbackBar queryId={response.meta.query_id} lang={lang} />
      <MetaRow meta={response.meta} lang={lang} />
    </section>
  )
}
