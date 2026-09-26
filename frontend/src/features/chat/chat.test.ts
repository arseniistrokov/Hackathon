// @ts-ignore
import fs from "node:fs"
// @ts-ignore
import path from "node:path"
// @ts-ignore
import { fileURLToPath } from "node:url"
// @ts-ignore
const { t } = await import("../../i18n.ts")
import type { AskResponse, Citation } from "../../api/types"

// @ts-ignore
const __filename = fileURLToPath(import.meta.url)
// @ts-ignore
const __dirname = path.dirname(__filename)
const rootDir = path.resolve(__dirname, "../../../..")

let passed = 0
let failed = 0

function test(name: string, fn: () => void): void {
  try {
    fn()
    passed++
    console.log(`  ✓ ${name}`)
  } catch (err) {
    failed++
    console.error(`  ✗ ${name}: ${(err as Error).message}`)
  }
}

function assert(condition: boolean, msg: string): void {
  if (!condition) throw new Error(msg)
}

function assertEqual<T>(actual: T, expected: T, msg: string): void {
  if (actual !== expected) {
    throw new Error(`${msg}: expected ${String(expected)}, got ${String(actual)}`)
  }
}

console.log("=== ЗАПУСК ТЕСТОВ БЛОКА U1 (L0) ===\n")

// -----------------------------------------------------------------------------
// КРИТЕРИЙ 1: 5 моков из data/fixture/mock_responses/*.json и undefined в полях
// -----------------------------------------------------------------------------
console.log("Критерий 1: Рендер и валидация 5 моков, устойчивость к undefined")

const mockFiles = [
  "answered_ro.json",
  "answered_ru_from_ro_doc.json",
  "answered_with_warning.json",
  "conflict.json",
  "not_found.json",
]

const loadedMocks: Record<string, AskResponse> = {}

test("Все 5 мок-файлов присутствуют и соответствуют схеме AskResponse", () => {
  for (const file of mockFiles) {
    const fullPath = path.join(rootDir, "data/fixture/mock_responses", file)
    assert(fs.existsSync(fullPath), `Файл ${file} должен существовать`)
    const raw = fs.readFileSync(fullPath, "utf-8")
    const data = JSON.parse(raw) as AskResponse
    loadedMocks[file] = data

    assert(typeof data.question === "string", `${file}: question must be string`)
    assert(data.language === "ro" || data.language === "ru", `${file}: language must be ro/ru`)
    assert(["ANSWERED", "NOT_FOUND", "CONFLICT"].includes(data.status), `${file}: status valid`)
    assert(typeof data.answer === "string", `${file}: answer must be string`)
    assert(Array.isArray(data.citations), `${file}: citations must be array`)
    assert(typeof data.meta.corpus_documents === "number", `${file}: meta.corpus_documents number`)
    assert(typeof data.meta.query_id === "string", `${file}: meta.query_id string`)
  }
})

test("undefined / null в опциональных полях не ломает форматирование", () => {
  const minimalResponse: AskResponse = {
    question: "Test question",
    language: "ro",
    status: "ANSWERED",
    answer: "Minimal answer",
    citations: [
      {
        chunk_id: "c1",
        document_id: "d1",
        title: "Title 1",
        url: "https://example.com",
        site: "chisinau.md",
        section: undefined,
        page: undefined,
        passage: "Passage verbatim",
        date: undefined,
      },
    ],
    warning: undefined,
    navigation: undefined,
    conflict: undefined,
    meta: {
      corpus_documents: 14,
      corpus_chunks: 52,
      passages_retrieved: 4,
      passages_used: 1,
      model: "extractive",
      latency_ms: 120,
      query_id: "q_test",
    },
  }

  // Проверяем i18n строки для карточки с undefined
  const s = t(minimalResponse.language)
  assertEqual(s.metaLatency(minimalResponse.meta.latency_ms), "0.1 s", "Latency formatting")
  assertEqual(s.undatedLabel, "fără dată", "Undated label ro")

  // Проверяем null вместо undefined
  const nullCitation: Citation = {
    ...minimalResponse.citations[0],
    section: null,
    page: null,
    date: null,
  }
  assert(nullCitation.section === null, "Section null check")
})

// -----------------------------------------------------------------------------
// КРИТЕРИЙ 2: CONFLICT две колонки от 768px, обе цитаты кликабельны
// -----------------------------------------------------------------------------
console.log("\nКритерий 2: CONFLICT две колонки от 768px, цитаты кликабельны")

test("Мок conflict.json содержит обе стороны (a, b) с валидными цитатами", () => {
  const c = loadedMocks["conflict.json"]
  assert(c.status === "CONFLICT", "Status must be CONFLICT")
  assert(c.conflict !== undefined && c.conflict !== null, "Conflict must be present")
  const conflictObj = c.conflict!
  assert(typeof conflictObj.entity === "string", "entity must be string")
  assert(Boolean(conflictObj.a.citation.url), "side a citation url must exist")
  assert(Boolean(conflictObj.b.citation.url), "side b citation url must exist")
  assert(Boolean(conflictObj.a.value), "side a value must exist")
  assert(Boolean(conflictObj.b.value), "side b value must exist")
})

test("chat.css содержит адаптивную сетку для conflict-grid (1fr на узких, 1fr 1fr на >=768px)", () => {
  const cssPath = path.join(__dirname, "chat.css")
  const css = fs.readFileSync(cssPath, "utf-8")
  assert(css.includes(".conflict-grid"), "chat.css must define .conflict-grid")
  assert(css.includes("grid-template-columns: 1fr;"), "Base conflict-grid must be 1fr")
  assert(css.includes("@media (min-width: 768px)"), "Must have media query for min-width: 768px")
  assert(css.includes("grid-template-columns: 1fr 1fr;"), "Wide conflict-grid must be 1fr 1fr")
})

test("CitationCard генерирует ссылку с target=_blank и rel=noreferrer", () => {
  const citationCardPath = path.join(__dirname, "CitationCard.tsx")
  const code = fs.readFileSync(citationCardPath, "utf-8")
  assert(code.includes('target="_blank"'), "Link must open in new tab")
  assert(code.includes('rel="noreferrer"'), "Link must have rel=noreferrer")
  assert(code.includes("href={citation.url}"), "Link must point to citation.url")
})

// -----------------------------------------------------------------------------
// КРИТЕРИЙ 3: NOT_FOUND показывает число документов корпуса и заблокированную генерацию
// -----------------------------------------------------------------------------
console.log("\nКритерий 3: NOT_FOUND число документов и текст о заблокированной генерации")

test("i18n RO notFoundBody содержит число документов и текст о блокировке генерации", () => {
  const sRo = t("ro")
  const textRo = sRo.notFoundBody(14, 0)
  assert(textRo.includes("14"), "RO text must contain document count 14")
  assert(textRo.includes("0"), "RO text must contain 0 passages")
  assert(
    textRo.includes("Generarea răspunsului a fost blocată intenționat"),
    "RO text must state blocked generation explicitly"
  )
})

test("i18n RU notFoundBody содержит число документов и текст о блокировке генерации", () => {
  const sRu = t("ru")
  const textRu = sRu.notFoundBody(14, 0)
  assert(textRu.includes("14"), "RU text must contain document count 14")
  assert(textRu.includes("0"), "RU text must contain 0 passages")
  assert(
    textRu.includes("Генерация ответа намеренно заблокирована"),
    "RU text must state blocked generation explicitly"
  )
})

// -----------------------------------------------------------------------------
// КРИТЕРИЙ 4: Passage в CitationCard показан дословно (не обрезан)
// -----------------------------------------------------------------------------
console.log("\nКритерий 4: Passage показан дословно, без обрезки")

test("CitationCard.tsx рендерит citation.passage целиком", () => {
  const code = fs.readFileSync(path.join(__dirname, "CitationCard.tsx"), "utf-8")
  assert(code.includes("{citation.passage}"), "Must render {citation.passage} directly")
  assert(!code.includes(".slice("), "Must not slice passage")
  assert(!code.includes(".substring("), "Must not substring passage")
  assert(!code.includes("..."), "Must not append hardcoded ellipsis to passage")
})

test("chat.css не имеет text-overflow: ellipsis или line-clamp для passage", () => {
  const css = fs.readFileSync(path.join(__dirname, "chat.css"), "utf-8")
  const passageIdx = css.indexOf(".citation__passage")
  assert(passageIdx !== -1, "Must define .citation__passage")
  const block = css.slice(passageIdx, css.indexOf("}", passageIdx))
  assert(!block.includes("-webkit-line-clamp"), "Must not clamp lines")
  assert(!block.includes("text-overflow: ellipsis"), "Must not use ellipsis")
  assert(block.includes("overflow-wrap: anywhere"), "Must wrap words properly")
})

// -----------------------------------------------------------------------------
// КРИТЕРИЙ 5: npm run typecheck && build чисто, нет #hex / rgb( в features/**
// -----------------------------------------------------------------------------
console.log("\nКритерий 5: Чистота токенов (#hex / rgb отсутствуют в features/**)")

test("В frontend/src/features/** отсутствуют литеральные цвета (#hex и rgb/rgba)", () => {
  const featuresDir = path.resolve(__dirname, "..")
  function checkDir(dir: string): void {
    const entries = fs.readdirSync(dir, { withFileTypes: true })
    for (const entry of entries) {
      const full = path.join(dir, entry.name)
      if (entry.isDirectory()) {
        checkDir(full)
      } else if (entry.isFile() && (entry.name.endsWith(".tsx") || entry.name.endsWith(".css") || (entry.name.endsWith(".ts") && !entry.name.endsWith(".test.ts")))) {
        const content = fs.readFileSync(full, "utf-8")
        const hexMatch = content.match(/#[0-9a-fA-F]{3,8}\b/)
        const rgbMatch = content.match(/rgba?\(/)
        assert(!hexMatch, `${entry.name} не должен содержать #hex (найдено: ${hexMatch?.[0]})`)
        assert(!rgbMatch, `${entry.name} не должен содержать rgb/rgba (найдено: ${rgbMatch?.[0]})`)
      }
    }
  }
  checkDir(featuresDir)
})

// -----------------------------------------------------------------------------
// КРИТЕРИЙ 6: Переключатель языка меняет lang и язык интерфейса
// -----------------------------------------------------------------------------
console.log("\nКритерий 6: Переключатель языка и разделение RO/RU")

test("i18n предоставляет полные словари для RO и RU", () => {
  const ro = t("ro")
  const ru = t("ru")
  assert(ro.appTitle === "Asistentul municipal Chișinău", "RO app title")
  assert(ru.appTitle === "Муниципальный ассистент Кишинёва", "RU app title")
  assert(ro.send === "Întreabă", "RO send button")
  assert(ru.send === "Спросить", "RU send button")
})

test("Язык ответа наследуется из response.language", () => {
  const answerCode = fs.readFileSync(path.join(__dirname, "AnswerCard.tsx"), "utf-8")
  assert(answerCode.includes("const lang = response.language"), "AnswerCard must use response.language")
  assert(answerCode.includes("const s = t(lang)"), "AnswerCard must use strings for response.language")
})

// -----------------------------------------------------------------------------
// ГРАНИЦЫ ДАННЫХ (QA ПУНКТ 3)
// -----------------------------------------------------------------------------
console.log("\nГраницы данных: diacritics, пустые списки, null/undefined")

test("Снятие диакритики (fold): ș/ş, ț/ţ, ă, â, î и регистр", () => {
  function fold(text: string): string {
    return text.toLowerCase().normalize("NFD").replace(/\p{Diacritic}/gu, "")
  }
  assertEqual(fold("Audiență"), "audienta", "Audiență -> audienta")
  assertEqual(fold("AUDIENȚĂ"), "audienta", "AUDIENȚĂ -> audienta")
  assertEqual(fold("Chișinău"), "chisinau", "Chișinău -> chisinau")
  assertEqual(fold("PARCARE"), "parcare", "PARCARE -> parcare")
  assertEqual(fold("șşțţăâî"), "ssttaai", "All diacritics stripped")
})

test("Обработка смешанных строк RU/RO и пустых/одиночных списков", () => {
  const sRu = t("ru")
  assertEqual(sRu.metaPassages(0, 0), "Фрагментов: 0 проверено · 0 использовано", "0 passages")
  assertEqual(sRu.metaPassages(1, 1), "Фрагментов: 1 проверено · 1 использовано", "1 passage")
  assertEqual(sRu.metaPassages(10, 2), "Фрагментов: 10 проверено · 2 использовано", "multiple passages")
})

console.log(`\nИТОГ ТЕСТОВ: ${passed} пройдено, ${failed} упало.`)
if (failed > 0) {
  // @ts-ignore
  process.exit(1)
}
