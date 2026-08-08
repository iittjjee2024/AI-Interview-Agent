import { useState } from 'react'
import { useInterview } from './hooks/useInterview'
import ChatWindow from './components/ChatWindow'
import CandidateSelect from './components/CandidateSelect'
import FeedbackPanel from './components/FeedbackPanel'
import ProgressBar from './components/ProgressBar'

function App() {
  const interview = useInterview()
  const [started, setStarted] = useState(false)

  const handleStart = async (candidateId: string) => {
    await interview.startInterview(candidateId)
    setStarted(true)
  }

  if (interview.isComplete && interview.feedback) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-4xl mx-auto">
          <FeedbackPanel feedback={interview.feedback} />
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-4xl mx-auto flex justify-between items-center">
          <h1 className="text-xl font-semibold text-gray-900">AI Technical Interview</h1>
          {started && (
            <button
              onClick={interview.endInterview}
              className="text-sm text-red-600 hover:text-red-800 font-medium"
              aria-label="End interview"
            >
              End Interview
            </button>
          )}
        </div>
      </header>

      <main className="flex-1 max-w-4xl mx-auto w-full p-4 flex flex-col">
        {!started ? (
          <CandidateSelect onStart={handleStart} isLoading={interview.isLoading} />
        ) : (
          <>
            <ProgressBar
              turn={interview.turn}
              daysCovered={interview.daysCovered}
              maxQuestions={15}
            />
            <ChatWindow
              messages={interview.messages}
              onSubmit={interview.submitAnswer}
              isLoading={interview.isLoading}
            />
          </>
        )}

        {interview.error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm" role="alert">
            {interview.error}
          </div>
        )}
      </main>
    </div>
  )
}

export default App
