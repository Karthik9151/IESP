import test from 'node:test'
import assert from 'node:assert/strict'
import { request } from '../src/api.js'

const originalFetch = globalThis.fetch

test.afterEach(() => { globalThis.fetch = originalFetch })

test('maps structured API errors and request ids', async () => {
  globalThis.fetch = async () => new Response(JSON.stringify({
    error: { code: 'RATE_LIMITED', message: 'Too many requests.', request_id: 'req-1', retry_after_seconds: 9 },
  }), { status: 429, headers: { 'content-type': 'application/json', 'X-Request-ID': 'req-1' } })
  await assert.rejects(() => request('/api/v1/analyze'), error => {
    assert.equal(error.status, 429)
    assert.equal(error.code, 'RATE_LIMITED')
    assert.equal(error.requestId, 'req-1')
    assert.equal(error.retryAfterSeconds, 9)
    return true
  })
})

test('distinguishes caller cancellation from a timeout', async () => {
  const controller = new AbortController()
  globalThis.fetch = (_url, options) => new Promise((_resolve, reject) => {
    options.signal.addEventListener('abort', () => {
      const error = new Error('aborted')
      error.name = 'AbortError'
      reject(error)
    }, { once: true })
  })
  const requestPromise = request('/api/v1/analyze', { signal: controller.signal, timeoutMs: 1000 })
  controller.abort()
  await assert.rejects(requestPromise, error => {
    assert.equal(error.code, 'CANCELLED')
    return true
  })
})

test('successful API response is parsed as JSON', async () => {
  globalThis.fetch = async () => new Response(JSON.stringify({ status: 'ok' }), { status: 200, headers: { 'content-type': 'application/json' } })
  assert.deepEqual(await request('/health'), { status: 'ok' })
})


test('returns a timeout error when the internal deadline aborts the request', async () => {
  globalThis.fetch = (_url, options) => new Promise((_resolve, reject) => {
    options.signal.addEventListener('abort', () => {
      const error = new Error('aborted')
      error.name = 'AbortError'
      reject(error)
    }, { once: true })
  })
  await assert.rejects(() => request('/api/v1/analyze', { timeoutMs: 10 }), error => {
    assert.equal(error.code, 'TIMEOUT')
    assert.match(error.message, /timed out/i)
    return true
  })
})

test('maps network failures without leaving raw fetch errors', async () => {
  globalThis.fetch = async () => { throw new TypeError('network down') }
  await assert.rejects(() => request('/api/v1/analyze'), error => {
    assert.equal(error.code, 'NETWORK_ERROR')
    assert.match(error.message, /unavailable/i)
    return true
  })
})
