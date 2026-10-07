import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api'
import { stateClass } from '../../lib/security'

const classifications = ['', 'PHISHING', 'SUSPICIOUS', 'REVIEW REQUIRED', 'NON-PHISHING']

export default function HistoryPage({ onOpenAnalysis }) {
  const [filters, setFilters] = useState({ q: '', classification: '', min_risk: '', max_risk: '', date_from: '', date_to: '', sort_by: 'created_at', sort_order: 'desc' })
  const [data, setData] = useState({ items: [], total: 0, page: 1, page_size: 25, pages: 0 })
  const [status, setStatus] = useState({ busy: true, error: '' })
  const [page, setPage] = useState(1)
  const query = useMemo(() => ({ ...filters, page, page_size: 25 }), [filters, page])

  useEffect(() => {
    let active = true
    const controller = new AbortController()
    setStatus({ busy: true, error: '' })
    api.history(query, controller.signal)
      .then(nextData => { if (active) setData(nextData) })
      .catch(error => { if (active && error.code !== 'CANCELLED') setStatus({ busy: false, error: error.message }) })
      .finally(() => { if (active) setStatus((current) => ({ ...current, busy: false })) })
    return () => { active = false; controller.abort() }
  }, [query])

  const update = (key, value) => { setPage(1); setFilters((current) => ({ ...current, [key]: value })) }

  return (
    <section className="page-stack" aria-labelledby="history-heading">
      <div className="page-heading compact-heading"><div><span className="eyebrow">History</span><h1 id="history-heading">Analysis history</h1><p>Search and review stored results within the current authenticated workspace.</p></div><span className="microcopy">{data.total} matching records</span></div>
      {status.error && <div className="error" role="alert">{status.error}</div>}
      <section className="panel filter-panel" aria-labelledby="filter-heading">
        <div className="section-title-row"><div><span className="eyebrow">Filters</span><h2 id="filter-heading">Refine results</h2></div>{status.busy && <span className="microcopy" role="status">Loading…</span>}</div>
        <div className="filter-grid">
          <label className="wide">Search sender or subject<input value={filters.q} onChange={(event) => update('q', event.target.value)} placeholder="Search email metadata" /></label>
          <label>Classification<select value={filters.classification} onChange={(event) => update('classification', event.target.value)}>{classifications.map((item) => <option key={item} value={item}>{item || 'All classifications'}</option>)}</select></label>
          <label>Minimum risk<input type="number" min="0" max="100" value={filters.min_risk} onChange={(event) => update('min_risk', event.target.value)} /></label>
          <label>Maximum risk<input type="number" min="0" max="100" value={filters.max_risk} onChange={(event) => update('max_risk', event.target.value)} /></label>
          <label>From date<input type="date" value={filters.date_from.replace(/T.*$/, '')} onChange={(event) => update('date_from', event.target.value ? event.target.value + 'T00:00:00Z' : '')} /></label>
          <label>To date<input type="date" value={filters.date_to.replace(/T.*$/, '')} onChange={(event) => update('date_to', event.target.value ? event.target.value + 'T23:59:59Z' : '')} /></label>
          <label>Sort by<select value={filters.sort_by} onChange={(event) => update('sort_by', event.target.value)}><option value="created_at">Date</option><option value="risk_score">Risk</option><option value="classification">Classification</option><option value="sender">Sender</option><option value="subject">Subject</option></select></label>
          <label>Order<select value={filters.sort_order} onChange={(event) => update('sort_order', event.target.value)}><option value="desc">Newest / highest first</option><option value="asc">Oldest / lowest first</option></select></label>
        </div>
      </section>
      <section className="panel" aria-labelledby="history-table-heading">
        <div className="section-title-row"><div><span className="eyebrow">Results</span><h2 id="history-table-heading">Stored analyses</h2></div><span className="microcopy">Page {data.page} of {Math.max(1, data.pages)}</span></div>
        {data.items.length ? <div className="table-wrap"><table className="responsive-table"><thead><tr><th>Date</th><th>Sender</th><th>Subject</th><th>Classification</th><th>Risk</th><th>Priority</th></tr></thead><tbody>{data.items.map((item) => <tr key={item.request_id + '-' + item.message_id} tabIndex="0" onClick={() => onOpenAnalysis(item.message_id)} onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); onOpenAnalysis(item.message_id) } }}><td data-label="Date">{new Date(item.created_at).toLocaleString()}</td><td data-label="Sender" className="break-value">{item.sender}</td><td data-label="Subject" className="break-value">{item.subject || '—'}</td><td data-label="Classification"><span className={'status-badge compact ' + stateClass(item.classification)}>{item.classification}</span></td><td data-label="Risk">{Math.round(item.risk_score)}</td><td data-label="Priority">{item.priority || '—'}</td></tr>)}</tbody></table></div> : <div className="empty-state"><strong>{status.busy ? 'Loading history…' : 'No matching analyses'}</strong><span>Adjust the filters or analyze an email to create stored history.</span></div>}
        <div className="pagination" aria-label="History pagination"><button className="button secondary" disabled={page <= 1 || status.busy} onClick={() => setPage((current) => current - 1)}>Previous</button><span>Page {data.page} / {Math.max(1, data.pages)}</span><button className="button secondary" disabled={!data.pages || page >= data.pages || status.busy} onClick={() => setPage((current) => current + 1)}>Next</button></div>
      </section>
    </section>
  )
}
