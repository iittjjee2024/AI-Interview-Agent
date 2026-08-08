import { useState } from 'react'

const CANDIDATES = [
  { id: 'candidate_001', name: 'Alex Chen', description: 'Strong RAG, weak deployment' },
  { id: 'candidate_002', name: 'Sarah Johnson', description: 'Strong across all areas' },
  { id: 'candidate_003', name: 'Mike Davis', description: 'Beginner, completed basics only' },
]

interface Props {
  onStart: (candidateId: string) => void
  isLoading: boolean
}

export default function CandidateSelect({ onStart, isLoading }: Props) {
  const [selected, setSelected] = useState('')

  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 w-full max-w-md">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Start Interview</h2>
        <p className="text-sm text-gray-600 mb-6">
          Select a candidate to begin the AI technical interview.
        </p>

        <div className="space-y-3 mb-6">
          {CANDIDATES.map(c => (
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
                className="mt-0.5 mr-3"
              />
              <div>
                <div className="font-medium text-gray-900">{c.name}</div>
                <div className="text-sm text-gray-500">{c.description}</div>
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
