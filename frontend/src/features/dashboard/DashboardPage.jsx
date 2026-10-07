import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api'
import { stateClass, verdictMeta } from '../../lib/security'

const emptyStats = { total: 0, phishing: 0, suspicious: 0, non_phishing: 0, review_required: 0, high_risk: 0, high_risk_percentage: 0 }

function StatCard({ label, value, hint, tone, icon }) {
  return <article className={'kpi-card ' + (tone || '')}><div className="kpi-top"><span>{label}</span><span className="kpi-icon" aria-hidden="true">{icon}</span></div><strong>{value}</strong><small>{hint}</small></article>
}

function Donut({ stats }) {
  const total = Math.max(1, stats.total)
  const ph = stats.phishing / total * 100
  const su = stats.suspicious / total * 100
  const rr = stats.review_required / total * 100
  const stop1 = ph
  const stop2 = stop1 + su
  const stop3 = stop2 + rr
  const background = `conic-gradient(#EF4444 0 ${stop1}%, #F59E0B ${stop1}% ${stop2}%, #8B5CF6 ${stop2}% ${stop3}%, #10B981 ${stop3}% 100%)`
  return <div className="donut-wrap"><div className="donut" style={{ background }} role="img" aria-label="Verdict distribution donut chart"><div><strong>{stats.total}</strong><span>analysed</span></div></div></div>
}

function ActivityChart({ items }) {
  const buckets = useMemo(() => {
    const map = new Map()
    items.forEach((item) => {
      const date = new Date(item.created_at)
      const key = date.toLocaleDateString()
      map.set(key, (map.get(key) || 0) + 1)
    })
    return Array.from(map.entries()).slice(-7)
  }, [items])
  if (!buckets.length) return <div className="chart-empty">No recent activity to plot yet.</div>
  const max = Math.max(...buckets.map(([, value]) => value), 1)
  const width = 560
  const height = 190
  const points = buckets.map(([, value], index) => {
    const x = buckets.length === 1 ? width / 2 : 20 + index * (width - 40) / (buckets.length - 1)
    const y = height - 28 - value / max * (height - 58)
    return [x, y]
  })
  const path = points.map(([x,y], index) => (index ? 'L' : 'M') + ' ' + x + ' ' + y).join(' ')
  return <div className="activity-chart"><svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Recent analyses by recorded date"><path d={path} fill="none" stroke="currentColor" strokeWidth="2.5"/>{points.map(([x,y], i) => <circle key={i} cx={x} cy={y} r="4" fill="currentColor"/>) }<line x1="20" x2="540" y1="162" y2="162" stroke="currentColor" opacity=".12"/>{buckets.map(([label],i) => { const x = buckets.length === 1 ? width/2 : 20 + i*(width-40)/(buckets.length-1); return <text key={label} x={x} y="180" textAnchor="middle" fontSize="10" fill="currentColor" opacity=".6">{label.slice(0,5)}</text> })}</svg></div>
}

export default function DashboardPage({ refreshKey, onOpenAnalysis, onAnalyze }) {
  const [stats, setStats] = useState(emptyStats)
  const [recent, setRecent] = useState([])
  const [status, setStatus] = useState({ busy: true, error: '' })

  useEffect(() => {
    const controller = new AbortController()
    setStatus({ busy: true, error: '' })
    Promise.all([api.stats(controller.signal), api.recent(20, controller.signal)])
      .then(([nextStats, nextRecent]) => { setStats(nextStats); setRecent(nextRecent.items || []) })
      .catch((error) => { if (error.code !== 'CANCELLED') setStatus({ busy: false, error: error.message }) })
      .finally(() => setStatus((current) => ({ ...current, busy: false })))
    return () => controller.abort()
  }, [refreshKey])

  const queue = recent.filter((item) => item.classification !== 'NON-PHISHING').slice(0, 4)

  return (
    <section className="page-stack" aria-labelledby="overview-heading">
      <div className="page-heading dashboard-heading"><div><span className="eyebrow">Threat overview</span><h1 id="overview-heading">Defence posture</h1><p>Live workspace totals from stored analysis records. No synthetic performance metrics are displayed.</p></div><button className="button primary" onClick={onAnalyze}>+ Analyze an email</button></div>
      {status.error && <div className="error" role="alert">{status.error}</div>}

      <div className="kpi-grid">
        <StatCard label="Emails analysed" value={stats.total} hint="Stored analysis records" icon="✉" />
        <StatCard label="Phishing blocked" value={stats.phishing} hint="Security verdict: PHISHING" tone="phishing" icon="!" />
        <StatCard label="Suspicious / review" value={stats.suspicious + stats.review_required} hint="Needs a human decision" tone="warning" icon="?" />
        <StatCard label="Safe emails" value={stats.non_phishing} hint="NON-PHISHING · priority eligible" tone="good" icon="✓" />
      </div>

      <div className="dashboard-grid">
        <section className="panel chart-panel" aria-labelledby="distribution-heading">
          <div className="section-title-row"><div><span className="eyebrow">Verdicts</span><h2 id="distribution-heading">Verdict distribution</h2></div><span className="microcopy">Current workspace</span></div>
          <div className="donut-layout"><Donut stats={stats}/><div className="legend-list">{[['PHISHING',stats.phishing],['SUSPICIOUS',stats.suspicious],['REVIEW REQUIRED',stats.review_required],['NON-PHISHING',stats.non_phishing]].map(([label,value]) => { const meta=verdictMeta(label); return <div key={label}><span className={'legend-icon '+meta.tone}>{meta.icon}</span><strong>{label}</strong><span>{value}</span></div> })}</div></div>
          <p className="chart-note">Counts are read directly from the stats API.</p>
        </section>

        <section className="panel chart-panel" aria-labelledby="activity-heading">
          <div className="section-title-row"><div><span className="eyebrow">Activity</span><h2 id="activity-heading">Analyses over recorded dates</h2></div><span className="microcopy">Based on the latest 20 records</span></div>
          <ActivityChart items={recent}/>
          <p className="chart-note">This view is limited to the latest records returned by the existing API; it does not invent a historical series.</p>
        </section>
      </div>

      <div className="dashboard-grid lower-grid">
        <section className="panel table-panel" aria-labelledby="recent-heading">
          <div className="section-title-row"><div><span className="eyebrow">Activity log</span><h2 id="recent-heading">Recent analyses</h2></div>{status.busy && <span className="microcopy" role="status">Refreshing…</span>}</div>
          {recent.length ? <div className="table-wrap"><table className="data-table"><thead><tr><th>Sender</th><th>Subject</th><th>Verdict</th><th>Priority</th><th>Time</th></tr></thead><tbody>{recent.slice(0,8).map((item) => { const meta=verdictMeta(item.classification); return <tr key={item.request_id+'-'+item.message_id} tabIndex="0" onClick={()=>onOpenAnalysis(item.message_id)} onKeyDown={(e)=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();onOpenAnalysis(item.message_id)}}}><td data-label="Sender" className="break-value mono-text">{item.sender}</td><td data-label="Subject" className="break-value">{item.subject||'—'}</td><td data-label="Verdict"><span className={'verdict-badge compact '+stateClass(item.classification)}><b>{meta.icon}</b>{item.classification}</span></td><td data-label="Priority">{item.priority ? <span className={'priority-chip '+item.priority.toLowerCase()}>{item.priority}</span> : <span className="withheld-text">withheld</span>}</td><td data-label="Time">{new Date(item.created_at).toLocaleString()}</td></tr> })}</tbody></table></div> : <div className="empty-state"><div className="empty-illustration">⌁</div><strong>No scans yet</strong><span>Analyze your first email to populate the command centre.</span><button className="button primary compact-button" onClick={onAnalyze}>Run your first scan</button></div>}
        </section>

        <section className="panel attention-panel" aria-labelledby="attention-heading">
          <div className="section-title-row"><div><span className="eyebrow">Priority queue</span><h2 id="attention-heading">Needs your attention</h2></div><span className="queue-count">{queue.length}</span></div>
          {queue.length ? <div className="attention-list">{queue.map((item)=>{const meta=verdictMeta(item.classification); return <button key={item.request_id+'-'+item.message_id} className="attention-item" onClick={()=>onOpenAnalysis(item.message_id)}><span className={'attention-icon '+meta.tone}>{meta.icon}</span><span><strong>{item.subject||'(no subject)'}</strong><small className="mono-text">{item.sender}</small></span><span className="attention-arrow">→</span></button>})}</div> : <div className="empty-state small"><strong>Nothing waiting</strong><span>Suspicious and review-required messages appear here first.</span></div>}
        </section>
      </div>
    </section>
  )
}
