import { useEffect, useState } from 'react'
import { api } from '../../api'
import { verdictMeta, stateClass } from '../../lib/security'

export default function ReportsPage() {
  const [report, setReport] = useState(null)
  const [status, setStatus] = useState({ busy: true, exporting: false, error: '' })

  useEffect(() => {
    const controller = new AbortController()
    api.reportSummary(controller.signal).then(setReport).catch(error => { if (error.code !== 'CANCELLED') setStatus({ busy:false, exporting:false, error:error.message }) }).finally(() => setStatus(current => ({ ...current, busy:false })))
    return () => controller.abort()
  }, [])

  const exportReport = async (format) => {
    setStatus(current=>({...current,exporting:true,error:''}))
    try {
      const blob=await api.exportReport(format)
      const url=URL.createObjectURL(blob)
      const link=document.createElement('a')
      link.href=url
      link.download='iesp-analysis-report.'+format
      document.body.appendChild(link); link.click(); link.remove(); URL.revokeObjectURL(url)
    } catch (error) {
      if (error.code !== 'CANCELLED') setStatus(current=>({...current,error:error.message}))
    } finally { setStatus(current=>({...current,exporting:false})) }
  }

  if (status.busy) return <section className="page-stack"><div className="panel loading-panel"><div className="scan-orb" aria-hidden="true"/><strong>Preparing report</strong><span className="microcopy">Reading stored workspace data…</span></div></section>
  if (!report) return <section className="page-stack"><div className="error" role="alert">{status.error || 'Report data is unavailable.'}</div></section>

  const stats=report.stats
  const total=Math.max(1,stats.total)
  const distribution=[['PHISHING',stats.phishing],['SUSPICIOUS',stats.suspicious],['REVIEW REQUIRED',stats.review_required],['NON-PHISHING',stats.non_phishing]]

  return (
    <section className="page-stack" aria-labelledby="reports-heading">
      <div className="page-heading"><div><span className="eyebrow">Operational reporting</span><h1 id="reports-heading">Security activity report</h1><p>Only recorded analysis metadata is included. Performance metrics are intentionally excluded unless your API provides them.</p></div><div className="button-row"><button className="button secondary" disabled={status.exporting} onClick={()=>exportReport('json')}>Export JSON</button><button className="button primary" disabled={status.exporting} onClick={()=>exportReport('csv')}>{status.exporting?'Exporting…':'Export CSV'}</button></div></div>
      {status.error && <div className="error" role="alert">{status.error}</div>}
      <div className="report-kpi-grid"><div className="report-tile"><span>Total analyses</span><strong>{stats.total}</strong><small>Stored records</small></div><div className="report-tile"><span>Phishing</span><strong>{stats.phishing}</strong><small>Security verdict</small></div><div className="report-tile"><span>Review queue</span><strong>{stats.suspicious+stats.review_required}</strong><small>Suspicious + review required</small></div><div className="report-tile"><span>High risk</span><strong>{stats.high_risk}</strong><small>{stats.high_risk_percentage}% of stored analyses</small></div></div>

      <div className="report-grid">
        <section className="panel"><div className="section-title-row"><div><span className="eyebrow">Distribution</span><h2>Threat distribution</h2></div><span className="microcopy">Generated {new Date(report.generated_at).toLocaleString()}</span></div><div className="distribution-list">{distribution.map(([label,value])=>{const meta=verdictMeta(label);return <div className="distribution-row" key={label}><div><span className={'legend-icon '+meta.tone}>{meta.icon}</span><strong>{label}</strong><span>{value} · {Math.round(value/total*100)}%</span></div><progress max={total} value={value} aria-label={label+' '+value}/></div>})}</div></section>
        <section className="panel"><div className="section-title-row"><div><span className="eyebrow">Export detail</span><h2>What the files contain</h2></div></div><div className="export-explain"><div><strong>CSV</strong><p>Flat rows for message ID, sender, subject, verdict, risk, priority, timestamps and model metadata.</p></div><div><strong>JSON</strong><p>The same stored records in a structured payload with generation metadata.</p></div></div></section>
      </div>

      <section className="panel"><div className="section-title-row"><div><span className="eyebrow">Attention set</span><h2>Highest-risk detections</h2></div><span className="microcopy">Up to 10 records returned by the API</span></div>{report.high_risk_items.length?<div className="attention-table">{report.high_risk_items.map(item=>{const meta=verdictMeta(item.classification);return <article key={item.request_id+'-'+item.message_id} className="report-item"><div><span className={'verdict-badge compact '+stateClass(item.classification)}><b>{meta.icon}</b>{item.classification}</span><strong>{item.subject||'(no subject)'}</strong><small className="mono-text">{item.sender}</small></div><strong className="risk-number">{Math.round(item.risk_score)}</strong></article>})}</div>:<div className="empty-state"><strong>No high-risk analyses</strong><span>Stored records will appear here when they cross the configured threshold.</span></div>}</section>
    </section>
  )
}
