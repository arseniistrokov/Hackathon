// Модалка «Deschide documentul»: открывается по клику на цитату в CitationCard.
// Данные берутся ИСКЛЮЧИТЕЛЬНО из уже полученного Citation — ничего не догружаем.
// Полный текст документа у нас нет, поэтому подсвечиваем сам цитируемый passage
// как единственный доступный фрагмент источника (честно, без выдумывания остального текста).
import { useEffect } from "react"
import type { Citation, Lang } from "@/api/types"
import { t } from "@/i18n"

export function DocumentViewer({
  citation,
  lang,
  onClose,
}: {
  citation: Citation
  lang: Lang
  onClose: () => void
}) {
  const s = t(lang)

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent): void {
      if (event.key === "Escape") onClose()
    }
    document.addEventListener("keydown", onKeyDown)
    return () => document.removeEventListener("keydown", onKeyDown)
  }, [onClose])

  return (
    <div className="doc-viewer-overlay" onClick={onClose}>
      <div
        className="doc-viewer"
        role="dialog"
        aria-modal="true"
        aria-label={citation.title}
        onClick={(event) => event.stopPropagation()}
      >
        <header className="doc-viewer__header">
          <h3 className="doc-viewer__title">{citation.title}</h3>
          <button
            type="button"
            className="doc-viewer__close-icon"
            aria-label={s.documentViewerCloseAria}
            onClick={onClose}
          >
            <XIcon />
          </button>
        </header>
        <div className="doc-viewer__meta">
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
        <div className="doc-viewer__body">
          <blockquote className="doc-viewer__passage">{citation.passage}</blockquote>
        </div>
        <footer className="doc-viewer__footer">
          <a
            className="doc-viewer__source-link"
            href={citation.url}
            target="_blank"
            rel="noreferrer"
          >
            {s.openSource}
            <ArrowRightIcon />
          </a>
          <button type="button" className="doc-viewer__close-btn" onClick={onClose}>
            {s.closeLabel}
          </button>
        </footer>
      </div>
    </div>
  )
}

function XIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <line x1="5" y1="5" x2="19" y2="19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <line x1="19" y1="5" x2="5" y2="19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

function ArrowRightIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
