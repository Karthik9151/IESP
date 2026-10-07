export const SECURITY_STATES = new Set(['PHISHING', 'SUSPICIOUS', 'NON-PHISHING', 'REVIEW REQUIRED'])

export function isPriorityEligible(result) {
  return result?.security?.classification === 'NON-PHISHING' && result?.priority != null
}

export function securityDescription(classification) {
  return {
    PHISHING: 'Strong phishing evidence was detected. Do not trust the message.',
    SUSPICIOUS: 'Security indicators need caution or manual review.',
    'REVIEW REQUIRED': 'Evidence is incomplete or conflicting. Treat the message as unsafe until reviewed.',
    'NON-PHISHING': 'No meaningful security concern was detected by the configured policy.',
  }[classification] || 'Unknown security state.'
}

export function stateClass(classification = '') {
  return classification.toLowerCase().replaceAll(' ', '-')
}
