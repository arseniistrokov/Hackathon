import { useState } from "react"
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

interface ChatItem {
  id: string
  title: string
  isPinned: boolean
}

export function NexaSidebar({
  activeTab,
  onTabChange,
  onNewChat,
  recentQueries,
  onSelectQuery,
  lang,
  onLangChange: _onLangChange,
  isOpen,
  onClose,
}: NexaSidebarProps) {
  const s = t(lang)
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [showSearchModal, setShowSearchModal] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [showProfileMenu, setShowProfileMenu] = useState(false)
  const [profileSubmenu, setProfileSubmenu] = useState<"main" | "accounts" | "help">("main")
  const [showEditProfile, setShowEditProfile] = useState(false)
  const [displayName, setDisplayName] = useState("Andrei Popescu")
  const [userName, setUserName] = useState("andreipopescu")

  // Базовые закрепленные чаты по референсу Figma
  const [pinnedList, setPinnedList] = useState<ChatItem[]>([
    { id: "p1", title: "Regulament parcări Chișinău ..", isPinned: true },
    { id: "p2", title: "Tarife transport public și RTEC ..", isPinned: true },
    { id: "p3", title: "Program audiență preturi de sector ..", isPinned: true },
  ])

  // Недавние чаты (комбинация переданных recentQueries и дефолтных)
  const defaultRecentItems: ChatItem[] = [
    { id: "r1", title: "Termenul de examinare a petițiilor ..", isPinned: false },
    { id: "r2", title: "Abonamente călătorie elevi și studenți ..", isPinned: false },
    { id: "r3", title: "Contacte oficiale Primăria Chișinău ..", isPinned: false },
  ]

  const recentList: ChatItem[] = recentQueries.length > 0
    ? recentQueries.slice(0, 5).map((q, idx) => ({ id: `dyn-${idx}`, title: `${q} ..`, isPinned: false }))
    : defaultRecentItems

  function togglePin(item: ChatItem) {
    if (item.isPinned) {
      setPinnedList((prev) => prev.filter((p) => p.id !== item.id))
    } else {
      setPinnedList((prev) => [{ ...item, isPinned: true }, ...prev])
    }
  }

  const allSearchItems = [...pinnedList, ...recentList]
  const filteredSearch = searchQuery.trim()
    ? allSearchItems.filter((i) => i.title.toLowerCase().includes(searchQuery.toLowerCase()))
    : allSearchItems

  return (
    <>
      {isOpen && (
        <div
          className="nexa-sidebar-overlay"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Выпадающее меню профиля (Figma popover) */}
      {showProfileMenu && (
        <>
          <div
            className="nexa-popover-backdrop"
            onClick={() => {
              setShowProfileMenu(false)
              setProfileSubmenu("main")
            }}
            aria-hidden="true"
          />
          <div className="nexa-profile-popover" role="dialog" aria-label="User menu">
            {profileSubmenu === "main" && (
              <div className="nexa-popover-menu">
                <button
                  type="button"
                  className="nexa-popover-item nexa-popover-item--user"
                  onClick={() => setProfileSubmenu("accounts")}
                >
                  <div className="nexa-popover-avatar">A</div>
                  <span className="nexa-popover-text">{displayName}</span>
                  <svg className="nexa-popover-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="9 18 15 12 9 6" />
                  </svg>
                </button>

                <div className="nexa-popover-divider" />

                <button
                  type="button"
                  className="nexa-popover-item"
                  onClick={() => {
                    setShowProfileMenu(false)
                    setShowEditProfile(true)
                  }}
                >
                  <svg className="nexa-popover-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                    <circle cx="12" cy="7" r="4" />
                  </svg>
                  <span>Profile</span>
                </button>

                <button
                  type="button"
                  className="nexa-popover-item"
                  onClick={() => setShowProfileMenu(false)}
                >
                  <svg className="nexa-popover-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="3" />
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
                  </svg>
                  <span>Settings</span>
                </button>

                <div className="nexa-popover-divider" />

                <button
                  type="button"
                  className="nexa-popover-item"
                  onClick={() => setProfileSubmenu("help")}
                >
                  <svg className="nexa-popover-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                    <line x1="12" y1="17" x2="12.01" y2="17" />
                  </svg>
                  <span>Help</span>
                  <svg className="nexa-popover-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="9 18 15 12 9 6" />
                  </svg>
                </button>

                <button
                  type="button"
                  className="nexa-popover-item"
                  onClick={() => setShowProfileMenu(false)}
                >
                  <svg className="nexa-popover-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                    <polyline points="16 17 21 12 16 7" />
                    <line x1="21" y1="12" x2="9" y2="12" />
                  </svg>
                  <span>Log out</span>
                </button>
              </div>
            )}

            {profileSubmenu === "accounts" && (
              <div className="nexa-popover-menu">
                <button
                  type="button"
                  className="nexa-popover-back-btn"
                  onClick={() => setProfileSubmenu("main")}
                >
                  ← Back
                </button>
                <div className="nexa-account-item">
                  <svg className="nexa-popover-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                    <circle cx="12" cy="7" r="4" />
                  </svg>
                  <span className="nexa-account-email">andreipopescu@gmail.com</span>
                </div>
                <div className="nexa-account-item nexa-account-item--active">
                  <div className="nexa-popover-avatar">A</div>
                  <span className="nexa-account-name">{displayName}</span>
                  <svg className="nexa-checkmark" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                </div>
                <div className="nexa-popover-divider" />
                <button
                  type="button"
                  className="nexa-popover-item nexa-add-account-btn"
                  onClick={() => setShowProfileMenu(false)}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
                    <line x1="12" y1="5" x2="12" y2="19" />
                    <line x1="5" y1="12" x2="19" y2="12" />
                  </svg>
                  <span>Add account</span>
                </button>
              </div>
            )}

            {profileSubmenu === "help" && (
              <div className="nexa-popover-menu">
                <button
                  type="button"
                  className="nexa-popover-back-btn"
                  onClick={() => setProfileSubmenu("main")}
                >
                  ← Back
                </button>
                <button type="button" className="nexa-popover-item">
                  <svg className="nexa-popover-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                    <line x1="12" y1="17" x2="12.01" y2="17" />
                  </svg>
                  <span>Help center</span>
                </button>
                <button type="button" className="nexa-popover-item">
                  <svg className="nexa-popover-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                  </svg>
                  <span>Privacy Center</span>
                </button>
                <button type="button" className="nexa-popover-item">
                  <svg className="nexa-popover-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="3" y="3" width="18" height="18" rx="2" />
                    <path d="M7 8h10M7 12h10M7 16h6" />
                  </svg>
                  <span>Keyboard shortcuts</span>
                </button>
                <div className="nexa-popover-divider" />
                <button type="button" className="nexa-popover-item">
                  <svg className="nexa-popover-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                  </svg>
                  <span>Terms of Service</span>
                </button>
                <button type="button" className="nexa-popover-item">
                  <svg className="nexa-popover-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="16" x2="12" y2="12" />
                    <line x1="12" y1="8" x2="12.01" y2="8" />
                  </svg>
                  <span>Privacy Policy</span>
                </button>
              </div>
            )}
          </div>
        </>
      )}

      {/* Модалка редактирования профиля (Figma Frame 92) */}
      {showEditProfile && (
        <div className="nexa-modal-overlay">
          <div className="nexa-edit-profile-card">
            <h2 className="nexa-edit-profile-title">Edit profile</h2>
            <div className="nexa-edit-profile-avatar-wrap">
              <div className="nexa-large-avatar">
                <span>A</span>
                <button type="button" className="nexa-avatar-camera-btn" aria-label="Upload avatar">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                    <circle cx="12" cy="13" r="4" />
                  </svg>
                </button>
              </div>
            </div>

            <div className="nexa-form-group">
              <label className="nexa-form-label">Display name</label>
              <input
                type="text"
                className="nexa-form-input"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
              />
            </div>

            <div className="nexa-form-group">
              <label className="nexa-form-label">Username</label>
              <input
                type="text"
                className="nexa-form-input"
                value={userName}
                onChange={(e) => setUserName(e.target.value)}
              />
            </div>

            <div className="nexa-modal-actions">
              <button
                type="button"
                className="nexa-btn-cancel"
                onClick={() => setShowEditProfile(false)}
              >
                Cancel
              </button>
              <button
                type="button"
                className="nexa-btn-save"
                onClick={() => setShowEditProfile(false)}
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Модалка поиска (Figma Search modal) */}
      {showSearchModal && (
        <div className="nexa-modal-overlay" onClick={() => setShowSearchModal(false)}>
          <div className="nexa-search-card" onClick={(e) => e.stopPropagation()}>
            <div className="nexa-search-header">
              <input
                type="text"
                className="nexa-search-input"
                placeholder="Search..."
                autoFocus
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <button
                type="button"
                className="nexa-search-close-btn"
                onClick={() => setShowSearchModal(false)}
                aria-label="Close search"
              >
                ✕
              </button>
            </div>

            <div className="nexa-search-body">
              <div className="nexa-search-title">Recent chats</div>
              <ul className="nexa-search-list">
                {filteredSearch.map((item) => (
                  <li key={item.id} className="nexa-search-item">
                    <button
                      type="button"
                      className="nexa-search-item-btn"
                      onClick={() => {
                        onSelectQuery(item.title.replace(/\s\.\.$/, ""))
                        if (activeTab !== "assistant") onTabChange("assistant")
                        setShowSearchModal(false)
                      }}
                    >
                      <span className="nexa-bubble-icon" aria-hidden="true" />
                      <span className="nexa-search-item-text">{item.title}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Сайдбар */}
      <aside className={`nexa-sidebar ${isOpen ? "nexa-sidebar--open" : ""} ${isCollapsed ? "nexa-sidebar--collapsed" : ""}`}>
        {/* Шапка брендинга */}
        <div className="nexa-sidebar__brand">
          {!isCollapsed ? (
            <>
              <div className="nexa-brand-logo" aria-label="nexa">
                <span className="nexa-brand-logo__text">ne</span>
                <span className="nexa-brand-logo__x" aria-hidden="true">
                  <svg width="22" height="24" viewBox="0 0 24 24" fill="none">
                    <path d="M3 6.5C7.5 13 16.5 13 21 6.5" stroke="var(--c-nexa-blue)" strokeWidth="3.4" strokeLinecap="round" />
                    <path d="M3 17.5C7.5 11 16.5 11 21 17.5" stroke="var(--c-send)" strokeWidth="3.4" strokeLinecap="round" />
                  </svg>
                </span>
                <span className="nexa-brand-logo__text">a</span>
              </div>

              <div className="nexa-sidebar__brand-actions">
                <button
                  type="button"
                  className="nexa-tool-btn"
                  title="Search"
                  aria-label="Search"
                  onClick={() => setShowSearchModal(true)}
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="11" cy="11" r="8" />
                    <line x1="21" y1="21" x2="16.65" y2="16.65" />
                  </svg>
                </button>
                <button
                  type="button"
                  className="nexa-tool-btn"
                  title="Collapse sidebar"
                  aria-label="Collapse sidebar"
                  onClick={() => setIsCollapsed(true)}
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="3" width="18" height="18" rx="2" />
                    <line x1="9" y1="3" x2="9" y2="21" />
                  </svg>
                </button>
              </div>
            </>
          ) : (
            <div className="nexa-collapsed-header">
              <button
                type="button"
                className="nexa-collapsed-logo-btn"
                onClick={() => setIsCollapsed(false)}
                title="Expand sidebar"
                aria-label="Expand sidebar"
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                  <path d="M4 6.5C8 12.5 16 12.5 20 6.5" stroke="var(--c-nexa-blue)" strokeWidth="3.2" strokeLinecap="round" />
                  <path d="M4 17.5C8 11.5 16 11.5 20 17.5" stroke="var(--c-send)" strokeWidth="3.2" strokeLinecap="round" />
                </svg>
              </button>
            </div>
          )}
        </div>

        {/* Действие: New chat */}
        <div className="nexa-sidebar__actions">
          <button
            type="button"
            className="nexa-new-chat-btn"
            title={s.nexaNewChat}
            onClick={() => {
              onNewChat()
              if (activeTab !== "assistant") onTabChange("assistant")
              onClose()
            }}
          >
            <span className="nexa-new-chat-btn__icon" aria-hidden="true">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 20h9" />
                <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
              </svg>
            </span>
            {!isCollapsed && <span>{s.nexaNewChat}</span>}
          </button>
        </div>

        {/* Навигация / Свернутые иконки */}
        {isCollapsed && (
          <div className="nexa-collapsed-nav">
            <button
              type="button"
              className="nexa-collapsed-item"
              title="Search"
              onClick={() => {
                setShowSearchModal(true)
              }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
            </button>
            <button
              type="button"
              className="nexa-collapsed-item"
              title="Pinned"
              onClick={() => setIsCollapsed(false)}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="17" x2="12" y2="22" />
                <path d="M5 17h14v-2l-2-2V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v8l-2 2v2z" />
              </svg>
            </button>
            <button
              type="button"
              className="nexa-collapsed-item"
              title="Recents"
              onClick={() => setIsCollapsed(false)}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <polyline points="12 6 12 12 16 14" />
              </svg>
            </button>
          </div>
        )}

        {/* Развернутые списки Pinned и Recents */}
        {!isCollapsed && (
          <div className="nexa-sidebar__scroll-area">
            {/* Секция Pinned */}
            <div className="nexa-sidebar__section">
              <div className="nexa-sidebar__section-header">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="12" y1="17" x2="12" y2="22" />
                  <path d="M5 17h14v-2l-2-2V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v8l-2 2v2z" />
                </svg>
                <span>{s.pinnedLabel}</span>
              </div>
              <ul className="nexa-item-list">
                {pinnedList.map((item) => (
                  <li key={item.id} className="nexa-chat-row">
                    <button
                      type="button"
                      className="nexa-chat-row__btn"
                      onClick={() => {
                        onSelectQuery(item.title.replace(/\s\.\.$/, ""))
                        if (activeTab !== "assistant") onTabChange("assistant")
                        onClose()
                      }}
                      title={item.title}
                    >
                      <span className="nexa-bubble-icon" aria-hidden="true" />
                      <span className="nexa-chat-row__title">{item.title}</span>
                    </button>
                    <div className="nexa-chat-row__actions">
                      <button
                        type="button"
                        className="nexa-row-action-btn"
                        title="Unpin"
                        onClick={(e) => {
                          e.stopPropagation()
                          togglePin(item)
                        }}
                      >
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <line x1="2" y1="2" x2="22" y2="22" />
                          <line x1="12" y1="17" x2="12" y2="22" />
                          <path d="M5 17h14v-2l-2-2V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v8l-2 2v2z" />
                        </svg>
                      </button>
                      <button
                        type="button"
                        className="nexa-row-action-btn"
                        title="More"
                        onClick={(e) => e.stopPropagation()}
                      >
                        •••
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            </div>

            {/* Секция Recents */}
            <div className="nexa-sidebar__section">
              <div className="nexa-sidebar__section-header">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 16 14" />
                </svg>
                <span>{s.recentLabel}</span>
              </div>
              <ul className="nexa-item-list">
                {recentList.map((item) => (
                  <li key={item.id} className="nexa-chat-row">
                    <button
                      type="button"
                      className="nexa-chat-row__btn"
                      onClick={() => {
                        onSelectQuery(item.title.replace(/\s\.\.$/, ""))
                        if (activeTab !== "assistant") onTabChange("assistant")
                        onClose()
                      }}
                      title={item.title}
                    >
                      <span className="nexa-chat-row__title">{item.title}</span>
                    </button>
                    <div className="nexa-chat-row__actions">
                      <button
                        type="button"
                        className="nexa-row-action-btn"
                        title="Pin"
                        onClick={(e) => {
                          e.stopPropagation()
                          togglePin(item)
                        }}
                      >
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <line x1="12" y1="17" x2="12" y2="22" />
                          <path d="M5 17h14v-2l-2-2V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v8l-2 2v2z" />
                        </svg>
                      </button>
                      <button
                        type="button"
                        className="nexa-row-action-btn"
                        title="More"
                        onClick={(e) => e.stopPropagation()}
                      >
                        •••
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Футер: профиль пользователя (Figma frame) */}
        <div className="nexa-sidebar__footer">
          <button
            type="button"
            className="nexa-user-pill"
            onClick={() => {
              setShowProfileMenu((prev) => !prev)
              setProfileSubmenu("main")
            }}
            aria-expanded={showProfileMenu}
            title={displayName}
          >
            <div className="nexa-avatar">A</div>
            {!isCollapsed && <span className="nexa-user-name">{displayName}</span>}
          </button>
        </div>
      </aside>
    </>
  )
}
