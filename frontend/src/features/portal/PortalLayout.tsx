import { useState, useRef } from "react"
import type { Lang } from "@/api/types"
import { ChatScreen } from "../chat/ChatScreen"
import { QuickChips } from "./QuickChips"
import { NexaSidebar } from "./NexaSidebar"

export type PortalTab = "assistant" | "services" | "contacts"

interface PortalStrings {
  title: string
  subtitle: string
  tabAssistant: string
  tabServices: string
  tabContacts: string
  inDevelopmentTitle: string
  inDevelopmentSubtitle: string
  askAssistantButton: string
  servicesTitle: string
  servicesDescription: string
  contactsTitle: string
  contactsDescription: string
  portalOnline: string
}

const STRINGS_RO: PortalStrings = {
  title: "Portal Municipal Chișinău",
  subtitle: "Servicii publice digitale și asistent municipal inteligent",
  tabAssistant: "💬 AI-Asistent",
  tabServices: "📋 Servicii",
  tabContacts: "🏛️ Contacte",
  inDevelopmentTitle: "Secțiune în curs de dezvoltare",
  inDevelopmentSubtitle:
    "Catalogul complet de servicii este în curs de integrare. Puteți adresa orice întrebare direct asistentului municipal.",
  askAssistantButton: "Adresează o întrebare AI-Asistentului",
  servicesTitle: "Catalogul serviciilor municipale",
  servicesDescription:
    "Găsiți informații oficiale, regulamente și proceduri pentru serviciile primăriei și subdiviziunilor municipale.",
  contactsTitle: "Contacte și audiențe",
  contactsDescription:
    "Date de contact oficiale ale Primăriei Municipiului Chișinău și ale preturilor de sector.",
  portalOnline: "Portal Activ",
}

const STRINGS_RU: PortalStrings = {
  title: "Муниципальный портал Кишинёва",
  subtitle: "Цифровые общественные услуги и интеллектуальный муниципальный ассистент",
  tabAssistant: "💬 AI-Ассистент",
  tabServices: "📋 Услуги",
  tabContacts: "🏛️ Контакты",
  inDevelopmentTitle: "Раздел в разработке",
  inDevelopmentSubtitle:
    "Полный каталог услуг находится в процессе интеграции. Вы можете задать любой вопрос напрямую муниципальному ассистенту.",
  askAssistantButton: "Задать вопрос AI-Ассистенту",
  servicesTitle: "Каталог муниципальных услуг",
  servicesDescription:
    "Официальная информация, регламенты и процедуры примэрии и муниципальных подразделений.",
  contactsTitle: "Контакты и приём граждан",
  contactsDescription:
    "Официальные контактные данные Примэрии муниципия Кишинёв и претур секторов.",
  portalOnline: "Портал активен",
}

interface ServiceItem {
  icon: string
  titleRo: string
  titleRu: string
  descRo: string
  descRu: string
  queryRo: string
  queryRu: string
}

const MUNICIPAL_SERVICES: ServiceItem[] = [
  {
    icon: "🚌",
    titleRo: "Transport public și mobilitate",
    titleRu: "Общественный транспорт",
    descRo: "Tarife RTEC și autobuze, rute, abonamente de călătorie și orare.",
    descRu: "Тарифы RTEC и автобусов, маршруты, проездные абонементы и расписания.",
    queryRo: "Tarife RTEC",
    queryRu: "Тарифы RTEC",
  },
  {
    icon: "📑",
    titleRo: "Petiții și cereri cetățeni",
    titleRu: "Петиции и обращения",
    descRo: "Procedura și termenele legale de examinare a petițiilor adresate primăriei.",
    descRu: "Процедура и установленные законом сроки рассмотрения петиций в примэрии.",
    queryRo: "Care este termenul de examinare a unei petiții?",
    queryRu: "В какой срок рассматривается петиция в примэрии?",
  },
  {
    icon: "🏢",
    titleRo: "Audiențe preturi de sector",
    titleRu: "Приём в претурах секторов",
    descRo: "Programul de audiență a cetățenilor la preturile sectoarelor Botanica, Centru, Rîșcani.",
    descRu: "График приёма граждан руководством претур секторов Ботаника, Центр, Рышкань.",
    queryRo: "Audiență pretură",
    queryRu: "Приём в претуре",
  },
  {
    icon: "🅿️",
    titleRo: "Parcări municipale și regulament",
    titleRu: "Парковки и штрафы",
    descRo: "Amplasarea parcărilor municipale, reguli de plată și achitarea amenzilor.",
    descRu: "Расположение муниципальных парковок, правила оплаты и штрафы.",
    queryRo: "Parcare",
    queryRu: "Парковки",
  },
]

interface ContactItem {
  nameRo: string
  nameRu: string
  address: string
  phone: string
  hoursRo: string
  hoursRu: string
  queryRo: string
  queryRu: string
}

const MUNICIPAL_CONTACTS: ContactItem[] = [
  {
    nameRo: "Primăria Municipiului Chișinău",
    nameRu: "Примэрия муниципия Кишинёв",
    address: "bd. Ștefan cel Mare și Sfânt 83",
    phone: "022 20-17-01",
    hoursRo: "Luni – Vineri, 08:00 – 17:00",
    hoursRu: "Понедельник – Пятница, 08:00 – 17:00",
    queryRo: "Care este termenul de examinare a unei petiții?",
    queryRu: "В какой срок рассматривается петиция в примэрии?",
  },
  {
    nameRo: "Pretura Sectorului Botanica",
    nameRu: "Претура сектора Ботаника",
    address: "bd. Dacia 49",
    phone: "022 76-72-31",
    hoursRo: "Audiență: Luni și Joi",
    hoursRu: "Приём: Понедельник и Четверг",
    queryRo: "Audiență pretură Botanica",
    queryRu: "Приём в претуре Ботаника",
  },
  {
    nameRo: "Pretura Sectorului Centru",
    nameRu: "Претура сектора Центр",
    address: "str. Bulgară 43",
    phone: "022 27-50-68",
    hoursRo: "Luni – Vineri, 08:00 – 17:00",
    hoursRu: "Понедельник – Пятница, 08:00 – 17:00",
    queryRo: "Audiență pretură",
    queryRu: "Приём в претуре",
  },
  {
    nameRo: "Pretura Sectorului Rîșcani",
    nameRu: "Претура сектора Рышкань",
    address: "str. Kiev 3",
    phone: "022 44-10-98",
    hoursRo: "Luni – Vineri, 08:00 – 17:00",
    hoursRu: "Понедельник – Пятница, 08:00 – 17:00",
    queryRo: "Audiență pretură",
    queryRu: "Приём в претуре",
  },
]

export function PortalLayout() {
  const [activeTab, setActiveTab] = useState<PortalTab>("assistant")
  const [lang, setLang] = useState<Lang>("ro")
  const [initialQuestion, setInitialQuestion] = useState<string | undefined>()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [recentQueries, setRecentQueries] = useState<string[]>([])

  const askFnRef = useRef<((question: string) => void) | null>(null)
  const resetChatRef = useRef<(() => void) | null>(null)
  const s = lang === "ru" ? STRINGS_RU : STRINGS_RO

  function handleQueryAsked(question: string): void {
    setRecentQueries((prev) => [question, ...prev.filter((q) => q !== question)].slice(0, 8))
  }

  function handleAsk(question: string): void {
    if (activeTab !== "assistant") {
      setActiveTab("assistant")
    }
    setInitialQuestion(question)
    handleQueryAsked(question)
    if (askFnRef.current) {
      askFnRef.current(question)
    }
  }

  function handleNewChat(): void {
    setActiveTab("assistant")
    setInitialQuestion(undefined)
    resetChatRef.current?.()
    setSidebarOpen(false)
  }

  return (
    <div className="portal">
      <NexaSidebar
        activeTab={activeTab}
        onTabChange={(tab) => {
          setActiveTab(tab)
          setSidebarOpen(false)
        }}
        onNewChat={handleNewChat}
        recentQueries={recentQueries}
        onSelectQuery={handleAsk}
        lang={lang}
        onLangChange={(l) => setLang(l)}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="portal-main">
        <header className="portal-topbar">
          <div className="portal-topbar__left">
            <button
              type="button"
              className="portal-topbar__menu-btn"
              aria-label={lang === "ru" ? "Открыть меню" : "Deschide meniul"}
              aria-expanded={sidebarOpen}
              onClick={() => setSidebarOpen((prev) => !prev)}
            >
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </svg>
            </button>
            <div className="portal-topbar__title-group">
              <span className="portal-topbar__badge" aria-hidden="true">🏛️</span>
              <div>
                <h1 className="portal-topbar__title">{s.title}</h1>
                <p className="portal-topbar__subtitle">{s.subtitle}</p>
              </div>
            </div>
          </div>

          <div className="portal-topbar__right">
            <div className="portal-lang" role="group" aria-label={lang === "ru" ? "Выбор языка" : "Selectare limbă"}>
              {(["ro", "ru"] as const).map((code) => (
                <button
                  key={code}
                  type="button"
                  className="portal-lang__button"
                  aria-pressed={lang === code}
                  onClick={() => setLang(code)}
                >
                  {code.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        </header>

        <main className="portal-content">
          {activeTab === "assistant" && (
            <section
              id="panel-assistant"
              role="tabpanel"
              aria-labelledby="tab-assistant"
              className="portal-panel"
            >
              <ChatScreen
                showHeader={false}
                initialQuestion={initialQuestion}
                currentLang={lang}
                onLangChange={(newLang) => setLang(newLang)}
                onQuickAsk={(askFn) => {
                  askFnRef.current = askFn
                }}
                onQueryAsked={handleQueryAsked}
                onResetRegistered={(resetFn) => {
                  resetChatRef.current = resetFn
                }}
                chipsSlot={<QuickChips onAsk={handleAsk} lang={lang} />}
              />
            </section>
          )}

          {activeTab === "services" && (
            <section
              id="panel-services"
              role="tabpanel"
              aria-labelledby="tab-services"
              className="portal-panel portal-panel--catalog"
            >
              <div className="portal-banner">
                <span className="portal-banner__badge">{s.inDevelopmentTitle}</span>
                <h2 className="portal-banner__title">{s.servicesTitle}</h2>
                <p className="portal-banner__body">{s.inDevelopmentSubtitle}</p>
              </div>

              <div className="portal-grid">
                {MUNICIPAL_SERVICES.map((service, index) => {
                  const title = lang === "ru" ? service.titleRu : service.titleRo
                  const desc = lang === "ru" ? service.descRu : service.descRo
                  const query = lang === "ru" ? service.queryRu : service.queryRo
                  return (
                    <article className="portal-card" key={index}>
                      <div className="portal-card__icon" aria-hidden="true">
                        {service.icon}
                      </div>
                      <div className="portal-card__content">
                        <h3 className="portal-card__title">{title}</h3>
                        <p className="portal-card__desc">{desc}</p>
                        <button
                          type="button"
                          className="portal-card__action"
                          onClick={() => handleAsk(query)}
                        >
                          {s.askAssistantButton} →
                        </button>
                      </div>
                    </article>
                  )
                })}
              </div>
            </section>
          )}

          {activeTab === "contacts" && (
            <section
              id="panel-contacts"
              role="tabpanel"
              aria-labelledby="tab-contacts"
              className="portal-panel portal-panel--catalog"
            >
              <div className="portal-banner">
                <span className="portal-banner__badge">{s.inDevelopmentTitle}</span>
                <h2 className="portal-banner__title">{s.contactsTitle}</h2>
                <p className="portal-banner__body">{s.contactsDescription}</p>
              </div>

              <div className="portal-grid">
                {MUNICIPAL_CONTACTS.map((contact, index) => {
                  const name = lang === "ru" ? contact.nameRu : contact.nameRo
                  const hours = lang === "ru" ? contact.hoursRu : contact.hoursRo
                  const query = lang === "ru" ? contact.queryRu : contact.queryRo
                  return (
                    <article className="portal-card" key={index}>
                      <div className="portal-card__icon" aria-hidden="true">
                        🏛️
                      </div>
                      <div className="portal-card__content">
                        <h3 className="portal-card__title">{name}</h3>
                        <p className="portal-card__desc">
                          <strong>📍 {contact.address}</strong>
                          <br />
                          📞 {contact.phone}
                          <br />
                          🕒 {hours}
                        </p>
                        <button
                          type="button"
                          className="portal-card__action"
                          onClick={() => handleAsk(query)}
                        >
                          {s.askAssistantButton} →
                        </button>
                      </div>
                    </article>
                  )
                })}
              </div>
            </section>
          )}
        </main>
      </div>
    </div>
  )
}
