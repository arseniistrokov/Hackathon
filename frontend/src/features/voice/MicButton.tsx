import { useEffect, useRef, useState } from "react"
import "./mic.css"

export interface MicButtonProps {
  onTranscript: (text: string) => void
  lang: "ro" | "ru"
  recognitionFactory?: () => any
}

export function getSpeechRecognitionClass(): any {
  if (typeof window === "undefined") return null
  const win = window as any
  return win.SpeechRecognition || win.webkitSpeechRecognition || null
}

export function isSpeechRecognitionSupported(): boolean {
  return Boolean(getSpeechRecognitionClass())
}

export function resolveSpeechLang(lang: "ro" | "ru"): string {
  return lang === "ru" ? "ru-RU" : "ro-RO"
}

export function MicButton({
  onTranscript,
  lang,
  recognitionFactory,
}: MicButtonProps) {
  const [isSupported, setIsSupported] = useState<boolean>(() => {
    if (recognitionFactory) return true
    return isSpeechRecognitionSupported()
  })
  const [isListening, setIsListening] = useState<boolean>(false)
  const recognitionRef = useRef<any>(null)

  useEffect(() => {
    setIsSupported(Boolean(recognitionFactory || isSpeechRecognitionSupported()))
  }, [recognitionFactory])

  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort?.()
        } catch {
          // ignore
        }
      }
    }
  }, [])

  if (!isSupported) {
    return null
  }

  const handleClick = () => {
    if (isListening) {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop?.()
        } catch {
          // ignore
        }
      }
      setIsListening(false)
      return
    }

    const SpeechRecClass = recognitionFactory
      ? recognitionFactory()
      : getSpeechRecognitionClass()

    if (!SpeechRecClass) {
      setIsSupported(false)
      return
    }

    try {
      const recognition =
        typeof SpeechRecClass === "function" ? new SpeechRecClass() : SpeechRecClass

      recognitionRef.current = recognition
      recognition.lang = resolveSpeechLang(lang)
      recognition.interimResults = false

      recognition.onresult = (event: any) => {
        const text = event?.results?.[0]?.[0]?.transcript ?? ""
        if (text) {
          onTranscript(text)
        }
        setIsListening(false)
      }

      recognition.onerror = () => {
        setIsListening(false)
      }

      recognition.onend = () => {
        setIsListening(false)
      }

      recognition.start()
      setIsListening(true)
    } catch (err) {
      console.error("SpeechRecognition start error:", err)
      setIsListening(false)
    }
  }

  const label = isListening
    ? lang === "ru"
      ? "Остановить запись"
      : "Oprește înregistrarea"
    : lang === "ru"
      ? "Голосовой ввод"
      : "Introducere vocală"

  // Честно про голос (EU alignment C3): Web Speech API отправляет аудио в облачный
  // сервис браузера, а не обрабатывает его локально — пользователь должен это знать.
  const privacyNote =
    lang === "ru"
      ? "звук обрабатывается облачным сервисом браузера (Web Speech API), не локально"
      : "sunetul este procesat de serviciul cloud al browserului (Web Speech API), nu local"

  return (
    <button
      type="button"
      className={`mic-btn ${isListening ? "mic-btn--listening" : ""}`}
      onClick={handleClick}
      aria-label={label}
      aria-pressed={isListening}
      title={`${label} — ${privacyNote}`}
    >
      <span className="mic-btn__icon" aria-hidden="true">
        🎙️
      </span>
    </button>
  )
}
