import { useEffect, useState } from 'react'
import { api } from '../../api'
import { stateClass } from '../../lib/security'

export default function ReportsPage() {
  const [report, setReport] = useState(null)
  const [status, setStatus] = useState({ busy: true, exporting: false, error: '' })

  useEffect(() => {
    const controller = new AbortController()
    api.reportSummary(controller.signal)
      .then(setReport)
      .catch(error => { if (error.code !== 'CANCELLED') setStatus({ busy: false, exporting: false, error: error.message }) })
      .finally(() => setStatus(current => ({ ...current, busy: false })))
    return () => controller.abort()
  }, [])

  const exportReport = async (format) => {
    setStatus(current => ({ ...current, exporting: true, error: '' }))
    try {
      const blob = await api.exportReport(format)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'iesp-analysis-report.' + format
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
    } catch (error) {
      if (error.code !== 'CANCELLED') setStatus(current => ({ ...current, error: error.message }))
    } finally {
      setStatus(current => ({ ...current, exporting: false }))
    }
  }

  if (status.busy) return <section className="page-stack"><div className="panel loading-panel" role="status">Building report from stored workspace data…</div></section>
  if (!report) return <section className="page-stack"><div className="error" role="alert">{status.error || 'Report data is unavailable.'}</div></section>

  const stats = report.stats
  const distribution = [
    ['PHISHING', stats.phishing],
    ['SUSPICIOUS', stats.suspicious],
    ['REVIEW REQUIRED', stats.review_required],
    ['NON-PHISHING', stats.non_phishing],
  ]
  const total = Math.max(1, stats.total)

  return (
    <section className="page-stack" aria-labelledby="reports-heading">
      <div className="page-heading"><div><span className="eyebrow">Reports</span><h1 id="reports-heading">Security activity report</h1><p>Summary and export generated only from stored analysis metadata in this workspace.</p></div><div className="button-row"><button className="button secondary" disabled={status.exporting} onClick={() => exportReport('json')}>Export JSON</button><button className="button primary-auto" disabled={status.exporting} onClick={() => exportReport('csv')}>{status.exporting ? 'Exporting…' : 'Export CSV'}</button></div></div>
      {status.error && <div className="error" role="alert">{status.error}</div>}
      <div className="report-grid">
        <section className="panel" aria-labelledby="distribution-heading"><div className="section-title-row"><div><span className="eyebrow">Distribution</span><h2 id="distribution-heading">Threat distribution</h2></div><span className="microcopy">Generated {new Date(report.generated_at).toLocaleString()}</span></div><div className="distribution-list">{distribution.map(([label, value]) => <div className="distribution-row" key={label}><div><strong>{label}</strong><span>{value} ({Math.round(value / total * 100)}%)</span></div><progress max={total} value={value} aria-label={label + ' ' + value} /></div>)}</div></section>
        <section className="panel" aria-labelledby="risk-heading"><div className="section-title-row"><div><span className="eyebrow">Exposure</span><h2 id="risk-heading">High-risk activity</h2></div><span className="microcopy">{stats.high_risk_percentage}% of stored analyses</span></div><p className="summary">{stats.high_risk} analysis records meet the configured high-risk threshold.</p></section>
      </div>
      <section className="panel" aria-labelledby="high-risk-heading"><div className="section-title-row"><div><span className="eyebrow">Priority review</span><h2 id="high-risk-heading">Highest-risk detections</h2></div><span className="microcopy">Up to 10 records</span></div>{report.high_risk_items.length ? <div className="high-risk-list">{report.high_risk_items.map(item => <article className="risk-item" key={item.request_id + '-' + item.message_id}><div><strong>{item.subject || '(no subject)'}</strong><span className="break-value">{item.sender}</span><span className={'status-badge compact ' + stateClass(item.classification)}>{item.classification}</span></div><strong>{Math.round(item.risk_score)}</strong></article>)}</div> : <div className="empty-state"><strong>No high-risk analyses</strong><span>Stored analysis records will appear here when they cross the configured threshold.</span></div>}</section>
    </section>
  )
}
