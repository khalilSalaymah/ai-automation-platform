import React, { useState, useEffect, useRef } from 'react'
import { useAuth } from '@ui/components'

// Use relative URL to leverage Vite proxy, or absolute URL if specified
const API_URL = import.meta.env.VITE_API_URL || ''

export default function Chat() {
  const { token } = useAuth()
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId] = useState(() => `session-${Date.now()}`)
  const [documents, setDocuments] = useState([])
  const [showDocuments, setShowDocuments] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [theme, setTheme] = useState(() => {
    if (typeof window === 'undefined') return 'light'
    return localStorage.getItem('rag-theme') || 'light'
  })

  const messagesEndRef = useRef(null)
  const fileInputRef = useRef(null)

  // Sync theme with document
  useEffect(() => {
    if (typeof window === 'undefined') return
    const root = document.documentElement
    if (theme === 'dark') {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
    localStorage.setItem('rag-theme', theme)
  }, [theme])

  useEffect(() => {
    loadDocuments()
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))
  }

  const loadDocuments = async () => {
    try {
      const response = await fetch(`${API_URL || ''}/api/documents`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      if (response.ok) {
        const data = await response.json()
        setDocuments(data)
      }
    } catch (error) {
      console.error('Error loading documents:', error)
    }
  }

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setLoading(true)

    // Add user message to chat
    const newUserMessage = {
      id: Date.now(),
      text: userMessage,
      role: 'user',
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, newUserMessage])

    try {
      const response = await fetch(`${API_URL || ''}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: userMessage,
          session_id: sessionId,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to get response')
      }

      const data = await response.json()

      // Add bot response with sources
      const botMessage = {
        id: Date.now() + 1,
        text: data.response,
        role: 'assistant',
        sources: data.sources || [],
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, botMessage])
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Sorry, I encountered an error. Please try again.',
        role: 'assistant',
        error: true,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(`${API_URL || ''}/api/documents/upload`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      })

      if (response.ok) {
        const data = await response.json()
        await loadDocuments()
        // Show success message
        const successMessage = {
          id: Date.now(),
          text: `Document "${data.filename}" uploaded successfully!`,
          role: 'system',
          timestamp: new Date(),
        }
        setMessages((prev) => [...prev, successMessage])
      } else {
        throw new Error('Upload failed')
      }
    } catch (error) {
      console.error('Error uploading file:', error)
      const errorMessage = {
        id: Date.now(),
        text: 'Failed to upload document. Please try again.',
        role: 'system',
        error: true,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleKeyPress = (e) => {
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
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </span>
              RAG Chat
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
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" />
                </svg>
              )}
            </button>

            <button
              onClick={() => setShowDocuments(!showDocuments)}
              className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                showDocuments
                  ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                  : 'bg-slate-100 dark:bg-surface-dark text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-black border border-slate-200 dark:border-border-dark'
              }`}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span className="hidden sm:inline font-medium">Documents</span>
              {documents.length > 0 && (
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-white/20 dark:bg-black/30">
                  {documents.length}
                </span>
              )}
            </button>

            <label className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors cursor-pointer">
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                onChange={handleFileUpload}
                accept=".pdf,.txt,.doc,.docx,.md"
                disabled={uploading}
              />
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <span className="text-sm font-medium">
                {uploading ? 'Uploading...' : 'Upload'}
              </span>
            </label>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Documents Sidebar */}
        {showDocuments && (
          <div className="w-80 bg-white dark:bg-surface-dark border-r border-slate-200 dark:border-border-dark flex flex-col flex-shrink-0">
            <div className="px-4 py-4 border-b border-slate-200 dark:border-border-dark">
              <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-50 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                Your Documents
              </h2>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              {documents.length === 0 ? (
                <div className="text-center text-slate-500 dark:text-slate-400 py-12">
                  <svg
                    className="w-16 h-16 mx-auto mb-4 text-slate-300 dark:text-slate-700"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                  <p className="font-medium">No documents yet</p>
                  <p className="text-sm mt-2">Upload a document to get started.</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {documents.map((doc) => (
                    <div
                      key={doc.id}
                      className="p-3 bg-slate-50 dark:bg-black/50 rounded-lg border border-slate-200 dark:border-border-dark hover:bg-slate-100 dark:hover:bg-black transition-colors cursor-pointer"
                    >
                      <div className="flex items-start gap-3">
                        <svg
                          className="w-5 h-5 text-indigo-600 dark:text-indigo-400 mt-0.5 flex-shrink-0"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                          />
                        </svg>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-slate-900 dark:text-slate-50 truncate">
                            {doc.filename}
                          </p>
                          <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">
                            Indexed {new Date(doc.indexed_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

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
                      d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                    />
                  </svg>
                </div>
                <p className="text-xl font-semibold text-slate-900 dark:text-slate-100">Start a conversation</p>
                <p className="text-sm mt-2 text-slate-600 dark:text-slate-400">Ask questions about your documents.</p>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[75%] rounded-2xl px-5 py-4 text-sm ${
                      message.role === 'user'
                        ? 'bg-indigo-600 text-white shadow-lg'
                        : message.error
                        ? 'bg-red-50 text-red-900 border border-red-200 dark:bg-red-950/30 dark:text-red-300 dark:border-red-900'
                        : message.role === 'system'
                        ? 'bg-amber-50 text-amber-900 border border-amber-200 dark:bg-amber-950/30 dark:text-amber-200 dark:border-amber-900'
                        : 'bg-slate-100 text-slate-900 border border-slate-200 dark:bg-surface-dark dark:text-slate-100 dark:border-border-dark shadow-sm'
                    }`}
                  >
                    <p className="whitespace-pre-wrap break-words leading-relaxed">{message.text}</p>
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-white/20 dark:border-border-dark">
                        <p className="text-xs font-semibold mb-2 text-slate-600 dark:text-slate-400">
                          Sources:
                        </p>
                        <ul className="space-y-1">
                          {message.sources.map((source, idx) => (
                            <li key={idx} className="text-xs text-slate-600 dark:text-slate-400">
                              • {source}
                            </li>
                          ))}
                        </ul>
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
                  onKeyDown={handleKeyPress}
                  placeholder="Type your question here... (Enter to send, Shift+Enter = new line)"
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
    </div>
  )
}
