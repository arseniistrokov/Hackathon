// Все строки интерфейса. Ключ — язык ОТВЕТА (response.language) для блока ответа
// и выбранный язык интерфейса для шапки и композера. В компонентах текста быть не должно.

import type { Lang } from "./api/types"

export interface Strings {
  appTitle: string
  appTagline: string
  disclaimer: string
  langLabel: string
  questionLabel: string
  questionPlaceholder: string
  send: string
  sending: string
  emptyTitle: string
  emptyBody: string
  quickPrompts: string[]
  loading: string
  errorTitle: string
  errorBody: string
  retry: string
  answeredLabel: string
  warningLabel: string
  sourcesLabel: string
  openDocument: string
  sectionLabel: string
  pageLabel: string
  undatedLabel: string
  notFoundLabel: string
  notFoundTitle: string
  notFoundBody: (documents: number, passagesUsed: number) => string
  conflictLabel: string
  conflictTitle: string
  conflictEntity: string
  conflictSide: (index: number) => string
  navigationLabel: string
  metaCorpus: (documents: number, chunks: number) => string
  metaPassages: (retrieved: number, used: number) => string
  metaModel: string
  metaLatency: (ms: number) => string
  feedbackAriaLabel: string
  feedbackUseful: string
  feedbackNotUseful: string
  feedbackThanks: string
  feedbackCommentPlaceholder: string
  feedbackCommentAriaLabel: string
  feedbackSubmit: string
  statsAriaLabel: string
  statsLoading: string
  statsUnavailable: string
  statsDocuments: string
  statsChunks: string
  statsSites: string
  statsConflicts: string
  statsQueries: string
  statsFeedback: string
  statsModel: string
  logoText: string
  logoSubtitle: string
  searchAria: string
  collapseSidebarAria: string
  expandSidebarAria: string
  menuAria: string
  newChat: string
  pinnedLabel: string
  recentsLabel: string
  heroLine1: string
  heroLine2: string
  composerPlaceholder: string
  mascotAlt: string
  interfaceLangLabel: string
  searchModalTitle: string
  searchPlaceholder: string
  searchNoResults: string
  searchCloseAria: string
  documentViewerCloseAria: string
  openSource: string
  closeLabel: string
  closeSidebarAria: string
  aboutNavLabel: string
  guestName: string
  backToChatLabel: string
  aboutTitle: string
  aboutSubtitle: string
  aboutFooterNote: string
  aboutHowItWorksTitle: string
  aboutHowItWorksBody: string
  attachBtnAria: string
  attachAddPhotos: string
  attachUploadComputer: string
  recording: string
  recognizing: string
  micUnavailable: string
  micStart: string
  micStop: string
}

const ro: Strings = {
  appTitle: "Asistentul municipal Chișinău",
  appTagline: "Răspunsuri din surse oficiale, cu citat și link către document",
  disclaimer:
    "Răspunsurile sunt generate de AI pe baza documentelor oficiale. Verificați la sursă. Nu constituie consultanță juridică.",
  langLabel: "Limba",
  questionLabel: "Întrebarea dumneavoastră",
  questionPlaceholder: "Care este termenul de examinare a unei petiții?",
  send: "Întreabă",
  sending: "Se caută…",
  emptyTitle: "Puneți o întrebare despre serviciile municipale",
  emptyBody:
    "Fiecare răspuns arată documentul din care provine și fragmentul exact. Dacă răspunsul nu există în surse, asistentul o spune direct.",
  quickPrompts: [
    "Care este termenul de examinare a unei petiții?",
    "Cum depun o petiție la primărie?",
    "Cine este responsabil de curățenia stradală?",
  ],
  loading: "Se caută în surse…",
  errorTitle: "Cererea nu a reușit",
  errorBody: "Serviciul nu a răspuns. Verificați conexiunea și încercați din nou.",
  retry: "Încearcă din nou",
  answeredLabel: "Răspuns confirmat",
  warningLabel: "Atenție",
  sourcesLabel: "Surse",
  openDocument: "Deschide documentul",
  sectionLabel: "Secțiunea",
  pageLabel: "pagina",
  undatedLabel: "fără dată",
  notFoundLabel: "Fără răspuns",
  notFoundTitle: "Nu există răspuns în sursele oficiale",
  notFoundBody: (documents, passagesUsed) =>
    `Corpus: ${documents} documente. Fragmente care confirmă răspunsul: ${passagesUsed}. Generarea răspunsului a fost blocată intenționat — asistentul nu inventează.`,
  conflictLabel: "Surse contradictorii",
  conflictTitle: "Sursele oficiale se contrazic",
  conflictEntity: "Subiectul divergenței",
  conflictSide: (index) => `Sursa ${index}`,
  navigationLabel: "Pagina utilă",
  metaCorpus: (documents, chunks) => `Corpus: ${documents} documente · ${chunks} fragmente`,
  metaPassages: (retrieved, used) => `Fragmente: ${retrieved} verificate · ${used} folosite`,
  metaModel: "Model",
  metaLatency: (ms) => `${(ms / 1000).toFixed(1)} s`,
  feedbackAriaLabel: "Feedback",
  feedbackUseful: "Util",
  feedbackNotUseful: "Nu a ajutat",
  feedbackThanks: "Mulțumim pentru feedback!",
  feedbackCommentPlaceholder: "Ce poate fi îmbunătățit? (opțional)",
  feedbackCommentAriaLabel: "Textul feedback-ului",
  feedbackSubmit: "Trimite",
  statsAriaLabel: "Statistica serviciului",
  statsLoading: "Se încarcă statistica…",
  statsUnavailable: "Statistica indisponibilă",
  statsDocuments: "Documente",
  statsChunks: "Fragmente",
  statsSites: "Site-uri",
  statsConflicts: "Conflicte",
  statsQueries: "Interogări",
  statsFeedback: "Feedback",
  statsModel: "Model",
  logoText: "nexa",
  logoSubtitle: "Asistent Chișinău",
  searchAria: "Căutare în conversații",
  collapseSidebarAria: "Restrânge meniul lateral",
  expandSidebarAria: "Extinde meniul lateral",
  menuAria: "Meniu",
  newChat: "Chat nou",
  pinnedLabel: "Fixate",
  recentsLabel: "Recente",
  heroLine1: "Bună, sunt NEXA",
  heroLine2: "Cu ce te pot ajuta?",
  composerPlaceholder: "Întreabă NEXA…",
  mascotAlt: "Mascotă AI",
  interfaceLangLabel: "Interfață",
  searchModalTitle: "Caută în conversații",
  searchPlaceholder: "Caută…",
  searchNoResults: "Nimic găsit",
  searchCloseAria: "Închide căutarea",
  documentViewerCloseAria: "Închide fereastra documentului",
  openSource: "Deschide sursa oficială",
  closeLabel: "Închide",
  closeSidebarAria: "Închide meniul lateral",
  aboutNavLabel: "Despre proiect",
  guestName: "Oaspete",
  backToChatLabel: "Înapoi la chat",
  aboutTitle: "Despre proiect",
  aboutSubtitle: "Asistent municipal Chișinău — statistica serviciului, live.",
  aboutFooterNote:
    "Datele sunt actualizate live din serviciul de backend. Pentru detalii tehnice, vezi documentația proiectului.",
  aboutHowItWorksTitle: "Cum funcționează",
  aboutHowItWorksBody:
    "Fiecare răspuns trece prin trei pași: căutare în surse (retrieval) → verificare a fragmentelor găsite → răspuns cu citate exacte din documente oficiale.",
  attachBtnAria: "Atașează fișier",
  attachAddPhotos: "Adaugă fotografii și fișiere",
  attachUploadComputer: "Încarcă de pe computer",
  recording: "Înregistrare…",
  recognizing: "Recunoaștere…",
  micUnavailable: "Microfonul nu este disponibil",
  micStart: "Introducere vocală",
  micStop: "Oprește înregistrarea",}

const ru: Strings = {
  appTitle: "Муниципальный ассистент Кишинёва",
  appTagline: "Ответы из официальных источников — с цитатой и ссылкой на документ",
  disclaimer:
    "Ответы формирует AI на основе официальных документов. Проверяйте по источнику. Не является юридической консультацией.",
  langLabel: "Язык",
  questionLabel: "Ваш вопрос",
  questionPlaceholder: "В какой срок рассматривается петиция в примэрии?",
  send: "Спросить",
  sending: "Идёт поиск…",
  emptyTitle: "Задайте вопрос о муниципальных услугах",
  emptyBody:
    "К каждому ответу прилагается документ-источник и дословный фрагмент. Если ответа в источниках нет, ассистент скажет об этом прямо.",
  quickPrompts: [
    "В какой срок рассматривается петиция в примэрии?",
    "Как подать петицию в примэрию?",
    "Кто отвечает за уборку улиц?",
  ],
  loading: "Идёт поиск по источникам…",
  errorTitle: "Запрос не удался",
  errorBody: "Сервис не ответил. Проверьте соединение и попробуйте снова.",
  retry: "Повторить",
  answeredLabel: "Ответ подтверждён",
  warningLabel: "Важно",
  sourcesLabel: "Источники",
  openDocument: "Открыть документ",
  sectionLabel: "Раздел",
  pageLabel: "стр.",
  undatedLabel: "без даты",
  notFoundLabel: "Ответа нет",
  notFoundTitle: "В официальных источниках ответа нет",
  notFoundBody: (documents, passagesUsed) =>
    `Корпус: ${documents} документов. Подтверждающих фрагментов: ${passagesUsed}. Генерация ответа намеренно заблокирована — ассистент не выдумывает.`,
  conflictLabel: "Источники расходятся",
  conflictTitle: "Официальные источники противоречат друг другу",
  conflictEntity: "В чём расхождение",
  conflictSide: (index) => `Источник ${index}`,
  navigationLabel: "Полезная страница",
  metaCorpus: (documents, chunks) => `Корпус: ${documents} документов · ${chunks} фрагментов`,
  metaPassages: (retrieved, used) => `Фрагментов: ${retrieved} проверено · ${used} использовано`,
  metaModel: "Модель",
  metaLatency: (ms) => `${(ms / 1000).toFixed(1)} с`,
  feedbackAriaLabel: "Обратная связь",
  feedbackUseful: "Полезно",
  feedbackNotUseful: "Не помогло",
  feedbackThanks: "Спасибо за отзыв!",
  feedbackCommentPlaceholder: "Что можно улучшить? (необязательно)",
  feedbackCommentAriaLabel: "Текст отзыва",
  feedbackSubmit: "Отправить",
  statsAriaLabel: "Статистика сервиса",
  statsLoading: "Загрузка статистики…",
  statsUnavailable: "Статистика недоступна",
  statsDocuments: "Документы",
  statsChunks: "Фрагменты",
  statsSites: "Сайты",
  statsConflicts: "Конфликты",
  statsQueries: "Запросы",
  statsFeedback: "Отзывы",
  statsModel: "Модель",
  logoText: "nexa",
  logoSubtitle: "Asistent Chișinău",
  searchAria: "Поиск по беседам",
  collapseSidebarAria: "Свернуть боковую панель",
  expandSidebarAria: "Развернуть боковую панель",
  menuAria: "Меню",
  newChat: "Новый чат",
  pinnedLabel: "Закреплённые",
  recentsLabel: "Недавние",
  heroLine1: "Привет, я NEXA",
  heroLine2: "Чем могу помочь?",
  composerPlaceholder: "Спроси NEXA…",
  mascotAlt: "AI-маскот",
  interfaceLangLabel: "Интерфейс",
  searchModalTitle: "Поиск по беседам",
  searchPlaceholder: "Поиск…",
  searchNoResults: "Ничего не найдено",
  searchCloseAria: "Закрыть поиск",
  documentViewerCloseAria: "Закрыть окно документа",
  openSource: "Открыть официальный источник",
  closeLabel: "Закрыть",
  closeSidebarAria: "Закрыть боковую панель",
  aboutNavLabel: "О проекте",
  guestName: "Гость",
  backToChatLabel: "Назад к чату",
  aboutTitle: "О проекте",
  aboutSubtitle: "Муниципальный ассистент Кишинёва — статистика сервиса, вживую.",
  aboutFooterNote:
    "Данные обновляются вживую из сервиса бэкенда. Технические детали — в документации проекта.",
  aboutHowItWorksTitle: "Как это работает",
  aboutHowItWorksBody:
    "Каждый ответ проходит три шага: поиск по источникам (retrieval) → проверка найденных фрагментов → ответ с точными цитатами из официальных документов.",
  attachBtnAria: "Прикрепить файл",
  attachAddPhotos: "Добавить фото и файлы",
  attachUploadComputer: "Загрузить с компьютера",
  recording: "Запись…",
  recognizing: "Распознавание…",
  micUnavailable: "Микрофон недоступен",
  micStart: "Голосовой ввод",
  micStop: "Остановить запись",
}

const STRINGS: Record<Lang, Strings> = { ro, ru }

export function t(lang: Lang): Strings {
  return STRINGS[lang]
}
