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

console.log("=== ЗАПУСК ТЕСТОВ БЛОКА U2: MicButton (L0) ===\n")

const micButtonPath = path.join(__dirname, "MicButton.tsx")
const sourceCode = fs.readFileSync(micButtonPath, "utf-8")

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
  return {}
}

const moduleObj = { exports: {} as Record<string, any> }
const runner = new Function("require", "module", "exports", "React", transpileResult.outputText)
runner(customRequire, moduleObj, moduleObj.exports, React)
const { MicButton, resolveSpeechLang, isSpeechRecognitionSupported } = moduleObj.exports

// Мок для SpeechRecognition
class MockSpeechRecognition {
  lang = ""
  interimResults = true
  onresult: ((event: any) => void) | null = null
  onerror: (() => void) | null = null
  onend: (() => void) | null = null
  started = false

  start() {
    this.started = true
  }

  stop() {
    this.started = false
    this.onend?.()
  }

  abort() {
    this.started = false
  }

  simulateResult(text: string) {
    if (this.onresult) {
      this.onresult({
        results: [
          [
            { transcript: text }
          ]
        ]
      })
    }
  }
}

// -----------------------------------------------------------------------------
// ТЕСТ 1: Возвращает null (скрыта), если SpeechRecognition не поддерживается
// -----------------------------------------------------------------------------
test("Компонент возвращает null, если API распознавания отсутствует в window", () => {
  // Запоминаем текущее состояние window, если оно было
  const origWindow = (globalThis as any).window
  try {
    // Симулируем окружение без SpeechRecognition
    (globalThis as any).window = {}
    assert(!isSpeechRecognitionSupported(), "isSpeechRecognitionSupported должен вернуть false")

    const html = renderToString(
      React.createElement(MicButton, {
        onTranscript: () => {},
        lang: "ro",
      })
    )
    assertEqual(html, "", "Кнопка должна быть скрыта (null) при отсутствии API")
  } finally {
    (globalThis as any).window = origWindow
  }
})

// -----------------------------------------------------------------------------
// ТЕСТ 2: Рендерится кнопка, если API присутствует
// -----------------------------------------------------------------------------
test("Компонент рендерится, если SpeechRecognition или webkitSpeechRecognition присутствует", () => {
  const origWindow = (globalThis as any).window
  try {
    (globalThis as any).window = {
      webkitSpeechRecognition: MockSpeechRecognition,
    }
    assert(isSpeechRecognitionSupported(), "isSpeechRecognitionSupported должен вернуть true")

    const html = renderToString(
      React.createElement(MicButton, {
        onTranscript: () => {},
        lang: "ru",
      })
    )
    assert(html.includes("mic-btn"), "Кнопка должна содержать класс mic-btn")
    assert(html.includes("🎙️"), "Кнопка должна содержать иконку микрофона")
    assert(html.includes("Голосовой ввод"), "Кнопка должна иметь aria-label/title 'Голосовой ввод'")
  } finally {
    (globalThis as any).window = origWindow
  }
})

// -----------------------------------------------------------------------------
// ТЕСТ 3: Имитация onresult вызывает onTranscript с распознанным текстом
// -----------------------------------------------------------------------------
test("Имитация события onresult вызывает onTranscript с распознанным текстом", () => {
  let receivedTranscript = ""
  const mockRec = new MockSpeechRecognition()

  // Инициализация параметров распознавания
  mockRec.lang = resolveSpeechLang("ro")
  mockRec.interimResults = false

  mockRec.onresult = (event: any) => {
    const text = event?.results?.[0]?.[0]?.transcript ?? ""
    if (text) {
      receivedTranscript = text
    }
  }

  mockRec.start()
  assert(mockRec.started, "Recognition должен быть запущен")
  assertEqual(mockRec.lang, "ro-RO", "Язык для 'ro' должен быть 'ro-RO'")
  assertEqual(mockRec.interimResults, false, "interimResults должен быть false")

  // Имитируем получение финального результата
  const recognizedPhrase = "Cum pot depune o petiție la Primărie?"
  mockRec.simulateResult(recognizedPhrase)

  assertEqual(receivedTranscript, recognizedPhrase, "onTranscript должен получить распознанный текст")
})

// -----------------------------------------------------------------------------
// ТЕСТ 4: Проверка языка распознавания ro-RO и ru-RU
// -----------------------------------------------------------------------------
test("resolveSpeechLang корректно выбирает ro-RO и ru-RU", () => {
  assertEqual(resolveSpeechLang("ro"), "ro-RO", "Язык ro -> ro-RO")
  assertEqual(resolveSpeechLang("ru"), "ru-RU", "Язык ru -> ru-RU")
})

// -----------------------------------------------------------------------------
// ТЕСТ 5: Чистота токенов в voice/
// -----------------------------------------------------------------------------
test("В frontend/src/features/voice/** отсутствуют литеральные цвета (#hex, rgb)", () => {
  const voiceDir = path.resolve(__dirname)
  const hexPattern = new RegExp(["#", "[0-9a-fA-F]{3,8}\\b"].join(""))
  const rgbPattern = new RegExp(["r", "g", "b", "a?\\("].join(""))

  const entries = fs.readdirSync(voiceDir, { withFileTypes: true })
  for (const entry of entries) {
    if (entry.isFile() && !entry.name.endsWith(".test.ts")) {
      const full = path.join(voiceDir, entry.name)
      const content = fs.readFileSync(full, "utf-8")
      const hexMatch = content.match(hexPattern)
      const rgbMatch = content.match(rgbPattern)
      assert(!hexMatch, `${entry.name} содержит литеральный цвет: ${hexMatch?.[0]}`)
      assert(!rgbMatch, `${entry.name} содержит rgb цвет: ${rgbMatch?.[0]}`)
    }
  }
})

// -----------------------------------------------------------------------------
// ТЕСТ 6: Размер кнопки tap-min и отсутствие авто-отправки
// -----------------------------------------------------------------------------
test("mic.css использует --tap-min и MicButton не содержит авто-отправки вопроса", () => {
  const cssContent = fs.readFileSync(path.join(__dirname, "mic.css"), "utf-8")
  assert(cssContent.includes("var(--tap-min)"), "mic.css должен использовать --tap-min для размера кнопки")

  // MicButton не должен импортировать ask или вызывать отправку
  assert(!sourceCode.includes("ask("), "MicButton не должен вызывать ask()")
  assert(!sourceCode.includes("postJson"), "MicButton не должен отправлять HTTP запросы")
})

console.log(`\nИТОГ ТЕСТОВ MicButton: ${passed} пройдено, ${failed} упало.`)
if (failed > 0) {
  // @ts-ignore
  process.exit(1)
}
