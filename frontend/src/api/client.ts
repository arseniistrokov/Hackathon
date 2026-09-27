// Порт блока U1: ask / sendFeedback / getStats. Переключатель уровня — VITE_USE_MOCK (по умолчанию true = L0).
// L0: ответы из data/fixture/mock_responses (tsconfig include + resolveJsonModule уже настроены каркасом).
// L1: реальный /api через vite proxy. Ошибка сети НЕ подменяется моком: экран обязан показать состояние
// error с «повторить» (порт U1 и QA 11), а выдавать фикстуру за настоящий ответ на демо нельзя.

import answeredRo from "../../../data/fixture/mock_responses/answered_ro.json"
import answeredRuFromRoDoc from "../../../data/fixture/mock_responses/answered_ru_from_ro_doc.json"
import answeredWithWarning from "../../../data/fixture/mock_responses/answered_with_warning.json"
import conflict from "../../../data/fixture/mock_responses/conflict.json"
import notFound from "../../../data/fixture/mock_responses/not_found.json"
import type { AskResponse, FeedbackRequest, Lang, Stats } from "./types"

const TIMEOUT_MS = 60_000
const MOCK_LATENCY_MS = 400

export const USE_MOCK = false

const MOCKS: Record<string, AskResponse> = {
  answered_ro: answeredRo as AskResponse,
  answered_ru_from_ro_doc: answeredRuFromRoDoc as AskResponse,
  answered_with_warning: answeredWithWarning as AskResponse,
  conflict: conflict as AskResponse,
  not_found: notFound as AskResponse,
}

// Правило выбора мока задано в frontend/README.md (раздел «Mock ↔ реальный API») и согласовано
// с тем, что зашито в mini_corpus (data/fixture/README.md). Порядок важен: первое совпадение выигрывает.
const MOCK_RULES: ReadonlyArray<{ pattern: RegExp; key: string }> = [
  { pattern: /parcare|amend|cain|парков|штраф|налог|собак/, key: "not_found" },
  { pattern: /audien|pretur|приём|приемн|претур/, key: "conflict" },
  { pattern: /troleibuz|autobuz|tarif|троллейбус|автобус|тариф|проезд/, key: "answered_with_warning" },
]

const CYRILLIC = /[а-яё]/i

// Складываем регистр и снимаем диакритику: «audiență» и «audienta» должны совпасть.
// Тот же принцип, что у FTS5 remove_diacritics 2 на бэкенде.
function fold(text: string): string {
  return text.toLowerCase().normalize("NFD").replace(/\p{Diacritic}/gu, "")
}

function pickMock(question: string, lang?: Lang | null): AskResponse {
  const q = fold(question)
  const hit = MOCK_RULES.find((rule) => rule.pattern.test(q))
  if (hit) return MOCKS[hit.key]
  const ru = CYRILLIC.test(question) || lang === "ru"
  return ru ? MOCKS.answered_ru_from_ro_doc : MOCKS.answered_ro
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)
  try {
    const response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: controller.signal,
    })
    if (!response.ok) throw new Error(`${path} → ${response.status}`)
    return (await response.json()) as T
  } finally {
    clearTimeout(timer)
  }
}

async function getJson<T>(path: string): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)
  try {
    const response = await fetch(path, { signal: controller.signal })
    if (!response.ok) throw new Error(`${path} → ${response.status}`)
    return (await response.json()) as T
  } finally {
    clearTimeout(timer)
  }
}

export async function ask(question: string, lang?: Lang | null): Promise<AskResponse> {
  if (USE_MOCK) {
    await sleep(MOCK_LATENCY_MS)
    const mock = pickMock(question, lang)
    // Вопрос — заданный пользователем, а не зашитый в фикстуру. language следует за переключателем,
    // иначе на моках не видно, что он вообще работает (критерии 3 и 6). Только для L0.
    return { ...mock, question, language: lang ?? mock.language }
  }
  return postJson<AskResponse>("/api/ask", { question, lang: lang ?? null })
}

export async function sendFeedback(feedback: FeedbackRequest): Promise<void> {
  if (USE_MOCK) {
    await sleep(MOCK_LATENCY_MS)
    return
  }
  await postJson<unknown>("/api/feedback", feedback)
}

export async function getStats(): Promise<Stats> {
  if (USE_MOCK) {
    await sleep(MOCK_LATENCY_MS)
    // Числа — из data/fixture/expect.json (documents 14, sites 8) и conflicts.json (2 пары);
    // chunks и model — из meta моков. Свои значения не выдумываем.
    return {
      corpus_documents: 14,
      corpus_chunks: 52,
      sites: 8,
      conflicts: 2,
      queries: 0,
      feedback_up: 0,
      feedback_down: 0,
      model: MOCKS.answered_ro.meta.model,
    }
  }
  return getJson<Stats>("/api/stats")
}
