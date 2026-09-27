import { useEffect, useState } from "react"
import { getStats } from "@/api/client"
import type { Lang, Stats } from "@/api/types"
import { t } from "@/i18n"
import "./stats.css"

export interface StatsFooterProps {
  lang?: Lang
  stats?: Stats | null
  getStatsFn?: () => Promise<Stats>
}

export function StatsFooter({
  lang = "ru",
  stats: propsStats,
  getStatsFn = getStats,
}: StatsFooterProps) {
  const s = t(lang)
  const [stats, setStats] = useState<Stats | null>(propsStats ?? null)
  const [loading, setLoading] = useState<boolean>(propsStats === undefined)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (propsStats !== undefined) {
      setStats(propsStats)
      setLoading(false)
      return
    }

    let isMounted = true
    setLoading(true)
    setError(null)

    getStatsFn()
      .then((data) => {
        if (isMounted) {
          setStats(data)
          setLoading(false)
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError((err as Error).message || s.statsUnavailable)
          setLoading(false)
        }
      })

    return () => {
      isMounted = false
    }
  }, [propsStats, getStatsFn])

  if (loading) {
    return (
      <footer className="stats-footer stats-footer--loading" role="status" aria-label={s.statsAriaLabel}>
        <span className="stats-footer__loading">{s.statsLoading}</span>
      </footer>
    )
  }

  if (error || !stats) {
    return (
      <footer className="stats-footer stats-footer--empty" aria-label={s.statsAriaLabel}>
        <span className="stats-footer__empty-msg">{s.statsUnavailable}</span>
      </footer>
    )
  }

  return (
    <footer className="stats-footer" aria-label={s.statsAriaLabel}>
      <div className="stats-footer__grid">
        <div className="stats-footer__item">
          <span className="stats-footer__label">{s.statsDocuments}</span>
          <span className="stats-footer__value">{stats.corpus_documents ?? 0}</span>
        </div>
        <div className="stats-footer__item">
          <span className="stats-footer__label">{s.statsChunks}</span>
          <span className="stats-footer__value">{stats.corpus_chunks ?? 0}</span>
        </div>
        <div className="stats-footer__item">
          <span className="stats-footer__label">{s.statsSites}</span>
          <span className="stats-footer__value">{stats.sites ?? 0}</span>
        </div>
        <div className="stats-footer__item">
          <span className="stats-footer__label">{s.statsConflicts}</span>
          <span className="stats-footer__value">{stats.conflicts ?? 0}</span>
        </div>
        <div className="stats-footer__item">
          <span className="stats-footer__label">{s.statsQueries}</span>
          <span className="stats-footer__value">{stats.queries ?? 0}</span>
        </div>
        <div className="stats-footer__item">
          <span className="stats-footer__label">{s.statsFeedback}</span>
          <span className="stats-footer__value">
            👍 {stats.feedback_up ?? 0} · 👎 {stats.feedback_down ?? 0}
          </span>
        </div>
        <div className="stats-footer__item stats-footer__item--model">
          <span className="stats-footer__label">{s.statsModel}</span>
          <span className="stats-footer__value">{stats.model ?? "—"}</span>
        </div>
      </div>
    </footer>
  )
}
