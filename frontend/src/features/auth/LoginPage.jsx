import { useState } from 'react'
import { api } from '../../api'

export default function LoginPage({ onAuthenticated }) {
  const [registerMode, setRegisterMode] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [status, setStatus] = useState({ busy: false, error: '' })

  const submit = async (event) => {
    event.preventDefault()
    if (status.busy) return
    setStatus({ busy: true, error: '' })
    try {
      const session = registerMode ? await api.register(email, password) : await api.login(email, password)
      onAuthenticated(session)
    } catch (error) {
      setStatus({ busy: false, error: error.message })
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-card panel" aria-labelledby="auth-heading">
        <div className="brand-mark">IESP</div>
        <span className="eyebrow">Intelligent Email Security Platform</span>
        <h1 id="auth-heading">{registerMode ? 'Create your secure workspace' : 'Sign in to your workspace'}</h1>
        <p>Analyze untrusted email content without exposing a browser API key or rendering attacker-controlled HTML.</p>
        <form className="form-stack" onSubmit={submit}>
          <label>Email<input type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} /></label>
          <label>Password<input type="password" autoComplete={registerMode ? 'new-password' : 'current-password'} minLength="10" required value={password} onChange={(event) => setPassword(event.target.value)} /></label>
          {status.error && <div className="error" role="alert">{status.error}</div>}
          <button className="button primary" disabled={status.busy}>{status.busy ? 'Please wait…' : registerMode ? 'Create workspace' : 'Sign in'}</button>
        </form>
        <button className="text-button" type="button" onClick={() => { setRegisterMode((current) => !current); setStatus({ busy: false, error: '' }) }}>{registerMode ? 'Already have an account? Sign in' : 'New here? Create a workspace'}</button>
      </section>
    </main>
  )
}
