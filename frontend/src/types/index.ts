export interface StartResponse {
  interview_id: string
  status: string
  message: string
  question: string
  turn: number
  curriculum_days_covered: number
}

export interface AnswerResponse {
  interview_id: string
  status: string
  message: string
  turn: number
  curriculum_days_covered: number
  is_complete: boolean
}

export interface FeedbackResponse {
  summary: string
  strengths: string[]
  gaps: string[]
  next: string[]
}

export interface Message {
  role: 'interviewer' | 'candidate'
  content: string
}

export interface Candidate {
  candidate_id: string
  name: string
}
