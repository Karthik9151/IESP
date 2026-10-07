import { useRef, useState } from 'react'
import { api, MAX_EMAIL_BYTES } from '../../api'
import ResultPanel from './ResultPanel'

const starter = {
  message_id: 'message-1',
  sender: 'sender@example.com',
  recipients: ['analyst@example.com'],
  subject: '',
  text_body: '',
  html_body: '',
  headers: {},
  attachments: [],
}

function makeMessageId() {
  try { return crypto.randomUUID() } catch { return 'message-' + Date.now() }
}

export default function AnalyzePage({ onAnalyzed }) {
  const [mode, setMode] = useState('paste')
  const [form, setForm] = useState({ ...starter, message_id: makeMessageId() })
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
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
    if (validationError) {
      setFile(null)
      setError(validationError)
      return
    }
    setError('')
    setFile(candidate)
  }

  const startAnalysis = async (submit) => {
    if (busy) return
    setBusy(true)
    setError('')
    const controller = new AbortController()
    abortRef.current = controller
    try {
      const nextResult = await submit(controller.signal)
      setResult(nextResult)
      onAnalyzed?.()
    } catch (analysisError) {
      if (analysisError.code !== 'CANCELLED') {
        setError(analysisError.message + (analysisError.requestId ? ' (' + analysisError.requestId + ')' : ''))
      }
    } finally {
      if (abortRef.current === controller) abortRef.current = null
      setBusy(false)
    }
  }

  const submitPaste = (event) => {
    event.preventDefault()
    startAnalysis((signal) => api.analyze(form, signal))
  }

  const submitFile = () => {
    if (!file) {
      setError('Select a valid .eml file first.')
      return
    }
    startAnalysis((signal) => api.analyzeEml(file, signal))
  }

  return (
    <section className="page-stack" aria-labelledby="analyze-heading">
      <div className="page-heading">
        <div><span className="eyebrow">Analyze</span><h1 id="analyze-heading">Inspect an untrusted email</h1><p>Paste structured email fields or upload a bounded .eml message. IESP does not render submitted HTML or automatically visit URLs.</p></div>
      </div>
      {error && <div className="error" role="alert">{error}</div>}
      <div className="analysis-layout">
        <section className="panel" aria-labelledby="input-heading">
          <div className="section-title-row">
            <div><span className="eyebrow">Input</span><h2 id="input-heading">Choose a workflow</h2></div>
            {busy && <button type="button" className="button subtle" onClick={() => abortRef.current?.abort()}>Cancel analysis</button>}
          </div>
          <div className="segmented" role="tablist" aria-label="Analysis input mode">
            <button type="button" role="tab" aria-selected={mode === 'paste'} className={mode === 'paste' ? 'active' : ''} onClick={() => setMode('paste')}>Paste email</button>
            <button type="button" role="tab" aria-selected={mode === 'file'} className={mode === 'file' ? 'active' : ''} onClick={() => setMode('file')}>Upload .eml</button>
          </div>
          {mode === 'paste' ? (
            <form className="form-stack" onSubmit={submitPaste}>
              <div className="form-grid">
                <label>Message ID<input required value={form.message_id} onChange={(event) => update('message_id', event.target.value)} /></label>
                <label>From<input required type="email" value={form.sender} onChange={(event) => update('sender', event.target.value)} /></label>
                <label>To<input required value={form.recipients.join(', ')} onChange={(event) => update('recipients', event.target.value.split(',').map((value) => value.trim()).filter(Boolean))} /></label>
                <label>Subject<input value={form.subject} onChange={(event) => update('subject', event.target.value)} /></label>
                <label className="wide">Plain-text body<textarea rows="12" value={form.text_body} onChange={(event) => update('text_body', event.target.value)} /></label>
                <label className="wide">HTML body <span className="field-note">Structural analysis only; never rendered.</span><textarea rows="8" value={form.html_body} onChange={(event) => update('html_body', event.target.value)} /></label>
              </div>
              <button className="button primary" disabled={busy} type="submit">{busy ? 'Analyzing…' : 'Analyze email'}</button>
            </form>
          ) : (
            <div className="form-stack">
              <div className={'dropzone ' + (dragging ? 'dragging' : '')} onDragOver={(event) => { event.preventDefault(); setDragging(true) }} onDragLeave={() => setDragging(false)} onDrop={(event) => { event.preventDefault(); setDragging(false); chooseFile(event.dataTransfer.files?.[0]) }}>
                <span className="upload-icon" aria-hidden="true">⇩</span>
                <strong>{file ? file.name : 'Drop an .eml file here'}</strong>
                <span>{file ? (file.size / 1024).toFixed(1) + ' KB selected' : 'or choose a file from this device'}</span>
                <label className="button secondary upload-button">Choose .eml<input type="file" accept=".eml,message/rfc822" onChange={(event) => chooseFile(event.target.files?.[0])} /></label>
                <small>Maximum size: 2 MB. Attachments are treated as metadata only.</small>
              </div>
              {file && <div className="file-summary" aria-live="polite"><div><span className="label">Selected file</span><strong>{file.name}</strong></div><div><span className="label">Size</span><span>{(file.size / 1024).toFixed(1)} KB</span></div><div><span className="label">Type</span><span>message/rfc822</span></div></div>}
              <button className="button primary" type="button" disabled={busy || !file} onClick={submitFile}>{busy ? 'Analyzing…' : 'Analyze .eml'}</button>
            </div>
          )}
        </section>
        <ResultPanel data={result} />
      </div>
    </section>
  )
}
