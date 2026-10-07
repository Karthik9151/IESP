export const SECURITY_STATES = new Set(['PHISHING', 'SUSPICIOUS', 'NON-PHISHING', 'REVIEW REQUIRED'])

export function isPriorityEligible(result) {
  return result?.security?.classification === 'NON-PHISHING' && result?.priority != null
}

export function securityDescription(classification) {
  return {
    PHISHING: 'This message shows strong phishing indicators. Do not click links or open attachments.',
    SUSPICIOUS: 'This message contains indicators that deserve caution and manual review.',
    'REVIEW REQUIRED': 'The available evidence is incomplete or conflicting. Treat the message as unsafe until reviewed.',
    'NON-PHISHING': 'The configured policy found no meaningful security concern in this message.',
  }[classification] || 'Unknown security state.'
}

export function stateClass(classification = '') {
  return classification.toLowerCase().replaceAll(' ', '-')
}

export function verdictMeta(classification) {
  return {
    PHISHING: { icon: '!', tone: 'phishing', label: 'Phishing', action: 'Do not interact' },
    SUSPICIOUS: { icon: '!', tone: 'suspicious', label: 'Suspicious', action: 'Review before trusting' },
    'REVIEW REQUIRED': { icon: '?', tone: 'review-required', label: 'Review required', action: 'Manual review first' },
    'NON-PHISHING': { icon: '✓', tone: 'non-phishing', label: 'Non-phishing', action: 'Priority eligible' },
  }[classification] || { icon: '•', tone: '', label: classification || 'Unknown', action: 'Review' }
}

export function priorityLabel(result) {
  if (!isPriorityEligible(result)) return null
  return result.priority?.label || null
}

export function defangText(value = '') {
  return String(value)
    .replace(/https:\/\//gi, 'hxxps://')
    .replace(/http:\/\//gi, 'hxxp://')
    .replace(/ftp:\/\//gi, 'fxp://')
    .replace(/([a-z0-9-]+)\./gi, '$1[.]')
}

export function safeUrl(value = '') {
  return String(value).replace(/^https:\/\//i, 'hxxps://').replace(/^http:\/\//i, 'hxxp://')
}
