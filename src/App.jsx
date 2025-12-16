import React from 'react'

const apps = [
  {
    name: 'RAG Chat',
    description: 'Ask questions over your documents with retrieval-augmented generation.',
    href: '/rag-chat/',
    accent: 'from-primary to-secondary',
  },
  {
    name: 'AIOps Bot',
    description: 'Proactive monitoring and incident assistance for your infrastructure.',
    href: '/aiops-bot/',
    accent: 'from-secondary to-accent',
  },
  {
    name: 'Email Agent',
    description: 'Automate inbox triage, drafting, and follow-ups.',
    href: '/email-agent/',
    accent: 'from-accent to-primary',
  },
  {
    name: 'Scraper Agent',
    description: 'Structured data extraction from websites and APIs.',
    href: '/scraper-agent/',
    accent: 'from-primary to-accent',
  },
  {
    name: 'Support Bot',
    description: 'AI-powered support assistant for your customers.',
    href: '/support-bot/',
    accent: 'from-secondary to-primary',
  },
]

function App() {
  return (
    <div className="min-h-screen bg-bg-dark text-white flex items-center justify-center px-4">
      <div className="max-w-6xl w-full py-12 md:py-20">
        <header className="mb-12 text-center animate-fade-in-up">
          <p className="inline-flex items-center gap-2 rounded-full border border-border-dark bg-surface-dark/60 px-4 py-1 text-xs md:text-sm text-gray-300 shadow-soft-xl backdrop-blur">
            <span className="h-1.5 w-1.5 rounded-full bg-accent animate-pulse" />
            AI Automation Platform
          </p>
          <h1 className="mt-6 text-3xl md:text-5xl font-semibold tracking-tight">
            Orchestrate your <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary">AI agents</span>{' '}
            from one place
          </h1>
          <p className="mt-4 text-gray-300 max-w-2xl mx-auto text-sm md:text-base">
            Jump into any specialized agent experience – from RAG-powered chat to support automation – all sharing the
            same cohesive design system.
          </p>
        </header>

        <main className="grid gap-6 md:gap-8 md:grid-cols-2 lg:grid-cols-3">
          {apps.map((app, index) => (
            <a
              key={app.name}
              href={app.href}
              className="group relative rounded-2xl border border-border-dark bg-surface-dark/80 p-[1px] shadow-soft-xl overflow-hidden"
              style={{ animationDelay: `${index * 60}ms` }}
            >
              <div className="absolute inset-0 bg-gradient-to-br opacity-0 group-hover:opacity-100 transition-opacity duration-300 blur-2xl group-hover:blur-3xl pointer-events-none bg-primary/30" />
              <div className="relative flex h-full flex-col justify-between rounded-2xl bg-gradient-to-br from-surface-dark/90 to-black/80 px-5 py-6 md:px-6 md:py-7 animate-fade-in-up group-hover:animate-float">
                <div>
                  <div
                    className={`inline-flex items-center justify-center rounded-full bg-gradient-to-r ${app.accent} px-3 py-1 text-xs font-medium text-white mb-4`}
                  >
                    {app.name}
                  </div>
                  <h2 className="text-lg md:text-xl font-semibold mb-2">{app.name}</h2>
                  <p className="text-sm text-gray-300">{app.description}</p>
                </div>
                <div className="mt-6 flex items-center justify-between text-xs md:text-sm text-gray-300">
                  <span className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-accent group-hover:bg-primary transition-colors" />
                    Open app
                  </span>
                  <span className="inline-flex items-center gap-1 text-primary group-hover:text-accent transition-colors">
                    Launch
                    <span aria-hidden="true" className="translate-y-[1px] group-hover:translate-x-0.5 transition-transform">
                      →
                    </span>
                  </span>
                </div>
              </div>
            </a>
          ))}
        </main>
      </div>
    </div>
  )
}

export default App


