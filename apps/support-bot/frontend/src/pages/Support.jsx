import React, { useState, useEffect, useRef } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8083'
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8083/api/ws'

export default function Support() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sessionId] = useState(() => crypto.randomUUID())
  const [loading, setLoading] = useState(false)
  const [connecting, setConnecting] = useState(false)
  const [ws, setWs] = useState(null)
  const [theme, setTheme] = useState(() => {
    if (typeof window === 'undefined') return 'light'
    return localStorage.getItem('support-theme') || 'light'
  })

  const messagesEndRef = useRef(null)

  // Sync theme with document
  useEffect(() => {
    if (typeof window === 'undefined') return
    const root = document.documentElement
    if (theme === 'dark') {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
    localStorage.setItem('support-theme', theme)
  }, [theme])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef?.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))
  }

  const appendMessage = (msg) => {
    setMessages((prev) => [...prev, { ...msg, id: Date.now(), timestamp: new Date() }])
  }

  const connectWebSocket = () => {
    if (ws || connecting) return
    setConnecting(true)
    const socket = new WebSocket(WS_URL)
    socket.onopen = () => {
      setConnecting(false)
      setWs(socket)
    }
    socket.onclose = () => {
      setWs(null)
    }
    socket.onerror = () => {
      setConnecting(false)
      setWs(null)
    }
    socket.onmessage = (evt) => {
      const data = JSON.parse(evt.data)
      appendMessage({
        role: 'assistant',
        text: data.response || data.message,
        intent: data.intent,
        confidence: data.confidence,
        escalated: data.escalated,
        ticketId: data.ticket_id,
        sources: data.sources || [],
      })
    }
  }

  const sendMessage = async () => {
    const trimmed = input.trim()
    if (!trimmed || loading) return

    appendMessage({ role: 'user', text: trimmed })
    setInput('')
    setLoading(true)

    const payload = {
      message: trimmed,
      session_id: sessionId,
    }

    try {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(payload))
        setLoading(false)
      } else {
        const res = await fetch(`${API_URL}/api/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
        const data = await res.json()
        appendMessage({
          role: 'assistant',
          text: data.response || data.message,
          intent: data.intent,
          confidence: data.confidence,
          escalated: data.escalated,
          ticketId: data.ticket_id,
          sources: data.sources || [],
        })
        setLoading(false)
      }
    } catch (err) {
      console.error('Support chat error', err)
      appendMessage({
        role: 'assistant',
        text: 'There was an error contacting the support service. Please try again later.',
        error: true,
      })
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="h-screen w-screen bg-white dark:bg-bg-dark flex flex-col overflow-hidden">
      {/* Header */}
      <div className="bg-white dark:bg-surface-dark border-b border-slate-200 dark:border-border-dark px-6 py-4 flex-shrink-0">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-50 flex items-center gap-3">
              <span className="inline-flex items-center justify-center w-10 h-10 rounded-lg bg-indigo-600 dark:bg-indigo-500 text-white">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z"
                  />
                </svg>
              </span>
              Support Bot
            </h1>
            <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900 text-xs font-medium text-emerald-700 dark:text-emerald-400">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>Online</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Theme toggle */}
            <button
              onClick={toggleTheme}
              className="inline-flex items-center justify-center w-10 h-10 rounded-lg border border-slate-200 dark:border-border-dark bg-white dark:bg-surface-dark text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-black transition-colors"
              aria-label="Toggle dark mode"
            >
              {theme === 'dark' ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
                  />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"
                  />
                </svg>
              )}
            </button>

            {/* WebSocket toggle */}
            <button
              onClick={connectWebSocket}
              disabled={!!ws || connecting}
              className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                ws
                  ? 'bg-emerald-600 text-white hover:bg-emerald-700'
                  : 'bg-slate-100 dark:bg-surface-dark text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-black border border-slate-200 dark:border-border-dark disabled:opacity-50'
              }`}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01M15 9a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
              <span className="hidden sm:inline font-medium">
                {ws ? 'Live' : connecting ? 'Connecting...' : 'Enable Live'}
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col bg-white dark:bg-bg-dark overflow-hidden">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-slate-500 dark:text-slate-400">
              <div className="w-20 h-20 rounded-full bg-indigo-100 dark:bg-indigo-950/30 flex items-center justify-center mb-6">
                <svg
                  className="w-10 h-10 text-indigo-600 dark:text-indigo-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z"
                  />
                </svg>
              </div>
              <p className="text-xl font-semibold text-slate-900 dark:text-slate-100">Start a conversation</p>
              <p className="text-sm mt-2 text-slate-600 dark:text-slate-400">
                Ask questions about billing, technical issues, or general support.
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[75%] rounded-2xl px-5 py-4 text-sm ${
                    message.role === 'user'
                      ? 'bg-indigo-600 text-white shadow-lg'
                      : message.error
                      ? 'bg-red-50 text-red-900 border border-red-200 dark:bg-red-950/30 dark:text-red-300 dark:border-red-900'
                      : 'bg-slate-100 text-slate-900 border border-slate-200 dark:bg-surface-dark dark:text-slate-100 dark:border-border-dark shadow-sm'
                  }`}
                >
                  <p className="whitespace-pre-wrap break-words leading-relaxed">{message.text}</p>
                  {message.role === 'assistant' && (
                    <div className="mt-3 pt-3 border-t border-slate-200 dark:border-border-dark flex flex-wrap items-center gap-2">
                      {message.intent && (
                        <span className="inline-flex items-center rounded-full bg-slate-200 dark:bg-black/50 px-2 py-0.5 text-xs font-medium text-slate-700 dark:text-slate-300">
                          {message.intent}
                        </span>
                      )}
                      {typeof message.confidence === 'number' && (
                        <span className="inline-flex items-center rounded-full bg-emerald-100 dark:bg-emerald-950/30 px-2 py-0.5 text-xs font-medium text-emerald-700 dark:text-emerald-400">
                          {(message.confidence * 100).toFixed(0)}% confident
                        </span>
                      )}
                      {message.escalated && (
                        <span className="inline-flex items-center rounded-full bg-red-100 dark:bg-red-950/30 px-2 py-0.5 text-xs font-medium text-red-700 dark:text-red-400">
                          Escalated to human
                        </span>
                      )}
                    </div>
                  )}
                  {message.role === 'assistant' && message.sources && message.sources.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-slate-200 dark:border-border-dark">
                      <p className="text-xs font-semibold mb-2 text-slate-600 dark:text-slate-400">Sources:</p>
                      <ul className="space-y-1">
                        {message.sources.map((source, idx) => (
                          <li key={idx} className="text-xs text-slate-600 dark:text-slate-400">
                            • {source}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {message.role === 'assistant' && message.ticketId && (
                    <div className="mt-3 pt-3 border-t border-red-200 dark:border-red-900">
                      <p className="text-xs font-semibold text-red-700 dark:text-red-400">
                        Ticket ID: <span className="font-mono">{message.ticketId}</span>
                      </p>
                    </div>
                  )}
                  <p className="text-[10px] mt-3 opacity-60 text-right">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))
          )}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-slate-100 dark:bg-surface-dark rounded-2xl px-5 py-4 border border-slate-200 dark:border-border-dark">
                <div className="flex space-x-2">
                  <div className="w-2 h-2 bg-slate-400 dark:bg-slate-500 rounded-full animate-bounce"></div>
                  <div
                    className="w-2 h-2 bg-slate-400 dark:bg-slate-500 rounded-full animate-bounce"
                    style={{ animationDelay: '0.2s' }}
                  ></div>
                  <div
                    className="w-2 h-2 bg-slate-400 dark:bg-slate-500 rounded-full animate-bounce"
                    style={{ animationDelay: '0.4s' }}
                  ></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-slate-200 dark:border-border-dark px-6 py-4 bg-white dark:bg-bg-dark flex-shrink-0">
          <div className="max-w-4xl mx-auto flex gap-3 items-end">
            <div className="flex-1 relative">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your message here... (Enter to send, Shift+Enter = new line)"
                className="w-full resize-none border border-slate-300 dark:border-border-dark rounded-xl px-4 py-3 bg-white dark:bg-surface-dark text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm placeholder-slate-400 dark:placeholder-slate-600"
                rows={2}
                disabled={loading}
              />
            </div>
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="px-6 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:bg-slate-400 disabled:cursor-not-allowed transition-colors flex items-center gap-2 shadow-lg shadow-indigo-500/20 font-medium"
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  <span>Sending...</span>
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                    />
                  </svg>
                  <span>Send</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
