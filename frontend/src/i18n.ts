// Все строки интерфейса. Ключ — язык ОТВЕТА (response.language) для блока ответа
// и выбранный язык интерфейса для шапки и композера. В компонентах текста быть не должно.

import type { Lang } from "./api/types"

export interface Strings {
  appTitle: string
  appTagline: string
  langLabel: string
  questionLabel: string
  questionPlaceholder: string
  send: string
  sending: string
  emptyTitle: string
  emptyBody: string
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
}

const ro: Strings = {
  appTitle: "Asistentul municipal Chișinău",
  appTagline: "Răspunsuri din surse oficiale, cu citat și link către document",
  langLabel: "Limba",
  questionLabel: "Întrebarea dumneavoastră",
  questionPlaceholder: "Care este termenul de examinare a unei petiții?",
  send: "Întreabă",
  sending: "Se caută…",
  emptyTitle: "Puneți o întrebare despre serviciile municipale",
  emptyBody:
    "Fiecare răspuns arată documentul din care provine și fragmentul exact. Dacă răspunsul nu există în surse, asistentul o spune direct.",
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
}

const ru: Strings = {
  appTitle: "Муниципальный ассистент Кишинёва",
  appTagline: "Ответы из официальных источников — с цитатой и ссылкой на документ",
  langLabel: "Язык",
  questionLabel: "Ваш вопрос",
  questionPlaceholder: "В какой срок рассматривается петиция в примэрии?",
  send: "Спросить",
  sending: "Идёт поиск…",
  emptyTitle: "Задайте вопрос о муниципальных услугах",
  emptyBody:
    "К каждому ответу прилагается документ-источник и дословный фрагмент. Если ответа в источниках нет, ассистент скажет об этом прямо.",
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
}

const STRINGS: Record<Lang, Strings> = { ro, ru }

export function t(lang: Lang): Strings {
  return STRINGS[lang]
}
