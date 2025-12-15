import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import ThemeToggle from './ThemeToggle'

export const ForgotPassword = () => {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)
  const { forgotPassword } = useAuth()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess(false)
    setLoading(true)

    const result = await forgotPassword(email)
    if (result.success) {
      setSuccess(true)
    } else {
      setError(result.error)
    }
    setLoading(false)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-bg-dark dark:via-slate-950 dark:to-bg-dark flex items-center justify-center px-4 py-12">
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>
      <div className="relative max-w-md w-full">
        <div className="bg-white/90 dark:bg-slate-900/90 backdrop-blur rounded-2xl shadow-soft-xl border border-slate-100 dark:border-slate-800 p-8 space-y-6">
          <div className="space-y-2 text-center">
            <h2 className="mt-2 text-3xl font-extrabold text-slate-900 dark:text-slate-50">
              Reset your password
            </h2>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
              Enter your email and we'll send you a link to reset your password.
            </p>
          </div>
          <form className="mt-4 space-y-6" onSubmit={handleSubmit}>
            {error && (
              <div className="rounded-md bg-red-50 dark:bg-red-900/30 p-4 border border-red-200 dark:border-red-700">
                <div className="text-sm text-red-800 dark:text-red-100">{error}</div>
              </div>
            )}
            {success && (
              <div className="rounded-md bg-emerald-50 dark:bg-emerald-900/30 p-4 border border-emerald-200 dark:border-emerald-700">
                <div className="text-sm text-emerald-800 dark:text-emerald-100">
                  If an account exists with that email, a password reset link has been sent.
                </div>
              </div>
            )}
            <div>
              <label htmlFor="email" className="sr-only">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                className="appearance-none relative block w-full px-3 py-2 border border-slate-300 dark:border-slate-700 placeholder-slate-500 text-slate-900 dark:text-slate-100 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm bg-white dark:bg-slate-900"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="group relative w-full flex justify-center py-2.5 px-4 border border-transparent text-sm font-medium rounded-xl text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 shadow-md shadow-blue-500/30"
              >
                {loading ? 'Sending...' : 'Send reset link'}
              </button>
            </div>

            <div className="text-center text-sm">
              <Link
                to="/login"
                className="font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400 dark:hover:text-blue-300"
              >
                Back to sign in
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}