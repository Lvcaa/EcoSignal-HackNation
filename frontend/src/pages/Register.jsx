import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useRegister } from '../hooks/useAuth'

export default function Register() {
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const register = useRegister()

  const handleSubmit = (e) => {
    e.preventDefault()
    register.mutate({ email, password, display_name: displayName })
  }

  return (
    <div className="min-h-screen bg-surface max-w-md mx-auto flex flex-col relative overflow-hidden">
      <div className="absolute -top-20 -left-20 w-60 h-60 bg-primary-fixed/20 rounded-full blur-3xl" />

      <header className="px-5 py-4">
        <span className="text-primary font-extrabold text-lg italic">Green Buddy</span>
      </header>

      <div className="flex-1 flex flex-col justify-center px-6">
        <h1 className="text-3xl font-black text-on-surface mb-2">Create account</h1>
        <p className="text-on-surface/50 text-sm mb-8">Start tracking your environmental impact</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-on-surface/60 uppercase tracking-wider">Name</label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="w-full mt-1.5 px-4 py-3 rounded-2xl bg-surface-container-lowest border border-outline-variant/40 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all text-sm"
              placeholder="Your name"
              required
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-on-surface/60 uppercase tracking-wider">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full mt-1.5 px-4 py-3 rounded-2xl bg-surface-container-lowest border border-outline-variant/40 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all text-sm"
              placeholder="you@example.com"
              required
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-on-surface/60 uppercase tracking-wider">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full mt-1.5 px-4 py-3 rounded-2xl bg-surface-container-lowest border border-outline-variant/40 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all text-sm"
              placeholder="Min. 8 characters"
              required
              minLength={8}
            />
          </div>

          {register.error && (
            <p className="text-red-500 text-xs">
              {register.error.response?.data?.detail || 'Registration failed. Try again.'}
            </p>
          )}

          <button
            type="submit"
            disabled={register.isPending}
            className="w-full bg-primary text-on-primary font-bold py-3.5 rounded-2xl active:scale-95 transition-all ease-out-expo disabled:opacity-50"
          >
            {register.isPending ? 'Creating...' : 'Create Account'}
          </button>
        </form>

        <p className="text-center text-sm text-on-surface/50 mt-6">
          Already have an account?{' '}
          <Link to="/login" className="text-primary font-semibold">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
