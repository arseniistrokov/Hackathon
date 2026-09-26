import type { Lang } from "@/api/types"
import type { PortalTab } from "./PortalLayout"
import { t } from "@/i18n"

export interface NexaSidebarProps {
  activeTab: PortalTab
  onTabChange: (tab: PortalTab) => void
  onNewChat: () => void
  recentQueries: string[]
  onSelectQuery: (query: string) => void
  lang: Lang
  onLangChange: (lang: Lang) => void
  isOpen: boolean
  onClose: () => void
}

export function NexaSidebar({
  activeTab,
  onTabChange,
  onNewChat,
  recentQueries,
  onSelectQuery,
  lang,
  onLangChange,
  isOpen,
  onClose,
}: NexaSidebarProps) {
  const isRu = lang === "ru"
  const s = t(lang)

  const defaultRecent = isRu
    ? [
        "Тарифы на проезд в троллейбусе",
        "Сроки рассмотрения петиций",
        "Приём граждан в претуре",
      ]
    : [
        "Tarife călătorie troleibuz RTEC",
        "Termenul de examinare a petițiilor",
        "Program audiență pretură",
      ]

  const queries = recentQueries.length > 0 ? recentQueries : defaultRecent

  return (
    <>
      {isOpen && (
        <div
          className="nexa-sidebar-overlay"
          onClick={onClose}
          aria-hidden="true"
        />
      )}
      <aside className={`nexa-sidebar ${isOpen ? "nexa-sidebar--open" : ""}`}>
        <div className="nexa-sidebar__brand">
          <div className="nexa-logo">
            <span className="nexa-logo__symbol" aria-hidden="true">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                <circle cx="7" cy="12" r="5" stroke="var(--c-nexa-cyan)" strokeWidth="2.5" />
                <circle cx="17" cy="12" r="5" stroke="var(--c-nexa-blue)" strokeWidth="2.5" />
                <path d="M10 9L14 15" stroke="var(--c-accent)" strokeWidth="2" strokeLinecap="round" />
              </svg>
            </span>
            <span className="nexa-logo__text">nexa</span>
          </div>
          <span className="nexa-sidebar__tag">Chișinău Smart City</span>
        </div>

        <div className="nexa-sidebar__actions">
          <button
            type="button"
            className="nexa-new-chat-btn"
            onClick={() => {
              onNewChat()
              if (activeTab !== "assistant") onTabChange("assistant")
              onClose()
            }}
          >
            <span className="nexa-new-chat-btn__icon" aria-hidden="true">+</span>
            <span>{s.nexaNewChat}</span>
          </button>
        </div>

        <nav className="nexa-sidebar__nav" aria-label="Разделы">
          <button
            type="button"
            className={`nexa-nav-item ${activeTab === "assistant" ? "nexa-nav-item--active" : ""}`}
            onClick={() => {
              onTabChange("assistant")
              onClose()
            }}
          >
            <span className="nexa-nav-item__icon" aria-hidden="true">💬</span>
            <span>{isRu ? "AI-Ассистент" : "AI Assistant"}</span>
          </button>
          <button
            type="button"
            className={`nexa-nav-item ${activeTab === "services" ? "nexa-nav-item--active" : ""}`}
            onClick={() => {
              onTabChange("services")
              onClose()
            }}
          >
            <span className="nexa-nav-item__icon" aria-hidden="true">📋</span>
            <span>{isRu ? "Услуги" : "Servicii"}</span>
          </button>
          <button
            type="button"
            className={`nexa-nav-item ${activeTab === "contacts" ? "nexa-nav-item--active" : ""}`}
            onClick={() => {
              onTabChange("contacts")
              onClose()
            }}
          >
            <span className="nexa-nav-item__icon" aria-hidden="true">🏛️</span>
            <span>{isRu ? "Контакты" : "Contacte"}</span>
          </button>
        </nav>

        <div className="nexa-sidebar__recent">
          <div className="nexa-sidebar__section-title">
            {s.nexaRecentTitle}
          </div>
          <ul className="nexa-recent-list">
            {queries.slice(0, 3).map((q, idx) => (
              <li key={idx} className="nexa-recent-item">
                <button
                  type="button"
                  className="nexa-recent-btn"
                  onClick={() => {
                    onSelectQuery(q)
                    if (activeTab !== "assistant") onTabChange("assistant")
                    onClose()
                  }}
                  title={q}
                >
                  <span className="nexa-recent-btn__bullet" aria-hidden="true">›</span>
                  <span className="nexa-recent-btn__text">{q}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div className="nexa-sidebar__footer">
          <div className="nexa-user-profile">
            <div className="nexa-avatar" aria-hidden="true">A</div>
            <div className="nexa-user-info">
              <span className="nexa-user-name">Andrei</span>
            </div>
          </div>

          <div className="nexa-lang-switch" role="group" aria-label="Limbă / Язык">
            {(["ro", "ru"] as const).map((code) => (
              <button
                key={code}
                type="button"
                className="nexa-lang-btn"
                aria-pressed={lang === code}
                onClick={() => onLangChange(code)}
              >
                {code.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
      </aside>
    </>
  )
}
