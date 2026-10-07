const API_BASE = (import.meta.env?.VITE_API_BASE_URL || '').replace(/\/$/, '')
export const MAX_EMAIL_BYTES = 2000000

export class ApiError extends Error {
  constructor(message, options = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = options.status || 0
    this.code = options.code || 'REQUEST_FAILED'
    this.requestId = options.requestId || ''
    this.retryAfterSeconds = options.retryAfterSeconds ?? null
  }
}

function endpoint(path) { return API_BASE + path }

function getError(response, data) {
  const payload = data?.error || data?.detail || {}
  return new ApiError(payload.message || ('Request failed (' + response.status + ')'), {
    status: response.status,
    code: payload.code || ('HTTP_' + response.status),
    requestId: payload.request_id || response.headers.get('X-Request-ID') || '',
    retryAfterSeconds: payload.retry_after_seconds ?? null,
  })
}

export async function request(path, options = {}) {
  const controller = new AbortController()
  const parentSignal = options.signal
  if (parentSignal) {
    if (parentSignal.aborted) controller.abort()
    else parentSignal.addEventListener('abort', () => controller.abort(), { once: true })
  }
  const timeout = setTimeout(() => controller.abort(), options.timeoutMs ?? 15000)
  const fetchOptions = { ...options }
  delete fetchOptions.timeoutMs
  const headers = new Headers(fetchOptions.headers || {})
  headers.set('Accept', 'application/json')
  if (fetchOptions.body && !(fetchOptions.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  try {
    const response = await fetch(endpoint(path), { ...fetchOptions, headers, credentials: 'include', signal: controller.signal })
    const contentType = response.headers.get('content-type') || ''
    const data = contentType.includes('application/json') ? await response.json() : null
    if (!response.ok) throw getError(response, data)
    return data
  } catch (error) {
    if (error?.name === 'AbortError') {
      if (parentSignal?.aborted) throw new ApiError('Request cancelled.', { code: 'CANCELLED' })
      throw new ApiError('The request timed out. Please try again.', { code: 'TIMEOUT' })
    }
    if (error instanceof ApiError) throw error
    if (error instanceof TypeError) throw new ApiError('IESP is unavailable. Check the connection and try again.', { code: 'NETWORK_ERROR' })
    throw error
  } finally {
    clearTimeout(timeout)
  }
}

async function requestBlob(path, options = {}) {
  const response = await fetch(endpoint(path), {
    ...options,
    credentials: 'include',
    headers: { Accept: 'text/csv, application/json', ...(options.headers || {}) },
  })
  if (!response.ok) throw getError(response, await response.json().catch(() => null))
  return response.blob()
}

export const api = {
  register: (email, password) => request('/api/v1/auth/register', { method: 'POST', body: JSON.stringify({ email, password }) }),
  login: (email, password) => request('/api/v1/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  logout: () => request('/api/v1/auth/logout', { method: 'POST' }),
  me: () => request('/api/v1/auth/me'),
  health: (signal) => request('/health', { signal, timeoutMs: 6000 }),
  ready: (signal) => request('/ready', { signal, timeoutMs: 6000 }),
  analyze: (payload, signal) => request('/api/v1/analyze', { method: 'POST', body: JSON.stringify(payload), signal, timeoutMs: 30000 }),
  analyzeRaw: (rawEmail, signal) => request('/api/v1/analyze/raw', { method: 'POST', body: JSON.stringify({ raw_email: rawEmail }), signal, timeoutMs: 30000 }),
  analyzeEml: (file, signal) => {
    if (!file?.name?.toLowerCase().endsWith('.eml')) return Promise.reject(new ApiError('Only .eml files are accepted.', { code: 'UNSUPPORTED_FILE' }))
    if (file.size > MAX_EMAIL_BYTES) return Promise.reject(new ApiError('The email is too large.', { code: 'EMAIL_TOO_LARGE' }))
    const form = new FormData()
    form.append('file', file)
    return request('/api/v1/analyze/eml', { method: 'POST', body: form, signal, timeoutMs: 30000 })
  },
  stats: (signal) => request('/api/v1/stats', { signal }),
  history: (params = {}, signal) => {
    const q = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => { if (v !== '' && v !== null && v !== undefined) q.set(k, v) })
    const s = q.toString()
    return request('/api/v1/history' + (s ? '?' + s : ''), { signal })
  },
  recent: (limit = 8, signal) => request('/api/v1/recent?limit=' + encodeURIComponent(limit), { signal }),
  analysis: (id, signal) => request('/api/v1/analysis/' + encodeURIComponent(id), { signal }),
  reportSummary: (signal) => request('/api/v1/reports/summary', { signal }),
  exportReport: (format, signal) => requestBlob('/api/v1/reports/export?format=' + encodeURIComponent(format), { signal }),
  oauthConnections: () => request('/api/v1/oauth/connections'),
  disconnectOAuth: (provider) => request('/api/v1/oauth/' + provider, { method: 'DELETE' }),
  listProviderMessages: (provider) => request('/api/v1/oauth/' + provider + '/messages'),
  analyzeProviderMessage: (provider, id) => request('/api/v1/oauth/' + provider + '/messages/' + encodeURIComponent(id) + '/analyze', { method: 'POST' }),
}
