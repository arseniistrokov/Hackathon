import { useState } from "react"
import { sendFeedback } from "@/api/client"
import type { FeedbackRequest, Lang } from "@/api/types"
import "./feedback.css"

export interface FeedbackBarProps {
  queryId: string
  onSubmit?: () => void
  initialRating?: 1 | -1 | null
  initialSubmitted?: boolean
  sendFeedbackFn?: (data: FeedbackRequest) => Promise<void>
  lang?: Lang
}

export function handleRatingAction(
  currentRating: 1 | -1 | null,
  nextRating: 1 | -1,
  isSubmitted: boolean
): 1 | -1 | null {
  if (isSubmitted) return currentRating
  if (currentRating === nextRating) return currentRating
  return nextRating
}

export function validateComment(text: string): string {
  return text.slice(0, 2000)
}

export function FeedbackBar({
  queryId,
  onSubmit,
  initialRating = null,
  initialSubmitted = false,
  sendFeedbackFn = sendFeedback,
  lang = "ru",
}: FeedbackBarProps) {
  const [rating, setRating] = useState<1 | -1 | null>(initialRating)
  const [comment, setComment] = useState("")
  const [isSubmitted, setIsSubmitted] = useState(initialSubmitted)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleRating = (nextRating: 1 | -1) => {
    if (isSubmitted || isSubmitting) return
    if (rating === nextRating) return
    setRating(nextRating)
  }

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (rating === null || isSubmitted || isSubmitting) return

    setIsSubmitting(true)
    try {
      await sendFeedbackFn({
        query_id: queryId,
        rating,
        comment: validateComment(comment),
      })
      setIsSubmitted(true)
      onSubmit?.()
    } catch (err) {
      console.error("Ошибка при отправке отзыва:", err)
    } finally {
      setIsSubmitting(false)
    }
  }

  const isRo = lang === "ro"
  const positiveLabel = isRo ? "Răspuns util" : "Полезный ответ"
  const negativeLabel = isRo ? "Răspuns inutil" : "Бесполезный ответ"

  return (
    <div className="feedback animate-fade-in" aria-label="Обратная связь">
      <div className="feedback__rating-group">
        <button
          type="button"
          className={`feedback__btn ${rating === 1 ? "feedback__btn--active" : ""}`}
          disabled={isSubmitted || isSubmitting}
          onClick={() => handleRating(1)}
          aria-label={positiveLabel}
          aria-pressed={rating === 1}
        >
          👍
        </button>
        <button
          type="button"
          className={`feedback__btn ${rating === -1 ? "feedback__btn--active" : ""}`}
          disabled={isSubmitted || isSubmitting}
          onClick={() => handleRating(-1)}
          aria-label={negativeLabel}
          aria-pressed={rating === -1}
        >
          👎
        </button>
      </div>

      {isSubmitted && (
        <p className="feedback__message" role="status">
          Спасибо за отзыв!
        </p>
      )}

      {rating !== null && !isSubmitted && (
        <form className="feedback__form" onSubmit={handleSubmit}>
          <textarea
            className="feedback__textarea"
            value={comment}
            onChange={(e) => setComment(validateComment(e.target.value))}
            maxLength={2000}
            placeholder="Что можно улучшить? (необязательно)"
            disabled={isSubmitting}
            rows={2}
            aria-label="Текст отзыва"
          />
          <div className="feedback__actions">
            <button
              type="submit"
              className="feedback__submit-btn"
              disabled={isSubmitting}
            >
              Отправить
            </button>
          </div>
        </form>
      )}
    </div>
  )
}
