import React, { useState } from 'react'

export default function AiOps() {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState(null)

  const handleAnalyze = async () => {
    const response = await fetch('/api/aiops/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, metrics: {} }),
    })
    const data = await response.json()
    setResult(data)
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">AIOps Bot</h1>
        <div className="bg-white rounded-lg shadow p-6">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your query"
            className="w-full border rounded px-4 py-2 mb-4"
            rows={4}
          />
          <button
            onClick={handleAnalyze}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            Analyze
          </button>
          {result && (
            <div className="mt-4 p-4 bg-gray-50 rounded">
              <h3 className="font-semibold mb-2">Analysis:</h3>
              <p>{result.analysis}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

