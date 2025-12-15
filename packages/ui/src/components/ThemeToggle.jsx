import { useEffect, useState } from 'react'

/**
 * Simple theme toggle that syncs a `dark` class on <html>
 * and persists preference in localStorage.
 *
 * Shared across apps so login/register and in-app views stay consistent.
 */
export default function ThemeToggle({ className = '' }) {
  const [theme, setTheme] = useState(() => {
    if (typeof window === 'undefined') return 'light'
    return localStorage.getItem('rag-theme') || 'light'
  })

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

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))
  }

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={
        'inline-flex items-center gap-2 px-3 py-2 rounded-full border border-slate-200 dark:border-slate-700 ' +
        'bg-white/80 dark:bg-slate-900/80 text-slate-700 dark:text-slate-200 ' +
        'hover:border-indigo-400 dark:hover:border-indigo-400 transition-colors shadow-sm ' +
        className
      }
      aria-label="Toggle dark mode"
    >
      {theme === 'dark' ? (
        <>
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
            />
          </svg>
          <span className="text-xs font-medium">Light</span>
        </>
      ) : (
        <>
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"
            />
          </svg>
          <span className="text-xs font-medium">Dark</span>
        </>
      )}
    </button>
  )
}

