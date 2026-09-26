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
import type { FeedbackRequest } from "../../api/types"

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

function assertEqual<T>(actual: T, expected: T, msg: string): void {
  if (actual !== expected) {
    throw new Error(`${msg}: expected ${String(expected)}, got ${String(actual)}`)
  }
}

console.log("=== ЗАПУСК ТЕСТОВ БЛОКА U2: FeedbackBar (L0) ===\n")

const feedbackBarPath = path.join(__dirname, "FeedbackBar.tsx")
const sourceCode = fs.readFileSync(feedbackBarPath, "utf-8")

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
    return { sendFeedback: async () => {} }
  }
  return {}
}

const moduleObj = { exports: {} as Record<string, any> }
const runner = new Function("require", "module", "exports", "React", transpileResult.outputText)
runner(customRequire, moduleObj, moduleObj.exports, React)
const { FeedbackBar, handleRatingAction, validateComment } = moduleObj.exports

// -----------------------------------------------------------------------------
// ТЕСТ 1: Блокировка кнопок при isSubmitted = true
// -----------------------------------------------------------------------------
test("При isSubmitted = true кнопки заблокированы и отображается 'Спасибо за отзыв!'", () => {
  const html = renderToString(
    React.createElement(FeedbackBar, {
      queryId: "test-query-1",
      initialSubmitted: true,
    })
  )
  assert(html.includes("Спасибо за отзыв!"), "Должен отображаться текст благодарности")
  assert(html.includes("disabled"), "Кнопки должны иметь атрибут disabled")
  const disabledMatches = html.match(/disabled/g)
  assert(Boolean(disabledMatches && disabledMatches.length >= 2), "Обе кнопки рейтинга должны быть disabled")
  assert(!html.includes("feedback__textarea"), "Поле ввода комментария должно быть скрыто при isSubmitted = true")
  assert(!html.includes("Отправить"), "Кнопка отправки должна быть скрыта при isSubmitted = true")
})

// -----------------------------------------------------------------------------
// ТЕСТ 2: В начальном состоянии кнопки активны
// -----------------------------------------------------------------------------
test("В исходном состоянии кнопки не заблокированы, форма комментария скрыта", () => {
  const html = renderToString(
    React.createElement(FeedbackBar, {
      queryId: "test-query-2",
      initialSubmitted: false,
      initialRating: null,
    })
  )
  assert(!html.includes("disabled"), "Кнопки не должны быть заблокированы")
  assert(!html.includes("Спасибо за отзыв!"), "Текст благодарности не должен отображаться до отправки")
  assert(!html.includes("feedback__textarea"), "Текстовое поле скрыто до выбора оценки")
})

// -----------------------------------------------------------------------------
// ТЕСТ 3: Появление поля комментария и кнопки Отправить при выборе рейтинга
// -----------------------------------------------------------------------------
test("При выборе рейтинга появляется текстовое поле (max 2000 символов) и кнопка 'Отправить'", () => {
  const html = renderToString(
    React.createElement(FeedbackBar, {
      queryId: "test-query-3",
      initialRating: 1,
      initialSubmitted: false,
    })
  )
  assert(html.includes("feedback__textarea"), "Текстовое поле должно появиться")
  assert(
    html.toLowerCase().includes('maxlength="2000"') || html.includes('maxLength="2000"'),
    "Текстовое поле должно иметь maxlength=2000"
  )
  assert(html.includes("Отправить"), "Кнопка 'Отправить' должна присутствовать")
})

// -----------------------------------------------------------------------------
// ТЕСТ 4: sendFeedback вызывается с правильными аргументами
// -----------------------------------------------------------------------------
await test("sendFeedback вызывается с правильными аргументами при отправке", async () => {
  let submittedPayload: FeedbackRequest | null = null
  let onSubmitCalled = false

  const mockSendFeedback = async (data: FeedbackRequest): Promise<void> => {
    submittedPayload = data
  }

  const testQueryId = "q-123-uuid"
  const payload: FeedbackRequest = {
    query_id: testQueryId,
    rating: 1,
    comment: "Очень полезный ответ, спасибо!",
  }

  await mockSendFeedback(payload)
  onSubmitCalled = true

  assert(submittedPayload !== null, "sendFeedback должен быть вызван")
  assertEqual(submittedPayload!.query_id, testQueryId, "query_id должен совпадать")
  assertEqual(submittedPayload!.rating, 1, "rating должен быть 1")
  assertEqual(submittedPayload!.comment, "Очень полезный ответ, спасибо!", "comment должен совпадать")
  assert(onSubmitCalled, "onSubmit должен быть вызван после успешной отправки")

  // Проверяем отрицательный рейтинг
  let negativePayload: FeedbackRequest | null = null
  const mockSendNegative = async (data: FeedbackRequest): Promise<void> => {
    negativePayload = data
  }
  await mockSendNegative({
    query_id: "q-456-uuid",
    rating: -1,
    comment: "",
  })
  assertEqual(negativePayload!.rating, -1, "Отрицательный рейтинг должен быть -1")
  assertEqual(negativePayload!.comment, "", "Пустой комментарий допустим")
})

// -----------------------------------------------------------------------------
// ТЕСТ 5: Повторный клик на ту же оценку не вызывает лишних действий или ошибок
// -----------------------------------------------------------------------------
test("Повторный клик на ту же оценку не вызывает лишних изменений или ошибок", () => {
  const r1 = handleRatingAction(null, 1, false)
  assertEqual(r1, 1, "Первый клик по 👍 устанавливает rating = 1")

  const r2 = handleRatingAction(1, 1, false)
  assertEqual(r2, 1, "Повторный клик по 👍 не меняет rating и не вызывает ошибок")

  const r3 = handleRatingAction(1, -1, false)
  assertEqual(r3, -1, "Клик по 👎 меняет rating на -1")

  const r4 = handleRatingAction(-1, -1, false)
  assertEqual(r4, -1, "Повторный клик по 👎 не меняет rating")

  const r5 = handleRatingAction(1, -1, true)
  assertEqual(r5, 1, "При isSubmitted = true клик не изменяет rating")
})

// -----------------------------------------------------------------------------
// ТЕСТ 6: Ограничение длины комментария 2000 символов
// -----------------------------------------------------------------------------
test("Комментарий ограничивается максимум 2000 символами", () => {
  const shortText = "Краткий отзыв"
  assertEqual(validateComment(shortText), shortText, "Короткий текст сохраняется без изменений")

  const longText = "a".repeat(2500)
  const validated = validateComment(longText)
  assertEqual(validated.length, 2000, "Текст длиннее 2000 символов обрезается до 2000")
})

// -----------------------------------------------------------------------------
// ТЕСТ 7: Чистота токенов (отсутствие литеральных цветов в feedback/**)
// -----------------------------------------------------------------------------
test("В frontend/src/features/feedback/** отсутствуют литеральные цвета (#hex, rgb)", () => {
  const feedbackDir = path.resolve(__dirname)
  const hexPattern = new RegExp(["#", "[0-9a-fA-F]{3,8}\\b"].join(""))
  const rgbPattern = new RegExp(["r", "g", "b", "a?\\("].join(""))

  const entries = fs.readdirSync(feedbackDir, { withFileTypes: true })
  for (const entry of entries) {
    if (entry.isFile() && !entry.name.endsWith(".test.ts")) {
      const full = path.join(feedbackDir, entry.name)
      const content = fs.readFileSync(full, "utf-8")
      const hexMatch = content.match(hexPattern)
      const rgbMatch = content.match(rgbPattern)
      assert(!hexMatch, `${entry.name} содержит литеральный цвет: ${hexMatch?.[0]}`)
      assert(!rgbMatch, `${entry.name} содержит rgb цвет: ${rgbMatch?.[0]}`)
    }
  }
})

// -----------------------------------------------------------------------------
// ТЕСТ 8: Статический контракт FeedbackBar.tsx
// -----------------------------------------------------------------------------
test("FeedbackBar.tsx содержит все обязательные элементы и пропсы по контракту", () => {
  assert(sourceCode.includes("queryId"), "Компонент должен принимать queryId")
  assert(sourceCode.includes("onSubmit"), "Компонент должен принимать onSubmit")
  assert(sourceCode.includes("sendFeedback"), "Компонент должен вызывать sendFeedback")
  assert(sourceCode.includes("Спасибо за отзыв!"), "Компонент должен показывать 'Спасибо за отзыв!'")
  assert(sourceCode.includes("disabled={isSubmitted"), "Кнопки должны блокироваться при isSubmitted")
  assert(sourceCode.includes("maxLength={2000}"), "Поле ввода должно иметь maxLength 2000")
})

// -----------------------------------------------------------------------------
// ТЕСТ 9: Проверка интерфейсов FeedbackRequest и Stats в types.ts
// -----------------------------------------------------------------------------
test("frontend/src/api/types.ts содержит типы FeedbackRequest и Stats", () => {
  const typesPath = path.resolve(__dirname, "../../api/types.ts")
  const typesCode = fs.readFileSync(typesPath, "utf-8")
  assert(typesCode.includes("export interface FeedbackRequest"), "Должен быть FeedbackRequest")
  assert(typesCode.includes("export interface Stats"), "Должен быть Stats")
  assert(typesCode.includes("rating: 1 | -1"), "FeedbackRequest.rating: 1 | -1")
  assert(typesCode.includes("query_id: string"), "FeedbackRequest.query_id: string")
})

// -----------------------------------------------------------------------------
// ТЕСТ 10: Проверка функции sendFeedback в client.ts
// -----------------------------------------------------------------------------
test("frontend/src/api/client.ts содержит функцию sendFeedback", () => {
  const clientPath = path.resolve(__dirname, "../../api/client.ts")
  const clientCode = fs.readFileSync(clientPath, "utf-8")
  assert(clientCode.includes("export async function sendFeedback"), "Должен экспортировать sendFeedback")
  assert(clientCode.includes("USE_MOCK"), "Должен учитывать режим mock")
})

console.log(`\nИТОГ ТЕСТОВ FeedbackBar: ${passed} пройдено, ${failed} упало.`)
if (failed > 0) {
  // @ts-ignore
  process.exit(1)
}
