const DEFAULT_BASE_URL = 'http://localhost:8000'

export function getApiBaseUrl() {
  return (import.meta.env.VITE_API_BASE_URL || DEFAULT_BASE_URL).replace(/\/$/, '')
}

export function getStoredApiKey() {
  return sessionStorage.getItem('iesp_api_key') || import.meta.env.VITE_API_KEY || ''
}

export function setStoredApiKey(value) {
  if (value) sessionStorage.setItem('iesp_api_key', value)
  else sessionStorage.removeItem('iesp_api_key')
}

async function request(path, options = {}) {
  const apiKey = getStoredApiKey()
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) }
  if (apiKey) headers['X-API-Key'] = apiKey
  const response = await fetch(`${getApiBaseUrl()}${path}`, { ...options, headers })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const message = data?.detail?.message || data?.message || `Request failed (${response.status})`
    const error = new Error(message)
    error.status = response.status
    error.payload = data
    throw error
  }
  return data
}

export function analyzeEmail(payload) {
  return request('/api/v1/analyze', { method: 'POST', body: JSON.stringify(payload) })
}
export function fetchStats() { return request('/api/v1/stats') }
export function fetchRecent(limit = 20) { return request(`/api/v1/recent?limit=${limit}`) }
