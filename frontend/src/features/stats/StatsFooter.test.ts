// @ts-ignore
import fs from "node:fs"
// @ts-ignore
import path from "node:path"
// @ts-ignore
import { fileURLToPath } from "node:url"
import React from "react"
import { renderToString } from "react-dom/server"
// @ts-ignore
import ts from "typescript"
import type { Stats } from "../../api/types"

// @ts-ignore
const __filename = fileURLToPath(import.meta.url)
// @ts-ignore
const __dirname = path.dirname(__filename)

let passed = 0
let failed = 0

function test(name: string, fn: () => void | Promise<void>): void | Promise<void> {
  try {
    const res = fn()
    if (res && typeof (res as Promise<void>).then === "function") {
      return (res as Promise<void>)
        .then(() => {
          passed++
          console.log(`  ✓ ${name}`)
        })
        .catch((err) => {
          failed++
          console.error(`  ✗ ${name}: ${(err as Error).message}`)
        })
    }
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

console.log("=== ЗАПУСК ТЕСТОВ БЛОКА U2: StatsFooter (L0) ===\n")

const statsFooterPath = path.join(__dirname, "StatsFooter.tsx")
const sourceCode = fs.readFileSync(statsFooterPath, "utf-8")

// Транспилируем TSX в CommonJS с React.createElement
const transpileResult = ts.transpileModule(sourceCode, {
  compilerOptions: {
    jsx: ts.JsxEmit.React,
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2022,
  },
})

const customRequire = (id: string) => {
  if (id === "react") return React
  if (id.endsWith(".css")) return {}
  if (id === "@/api/client" || id.endsWith("api/client")) {
    return {
      getStats: async (): Promise<Stats> => ({
        corpus_documents: 14,
        corpus_chunks: 52,
        sites: 8,
        conflicts: 2,
        queries: 0,
        feedback_up: 0,
        feedback_down: 0,
        model: "extractive",
      }),
    }
  }
  return {}
}

const moduleObj = { exports: {} as Record<string, any> }
const runner = new Function("require", "module", "exports", "React", transpileResult.outputText)
runner(customRequire, moduleObj, moduleObj.exports, React)
const { StatsFooter } = moduleObj.exports

// -----------------------------------------------------------------------------
// ТЕСТ 1: Рендер с валидным объектом Stats
// -----------------------------------------------------------------------------
test("Рендер с валидным объектом Stats отображает все 8 полей", () => {
  const mockStats: Stats = {
    corpus_documents: 14,
    corpus_chunks: 52,
    sites: 8,
    conflicts: 2,
    queries: 105,
    feedback_up: 42,
    feedback_down: 3,
    model: "extractive-v1",
  }

  const html = renderToString(React.createElement(StatsFooter, { stats: mockStats }))

  assert(html.includes("14"), "Должно отображаться число документов: 14")
  assert(html.includes("52"), "Должно отображаться число фрагментов: 52")
  assert(html.includes("8"), "Должно отображаться число сайтов: 8")
  assert(html.includes("2"), "Должно отображаться число конфликтов: 2")
  assert(html.includes("105"), "Должно отображаться число запросов: 105")
  assert(html.includes("42"), "Должно отображаться число лайков: 42")
  assert(html.includes("3"), "Должно отображаться число дизлайков: 3")
  assert(html.includes("extractive-v1"), "Должна отображаться модель: extractive-v1")
  assert(html.includes("stats-footer"), "Должен содержать корневой класс stats-footer")
})

// -----------------------------------------------------------------------------
// ТЕСТ 2: Рендер без переданных данных (stats = undefined) показывает состояние загрузки
// -----------------------------------------------------------------------------
test("Рендер с undefined данными отображает состояние загрузки", () => {
  const html = renderToString(React.createElement(StatsFooter, {}))
  assert(html.includes("stats-footer--loading"), "Должен содержать класс stats-footer--loading")
  assert(html.includes("Загрузка статистики"), "Должен отображать текст загрузки")
})

// -----------------------------------------------------------------------------
// ТЕСТ 3: Рендер с пустым/частичным объектом (null / пустые поля) не падает
// -----------------------------------------------------------------------------
test("Рендер с пустым или частичным объектом не падает и отображает значения по умолчанию", () => {
  const partialStats = {
    corpus_documents: 0,
    corpus_chunks: 0,
    sites: 0,
    conflicts: 0,
    queries: 0,
    feedback_up: 0,
    feedback_down: 0,
    model: "",
  } as Stats

  const html = renderToString(React.createElement(StatsFooter, { stats: partialStats }))
  assert(html.includes("stats-footer"), "Должен успешно отрендерить footer")
  assert(html.includes("Документы"), "Должен содержать подпись 'Документы'")

  // Проверка рендера с null
  const nullHtml = renderToString(React.createElement(StatsFooter, { stats: null }))
  assert(nullHtml.includes("stats-footer--empty"), "Должен корректно обработать stats=null")
  assert(nullHtml.includes("Статистика недоступна"), "Должен отобразить сообщение об отсутствии данных")
})

// -----------------------------------------------------------------------------
// ТЕСТ 4: Чистота токенов в stats/
// -----------------------------------------------------------------------------
test("В frontend/src/features/stats/** отсутствуют литеральные цвета (#hex, rgb)", () => {
  const statsDir = path.resolve(__dirname)
  const hexPattern = new RegExp(["#", "[0-9a-fA-F]{3,8}\\b"].join(""))
  const rgbPattern = new RegExp(["r", "g", "b", "a?\\("].join(""))

  const entries = fs.readdirSync(statsDir, { withFileTypes: true })
  for (const entry of entries) {
    if (entry.isFile() && !entry.name.endsWith(".test.ts")) {
      const full = path.join(statsDir, entry.name)
      const content = fs.readFileSync(full, "utf-8")
      const hexMatch = content.match(hexPattern)
      const rgbMatch = content.match(rgbPattern)
      assert(!hexMatch, `${entry.name} содержит литеральный цвет: ${hexMatch?.[0]}`)
      assert(!rgbMatch, `${entry.name} содержит rgb цвет: ${rgbMatch?.[0]}`)
    }
  }
})

// -----------------------------------------------------------------------------
// ТЕСТ 5: Статический контракт StatsFooter.tsx
// -----------------------------------------------------------------------------
test("StatsFooter.tsx соответствует контракту порта U2", () => {
  assert(sourceCode.includes("corpus_documents"), "Должен использовать corpus_documents")
  assert(sourceCode.includes("corpus_chunks"), "Должен использовать corpus_chunks")
  assert(sourceCode.includes("sites"), "Должен использовать sites")
  assert(sourceCode.includes("conflicts"), "Должен использовать conflicts")
  assert(sourceCode.includes("queries"), "Должен использовать queries")
  assert(sourceCode.includes("feedback_up"), "Должен использовать feedback_up")
  assert(sourceCode.includes("feedback_down"), "Должен использовать feedback_down")
  assert(sourceCode.includes("model"), "Должен использовать model")
  assert(sourceCode.includes("getStats"), "Должен импортировать getStats")
})

// -----------------------------------------------------------------------------
// ТЕСТ 6: client.ts getStats возвращает ожидаемые значения на L0 (USE_MOCK)
// -----------------------------------------------------------------------------
test("client.ts getStats() возвращает согласованные данные на моках", () => {
  const clientPath = path.resolve(__dirname, "../../api/client.ts")
  const clientCode = fs.readFileSync(clientPath, "utf-8")
  assert(clientCode.includes("getStats"), "client.ts должен экспортировать getStats")
  assert(clientCode.includes("corpus_documents: 14"), "corpus_documents на L0 должен быть 14")
  assert(clientCode.includes("corpus_chunks: 52"), "corpus_chunks на L0 должен быть 52")
  assert(clientCode.includes("sites: 8"), "sites на L0 должен быть 8")
  assert(clientCode.includes("conflicts: 2"), "conflicts на L0 должен быть 2")
})

console.log(`\nИТОГ ТЕСТОВ StatsFooter: ${passed} пройдено, ${failed} упало.`)
if (failed > 0) {
  // @ts-ignore
  process.exit(1)
}
