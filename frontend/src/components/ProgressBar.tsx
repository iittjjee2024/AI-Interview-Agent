interface Props {
  turn: number
  daysCovered: number
  maxQuestions: number
}

export default function ProgressBar({ turn, daysCovered, maxQuestions }: Props) {
  const progress = Math.min((turn / maxQuestions) * 100, 100)

  return (
    <div className="bg-white rounded-lg border border-gray-200 px-4 py-3 mb-4">
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm text-gray-600">Progress</span>
        <div className="flex gap-4 text-sm text-gray-600">
          <span>Questions: <strong className="text-gray-900">{turn}</strong></span>
          <span>Topics: <strong className="text-gray-900">{daysCovered}</strong></span>
        </div>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-2" role="progressbar" aria-valuenow={turn} aria-valuemax={maxQuestions}>
        <div
          className="bg-blue-600 h-2 rounded-full transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  )
}
