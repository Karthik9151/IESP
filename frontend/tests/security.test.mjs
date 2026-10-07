import test from 'node:test'
import assert from 'node:assert/strict'
import { isPriorityEligible, securityDescription } from '../src/lib/security.js'

test('priority is only eligible for NON-PHISHING results with a priority object', () => {
  assert.equal(isPriorityEligible({ security: { classification: 'NON-PHISHING' }, priority: { label: 'P2' } }), true)
  assert.equal(isPriorityEligible({ security: { classification: 'PHISHING' }, priority: { label: 'P1' } }), false)
  assert.equal(isPriorityEligible({ security: { classification: 'SUSPICIOUS' }, priority: { label: 'P1' } }), false)
  assert.equal(isPriorityEligible({ security: { classification: 'REVIEW REQUIRED' }, priority: { label: 'P2' } }), false)
})

test('security explanations cover every supported state', () => {
  for (const state of ['PHISHING','SUSPICIOUS','NON-PHISHING','REVIEW REQUIRED']) assert.ok(securityDescription(state).length > 20)
})


test('scans frontend source for unsafe HTML rendering, navigation, and browser credential shortcuts', async () => {
  const fs = await import('node:fs/promises')
  const path = await import('node:path')
  const root = path.resolve(new URL('../src/', import.meta.url).pathname)
  const forbidden = [
    'dangerouslySetInnerHTML',
    '<iframe',
    'window.open(',
    'location.href',
    'location.assign(',
    'location.replace(',
    'document.write(',
    'eval(',
    'new Function(',
    'VITE_API_KEY',
    'X-API-Key',
    'Authorization: Bearer',
  ]
  const externalImage = /<img[^>]+src\s*=\s*["'](?:https?:|\/\/)/i

  async function walk(dir) {
    const entries = await fs.readdir(dir, { withFileTypes: true })
    const files = []
    for (const entry of entries) {
      const target = path.join(dir, entry.name)
      if (entry.isDirectory()) files.push(...await walk(target))
      else if (/\.(m?js|jsx)$/.test(entry.name)) files.push(target)
    }
    return files
  }

  for (const file of await walk(root)) {
    const source = await fs.readFile(file, 'utf8')
    for (const token of forbidden) assert.equal(source.includes(token), false, `${file} contains forbidden token: ${token}`)
    assert.equal(externalImage.test(source), false, `${file} contains an external image URL`)
  }
})


test('does not label model margins as probabilities and exposes the required result metadata', async () => {
  const fs = await import('node:fs/promises')
  const path = await import('node:path')
  const file = path.resolve(new URL('../src/features/analysis/ResultPanel.jsx', import.meta.url).pathname)
  const source = await fs.readFile(file, 'utf8')
  for (const label of [
    'Security verdict',
    'Policy risk score',
    'not a probability',
    'Model decision margin',
    'Security reasons',
    'Priority assessment',
    'Model metadata',
    'Analysis time',
    'Request ID',
  ]) assert.equal(source.includes(label), true, `missing result label: ${label}`)
  const probabilityMentions = source.match(/probability/gi) || []
  assert.equal(probabilityMentions.length, 1)
})
