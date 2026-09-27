// Зеркало app/contracts/models.py (только чтение). Поля, имена и опциональность — как там, snake_case.
// Даты в JSON приходят строками ISO (dt.date → "2023-05-18"). Опциональные поля допускают null и undefined:
// бэкенд присылает null, а моки/частичные ответы могут поле не прислать вовсе — экран не должен падать ни там, ни там.

export type Lang = "ro" | "ru"
export type Status = "ANSWERED" | "NOT_FOUND" | "CONFLICT"

export interface Citation {
  chunk_id: string
  document_id: string
  title: string
  url: string
  site: string
  section?: string | null
  page?: number | null
  passage: string
  date?: string | null
}

export interface ConflictSide {
  citation: Citation
  value: string
  date?: string | null
}

export interface Conflict {
  id: string
  entity: string
  a: ConflictSide
  b: ConflictSide
  resolved_by_date: boolean
}

export interface Navigation {
  label: string
  url: string
}

export interface Meta {
  corpus_documents: number
  corpus_chunks: number
  passages_retrieved: number
  passages_used: number
  model: string
  latency_ms: number
  query_id: string
}

export interface AskRequest {
  question: string
  lang?: Lang | null
}

export interface AskResponse {
  question: string
  language: Lang
  status: Status
  answer: string
  citations: Citation[]
  conflict?: Conflict | null
  warning?: string | null
  navigation?: Navigation | null
  meta: Meta
}

export interface FeedbackRequest {
  query_id: string
  rating: 1 | -1
  comment: string
}

export interface Stats {
  corpus_documents: number
  corpus_chunks: number
  sites: number
  conflicts: number
  queries: number
  feedback_up: number
  feedback_down: number
  model: string
}

export interface TranscribeResponse {
  text: string
  lang?: string | null
  duration_ms?: number
}

