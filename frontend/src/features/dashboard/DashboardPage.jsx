import { useEffect, useState } from 'react'
import { api } from '../../api'
import { stateClass } from '../../lib/security'

const emptyStats = { total: 0, phishing: 0, suspicious: 0, non_phishing: 0, review_required: 0, high_risk: 0, high_risk_percentage: 0 }

function StatCard({ label, value, hint, tone }) {
  return <article className={'stat-card ' + (tone || '')}><span>{label}</span><strong>{value}</strong>{hint && <small>{hint}</small>}</article>
}

export default function DashboardPage({ refreshKey, onOpenAnalysis }) {
  const [stats, setStats] = useState(emptyStats)
  const [recent, setRecent] = useState([])
  const [status, setStatus] = useState({ busy: true, error: '' })

  useEffect(() => {
    const controller = new AbortController()
    setStatus({ busy: true, error: '' })
    Promise.all([api.stats(controller.signal), api.recent(8, controller.signal)])
      .then(([nextStats, nextRecent]) => { setStats(nextStats); setRecent(nextRecent.items || []) })
      .catch((error) => { if (error.code !== 'CANCELLED') setStatus({ busy: false, error: error.message }) })
      .finally(() => setStatus((current) => ({ ...current, busy: false })))
    return () => controller.abort()
  }, [refreshKey])

  const total = stats.total || 0
  return (
    <section className="page-stack" aria-labelledby="overview-heading">
      <div className="page-heading"><div><span className="eyebrow">Overview</span><h1 id="overview-heading">Email threat triage</h1><p>Use the configured IESP security pipeline to review email risk, evidence, and model decisions inside this workspace.</p></div><div className="page-heading-meta"><span className="status-dot">Workspace data</span><span className="microcopy">No synthetic metrics are shown.</span></div></div>
      {status.error && <div className="error" role="alert">{status.error}</div>}
      <div className="stats-grid">
        <StatCard label="Total analyzed" value={stats.total} hint="Stored analyses" />
        <StatCard label="Phishing" value={stats.phishing} hint={total ? Math.round(stats.phishing / total * 100) + '% of total' : 'No data'} tone="danger" />
        <StatCard label="Suspicious" value={stats.suspicious} hint="Needs caution" tone="warning" />
        <StatCard label="Review required" value={stats.review_required} hint="Evidence incomplete or conflicting" />
        <StatCard label="Non-phishing" value={stats.non_phishing} hint="No meaningful concern" tone="good" />
        <StatCard label="High risk" value={stats.high_risk_percentage + '%'} hint={stats.high_risk + ' stored analyses at or above threshold'} tone="danger" />
      </div>
      <section className="panel" aria-labelledby="recent-heading">
        <div className="section-title-row"><div><span className="eyebrow">Activity</span><h2 id="recent-heading">Recent analyses</h2></div>{status.busy && <span className="microcopy" role="status">Refreshing…</span>}</div>
        {recent.length ? <div className="table-wrap"><table className="responsive-table"><thead><tr><th>Date</th><th>Sender</th><th>Subject</th><th>Classification</th><th>Risk</th><th>Priority</th></tr></thead><tbody>{recent.map((item) => <tr key={item.request_id + '-' + item.message_id} tabIndex="0" onClick={() => onOpenAnalysis(item.message_id)} onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); onOpenAnalysis(item.message_id) } }}><td data-label="Date">{new Date(item.created_at).toLocaleString()}</td><td data-label="Sender" className="break-value">{item.sender}</td><td data-label="Subject" className="break-value">{item.subject || '—'}</td><td data-label="Classification"><span className={'status-badge compact ' + stateClass(item.classification)}>{item.classification}</span></td><td data-label="Risk">{Math.round(item.risk_score)}</td><td data-label="Priority">{item.priority || '—'}</td></tr>)}</tbody></table></div> : <div className="empty-state"><strong>No analyses yet</strong><span>Run your first email analysis to populate the workspace dashboard.</span></div>}
      </section>
    </section>
  )
}
