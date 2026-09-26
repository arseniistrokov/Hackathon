import { useEffect, useState } from "react"
import { getStats } from "@/api/client"
import type { Stats } from "@/api/types"
import "./stats.css"

export interface StatsFooterProps {
  stats?: Stats | null
  getStatsFn?: () => Promise<Stats>
}

export function StatsFooter({
  stats: propsStats,
  getStatsFn = getStats,
}: StatsFooterProps) {
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
          setError((err as Error).message || "Ошибка загрузки")
          setLoading(false)
        }
      })

    return () => {
      isMounted = false
    }
  }, [propsStats, getStatsFn])

  if (loading) {
    return (
      <footer className="stats-footer stats-footer--loading" role="status" aria-label="Статистика сервиса">
        <span className="stats-footer__loading">Загрузка статистики…</span>
      </footer>
    )
  }

  if (error || !stats) {
    return (
      <footer className="stats-footer stats-footer--empty" aria-label="Статистика сервиса">
        <span className="stats-footer__empty-msg">Статистика недоступна</span>
      </footer>
    )
  }

  return (
    <footer className="stats-footer" aria-label="Статистика сервиса">
      <div className="stats-footer__grid">
        <div className="stats-footer__item">
          <span className="stats-footer__label">Документы</span>
          <span className="stats-footer__value">{stats.corpus_documents ?? 0}</span>
        </div>
        <div className="stats-footer__item">
          <span className="stats-footer__label">Фрагменты</span>
          <span className="stats-footer__value">{stats.corpus_chunks ?? 0}</span>
        </div>
        <div className="stats-footer__item">
          <span className="stats-footer__label">Сайты</span>
          <span className="stats-footer__value">{stats.sites ?? 0}</span>
        </div>
        <div className="stats-footer__item">
          <span className="stats-footer__label">Конфликты</span>
          <span className="stats-footer__value">{stats.conflicts ?? 0}</span>
        </div>
        <div className="stats-footer__item">
          <span className="stats-footer__label">Запросы</span>
          <span className="stats-footer__value">{stats.queries ?? 0}</span>
        </div>
        <div className="stats-footer__item">
          <span className="stats-footer__label">Отзывы</span>
          <span className="stats-footer__value">
            👍 {stats.feedback_up ?? 0} · 👎 {stats.feedback_down ?? 0}
          </span>
        </div>
        <div className="stats-footer__item stats-footer__item--model">
          <span className="stats-footer__label">Модель</span>
          <span className="stats-footer__value">{stats.model ?? "—"}</span>
        </div>
      </div>
    </footer>
  )
}
