// Экран "Despre proiect": отдельная вьюха для жюри, переключается из сайдбара через state
// (без роутера — см. ChatScreen: view === "about"). Данные — только из getStats(), ничего не выдумываем.
import { useEffect, useState } from "react"
import { getStats } from "@/api/client"
import type { Lang, Stats } from "@/api/types"
import { t } from "@/i18n"
import "./stats.css"

export function AboutScreen({
  lang,
  onBack,
  getStatsFn = getStats,
}: {
  lang: Lang
  onBack: () => void
  getStatsFn?: () => Promise<Stats>
}) {
  const s = t(lang)
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    let isMounted = true
    setLoading(true)
    setError(false)
    getStatsFn()
      .then((data) => {
        if (isMounted) {
          setStats(data)
          setLoading(false)
        }
      })
      .catch(() => {
        if (isMounted) {
          setError(true)
          setLoading(false)
        }
      })
    return () => {
      isMounted = false
    }
  }, [getStatsFn])

  const tiles: Array<{ key: string; label: string; value: string; icon: React.ReactNode }> = stats
    ? [
        { key: "documents", label: s.statsDocuments, value: String(stats.corpus_documents ?? 0), icon: <DocIcon /> },
        { key: "chunks", label: s.statsChunks, value: String(stats.corpus_chunks ?? 0), icon: <ListIcon /> },
        { key: "sites", label: s.statsSites, value: String(stats.sites ?? 0), icon: <GlobeIcon /> },
        { key: "conflicts", label: s.statsConflicts, value: String(stats.conflicts ?? 0), icon: <ShieldIcon /> },
        { key: "queries", label: s.statsQueries, value: String(stats.queries ?? 0), icon: <SearchIcon /> },
        {
          key: "feedback",
          label: s.statsFeedback,
          value: `👍 ${stats.feedback_up ?? 0} · 👎 ${stats.feedback_down ?? 0}`,
          icon: <ChatIcon />,
        },
      ]
    : []

  return (
    <div className="about">
      <div className="about__topbar">
        <span className="about__logo">
          {s.logoText.split("").map((char, index) =>
            char.toLowerCase() === "x" ? (
              <span key={index} className="sidebar__logo-x">
                {char}
              </span>
            ) : (
              <span key={index}>{char}</span>
            )
          )}
        </span>
        <button type="button" className="about__back" onClick={onBack}>
          <ArrowLeftIcon />
          {s.backToChatLabel}
        </button>
      </div>

      <h1 className="about__title">{s.aboutTitle}</h1>
      <p className="about__subtitle">{s.aboutSubtitle}</p>

      {loading && <p className="about__status">{s.statsLoading}</p>}
      {error && !loading && <p className="about__status">{s.statsUnavailable}</p>}

      {!loading && !error && (
        <>
          <div className="about__grid">
            {tiles.map((tile) => (
              <div className="about__tile" key={tile.key}>
                <div className="about__tile-head">
                  <span className="about__tile-label">{tile.label}</span>
                  <span className="about__tile-icon">{tile.icon}</span>
                </div>
                <span className="about__tile-value">{tile.value}</span>
              </div>
            ))}
          </div>

          <div className="about__secondary">
            <span className="about__model-label">{s.statsModel}</span>
            <span className="about__model-badge">{stats?.model ?? "—"}</span>
          </div>

          <div className="about__how">
            <h2 className="about__how-title">{s.aboutHowItWorksTitle}</h2>
            <p className="about__how-body">{s.aboutHowItWorksBody}</p>
          </div>
        </>
      )}

      <p className="about__footer-note">{s.aboutFooterNote}</p>
    </div>
  )
}

function DocIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M6 3h8l4 4v14H6V3Z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
      <path d="M14 3v4h4" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
    </svg>
  )
}

function ListIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <line x1="9" y1="7" x2="19" y2="7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <line x1="9" y1="12" x2="19" y2="12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <line x1="9" y1="17" x2="19" y2="17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <circle cx="5" cy="7" r="1.2" fill="currentColor" />
      <circle cx="5" cy="12" r="1.2" fill="currentColor" />
      <circle cx="5" cy="17" r="1.2" fill="currentColor" />
    </svg>
  )
}

function GlobeIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2" />
      <path d="M3 12h18M12 3c2.5 2.5 4 5.7 4 9s-1.5 6.5-4 9c-2.5-2.5-4-5.7-4-9s1.5-6.5 4-9Z" stroke="currentColor" strokeWidth="2" />
    </svg>
  )
}

function ShieldIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3Z" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
      <line x1="12" y1="9" x2="12" y2="13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <circle cx="12" cy="16" r="1" fill="currentColor" />
    </svg>
  )
}

function SearchIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

function ChatIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M4 5h16v11H9l-5 4V5Z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function ArrowLeftIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M19 12H5M11 6l-6 6 6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
