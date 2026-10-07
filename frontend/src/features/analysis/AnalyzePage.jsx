import { useRef, useState } from 'react'
import { api, MAX_EMAIL_BYTES } from '../../api'
import ResultPanel from './ResultPanel'

const SAMPLE_EML = `From: security-alert@example.com
To: analyst@example.com
Subject: Urgent account verification
Message-ID: <sample-phishing@example.com>
Date: Wed, 07 Oct 2026 10:00:00 +0000
MIME-Version: 1.0
Content-Type: text/plain; charset="UTF-8"

Your account requires verification.
Please verify your access now:
https://example.com/verify
`

const starter = { message_id: '', sender: 'sender@example.com', recipients: ['analyst@example.com'], subject: '', text_body: '', html_body: '', headers: {}, attachments: [] }

function makeMessageId() {
  try { return crypto.randomUUID() } catch { return 'message-' + Date.now() }
}

export default function AnalyzePage({ onAnalyzed }) {
  const [mode, setMode] = useState('file')
  const [form, setForm] = useState({ ...starter, message_id: makeMessageId() })
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [preview, setPreview] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [progressStep, setProgressStep] = useState(-1)
  const [dragging, setDragging] = useState(false)
  const abortRef = useRef(null)

  const update = (key, value) => setForm((current) => ({ ...current, [key]: value }))

  const validateFile = (candidate) => {
    if (!candidate) return 'Choose an .eml file.'
    if (!candidate.name.toLowerCase().endsWith('.eml')) return 'Only .eml files are accepted.'
    if (candidate.size > MAX_EMAIL_BYTES) return 'The .eml file exceeds the 2 MB limit.'
    return ''
  }

  const chooseFile = (candidate) => {
    const validationError = validateFile(candidate)
    if (validationError) { setFile(null); setError(validationError); return }
    setError('')
    setFile(candidate)
  }

  const loadSample = () => {
    const sample = new File([SAMPLE_EML], 'sample-phishing.eml', { type: 'message/rfc822' })
    chooseFile(sample)
    setMode('file')
  }

  const runProgress = () => {
    setProgressStep(0)
    const interval = window.setInterval(() => setProgressStep((step) => step < 3 ? step + 1 : step), 520)
    return () => window.clearInterval(interval)
  }

  const startAnalysis = async (submit, safePreview, stopProgress) => {
    if (busy) return
    setBusy(true)
    setProgressStep(0)
    setError('')
    const controller = new AbortController()
    abortRef.current = controller
    try {
      const nextResult = await submit(controller.signal)
      setResult(nextResult)
      setPreview(safePreview)
      onAnalyzed?.()
      setProgressStep(4)
    } catch (analysisError) {
      if (analysisError.code !== 'CANCELLED') setError(analysisError.message + (analysisError.requestId ? ' (' + analysisError.requestId + ')' : ''))
    } finally {
      stopProgress?.()
      if (abortRef.current === controller) abortRef.current = null
      setBusy(false)
    }
  }

  const submitPaste = (event) => {
    event.preventDefault()
    const payload = { ...form, message_id: form.message_id || makeMessageId() }
    const stop = runProgress()
    startAnalysis((signal) => api.analyze(payload, signal), {
      sender: payload.sender,
      recipients: payload.recipients,
      subject: payload.subject,
      headers: payload.headers,
      text_body: payload.text_body,
      html_body: '',
      attachments: payload.attachments,
    }, stop)
  }

  const submitFile = async () => {
    if (!file) { setError('Select a valid .eml file first.'); return }
    const source = await file.text()
    const stop = runProgress()
    startAnalysis((signal) => api.analyzeEml(file, signal), { filename: file.name, raw: source }, stop)
  }

  return (
    <section className="page-stack" aria-labelledby="analyze-heading">
      <div className="page-heading"><div><span className="eyebrow">Secure intake</span><h1 id="analyze-heading">Analyze an email</h1><p>Inspect an untrusted message through the existing IESP pipeline. Nothing submitted here is executed.</p></div><button className="button secondary" onClick={loadSample}>Try a sample</button></div>
      {error && <div className="error" role="alert">{error}</div>}
      <div className="analysis-workspace">
        <section className="panel input-panel" aria-labelledby="input-heading">
          <div className="section-title-row"><div><span className="eyebrow">Step 1</span><h2 id="input-heading">Choose a message source</h2></div>{busy && <button type="button" className="button subtle" onClick={() => abortRef.current?.abort()}>Cancel</button>}</div>
          <div className="analysis-tabs" role="tablist" aria-label="Analysis input mode">
            <button type="button" role="tab" aria-selected={mode === 'file'} className={mode === 'file' ? 'active' : ''} onClick={() => setMode('file')}><span>⇩</span> Upload .eml</button>
            <button type="button" role="tab" aria-selected={mode === 'paste'} className={mode === 'paste' ? 'active' : ''} onClick={() => setMode('paste')}><span>⌘</span> Paste raw email</button>
          </div>
          {mode === 'file' ? (
            <div className="form-stack">
              <div className={'dropzone defence-dropzone ' + (dragging ? 'dragging' : '')} onDragOver={(event) => { event.preventDefault(); setDragging(true) }} onDragLeave={() => setDragging(false)} onDrop={(event) => { event.preventDefault(); setDragging(false); chooseFile(event.dataTransfer.files?.[0]) }}>
                <div className="dropzone-shield" aria-hidden="true">⇩</div><strong>{file ? file.name : 'Drop a bounded .eml file here'}</strong><span>{file ? (file.size / 1024).toFixed(1) + ' KB selected' : 'or choose a file from this device'}</span>
                <label className="button secondary upload-button">Choose .eml<input type="file" accept=".eml,message/rfc822" onChange={(event) => chooseFile(event.target.files?.[0])} /></label>
                <div className="intake-rules"><span>.eml only</span><span>≤ 2 MB</span><span>checked before upload</span></div>
              </div>
              {file && <div className="file-summary"><div><span className="label">Selected</span><strong>{file.name}</strong></div><div><span className="label">Size</span><span>{(file.size / 1024).toFixed(1)} KB</span></div><div><span className="label">Execution</span><span className="safe-text">Never</span></div></div>}
              <button className="button primary full-width" type="button" disabled={busy || !file} onClick={submitFile}>{busy ? 'Scanning pipeline…' : 'Analyze .eml'}</button>
            </div>
          ) : (
            <form className="form-stack" onSubmit={submitPaste}>
              <div className="form-grid">
                <label>Message ID<input className="input-mono" value={form.message_id} onChange={(e) => update('message_id', e.target.value)} /></label>
                <label>From<input required type="email" value={form.sender} onChange={(e) => update('sender', e.target.value)} /></label>
                <label>To<input required value={form.recipients.join(', ')} onChange={(e) => update('recipients', e.target.value.split(',').map((v) => v.trim()).filter(Boolean))} /></label>
                <label>Subject<input value={form.subject} onChange={(e) => update('subject', e.target.value)} /></label>
                <label className="wide">Raw/plain body<textarea rows="13" required value={form.text_body} onChange={(e) => update('text_body', e.target.value)} placeholder="Paste the text you want IESP to inspect." /></label>
                <label className="wide">HTML body <span className="field-note">Structural analysis only; never rendered.</span><textarea rows="6" value={form.html_body} onChange={(e) => update('html_body', e.target.value)} placeholder="Optional. IESP will not render this HTML." /></label>
              </div>
              <button className="button primary full-width" disabled={busy}>{busy ? 'Scanning pipeline…' : 'Analyze message'}</button>
            </form>
          )}
        </section>
        <section className="analysis-progress panel" aria-live="polite">
          <div className="section-title-row"><div><span className="eyebrow">Processing</span><h2>Security pipeline</h2></div>{busy && <span className="scan-badge">ACTIVE SCAN</span>}</div>
          <div className="stepper">{['Parse','Extract features','ML evidence','Policy decision'].map((label,index)=><div className={'stepper-item ' + (busy && index <= progressStep ? 'active' : result && index < 4 && !busy ? 'done' : '')} key={label}><span>{index+1}</span><small>{label}</small></div>)}</div>
          <div className="progress-track"><span style={{width:busy?Math.min(100,(progressStep+1)/4*100)+'%':result?'100%':'0%'}}/></div>
          <p className="microcopy">The progress strip reflects the configured processing flow; the API returns the final decision as one response.</p>
        </section>
        <ResultPanel data={result} preview={preview} />
      </div>
    </section>
  )
}
