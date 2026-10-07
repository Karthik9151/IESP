import { useState } from 'react'
import { api } from '../../api'

export default function LoginPage({ onAuthenticated }) {
  const [registerMode, setRegisterMode] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [status, setStatus] = useState({ busy: false, error: '' })

  const submit = async (event) => {
    event.preventDefault()
    if (status.busy) return
    if (registerMode && password.length < 10) {
      setStatus({ busy: false, error: 'Use at least 10 characters for your password.' })
      return
    }
    setStatus({ busy: true, error: '' })
    try {
      const session = registerMode ? await api.register(email, password) : await api.login(email, password)
      onAuthenticated(session)
    } catch (error) {
      setStatus({ busy: false, error: error.message })
    }
  }

  const pipeline = ['Mail source', 'Safe parser', 'Threat analysis', 'Clear decision']

  return (
    <main className="auth-shell">
      <section className="auth-split">
        <div className="auth-story">
          <div className="story-top"><div className="brand-mark auth-mark"><svg viewBox="0 0 48 48"><path d="M24 3 39 9v11c0 10.5-6.2 19.7-15 24-8.8-4.3-15-13.5-15-24V9l15-6Z" fill="none" stroke="currentColor" strokeWidth="2.2"/><path d="m16 22 5 5 11-12" fill="none" stroke="currentColor" strokeWidth="2.8" strokeLinecap="round" strokeLinejoin="round"/></svg><span>IESP</span></div><span className="security-stamp">SECURITY-FIRST</span></div>
          <span className="eyebrow">Cyber Defence Command Centre</span>
          <h1>Stop phishing before it reaches your inbox.</h1>
          <p className="auth-lede">IESP combines transparent security rules with phishing ML evidence so you can understand a decision, not just receive a label.</p>
          <div className="benefit-list">
            <div><span>01</span><strong>Safe parsing</strong><p>Email content stays inert.</p></div>
            <div><span>02</span><strong>Transparent scoring</strong><p>Risk reasons remain visible.</p></div>
            <div><span>03</span><strong>Read-only mailbox access</strong><p>Provider tokens stay server-side.</p></div>
          </div>
          <div className="pipeline-card" aria-label="IESP analysis pipeline">
            <div className="pipeline-line"/>
            {pipeline.map((item, index) => <div className="pipeline-node" key={item}><span>{index + 1}</span><small>{item}</small></div>)}
          </div>
          <p className="auth-footnote">Sessions use secure HTTP-only cookies. Email content is never executed.</p>
        </div>

        <div className="auth-form-side">
          <div className="auth-card panel">
            <div className="auth-tabs" role="tablist" aria-label="Authentication">
              <button role="tab" aria-selected={!registerMode} className={!registerMode ? 'active' : ''} onClick={() => { setRegisterMode(false); setStatus({ busy: false, error: '' }) }}>Sign in</button>
              <button role="tab" aria-selected={registerMode} className={registerMode ? 'active' : ''} onClick={() => { setRegisterMode(true); setStatus({ busy: false, error: '' }) }}>Register</button>
            </div>
            <span className="eyebrow">{registerMode ? 'New protected workspace' : 'Returning analyst'}</span>
            <h2>{registerMode ? 'Create your secure workspace' : 'Welcome back'}</h2>
            <p className="auth-form-copy">{registerMode ? 'Set up an account to start analysing email safely.' : 'Sign in to continue to your threat overview.'}</p>
            <form className="form-stack" onSubmit={submit}>
              <label>Email address<input className="input-mono" type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} /></label>
              <label>Password
                <span className="password-wrap"><input type={showPassword ? 'text' : 'password'} autoComplete={registerMode ? 'new-password' : 'current-password'} minLength="10" required value={password} onChange={(event) => setPassword(event.target.value)} /><button className="password-toggle" type="button" onClick={() => setShowPassword((v) => !v)}>{showPassword ? 'Hide' : 'Show'}</button></span>
              </label>
              {registerMode && <div className="password-rule" role="note"><span>✓</span> At least 10 characters</div>}
              {status.error && <div className="error" role="alert">{status.error}</div>}
              <button className="button primary full-width" disabled={status.busy}>{status.busy ? 'Securing session…' : registerMode ? 'Create workspace' : 'Sign in securely'}</button>
            </form>
            <p className="auth-switch">{registerMode ? 'Already have an account?' : 'New to IESP?'} <button type="button" onClick={() => setRegisterMode((v) => !v)}>{registerMode ? 'Sign in' : 'Create workspace'}</button></p>
          </div>
          <div className="auth-trust-row"><span>▣ HTTPS-ready</span><span>◌ HTTP-only session</span><span>⌁ No browser API key</span></div>
        </div>
      </section>
    </main>
  )
}
