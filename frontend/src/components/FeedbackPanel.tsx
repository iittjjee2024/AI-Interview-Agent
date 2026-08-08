import type { FeedbackResponse } from '../types'

interface Props {
  feedback: FeedbackResponse
}

export default function FeedbackPanel({ feedback }: Props) {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Interview Feedback</h2>
        <p className="text-gray-700">{feedback.summary}</p>
      </div>

      {feedback.strengths.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="font-semibold text-green-800 mb-3">Strengths</h3>
          <ul className="space-y-2">
            {feedback.strengths.map((s, i) => (
              <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                <span className="text-green-500 mt-0.5">&#10003;</span>
                {s}
              </li>
            ))}
          </ul>
        </div>
      )}

      {feedback.gaps.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="font-semibold text-red-800 mb-3">Areas for Improvement</h3>
          <ul className="space-y-2">
            {feedback.gaps.map((g, i) => (
              <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                <span className="text-red-400 mt-0.5">&#9679;</span>
                {g}
              </li>
            ))}
          </ul>
        </div>
      )}

      {feedback.next.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="font-semibold text-blue-800 mb-3">Recommended Next Steps</h3>
          <ul className="space-y-2">
            {feedback.next.map((n, i) => (
              <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                <span className="text-blue-500 mt-0.5">&#10147;</span>
                {n}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
