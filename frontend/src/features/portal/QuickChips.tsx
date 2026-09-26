import type { Lang } from "@/api/types"

export interface QuickChipItem {
  id: string
  label: string
  query: string
}

export interface QuickChipsProps {
  onAsk: (question: string) => void
  lang?: Lang
}

const CHIPS_RO: QuickChipItem[] = [
  { id: "rtec", label: "🚌 Tarife RTEC", query: "Tarife RTEC" },
  { id: "petitii", label: "📑 Termen petiții", query: "Care este termenul de examinare a unei petiții?" },
  { id: "pretura", label: "🏢 Audiență pretură", query: "Audiență pretură" },
  { id: "parcare", label: "🅿️ Parcare", query: "Parcare" },
]

const CHIPS_RU: QuickChipItem[] = [
  { id: "rtec", label: "🚌 Тарифы RTEC", query: "Тарифы RTEC" },
  { id: "petitii", label: "📑 Сроки петиций", query: "В какой срок рассматривается петиция в примэрии?" },
  { id: "pretura", label: "🏢 Приём в претуре", query: "Приём в претуре" },
  { id: "parcare", label: "🅿️ Парковки", query: "Парковки" },
]

export function QuickChips({ onAsk, lang = "ro" }: QuickChipsProps) {
  const chips = lang === "ru" ? CHIPS_RU : CHIPS_RO
  const heading = lang === "ru" ? "Быстрые вопросы" : "Întrebări frecvente"

  return (
    <nav className="quick-chips" aria-label={heading}>
      <span className="quick-chips__label">{heading}:</span>
      <div className="quick-chips__list" role="toolbar" aria-label={heading}>
        {chips.map((chip) => (
          <button
            key={chip.id}
            type="button"
            className="quick-chip"
            onClick={() => onAsk(chip.query)}
            aria-label={`${heading}: ${chip.label}`}
          >
            {chip.label}
          </button>
        ))}
      </div>
    </nav>
  )
}
