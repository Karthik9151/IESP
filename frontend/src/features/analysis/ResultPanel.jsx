import { securityDescription, verdictMeta, defangText, isPriorityEligible } from '../../lib/security'

async function copySafe(text, onDone) {
  try {
    await navigator.clipboard.writeText(defangText(text))
    onDone?.()
  } catch {}
}

function SafePreview({ preview }) {
  if (!preview) return <div className="safe-content-note"><strong>Stored analysis view</strong><span>The current API contract stores analysis metadata/results, not raw message bodies. Re-opened History records therefore do not expose original email content.</span></div>
  const raw = preview.raw || preview.text_body || ''
  const display = defangText(raw)
  const headers = preview.raw ? raw.split(/\r?\n\r?\n/, 1)[0] : ''
  const body = preview.raw ? raw.split(/\r?\n\r?\n/).slice(1).join('\n\n') : preview.text_body || ''
  const files = preview.attachments || []
  return (
    <section className="panel-inner safe-view" aria-labelledby="safe-view-heading">
      <div className="section-title-row"><div><span className="eyebrow">Untrusted content</span><h3 id="safe-view-heading">Safe view of email</h3></div><span className="safe-badge">NEVER EXECUTED</span></div>
      <div className="safe-note">HTML is never rendered. URLs are defanged and are not clickable.</div>
      {headers && <div className="safe-section"><div className="safe-section-head"><strong>Headers</strong><button className="text-action" onClick={() => copySafe(headers)}>Copy safely</button></div><pre className="mono-box">{defangText(headers)}</pre></div>}
      <div className="safe-section"><div className="safe-section-head"><strong>Body</strong><button className="text-action" onClick={() => copySafe(body)}>Copy safely</button></div><pre className="mono-box">{display || 'No text body supplied.'}</pre></div>
      {files.length ? <div className="attachment-grid">{files.map((file, index) => <div className="attachment-item" key={index}><span>▧</span><div><strong>{file.filename}</strong><small>{file.content_type || 'unknown type'} · {file.size_bytes ?? 'size unavailable'} bytes</small></div><em>NEVER EXECUTED</em></div>)}</div> : null}
    </section>
  )
}

function RiskReason({ reason }) {
  const severity = String(reason.severity || 'info').toLowerCase()
  return (
    <article className="risk-reason">
      <div className="risk-reason-icon" aria-hidden="true">{severity === 'critical' || severity === 'high' ? '!' : severity === 'medium' ? '•' : 'i'}</div>
      <div className="risk-reason-body">
        <div className="risk-reason-head"><strong>{reason.code}</strong><span className={'severity-chip ' + severity}>{reason.severity}</span></div>
        <p>{reason.message}</p>
        <details><summary>What this means</summary><p>{reason.category || 'Security signal'} is a structured indicator used by the configured policy. Evidence is shown as supplied by the analysis engine.</p></details>
      </div>
    </article>
  )
}

function EvidenceGauge({ value }) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return <div className="evidence-empty">No phishing-model margin was returned for this analysis.</div>
  const strength = Math.min(1, Math.abs(numeric) / 5)
  const rotation = -90 + strength * 180
  return (
    <div className="gauge-wrap">
      <div className="gauge" style={{ '--needle-rotation': rotation + 'deg' }} aria-label={'SVM ranking margin ' + numeric}>
        <div className="gauge-arc"/><div className="gauge-needle"/><div className="gauge-center">●</div>
      </div>
      <div className="gauge-value"><strong>{String(value)}</strong><span>SVM decision margin</span></div>
    </div>
  )
}

export default function ResultPanel({ data, preview }) {
  if (!data) {
    return <section className="panel result-empty" aria-labelledby="result-heading"><div className="empty-illustration" aria-hidden="true">⌁</div><span className="eyebrow">Security result</span><h2 id="result-heading">Ready for inspection</h2><p>Run a scan to see the verdict, ranked reasons, model evidence, safe email view, and next actions.</p></section>
  }

  const security = data.security
  const meta = verdictMeta(security.classification)
  const eligible = isPriorityEligible(data)
  const reasons = [...(security.reasons || [])]

  return (
    <section className="result-panel" aria-labelledby="result-heading">
      <div className={'verdict-banner ' + meta.tone}>
        <div className="verdict-icon" aria-hidden="true">{meta.icon}</div>
        <div><span className="eyebrow">Security verdict</span><h2 id="result-heading">{meta.label}</h2><p>{securityDescription(security.classification)}</p></div>
        <span className="verdict-label">{security.classification}</span>
      </div>

      <div className="result-grid">
        <section className="panel" aria-labelledby="why-heading">
          <div className="section-title-row"><div><span className="eyebrow">Evidence</span><h3 id="why-heading">Security reasons</h3></div><span className="microcopy">{reasons.length} signal{reasons.length === 1 ? '' : 's'}</span></div>
          {reasons.length ? <div className="risk-reasons">{reasons.map((reason, index) => <RiskReason reason={reason} key={(reason.code || 'reason') + index}/>)}</div> : <div className="empty-inline">No additional deterministic findings were produced.</div>}
        </section>

        <section className="panel" aria-labelledby="evidence-heading">
          <div className="section-title-row"><div><span className="eyebrow">ML evidence</span><h3 id="evidence-heading">Model decision margin</h3></div><span className="tooltip" title="This is the LinearSVC decision margin used for ranking; it is not a confidence percentage.">?</span></div>
          <EvidenceGauge value={security.model_score} />
          <div className="policy-risk-score"><strong>Policy risk score</strong><span>{typeof security.risk_score === 'number' && Number.isFinite(security.risk_score) ? Math.round(security.risk_score) + '/100' : 'Not available'}</span><small>Application risk/policy score, not a probability.</small></div>
          <p className="microcopy">A LinearSVC margin indicates relative evidence strength. It is not calibrated as a confidence percentage.</p>
        </section>

        <section className="panel priority-card" aria-labelledby="priority-heading">
          <div className="section-title-row"><div><span className="eyebrow">Priority</span><h3 id="priority-heading">Priority assessment</h3></div>{eligible ? <span className="priority-chip p2">Proxy label</span> : <span className="lock-chip">LOCKED</span>}</div>
          {eligible ? <><div className="priority-hero"><span className={'priority-chip ' + String(data.priority.label).toLowerCase()}>{data.priority.label}</span><strong>{data.priority.label === 'P1' ? 'Immediate attention' : data.priority.label === 'P2' ? 'Elevated attention' : 'Routine attention'}</strong></div><p>Priority was eligible because the security verdict is NON-PHISHING. These P1/P2/P3 labels are project proxy labels, not human-annotated urgency.</p></> : <div className="withheld"><span>▣</span><div><strong>Priority withheld – security review first</strong><p>Priority is never surfaced for PHISHING, SUSPICIOUS or REVIEW REQUIRED decisions.</p></div></div>}
        </section>

        <section className="panel" aria-labelledby="metadata-heading">
          <div className="section-title-row"><div><span className="eyebrow">Traceability</span><h3 id="metadata-heading">Model metadata</h3></div></div>
          <dl className="metadata-list">
            <div><dt>Message ID</dt><dd className="mono-text">{data.message_id}</dd></div>
            <div><dt>Request ID</dt><dd className="mono-text">{data.request_id}</dd></div>
            <div><dt>Sender</dt><dd>{data.email?.sender || '—'}</dd></div>
            <div><dt>Subject</dt><dd>{data.email?.subject || '—'}</dd></div>
            <div><dt>Analysis time</dt><dd>{data.analyzed_at ? new Date(data.analyzed_at).toLocaleString() : '—'}</dd></div>
          </dl>
        </section>
      </div>

      <SafePreview preview={preview} />

      <section className="panel" aria-labelledby="next-steps-heading">
        <div className="section-title-row"><div><span className="eyebrow">Response</span><h3 id="next-steps-heading">Recommended next steps</h3></div></div>
        <div className="next-steps">
          {['Report the message through your normal reporting channel.', 'Delete or quarantine it if your workflow requires.', 'Verify with the sender through another trusted channel.'].map((item,index) => <label key={item} className="check-row"><input type="checkbox"/><span><strong>{index + 1}</strong>{item}</span></label>)}
        </div>
      </section>

      <details className="panel advanced-panel">
        <summary>Model &amp; policy metadata</summary>
        <dl className="metadata-list metadata-grid">
          <div><dt>Phishing model</dt><dd>{data.model_info?.phishing || '—'}</dd></div>
          <div><dt>Priority model</dt><dd>{data.model_info?.priority || 'Not used for withheld states'}</dd></div>
          <div><dt>Model version</dt><dd>{data.model_info?.model_version || '—'}</dd></div>
          <div><dt>Policy version</dt><dd>{data.model_info?.policy_version || '—'}</dd></div>
        </dl>
      </details>
    </section>
  )
}
