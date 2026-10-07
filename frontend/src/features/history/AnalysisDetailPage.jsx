import { useEffect, useState } from 'react'
import { api } from '../../api'
import ResultPanel from '../analysis/ResultPanel'

export default function AnalysisDetailPage({ messageId, onBack }) {
  const [data, setData] = useState(null)
  const [status, setStatus] = useState({ busy: true, error: '' })

  useEffect(() => {
    const controller = new AbortController()
    setStatus({ busy: true, error: '' })
    api.analysis(messageId, controller.signal)
      .then(setData)
      .catch(error => { if (error.code !== 'CANCELLED') setStatus({ busy: false, error: error.message }) })
      .finally(() => setStatus(current => ({ ...current, busy: false })))
    return () => controller.abort()
  }, [messageId])

  return (
    <section className="page-stack" aria-labelledby="detail-heading">
      <div className="page-heading compact-heading">
        <div><span className="eyebrow">History detail</span><h1 id="detail-heading">Stored analysis</h1><p>Read-only view of analysis metadata preserved for the current workspace.</p></div>
        <button className="button secondary" onClick={onBack}>Back to history</button>
      </div>
      {status.error && <div className="error" role="alert">{status.error}</div>}
      {status.busy && <div className="panel loading-panel" role="status">Loading stored analysis…</div>}
      {!status.busy && data && <ResultPanel data={data} />}
    </section>
  )
}
