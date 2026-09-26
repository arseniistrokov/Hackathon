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
              <svg width="24" height="24" viewBox="0 0 28 28" fill="none">
                <circle cx="8" cy="14" r="6" stroke="var(--c-nexa-cyan)" strokeWidth="2.8" />
                <circle cx="20" cy="14" r="6" stroke="var(--c-send)" strokeWidth="2.8" />
                <path d="M12 10L16 18" stroke="var(--c-nexa-blue)" strokeWidth="2.4" strokeLinecap="round" />
              </svg>
            </span>
            <span className="nexa-logo__text">nexa</span>
          </div>
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
            <span className="nexa-new-chat-btn__icon" aria-hidden="true">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="16" />
                <line x1="8" y1="12" x2="16" y2="12" />
              </svg>
            </span>
            <span>{s.nexaNewChat}</span>
          </button>
        </div>

        <nav className="nexa-sidebar__nav" aria-label="Разделы">
          <button
            type="button"
            className={`nexa-nav-item ${activeTab === "services" ? "nexa-nav-item--active" : ""}`}
            onClick={() => {
              onTabChange("services")
              onClose()
            }}
          >
            <span className="nexa-nav-item__icon" aria-hidden="true">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
            </span>
            <span>{s.searchLabel}</span>
          </button>
          <button
            type="button"
            className={`nexa-nav-item ${activeTab === "contacts" ? "nexa-nav-item--active" : ""}`}
            onClick={() => {
              onTabChange("contacts")
              onClose()
            }}
          >
            <span className="nexa-nav-item__icon" aria-hidden="true">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="17" x2="12" y2="22" />
                <path d="M5 17h14v-2l-2-2V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v8l-2 2v2z" />
              </svg>
            </span>
            <span>{s.pinnedLabel}</span>
          </button>
        </nav>

        <div className="nexa-sidebar__recent">
          <div className="nexa-sidebar__section-title">
            {s.recentLabel}
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
                  <span className="nexa-recent-btn__text">{q} ..</span>
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div className="nexa-sidebar__footer">
          <div className="nexa-user-profile">
            <button
              type="button"
              className="nexa-avatar"
              onClick={() => onLangChange(lang === "ro" ? "ru" : "ro")}
              title={`Limbă: ${lang.toUpperCase()}`}
              aria-label={`Schimbă limba (${lang.toUpperCase()})`}
            >
              A
            </button>
            <div className="nexa-user-info">
              <span className="nexa-user-name">Andrei</span>
            </div>
          </div>

          <div className="nexa-sidebar__footer-icons">
            <button
              type="button"
              className="nexa-icon-btn"
              title="Settings"
              aria-label="Settings"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <circle cx="12" cy="12" r="3" />
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
              </svg>
            </button>
            <button
              type="button"
              className="nexa-icon-btn"
              title="Help"
              aria-label="Help"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <circle cx="12" cy="12" r="10" />
                <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
            </button>
          </div>
        </div>
      </aside>
    </>
  )
}
