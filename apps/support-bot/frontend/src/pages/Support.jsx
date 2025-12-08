import React from 'react'
import ChatWidget from '@ui/components/ChatWidget'

export default function Support() {
  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Support Bot</h1>
        <ChatWidget
          wsUrl="ws://localhost:8083/ws"
          restUrl="/api/support/chat"
        />
      </div>
    </div>
  )
}

