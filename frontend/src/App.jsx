import { useEffect, useMemo, useState } from 'react'
import { analyzeEmail, fetchRecent, fetchStats, getApiBaseUrl, getStoredApiKey, setStoredApiKey } from './api'
import { isPriorityEligible, securityDescription } from './lib/security'

const emptyStats = { total: 0, phishing: 0, suspicious: 0, non_phishing: 0, review_required: 0 }
const starter = { message_id: 'demo-message', sender: 'security@example.com', recipients: ['analyst@example.com'], subject: 'Example email for analysis', text_body: 'Please review this message and respond today.', html_body: '', headers: {}, attachments: [] }

function StatCard({ label, value }) {
  return <div className="stat-card"><span>{label}</span><strong>{value}</strong></div>
}

function ResultPanel({ result }) {
  if (!result) return <section className="panel empty"><h2>Analysis result</h2><p>Submit an email to see security findings.</p></section>
  const c = result.security.classification
  return <section className="panel">
    <div className="panel-heading"><div><span className="eyebrow">Security decision</span><h2>{c}</h2></div><span className={`badge ${c.replaceAll(' ', '-').toLowerCase()}`}>{c}</span></div>
    <p className="summary">{securityDescription(c)}</p>
    <div className="result-grid">
      <div><span className="label">Message ID</span><code>{result.message_id}</code></div>
      <div><span className="label">Request ID</span><code>{result.request_id}</code></div>
      <div><span className="label">Phishing model</span><span>{result.model_info?.phishing || 'unavailable'}</span></div>
      <div><span className="label">Priority eligibility</span><span>{isPriorityEligible(result) ? 'Eligible' : 'Suppressed'}</span></div>
    </div>
    <h3>Security findings</h3>
    {result.security.reasons?.length ? <div className="findings">{result.security.reasons.map((r, i) => <article className="finding" key={`${r.code}-${i}`}><div className="finding-top"><strong>{r.code}</strong><span>{r.severity}</span></div><p>{r.message}</p></article>)}</div> : <p className="muted">No additional deterministic findings.</p>}
    <div className="priority-box"><span className="eyebrow">Priority</span><strong>{result.priority?.label || 'SUPPRESSED'}</strong><p>{result.priority ? (result.priority.proxy_label ? 'Transparent project/proxy urgency label.' : 'Priority model result.') : 'Ordinary priority is blocked unless security classification is NON-PHISHING.'}</p></div>
  </section>
}

export default function App() {
  const [form, setForm] = useState(starter)
  const [apiKey, setApiKey] = useState(getStoredApiKey())
  const [stats, setStats] = useState(emptyStats)
  const [recent, setRecent] = useState([])
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function refreshDashboard() {
    if (!apiKey) return
    try {
      const [s, r] = await Promise.all([fetchStats(), fetchRecent(10)])
      setStats(s)
      setRecent(r.items || [])
    } catch (e) {
      setError(e.message)
    }
  }

  useEffect(() => { refreshDashboard() }, [apiKey])

  const recipients = useMemo(() => form.recipients.join(', '), [form.recipients])
  const update = (name, value) => setForm((current) => ({ ...current, [name]: value }))

  async function submit(event) {
    event.preventDefault()
    setError('')
    if (!apiKey) { setError('Enter the API key used by the backend.'); return }
    setStoredApiKey(apiKey)
    setBusy(true)
    try {
      const payload = { ...form, recipients: recipients.split(',').map(x => x.trim()).filter(Boolean) }
      const data = await analyzeEmail(payload)
      setResult(data)
      await refreshDashboard()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  return <div className="shell">
    <header className="topbar"><div><strong>IESP</strong><span className="brand-sub">Intelligent Email Security & Prioritization</span></div><span className="connection">{getApiBaseUrl()}</span></header>
    <main className="layout">
      <aside className="sidebar">
        <div className="side-block"><span className="eyebrow">Security first</span><p>Security classification always runs before ordinary priority.</p></div>
        <div className="side-block"><span className="eyebrow">API key</span><input value={apiKey} onChange={e => setApiKey(e.target.value)} placeholder="X-API-Key" type="password" autoComplete="off" /></div>
        <button className="secondary" onClick={refreshDashboard}>Refresh dashboard</button>
        <div className="side-note"><strong>Mailbox mode</strong><p>Analyze only. Provider adapters do not mutate mailbox state.</p></div>
      </aside>
      <div className="content">
        <section className="hero"><span className="eyebrow">Security operations</span><h1>Email threat triage</h1><p>Analyze untrusted email data, explain the security decision, and assign priority only when policy allows.</p></section>
        <section className="stats">
          <StatCard label="Total analyzed" value={stats.total} /><StatCard label="Phishing" value={stats.phishing} /><StatCard label="Suspicious" value={stats.suspicious} /><StatCard label="Review required" value={stats.review_required} />
        </section>
        <div className="work-grid">
          <form className="panel" onSubmit={submit}>
            <div className="panel-heading"><div><span className="eyebrow">Manual analysis</span><h2>Inspect an email</h2></div></div>
            <div className="form-grid">
              <label>Message ID<input value={form.message_id} onChange={e => update('message_id', e.target.value)} /></label>
              <label>Sender<input value={form.sender} onChange={e => update('sender', e.target.value)} /></label>
              <label className="wide">Recipients<input value={recipients} onChange={e => update('recipients', e.target.value.split(',').map(x => x.trim()))} /></label>
              <label className="wide">Subject<input value={form.subject} onChange={e => update('subject', e.target.value)} /></label>
              <label className="wide">Plain-text body<textarea rows="10" value={form.text_body} onChange={e => update('text_body', e.target.value)} /></label>
              <label className="wide">HTML body (structural analysis only)<textarea rows="7" value={form.html_body} onChange={e => update('html_body', e.target.value)} /></label>
            </div>
            {error && <div className="error">{error}</div>}
            <button className="primary" disabled={busy}>{busy ? 'Analyzing…' : 'Analyze email'}</button>
          </form>
          <ResultPanel result={result} />
        </div>
        <section className="panel"><div className="panel-heading"><div><span className="eyebrow">Audit trail</span><h2>Recent analyses</h2></div></div>
          {recent.length === 0 ? <p className="muted">No stored analysis metadata yet.</p> : <div className="table-wrap"><table><thead><tr><th>Message</th><th>Security</th><th>Priority</th><th>Created</th></tr></thead><tbody>{recent.map(item => <tr key={`${item.request_id}-${item.message_id}`}><td>{item.message_id}</td><td>{item.classification}</td><td>{item.priority || '—'}</td><td>{new Date(item.created_at).toLocaleString()}</td></tr>)}</tbody></table></div>}
        </section>
      </div>
    </main>
  </div>
}
