import { useState, useCallback } from 'react'
import type { Message, FeedbackResponse } from '../types'

const API_URL = '/api/interview'

interface InterviewState {
  sessionId: string | null
  messages: Message[]
  turn: number
  isLoading: boolean
  isComplete: boolean
  feedback: FeedbackResponse | null
  error: string | null
}

export function useInterview() {
  const [state, setState] = useState<InterviewState>({
    sessionId: null,
    messages: [],
    turn: 0,
    isLoading: false,
    isComplete: false,
    feedback: null,
    error: null,
  })

  const startInterview = useCallback(async (candidateId: string) => {
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
    setState(prev => ({ ...prev, isLoading: true, error: null }))

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId,
          candidate: { candidate_id: candidateId },
        }),
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()

      setState({
        sessionId,
        messages: [{ role: 'interviewer', content: data.reply }],
        turn: 1,
        isLoading: false,
        isComplete: false,
        feedback: null,
        error: null,
      })
    } catch (e: unknown) {
      setState(prev => ({ ...prev, isLoading: false, error: (e as Error).message }))
    }
  }, [])

  const submitAnswer = useCallback(async (answer: string) => {
    if (!state.sessionId) return
    setState(prev => ({
      ...prev,
      messages: [...prev.messages, { role: 'candidate', content: answer }],
      isLoading: true,
      error: null,
    }))

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId: state.sessionId,
          message: answer,
        }),
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()

      if (data.done) {
        setState(prev => ({
          ...prev,
          messages: [...prev.messages, { role: 'interviewer', content: data.reply }],
          turn: prev.turn + 1,
          isLoading: false,
          isComplete: true,
          feedback: data.feedback,
        }))
      } else {
        setState(prev => ({
          ...prev,
          messages: [...prev.messages, { role: 'interviewer', content: data.reply }],
          turn: prev.turn + 1,
          isLoading: false,
        }))
      }
    } catch (e: unknown) {
      setState(prev => ({ ...prev, isLoading: false, error: (e as Error).message }))
    }
  }, [state.sessionId])

  const endInterview = useCallback(async () => {
    if (!state.sessionId) return
    setState(prev => ({ ...prev, isLoading: true }))
    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId: state.sessionId,
          message: "[END_INTERVIEW]",
        }),
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setState(prev => ({
        ...prev,
        isLoading: false,
        isComplete: true,
        feedback: data.feedback || null,
      }))
    } catch (e: unknown) {
      setState(prev => ({ ...prev, isLoading: false, error: (e as Error).message }))
    }
  }, [state.sessionId])

  return { ...state, startInterview, submitAnswer, endInterview }
}
