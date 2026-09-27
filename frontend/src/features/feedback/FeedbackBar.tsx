import { useState } from "react"
import { sendFeedback } from "@/api/client"
import type { FeedbackRequest, Lang } from "@/api/types"
import { t } from "@/i18n"
import "./feedback.css"

export interface FeedbackBarProps {
  queryId: string
  lang?: Lang
  onSubmit?: () => void
  initialRating?: 1 | -1 | null
  initialSubmitted?: boolean
  sendFeedbackFn?: (data: FeedbackRequest) => Promise<void>
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
  lang = "ru",
  onSubmit,
  initialRating = null,
  initialSubmitted = false,
  sendFeedbackFn = sendFeedback,
}: FeedbackBarProps) {
  const s = t(lang)
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
      console.error("Feedback submit error:", err)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="feedback" aria-label={s.feedbackAriaLabel}>
      <div className="feedback__rating-group">
        <button
          type="button"
          className={`feedback__btn ${rating === 1 ? "feedback__btn--active" : ""}`}
          disabled={isSubmitted || isSubmitting}
          onClick={() => handleRating(1)}
          aria-label={s.feedbackUseful}
          aria-pressed={rating === 1}
        >
          👍
        </button>
        <button
          type="button"
          className={`feedback__btn ${rating === -1 ? "feedback__btn--active" : ""}`}
          disabled={isSubmitted || isSubmitting}
          onClick={() => handleRating(-1)}
          aria-label={s.feedbackNotUseful}
          aria-pressed={rating === -1}
        >
          👎
        </button>
      </div>

      {isSubmitted && (
        <p className="feedback__message" role="status">
          {s.feedbackThanks}
        </p>
      )}

      {rating !== null && !isSubmitted && (
        <form className="feedback__form" onSubmit={handleSubmit}>
          <textarea
            className="feedback__textarea"
            value={comment}
            onChange={(e) => setComment(validateComment(e.target.value))}
            maxLength={2000}
            placeholder={s.feedbackCommentPlaceholder}
            disabled={isSubmitting}
            rows={2}
            aria-label={s.feedbackCommentAriaLabel}
          />
          <div className="feedback__actions">
            <button
              type="submit"
              className="feedback__submit-btn"
              disabled={isSubmitting}
            >
              {s.feedbackSubmit}
            </button>
          </div>
        </form>
      )}
    </div>
  )
}
