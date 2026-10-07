import { securityDescription, stateClass } from '../../lib/security'

function CopyableValue({ children }) {
  return <span className="break-value">{children || '—'}</span>
}

export default function ResultPanel({ data }) {
  if (!data) {
    return (
      <section className="panel result-empty" aria-labelledby="result-heading">
        <span className="eyebrow">Security result</span>
        <h2 id="result-heading">Waiting for an analysis</h2>
        <p>Submit a message or upload an .eml file to see the security decision, evidence, and model metadata.</p>
      </section>
    )
  }
  const security = data.security
  const classificationClass = stateClass(security.classification)
  const modelScoreAvailable = security.model_score !== null && security.model_score !== undefined
  return (
    <section className="panel result-panel" aria-labelledby="result-heading">
      <div className="result-hero">
        <div><span className="eyebrow">Security verdict</span><h2 id="result-heading">{security.classification}</h2><p className="result-description">{securityDescription(security.classification)}</p></div>
        <span className={'status-badge ' + classificationClass}>{security.classification}</span>
      </div>
      <div className="score-layout">
        <div className="risk-score-card"><span className="label">Policy risk score</span><strong>{Math.round(security.risk_score)}/100</strong><progress max="100" value={security.risk_score} aria-label={'Policy risk score ' + Math.round(security.risk_score) + ' out of 100'} /><span className="microcopy">Application risk/policy score, not a probability.</span></div>
        <div className="model-score-card"><span className="label">Model evidence</span><strong>{modelScoreAvailable ? String(security.model_score) : 'Unavailable'}</strong><span>{modelScoreAvailable ? 'Model decision margin' : 'Phishing model evidence unavailable'}</span></div>
      </div>
      <div className="detail-grid">
        <div><span className="label">Sender</span><CopyableValue>{data.email?.sender}</CopyableValue></div>
        <div><span className="label">Recipients</span><CopyableValue>{data.email?.recipients?.join(', ')}</CopyableValue></div>
        <div className="detail-wide"><span className="label">Subject</span><CopyableValue>{data.email?.subject}</CopyableValue></div>
        <div><span className="label">Analysis time</span><CopyableValue>{data.analyzed_at ? new Date(data.analyzed_at).toLocaleString() : '—'}</CopyableValue></div>
        <div><span className="label">Request ID</span><CopyableValue>{data.request_id}</CopyableValue></div>
      </div>
      <section aria-labelledby="reasons-heading">
        <div className="section-title-row"><div><span className="eyebrow">Evidence</span><h3 id="reasons-heading">Security reasons</h3></div><span className="microcopy">{security.reasons?.length || 0} findings</span></div>
        {security.reasons?.length ? <div className="findings">{security.reasons.map((reason, index) => <article className="finding" key={reason.code + '-' + index}><div className="finding-top"><strong>{reason.code}</strong><span className={'severity ' + String(reason.severity).toLowerCase()}>{reason.severity}</span></div><p>{reason.message}</p>{reason.evidence && Object.keys(reason.evidence).length > 0 && <pre className="evidence">{JSON.stringify(reason.evidence, null, 2)}</pre>}</article>)}</div> : <p className="empty-inline">No additional deterministic findings were produced.</p>}
      </section>
      <div className="result-footer-grid">
        <div className="priority-box"><span className="eyebrow">Priority assessment</span><strong>{data.priority?.label || 'SUPPRESSED'}</strong><p>{data.priority ? 'Priority model eligibility was satisfied after the security decision.' : 'Priority is intentionally not produced for this security state.'}</p></div>
        <div className="metadata-box"><span className="eyebrow">Model metadata</span><dl><div><dt>Model</dt><dd>{data.model_info?.phishing || '—'}</dd></div><div><dt>Version</dt><dd>{data.model_info?.model_version || '—'}</dd></div><div><dt>Policy</dt><dd>{data.model_info?.policy_version || '—'}</dd></div></dl></div>
      </div>
      <div className="safe-content-note" role="note"><strong>Safe handling</strong><span>Submitted HTML is analyzed structurally and is never rendered as trusted DOM. URLs and attachments are not automatically opened or executed.</span></div>
    </section>
  )
}
