import { useState, useEffect } from 'react'

interface Candidate {
  id: string
  name: string
  jobRole: string
  yearsExperience: number
  missionsCompleted: number
  commitDays: number
}

interface Props {
  onStart: (candidateId: string) => void
  isLoading: boolean
}

export default function CandidateSelect({ onStart, isLoading }: Props) {
  const [selected, setSelected] = useState('')
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/candidates')
      .then(res => res.json())
      .then(data => {
        setCandidates(data.candidates || [])
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-gray-500">Loading candidates...</div>
      </div>
    )
  }

  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 w-full max-w-lg">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Start Interview</h2>
        <p className="text-sm text-gray-600 mb-6">
          Select a candidate to begin the AI technical interview.
        </p>

        <div className="space-y-2 mb-6 max-h-[400px] overflow-y-auto pr-2">
          {candidates.map(c => (
            <label
              key={c.id}
              className={`flex items-start p-3 border rounded-lg cursor-pointer transition-colors ${
                selected === c.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <input
                type="radio"
                name="candidate"
                value={c.id}
                checked={selected === c.id}
                onChange={(e) => setSelected(e.target.value)}
                className="mt-1 mr-3"
              />
              <div className="flex-1 min-w-0">
                <div className="font-medium text-gray-900">{c.name}</div>
                <div className="text-sm text-gray-500">{c.jobRole} &middot; {c.yearsExperience}y exp</div>
                <div className="text-xs text-gray-400 mt-0.5">
                  {c.missionsCompleted} missions &middot; {c.commitDays} days committed
                </div>
              </div>
            </label>
          ))}
        </div>

        <button
          onClick={() => onStart(selected)}
          disabled={!selected || isLoading}
          className="w-full py-2.5 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? 'Starting...' : 'Begin Interview'}
        </button>
      </div>
    </div>
  )
}
