import React, { useState } from 'react'

export default function Scraper() {
  const [url, setUrl] = useState('')
  const [result, setResult] = useState(null)

  const handleScrape = async () => {
    const response = await fetch('/api/scraper/scrape', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    })
    const data = await response.json()
    setResult(data)
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Web Scraper</h1>
        <div className="bg-white rounded-lg shadow p-6">
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Enter URL to scrape"
            className="w-full border rounded px-4 py-2 mb-4"
          />
          <button
            onClick={handleScrape}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            Scrape
          </button>
          {result && (
            <div className="mt-4 p-4 bg-gray-50 rounded">
              <pre className="whitespace-pre-wrap">{JSON.stringify(result, null, 2)}</pre>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

