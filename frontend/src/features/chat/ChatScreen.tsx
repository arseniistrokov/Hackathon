// Экран чата: ввод, переключатель ro/ru, сайдбар (Pinned/Recents), история вопросов, загрузка и ошибка.
// Уровень L0/L1 переключает только api/client.ts — здесь про моки ничего не известно.
// Раскладка перенесена 1:1 со структуры макета Figma NEXA (chatpage-44-8433): сайдбар слева,
// пустое состояние с шаром-маскотом и подсказками, композер-пилюля снизу.
import { useEffect, useRef, useState } from "react"
import { ask } from "@/api/client"
import type { AskResponse, Citation, Lang } from "@/api/types"
import { t } from "@/i18n"
import { AnswerCard } from "./AnswerCard"
import { DocumentViewer } from "./DocumentViewer"
import { MicButton } from "../voice/MicButton"
import { StatsFooter } from "../stats/StatsFooter"
import { AboutScreen } from "../stats/AboutScreen"
import "./chat.css"

const MIN_QUESTION_LENGTH = 2 // AskRequest.question: min_length=2
const RECENTS_KEY = "u1.recents"
const SIDEBAR_KEY = "u1.sidebarCollapsed"
const MAX_RECENTS = 8

interface Turn {
  id: number
  question: string
  response: AskResponse
}

function loadRecents(): string[] {
  try {
    const raw = localStorage.getItem(RECENTS_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed.filter((x) => typeof x === "string") : []
  } catch {
    return []
  }
}

// Логотип "nexa" из макета: буква x — фирменный зелёный (--c-brand-x). Текст берётся из i18n
// (s.logoText), здесь только разбивается посимвольно для подсветки — переводимого текста не добавляем.
function renderLogo(text: string): React.ReactNode {
  return text.split("").map((char, index) =>
    char.toLowerCase() === "x" ? (
      <span key={index} className="sidebar__logo-x">
        {char}
      </span>
    ) : (
      <span key={index}>{char}</span>
    )
  )
}

function loadCollapsed(): boolean {
  try {
    return localStorage.getItem(SIDEBAR_KEY) === "1"
  } catch {
    return false
  }
}

export function ChatScreen() {
  const [lang, setLang] = useState<Lang>("ro")
  const [draft, setDraft] = useState("")
  const [turns, setTurns] = useState<Turn[]>([])
  const [pending, setPending] = useState(false)
  const [failed, setFailed] = useState(false)
  const [lastQuestion, setLastQuestion] = useState("")
  const [recents, setRecents] = useState<string[]>(() => loadRecents())
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(() => loadCollapsed())
  const [mobileOpen, setMobileOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [openCitation, setOpenCitation] = useState<Citation | null>(null)
  const [view, setView] = useState<"chat" | "about">("chat")
  const [attachOpen, setAttachOpen] = useState(false)
  const attachRef = useRef<HTMLDivElement | null>(null)
  const attachToggleRef = useRef<HTMLButtonElement | null>(null)
  const threadEndRef = useRef<HTMLDivElement | null>(null)
  const lastTurnRef = useRef<HTMLElement | null>(null)
  const s = t(lang)

  useEffect(() => {
    if (pending) {
      threadEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" })
    } else if (turns.length > 0) {
      lastTurnRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })
    }
  }, [turns, pending])

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      const target = event.target as Node
      if (
        attachRef.current &&
        !attachRef.current.contains(target) &&
        attachToggleRef.current &&
        !attachToggleRef.current.contains(target)
      ) {
        setAttachOpen(false)
      }
    }
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setAttachOpen(false)
      }
    }
    if (attachOpen) {
      document.addEventListener("mousedown", handleClickOutside)
      document.addEventListener("keydown", handleKeyDown)
      return () => {
        document.removeEventListener("mousedown", handleClickOutside)
        document.removeEventListener("keydown", handleKeyDown)
      }
    }
  }, [attachOpen])

  useEffect(() => {
    try {
      localStorage.setItem(SIDEBAR_KEY, sidebarCollapsed ? "1" : "0")
    } catch {
      // localStorage может быть недоступен (приватный режим) — не критично.
    }
  }, [sidebarCollapsed])

  async function run(question: string): Promise<void> {
    const trimmed = question.trim()
    if (trimmed.length < MIN_QUESTION_LENGTH) return
    setPending(true)
    setFailed(false)
    setLastQuestion(trimmed)
    setMobileOpen(false)
    try {
      const response = await ask(trimmed, lang)
      setTurns((previous) => [...previous, { id: previous.length + 1, question: trimmed, response }])
      setDraft("")
      setRecents((previous) => {
        const next = [trimmed, ...previous.filter((q) => q !== trimmed)].slice(0, MAX_RECENTS)
        try {
          localStorage.setItem(RECENTS_KEY, JSON.stringify(next))
        } catch {
          // ignore
        }
        return next
      })
    } catch {
      setFailed(true)
    } finally {
      setPending(false)
    }
  }

  function onSubmit(event: React.FormEvent<HTMLFormElement>): void {
    event.preventDefault()
    if (pending) return
    void run(draft)
  }

  function newChat(): void {
    setTurns([])
    setFailed(false)
    setDraft("")
    setMobileOpen(false)
  }

  function openSearch(): void {
    setSearchQuery("")
    setSearchOpen(true)
  }

  function closeSearch(): void {
    setSearchOpen(false)
  }

  function runFromSearch(question: string): void {
    closeSearch()
    void run(question)
  }

  const canSend = draft.trim().length >= MIN_QUESTION_LENGTH && !pending
  const showEmpty = turns.length === 0 && !pending && !failed

  // Поиск по «Закреплённым» (quickPrompts) и «Недавним» (recents) — без дублей,
  // порядок: сначала закреплённые, затем недавние. Источник данных реальный,
  // ничего не выдумываем поверх localStorage/i18n.
  const searchItems = [
    ...s.quickPrompts.map((q) => ({ query: q, group: s.pinnedLabel })),
    ...recents
      .filter((q) => !s.quickPrompts.includes(q))
      .map((q) => ({ query: q, group: s.recentsLabel })),
  ]
  const filteredSearchItems = searchQuery.trim()
    ? searchItems.filter((item) => item.query.toLowerCase().includes(searchQuery.trim().toLowerCase()))
    : searchItems

  const langSwitch = (
    <div className="lang" role="group" aria-label={s.langLabel}>
      {(["ro", "ru"] as const).map((code) => (
        <button
          key={code}
          type="button"
          className={`lang__pill ${lang === code ? "lang__pill--active" : ""}`}
          aria-pressed={lang === code}
          onClick={() => setLang(code)}
        >
          {code.toUpperCase()}
        </button>
      ))}
    </div>
  )

  const sidebarBody = (
    <>
      <div className="sidebar__top">
        <div className="sidebar__brand">
          <span className="sidebar__logo">{renderLogo(s.logoText)}</span>
          <span className="sidebar__logo-subtitle">{s.logoSubtitle}</span>
        </div>
        <div className="sidebar__top-actions">
          <button type="button" className="sidebar__icon-btn" aria-label={s.searchAria} onClick={openSearch}>
            <SearchIcon />
          </button>
          <button
            type="button"
            className="sidebar__icon-btn"
            aria-label={mobileOpen ? s.closeSidebarAria : s.collapseSidebarAria}
            onClick={() => (mobileOpen ? setMobileOpen(false) : setSidebarCollapsed(true))}
          >
            {mobileOpen ? <CloseIcon /> : <CollapseIcon />}
          </button>
        </div>
      </div>

      <button type="button" className="sidebar__new-chat" onClick={newChat}>
        <PencilIcon />
        {s.newChat}
      </button>

      <nav className="sidebar__nav">
        <p className="sidebar__section-label">
          <PinIcon />
          {s.pinnedLabel}
        </p>
        <ul className="sidebar__list">
          {s.quickPrompts.map((prompt) => (
            <li key={prompt}>
              <button type="button" className="sidebar__item" onClick={() => void run(prompt)}>
                {prompt}
              </button>
            </li>
          ))}
        </ul>

        {recents.length > 0 && (
          <>
            <p className="sidebar__section-label">
              <ClockIcon />
              {s.recentsLabel}
            </p>
            <ul className="sidebar__list">
              {recents.map((question) => (
                <li key={question}>
                  <button type="button" className="sidebar__item" onClick={() => void run(question)}>
                    {question}
                  </button>
                </li>
              ))}
            </ul>
          </>
        )}
      </nav>

      <div className="sidebar__footer">
        <button
          type="button"
          className="sidebar__about-link"
          onClick={() => {
            setView("about")
            setMobileOpen(false)
          }}
        >
          <InfoIcon />
          {s.aboutNavLabel}
        </button>
        {langSwitch}
        <div className="sidebar__stats">
          <StatsFooter lang={lang} />
        </div>
      </div>
    </>
  )

  if (view === "about") {
    return <AboutScreen lang={lang} onBack={() => setView("chat")} />
  }

  return (
    <div className={`app ${sidebarCollapsed ? "app--sidebar-collapsed" : ""}`}>
      {mobileOpen && <div className="app__backdrop" onClick={() => setMobileOpen(false)} />}

      <aside
        className={`sidebar ${sidebarCollapsed ? "sidebar--collapsed" : ""} ${
          mobileOpen ? "sidebar--mobile-open" : ""
        }`}
      >
        {sidebarCollapsed ? (
          <div className="sidebar__collapsed-rail">
            <button
              type="button"
              className="sidebar__icon-btn"
              aria-label={s.expandSidebarAria}
              onClick={() => setSidebarCollapsed(false)}
            >
              <LogoMarkIcon />
            </button>
            <button type="button" className="sidebar__icon-btn" onClick={newChat} aria-label={s.newChat}>
              <PencilIcon />
            </button>
            <button type="button" className="sidebar__icon-btn" aria-label={s.searchAria} onClick={openSearch}>
              <SearchIcon />
            </button>
            <button type="button" className="sidebar__icon-btn" aria-label={s.pinnedLabel}>
              <PinIcon />
            </button>
            <button type="button" className="sidebar__icon-btn" aria-label={s.recentsLabel}>
              <ClockIcon />
            </button>
          </div>
        ) : (
          sidebarBody
        )}
      </aside>

      <div className="main">
        <header className="main__topbar">
          <button
            type="button"
            className="hamburger"
            aria-label={s.menuAria}
            onClick={() => setMobileOpen((v) => !v)}
          >
              <HamburgerIcon />
          </button>
          <span className="main__mobile-title">{renderLogo(s.logoText)}</span>
          {langSwitch}
        </header>

        <p className="chat__disclaimer" role="note">
          {s.disclaimer}
        </p>

        <main className="chat__thread">
          {showEmpty && (
            <section className="chat__empty">
              <div className="mascot" aria-hidden="true">
                <div className="mascot__glow" />
                <div className="mascot__ball" />
              </div>
              <h1 className="chat__empty-title">
                {s.heroLine1}
                <br />
                {s.heroLine2}
              </h1>
              <div className="chat__prompts">
                {s.quickPrompts.slice(0, 2).map((prompt) => (
                  <button key={prompt} type="button" className="chat__prompt-card" onClick={() => void run(prompt)}>
                    <span className="chat__prompt-card-head">
                      <span className="chat__prompt-card-title">{prompt}</span>
                      <span className="chat__prompt-card-chevron">
                        <ChevronIcon />
                      </span>
                    </span>
                    <span className="chat__prompt-card-body">{s.emptyBody}</span>
                  </button>
                ))}
              </div>
            </section>
          )}

          {turns.map((turn, index) => (
            <section
              className="turn"
              key={turn.id}
              ref={index === turns.length - 1 ? (element) => { lastTurnRef.current = element } : null}
            >
              <p className="turn__question">{turn.question}</p>
              <AnswerCard response={turn.response} onOpenDocument={setOpenCitation} />
            </section>
          ))}

          {pending && (
            <section className="skeleton" aria-busy="true">
              <p className="skeleton__caption">
                <SearchIcon />
                {s.loading}
              </p>
              <div className="skeleton__card">
                <div className="skeleton__bar" />
                <div className="skeleton__bar" />
                <div className="skeleton__bar skeleton__bar--short" />
              </div>
            </section>
          )}

          {failed && (
            <section className="error" role="alert">
              <h3 className="error__title">{s.errorTitle}</h3>
              <p className="error__body">{s.errorBody}</p>
              <button type="button" className="error__retry" onClick={() => void run(lastQuestion)}>
                {s.retry}
              </button>
            </section>
          )}

          <div ref={threadEndRef} />
        </main>

        <form className="composer" onSubmit={onSubmit}>
          <label className="composer__label" htmlFor="question">
            {s.questionLabel}
          </label>
          {attachOpen && (
            <div className="composer__attach-popup" ref={attachRef} role="dialog" aria-label={s.attachBtnAria}>
              <button
                type="button"
                className="composer__attach-btn"
                onClick={() => setAttachOpen(false)}
              >
                <PaperclipIcon />
                <span>{s.attachAddPhotos}</span>
              </button>
              <button
                type="button"
                className="composer__attach-btn composer__attach-btn--secondary"
                onClick={() => setAttachOpen(false)}
              >
                <span>{s.attachUploadComputer}</span>
              </button>
            </div>
          )}
          <div className="composer__row">
            <button
              ref={attachToggleRef}
              type="button"
              className={`composer__attach-btn-toggle ${attachOpen ? "composer__attach-btn-toggle--open" : ""}`}
              aria-label={s.attachBtnAria}
              aria-expanded={attachOpen}
              onClick={() => setAttachOpen((prev) => !prev)}
            >
              <PlusIcon />
            </button>
            <input
              id="question"
              className="composer__input"
              type="text"
              value={draft}
              placeholder={s.composerPlaceholder}
              maxLength={1000}
              autoComplete="off"
              onChange={(event) => setDraft(event.target.value)}
            />
            <MicButton lang={lang} onTranscript={(text) => setDraft(text)} />
            <button type="submit" className="composer__submit" disabled={!canSend} aria-label={s.send}>
              {pending ? <span className="composer__submit-spinner" /> : <ArrowUpIcon />}
            </button>
          </div>
        </form>
      </div>

      {searchOpen && (
        <div className="search-modal-overlay" onClick={closeSearch}>
          <div
            className="search-modal"
            role="dialog"
            aria-modal="true"
            aria-label={s.searchModalTitle}
            onClick={(event) => event.stopPropagation()}
          >
            <div className="search-modal__header">
              <SearchIcon />
              <input
                type="text"
                className="search-modal__input"
                placeholder={s.searchPlaceholder}
                value={searchQuery}
                autoFocus
                onChange={(event) => setSearchQuery(event.target.value)}
              />
              <button type="button" className="search-modal__close" aria-label={s.searchCloseAria} onClick={closeSearch}>
                <CloseIcon />
              </button>
            </div>
            <ul className="search-modal__list">
              {filteredSearchItems.length === 0 && (
                <li className="search-modal__empty">{s.searchNoResults}</li>
              )}
              {filteredSearchItems.map((item, index) => (
                <li key={`${item.group}-${item.query}-${index}`}>
                  <button
                    type="button"
                    className="search-modal__item"
                    onClick={() => runFromSearch(item.query)}
                  >
                    <span className="search-modal__item-group">{item.group}</span>
                    <span className="search-modal__item-text">{item.query}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {openCitation && (
        <DocumentViewer citation={openCitation} lang={lang} onClose={() => setOpenCitation(null)} />
      )}
    </div>
  )
}

/* --- иконки: инлайн SVG без внешних зависимостей, цвет наследуется через currentColor --- */

function SearchIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

function CloseIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <line x1="5" y1="5" x2="19" y2="19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <line x1="19" y1="5" x2="5" y2="19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

function CollapseIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="3" y="4" width="18" height="16" rx="3" stroke="currentColor" strokeWidth="2" />
      <line x1="9.5" y1="4" x2="9.5" y2="20" stroke="currentColor" strokeWidth="2" />
    </svg>
  )
}

function PencilIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M4 20h4L18.5 9.5a2.1 2.1 0 0 0-3-3L5 16v4Z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function PinIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M12 2v6.5M8 10h8l-1 3h1l2 6H6l2-6h1l-1-3Z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function ClockIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2" />
      <path d="M12 7v5l3 3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

function ChevronIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function ArrowUpIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 19V5M6 11l6-6 6 6" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function HamburgerIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <line x1="4" y1="7" x2="20" y2="7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <line x1="4" y1="12" x2="20" y2="12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <line x1="4" y1="17" x2="20" y2="17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

function InfoIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2" />
      <line x1="12" y1="11" x2="12" y2="16.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <circle cx="12" cy="7.75" r="1.15" fill="currentColor" />
    </svg>
  )
}

function LogoMarkIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M4 6l8 6-8 6M20 6l-8 6 8 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function PlusIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <line x1="12" y1="5" x2="12" y2="19" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
      <line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
    </svg>
  )
}

function PaperclipIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

