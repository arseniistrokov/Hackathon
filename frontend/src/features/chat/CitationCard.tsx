// Карточка цитаты: дословный passage из базы + путь до документа. Passage не обрезается.
import type { Citation, Lang } from "@/api/types"
import { t } from "@/i18n"

export function CitationCard({ citation, lang }: { citation: Citation; lang: Lang }) {
  const s = t(lang)
  return (
    <article className="citation animate-fade-in-up">
      <h4 className="citation__title">{citation.title}</h4>
      <div className="citation__crumbs">
        <span>{citation.site}</span>
        {citation.section && (
          <span>
            {s.sectionLabel}: {citation.section}
          </span>
        )}
        {citation.page != null && (
          <span>
            {s.pageLabel} {citation.page}
          </span>
        )}
        <span>{citation.date ? <time dateTime={citation.date}>{citation.date}</time> : s.undatedLabel}</span>
      </div>
      <blockquote className="citation__passage">{citation.passage}</blockquote>
      <a
        className="citation__link"
        href={citation.url}
        target="_blank"
        rel="noreferrer"
        aria-label={s.openDocumentAria}
      >
        {s.openDocument}
      </a>
    </article>
  )
}
