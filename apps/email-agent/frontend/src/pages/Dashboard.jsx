import React, { useState } from 'react'
import ChatWidget from '@ui/components/ChatWidget'

export default function Dashboard() {
  const [emails, setEmails] = useState([])

  const handleProcessEmail = async (emailData) => {
    try {
      const response = await fetch('/api/email/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(emailData),
      })
      const result = await response.json()
      setEmails([...emails, result])
    } catch (error) {
      console.error('Error processing email:', error)
    }
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Email Agent Dashboard</h1>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Email Processing</h2>
            <ChatWidget
              wsUrl="ws://localhost:8081/ws"
              restUrl="/api/email/process"
            />
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Processed Emails</h2>
            <div className="space-y-4">
              {emails.length === 0 ? (
                <p className="text-gray-500">No emails processed yet</p>
              ) : (
                emails.map((email, idx) => (
                  <div key={idx} className="border rounded p-4">
                    <p className="font-semibold">{email.category}</p>
                    <p className="text-sm text-gray-600">{email.response}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

