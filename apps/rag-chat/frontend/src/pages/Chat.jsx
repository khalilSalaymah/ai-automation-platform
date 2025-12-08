import React from 'react'
import ChatWidget from '@ui/components/ChatWidget'

export default function Chat() {
  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">RAG Chat</h1>
        <ChatWidget
          wsUrl="ws://localhost:8082/ws"
          restUrl="/api/chat"
        />
      </div>
    </div>
  )
}

