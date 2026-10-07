const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

async function request(path, options = {}) {
  const controller = new AbortController()\n  const parentSignal = options.signal\n  if (parentSignal) parentSignal.addEventListener('abort', () => controller.abort(), { once: true })
  const timeoutMs = options.timeoutMs || 15000
  const timeout = setTimeout(() => controller.abort(), timeoutMs)
  const headers = new Headers(options.headers || {})
  headers.set('Accept', 'application/json')
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  try {
    const response = await fetch(`${API_BASE}${path}`, { ...options, headers, credentials: 'include', signal: controller.signal })
    const requestId = response.headers.get('X-Request-ID')
    const data = (response.headers.get('content-type') || '').includes('application/json') ? await response.json() : null
    if (!response.ok) {
      const error = new Error(data?.message || data?.detail?.message || `Request failed (${response.status})`)
      error.status = response.status; error.code = data?.code || data?.detail?.code; error.requestId = requestId || data?.request_id; error.retryAfterSeconds = data?.retry_after_seconds
      throw error
    }
    return data
  } catch (error) {
    if (error.name === 'AbortError') { const e = new Error('The request timed out. Please try again.'); e.code = 'TIMEOUT'; throw e }
    if (error instanceof TypeError) { const e = new Error('IESP is unavailable. Check the connection and try again.'); e.code = 'NETWORK_ERROR'; throw e }
    throw error
  } finally { clearTimeout(timeout) }
}

export const api = {
  register: (email, password) => request('/api/v1/auth/register', { method: 'POST', body: JSON.stringify({ email, password }) }),
  login: (email, password) => request('/api/v1/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  logout: () => request('/api/v1/auth/logout', { method: 'POST' }),
  me: () => request('/api/v1/auth/me'),
  analyze: (payload, signal) => request('/api/v1/analyze', { method: 'POST', body: JSON.stringify(payload), signal }),
  analyzeRaw: (rawEmail, signal) => request('/api/v1/analyze/raw', { method: 'POST', body: JSON.stringify({ raw_email: rawEmail }), signal }),
  analyzeEml: (file, signal) => { const form = new FormData(); form.append('file', file); return request('/api/v1/analyze/eml', { method: 'POST', body: form, signal, timeoutMs: 30000 }) },
  stats: () => request('/api/v1/stats'),
  history: (params = {}) => request(`/api/v1/history?${new URLSearchParams(params)}`),
  recent: (limit = 20) => request(`/api/v1/recent?limit=${limit}`),
  analysis: (id) => request(`/api/v1/analysis/${encodeURIComponent(id)}`),
  report: (id) => request(`/api/v1/analysis/${encodeURIComponent(id)}/report`),
}

// Retained as no-op compatibility exports; secrets are never read or stored in the browser.
export function getStoredApiKey() { return '' }
export function setStoredApiKey() { return false }