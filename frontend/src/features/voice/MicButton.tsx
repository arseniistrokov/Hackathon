import { useEffect, useRef, useState } from "react"
import { transcribe } from "../../api/client"
import { t } from "../../i18n"
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

export function isMediaRecorderSupported(): boolean {
  if (typeof window === "undefined") return false
  const nav = typeof navigator !== "undefined" ? navigator : null
  return Boolean(nav?.mediaDevices?.getUserMedia && typeof MediaRecorder !== "undefined")
}

export function resolveSpeechLang(lang: "ro" | "ru"): string {
  return lang === "ru" ? "ru-RU" : "ro-RO"
}

type MicStatus = "idle" | "recording" | "recognizing" | "web_speech"

export function MicButton({
  onTranscript,
  lang,
  recognitionFactory,
}: MicButtonProps) {
  const strings = t(lang)
  const [sttBackendAvailable, setSttBackendAvailable] = useState<boolean | null>(null)
  const [status, setStatus] = useState<MicStatus>("idle")
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const recognitionRef = useRef<any>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioStreamRef = useRef<MediaStream | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const timeoutTimerRef = useRef<any>(null)

  // Проверяем /api/health на доступность STT
  useEffect(() => {
    let active = true
    if (typeof fetch === "function") {
      fetch("/api/health")
        .then((r) => {
          if (!r.ok) throw new Error("health check failed")
          return r.json()
        })
        .then((data) => {
          if (active) {
            setSttBackendAvailable(data?.stt === "whisper")
          }
        })
        .catch(() => {
          if (active) {
            setSttBackendAvailable(false)
          }
        })
    } else {
      setSttBackendAvailable(false)
    }
    return () => {
      active = false
    }
  }, [])

  // Очистка при размонтировании
  useEffect(() => {
    return () => {
      if (timeoutTimerRef.current) {
        clearTimeout(timeoutTimerRef.current)
      }
      if (audioStreamRef.current) {
        audioStreamRef.current.getTracks().forEach((track) => track.stop())
      }
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort?.()
        } catch {
          // ignore
        }
      }
    }
  }, [])

  const hasAnySupport =
    Boolean(recognitionFactory) ||
    isSpeechRecognitionSupported() ||
    isMediaRecorderSupported()

  if (!hasAnySupport) {
    return null
  }

  const stopMediaRecording = () => {
    if (timeoutTimerRef.current) {
      clearTimeout(timeoutTimerRef.current)
      timeoutTimerRef.current = null
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      try {
        mediaRecorderRef.current.stop()
      } catch {
        // ignore
      }
    }
    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach((track) => track.stop())
      audioStreamRef.current = null
    }
  }

  const startWebSpeech = () => {
    const SpeechRecClass = recognitionFactory
      ? recognitionFactory()
      : getSpeechRecognitionClass()

    if (!SpeechRecClass) {
      setErrorMessage(strings.micUnavailable)
      setStatus("idle")
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
        setStatus("idle")
      }

      recognition.onerror = () => {
        setStatus("idle")
      }

      recognition.onend = () => {
        setStatus("idle")
      }

      recognition.start()
      setStatus("web_speech")
    } catch (err) {
      console.error("SpeechRecognition start error:", err)
      setStatus("idle")
    }
  }

  const startMediaRecording = async () => {
    setErrorMessage(null)
    chunksRef.current = []

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      audioStreamRef.current = stream

      let recorder: MediaRecorder
      if (
        typeof MediaRecorder.isTypeSupported === "function" &&
        MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
      ) {
        recorder = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" })
      } else {
        recorder = new MediaRecorder(stream)
      }
      mediaRecorderRef.current = recorder

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          chunksRef.current.push(event.data)
        }
      }

      recorder.onstop = async () => {
        setStatus("recognizing")
        const mimeType = recorder.mimeType || "audio/webm"
        const audioBlob = new Blob(chunksRef.current, { type: mimeType })
        try {
          const res = await transcribe(audioBlob, lang)
          if (res.text) {
            onTranscript(res.text)
          }
          setStatus("idle")
        } catch (err) {
          console.warn("STT backend transcribe failed, falling back to Web Speech:", err)
          setStatus("idle")
          startWebSpeech()
        }
      }

      recorder.start()
      setStatus("recording")

      // Автоматическая остановка через 15 секунд
      timeoutTimerRef.current = setTimeout(() => {
        stopMediaRecording()
      }, 15_000)
    } catch (err) {
      console.warn("getUserMedia error:", err)
      setErrorMessage(strings.micUnavailable)
      setStatus("idle")
      if (isSpeechRecognitionSupported() || recognitionFactory) {
        startWebSpeech()
      }
    }
  }

  const handleClick = () => {
    if (status === "recording") {
      stopMediaRecording()
      return
    }

    if (status === "web_speech") {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop?.()
        } catch {
          // ignore
        }
      }
      setStatus("idle")
      return
    }

    if (status === "recognizing") {
      return
    }

    // Если бэкенд STT доступен (stt == 'whisper') и MediaRecorder поддерживается — основной путь
    const canUseWhisper = sttBackendAvailable === true && isMediaRecorderSupported()
    if (canUseWhisper) {
      void startMediaRecording()
    } else {
      startWebSpeech()
    }
  }

  // Лейблы и подсказки
  let label = strings.micStart
  let btnClass = "mic-btn"

  if (status === "recording") {
    label = strings.recording
    btnClass = "mic-btn mic-btn--recording"
  } else if (status === "recognizing") {
    label = strings.recognizing
    btnClass = "mic-btn mic-btn--recognizing"
  } else if (status === "web_speech") {
    label = strings.micStop
    btnClass = "mic-btn mic-btn--listening"
  }

  const privacyNote =
    lang === "ru"
      ? "звук обрабатывается облачным сервисом браузера (Web Speech API), не локально"
      : "sunetul este procesat de serviciul cloud al browserului (Web Speech API), nu local"

  const titleText = errorMessage
    ? errorMessage
    : status === "recording"
    ? strings.recording
    : status === "recognizing"
    ? strings.recognizing
    : `${label} — ${sttBackendAvailable ? "faster-whisper (local)" : privacyNote}`

  return (
    <button
      type="button"
      className={btnClass}
      onClick={handleClick}
      aria-label={label}
      aria-pressed={status !== "idle"}
      title={titleText}
    >
      <span className="mic-btn__icon" aria-hidden="true">
        {status === "recognizing" ? "⏳" : "🎙️"}
      </span>
      {status === "recording" && (
        <span className="mic-btn__dot" aria-hidden="true" />
      )}
    </button>
  )
}
