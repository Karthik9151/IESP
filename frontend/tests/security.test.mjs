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
