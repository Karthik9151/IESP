import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api'
import { stateClass, verdictMeta } from '../../lib/security'
import ResultPanel from '../analysis/ResultPanel'

const classifications = ['', 'PHISHING', 'SUSPICIOUS', 'REVIEW REQUIRED', 'NON-PHISHING']

export default function HistoryPage({ onOpenAnalysis, initialSearch = '' }) {
  const [filters, setFilters] = useState({ q: initialSearch, classification: '', min_risk: '', max_risk: '', date_from: '', date_to: '', sort_by: 'created_at', sort_order: 'desc' })
  const [data, setData] = useState({ items: [], total: 0, page: 1, page_size: 25, pages: 0 })
  const [status, setStatus] = useState({ busy: true, error: '' })
  const [page, setPage] = useState(1)
  const [selectedId, setSelectedId] = useState(null)
  const [selectedData, setSelectedData] = useState(null)
  const [selectedBusy, setSelectedBusy] = useState(false)
  const query = useMemo(() => ({ ...filters, page, page_size: 25 }), [filters, page])

  useEffect(() => {
    if (initialSearch && filters.q !== initialSearch) setFilters((current) => ({ ...current, q: initialSearch }))
  }, [initialSearch])

  useEffect(() => {
    const controller = new AbortController()
    setStatus({ busy: true, error: '' })
    api.history(query, controller.signal)
      .then(nextData => setData(nextData))
      .catch(error => { if (error.code !== 'CANCELLED') setStatus({ busy: false, error: error.message }) })
      .finally(() => setStatus((current) => ({ ...current, busy: false })))
    return () => controller.abort()
  }, [query])

  const update = (key, value) => { setPage(1); setFilters((current) => ({ ...current, [key]: value })) }

  const flipSort = (key) => setFilters((current) => ({ ...current, sort_by: key, sort_order: current.sort_by === key && current.sort_order === 'desc' ? 'asc' : 'desc' }))

  useEffect(() => {
    if (!selectedId) { setSelectedData(null); return }
    const controller = new AbortController()
    setSelectedBusy(true)
    api.analysis(selectedId, controller.signal).then(setSelectedData).catch(() => setSelectedData(null)).finally(() => setSelectedBusy(false))
    return () => controller.abort()
  }, [selectedId])

  return (
    <section className="page-stack" aria-labelledby="history-heading">
      <div className="page-heading"><div><span className="eyebrow">Forensics log</span><h1 id="history-heading">Analysis history</h1><p>Search stored analysis metadata inside the authenticated workspace.</p></div><span className="record-pill">{data.total} records</span></div>
      {status.error && <div className="error" role="alert">{status.error}</div>}

      <section className="panel filter-panel">
        <div className="section-title-row"><div><span className="eyebrow">Filter console</span><h2>Find a record</h2></div>{status.busy && <span className="microcopy" role="status">Loading…</span>}</div>
        <div className="filter-grid">
          <label className="wide">Search sender, subject or message ID<input value={filters.q} onChange={(e)=>update('q',e.target.value)} placeholder="Search protected workspace"/></label>
          <label>Verdict<select value={filters.classification} onChange={(e)=>update('classification',e.target.value)}>{classifications.map((item)=><option key={item} value={item}>{item||'All verdicts'}</option>)}</select></label>
          <label>Minimum risk<input type="number" min="0" max="100" value={filters.min_risk} onChange={(e)=>update('min_risk',e.target.value)}/></label>
          <label>Maximum risk<input type="number" min="0" max="100" value={filters.max_risk} onChange={(e)=>update('max_risk',e.target.value)}/></label>
          <label>From date<input type="date" value={filters.date_from.replace(/T.*$/,'')} onChange={(e)=>update('date_from',e.target.value?e.target.value+'T00:00:00Z':'')}/></label>
          <label>To date<input type="date" value={filters.date_to.replace(/T.*$/,'')} onChange={(e)=>update('date_to',e.target.value?e.target.value+'T23:59:59Z':'')}/></label>
          <label>Sort by<select value={filters.sort_by} onChange={(e)=>update('sort_by',e.target.value)}><option value="created_at">Recorded time</option><option value="risk_score">Risk score</option><option value="classification">Verdict</option><option value="sender">Sender</option><option value="subject">Subject</option></select></label>
          <button className="button secondary filter-apply" onClick={()=>setPage(1)}>Refresh results</button>
        </div>
        <div className="filter-chip-row">{filters.classification && <button className="filter-chip active" onClick={()=>update('classification','')}>{filters.classification} ×</button>}{filters.q && <button className="filter-chip active" onClick={()=>update('q','')}>{filters.q} ×</button>}{(filters.classification||filters.q||filters.min_risk||filters.max_risk||filters.date_from||filters.date_to) && <button className="text-action" onClick={()=>setFilters((current)=>({...current,q:'',classification:'',min_risk:'',max_risk:'',date_from:'',date_to:''}))}>Clear filters</button>}</div>
      </section>

      <section className="panel">
        <div className="section-title-row"><div><span className="eyebrow">Records</span><h2>Stored analyses</h2></div><span className="microcopy">Page {data.page} / {Math.max(1,data.pages)}</span></div>
        {data.items.length ? <div className="table-wrap"><table className="data-table"><thead><tr><th>Recorded</th><th>Sender</th><th>Subject</th><th>Verdict</th><th>Risk</th><th>Priority</th></tr></thead><tbody>{data.items.map((item)=>{const meta=verdictMeta(item.classification);return <tr key={item.request_id+'-'+item.message_id} tabIndex="0" onClick={()=>setSelectedId(item.message_id)} onKeyDown={(e)=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();setSelectedId(item.message_id)}}}><td data-label="Recorded">{new Date(item.created_at).toLocaleString()}</td><td data-label="Sender" className="break-value mono-text">{item.sender}</td><td data-label="Subject" className="break-value">{item.subject||'—'}</td><td data-label="Verdict"><span className={'verdict-badge compact '+stateClass(item.classification)}><b>{meta.icon}</b>{item.classification}</span></td><td data-label="Risk">{Math.round(item.risk_score)}</td><td data-label="Priority">{item.priority?<span className={'priority-chip '+item.priority.toLowerCase()}>{item.priority}</span>:<span className="withheld-text">withheld</span>}</td></tr>})}</tbody></table></div> : <div className="empty-state"><div className="empty-illustration">≡</div><strong>{status.busy?'Loading history…':'No matching analyses'}</strong><span>Adjust filters or analyze another email to create stored history.</span></div>}
        <div className="pagination"><button className="button secondary" disabled={page<=1||status.busy} onClick={()=>setPage(v=>v-1)}>Previous</button><span>Page {data.page} / {Math.max(1,data.pages)}</span><button className="button secondary" disabled={!data.pages||page>=data.pages||status.busy} onClick={()=>setPage(v=>v+1)}>Next</button></div>
      </section>
      {selectedId && <div className="drawer-backdrop" role="presentation" onClick={()=>setSelectedId(null)}>
  <aside className="detail-drawer" role="dialog" aria-modal="true" aria-label="Analysis detail" onClick={e=>e.stopPropagation()}>
    <div className="drawer-head"><div><span className="eyebrow">Forensic detail</span><h2>Analysis result</h2></div><button className="icon-button" onClick={()=>setSelectedId(null)} aria-label="Close analysis detail">×</button></div>
    {selectedBusy && <div className="loading-panel"><div className="scan-orb" aria-hidden="true"/><strong>Loading record…</strong></div>}
    {!selectedBusy && selectedData && <ResultPanel data={selectedData}/>}
    {!selectedBusy && !selectedData && <div className="error" role="alert">This analysis record could not be loaded.</div>}
    {!selectedBusy && selectedData && <button className="button secondary full-width" onClick={()=>onOpenAnalysis(selectedId)}>Open full result</button>}
  </aside>
</div>}
    </section>
  )
}
