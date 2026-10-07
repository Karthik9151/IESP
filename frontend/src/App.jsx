import { useEffect, useMemo, useState } from 'react'
import { api } from './api'
import LoginPage from './features/auth/LoginPage'
import AnalyzePage from './features/analysis/AnalyzePage'
import DashboardPage from './features/dashboard/DashboardPage'
import AnalysisDetailPage from './features/history/AnalysisDetailPage'
import HistoryPage from './features/history/HistoryPage'
import ReportsPage from './features/reports/ReportsPage'
import SettingsPage from './features/settings/SettingsPage'
import HelpPage from './features/help/HelpPage'

const NAV = [
  { id: 'overview', label: 'Dashboard', icon: '◉', key: 'D' },
  { id: 'analyze', label: 'Analyze', icon: '⌁', key: 'A' },
  { id: 'history', label: 'History', icon: '≡', key: 'H' },
  { id: 'reports', label: 'Reports', icon: '▥', key: 'R' },
  { id: 'settings', label: 'Settings', icon: '⚙', key: 'S' },
  { id: 'help', label: 'Help / How it works', icon: '?', key: '?' },
]

function BrandMark() {
  return (
    <div className="brand-mark" aria-hidden="true">
      <svg viewBox="0 0 48 48" role="presentation">
        <path d="M24 3 39 9v11c0 10.5-6.2 19.7-15 24-8.8-4.3-15-13.5-15-24V9l15-6Z" fill="none" stroke="currentColor" strokeWidth="2.2"/>
        <path d="m16 22 5 5 11-12" fill="none" stroke="currentColor" strokeWidth="2.8" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M15 32h18" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
      </svg>
      <span>IESP</span>
    </div>
  )
}

function SystemStatus() {
  const [state, setState] = useState({ health: false, ready: false, loading: true })
  useEffect(() => {
    const controller = new AbortController()
    Promise.allSettled([api.health(controller.signal), api.ready(controller.signal)])
      .then(([health, ready]) => setState({ health: health.status === 'fulfilled' && health.value?.status === 'ok', ready: ready.status === 'fulfilled' && ready.value?.status === 'ready', loading: false }))
    return () => controller.abort()
  }, [])
  const protectedState = state.health && state.ready
  return (
    <span className={'system-status ' + (protectedState ? 'healthy' : state.loading ? 'checking' : 'degraded')} title="Based on the backend /health and /ready checks">
      <span className="status-led" aria-hidden="true"/> {state.loading ? 'Checking system' : protectedState ? 'All systems protected' : 'Service attention'}
    </span>
  )
}

export default function App() {
  const [session, setSession] = useState(null)
  const [authLoading, setAuthLoading] = useState(true)
  const [page, setPage] = useState('overview')
  const [detailId, setDetailId] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const [theme, setTheme] = useState(() => localStorage.getItem('iesp.theme') || 'dark')
  const [showOnboarding, setShowOnboarding] = useState(() => localStorage.getItem('iesp.onboarding.dismissed') !== '1')
  const [shortcutHelp, setShortcutHelp] = useState(false)
  const [search, setSearch] = useState('')
  const [toast, setToast] = useState(null)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => localStorage.getItem('iesp.sidebarCollapsed') === '1')
  const [logoutBusy, setLogoutBusy] = useState(false)

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    localStorage.setItem('iesp.theme', theme)
  }, [theme])

  useEffect(() => {
    api.me().then(setSession).catch(() => setSession(null)).finally(() => setAuthLoading(false))
  }, [])

  useEffect(() => {
    let chord = ''
    const handler = (event) => {
      if ((event.target instanceof HTMLInputElement) || (event.target instanceof HTMLTextAreaElement) || (event.target instanceof HTMLSelectElement)) return
      if (event.key.toLowerCase() === 'g') { chord = 'g'; setTimeout(() => { chord = '' }, 600); return }
      if (chord === 'g') {
        const map = { d: 'overview', a: 'analyze', h: 'history', r: 'reports', s: 'settings' }
        if (map[event.key.toLowerCase()]) navigate(map[event.key.toLowerCase()])
        chord = ''
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  })

  const navigate = (nextPage) => { setDetailId(null); setPage(nextPage) }
  const openAnalysis = (messageId) => { setDetailId(messageId); setPage('detail') }
  const analyzed = () => { setRefreshKey((value) => value + 1); setToast({ type: 'success', message: 'Analysis stored in History.' }) }

  useEffect(() => { localStorage.setItem('iesp.sidebarCollapsed', sidebarCollapsed ? '1' : '0') }, [sidebarCollapsed])

  const dismissOnboarding = () => {
    localStorage.setItem('iesp.onboarding.dismissed', '1')
    setShowOnboarding(false)
  }

  const logout = async () => {
    if (logoutBusy || !window.confirm('Log out of IESP? Your current session will be ended.')) return
    setLogoutBusy(true)
    try { await api.logout() } catch { /* Local auth state is cleared even if the server request fails. */ }
    finally {
      setSession(null)
      setPage('overview')
      setDetailId(null)
      setSearch('')
      setLogoutBusy(false)
    }
  }

  if (authLoading) return <main className="auth-shell"><div className="loading-panel panel"><div className="scan-orb" aria-hidden="true"/><strong>Establishing secure session…</strong><span className="microcopy">Checking authentication state.</span></div></main>
  if (!session) return <LoginPage onAuthenticated={setSession} />

  const currentPage = page === 'detail' ? 'history' : page
  const userName = session.user.email.split('@')[0]

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-brand">
          <BrandMark />
          <div className="brand-copy"><strong>INTELLIGENT EMAIL SECURITY &amp; PRIORITIZATION</strong><span>Cyber Defence Command Centre</span></div>
        </div>
        <div className="topbar-center">
          <label className="search-shell" htmlFor="global-search">
            <span aria-hidden="true">⌕</span>
            <input id="global-search" value={search} onChange={(e) => setSearch(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && search.trim()) { navigate('history') } }} placeholder="Search message ID or sender" />
            <kbd>/</kbd>
          </label>
        </div>
        <div className="topbar-actions">
          <SystemStatus />
          <button className="icon-button" type="button" onClick={() => setTheme((v) => v === 'dark' ? 'light' : 'dark')} aria-label={'Switch to ' + (theme === 'dark' ? 'light' : 'dark') + ' mode'}>{theme === 'dark' ? '☼' : '☾'}</button>
          <button className="user-chip" type="button" onClick={() => navigate('settings')}><span className="avatar">{userName.slice(0,1).toUpperCase()}</span><span className="user-chip-copy"><strong>{userName}</strong><small>{session.workspace.role}</small></span></button>
        </div>
      </header>

      <div className={'app-layout ' + (sidebarCollapsed ? 'sidebar-collapsed' : '')}>
        <aside className={'sidebar ' + (sidebarCollapsed ? 'collapsed' : '')}>
          <button className="sidebar-toggle" type="button" onClick={() => setSidebarCollapsed(v => !v)} aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'} title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}><span aria-hidden="true">{sidebarCollapsed ? '»' : '«'}</span><small>{sidebarCollapsed ? 'Expand' : 'Collapse'}</small></button>
          <div className="workspace-card">
            <span className="eyebrow">Protected workspace</span>
            <strong>{session.workspace.name}</strong>
            <span className="microcopy">Session scoped · HTTP-only cookie</span>
          </div>
          <nav className="primary-nav" aria-label="Primary navigation">
            {NAV.map((item) => (
              <button key={item.id} className={currentPage === item.id ? 'active' : ''} aria-current={currentPage === item.id ? 'page' : undefined} onClick={() => navigate(item.id)}>
                <span className="nav-icon" aria-hidden="true">{item.icon}</span><span>{item.label}</span>{item.key && <kbd>{item.key}</kbd>}
              </button>
            ))}
          </nav>
          <div className="sidebar-callout">
            <div className="callout-icon">✓</div>
            <div><strong>Trust boundary</strong><p>Email HTML, URLs and attachments stay inert and are analysed as untrusted data.</p></div>
          </div>
          <button className="logout-button" type="button" onClick={logout} disabled={logoutBusy} aria-busy={logoutBusy}><span aria-hidden="true">↪</span> {logoutBusy ? 'Signing out…' : 'Logout'}</button>
        </aside>

        <main className="content-shell">
          {page === 'overview' && <DashboardPage refreshKey={refreshKey} onOpenAnalysis={openAnalysis} onAnalyze={() => navigate('analyze')} />}
          {page === 'analyze' && <AnalyzePage onAnalyzed={analyzed} />}
          {page === 'history' && <HistoryPage onOpenAnalysis={openAnalysis} initialSearch={search} />}
          {page === 'detail' && <AnalysisDetailPage messageId={detailId} onBack={() => navigate('history')} />}
          {page === 'reports' && <ReportsPage />}
          {page === 'settings' && <SettingsPage session={session} onToast={setToast} />}
          {page === 'help' && <HelpPage onStartTour={() => { setShowOnboarding(true); navigate('overview') }} />}
        </main>
      </div>

      <nav className="mobile-tabs" aria-label="Mobile navigation">
        {[NAV[0], NAV[1], NAV[2], NAV[5]].map((item) => <button key={item.id} className={currentPage === item.id ? 'active' : ''} onClick={() => navigate(item.id)}><span aria-hidden="true">{item.icon}</span><small>{item.id === 'help' ? 'More' : item.label}</small></button>)}
        <button className="mobile-logout" type="button" onClick={logout} disabled={logoutBusy} aria-busy={logoutBusy}><span aria-hidden="true">↪</span><small>{logoutBusy ? 'Signing out' : 'Logout'}</small></button>
      </nav>

      {showOnboarding && (
        <div className="modal-backdrop" role="presentation">
          <section className="onboarding-modal" role="dialog" aria-modal="true" aria-labelledby="tour-heading">
            <div className="onboarding-art" aria-hidden="true"><div className="radar-ring"/><div className="radar-core">✓</div></div>
            <span className="eyebrow">First-run orientation</span>
            <h2 id="tour-heading">Your first secure scan</h2>
            <p>IESP turns untrusted email into a clear security decision without executing its content.</p>
            <div className="tour-steps">
              <div><span>1</span><strong>Upload or paste</strong><small>Start with a message you want to inspect.</small></div>
              <div><span>2</span><strong>Read the verdict</strong><small>See the decision and the evidence behind it.</small></div>
              <div><span>3</span><strong>Take the safe action</strong><small>Follow the checklist, then find it in History.</small></div>
            </div>
            <div className="modal-actions"><button className="button secondary" onClick={dismissOnboarding}>Skip for now</button><button className="button primary" onClick={() => { dismissOnboarding(); navigate('analyze') }}>Start secure scan</button></div>
          </section>
        </div>
      )}

      {shortcutHelp && (
        <div className="modal-backdrop" role="presentation" onClick={() => setShortcutHelp(false)}>
          <section className="shortcut-modal" role="dialog" aria-modal="true" aria-labelledby="shortcut-heading" onClick={(e) => e.stopPropagation()}>
            <div className="section-title-row"><div><span className="eyebrow">Keyboard</span><h2 id="shortcut-heading">Shortcuts</h2></div><button className="icon-button" onClick={() => setShortcutHelp(false)} aria-label="Close shortcuts">×</button></div>
            <div className="shortcut-list">{[['/','Focus global search'],['g d','Dashboard'],['g a','Analyze'],['g h','History'],['g r','Reports'],['g s','Settings'],['?','Open this list']].map(([key, label]) => <div key={key}><kbd>{key}</kbd><span>{label}</span></div>)}</div>
          </section>
        </div>
      )}

      {toast && <div className={'toast ' + toast.type} role="status" onAnimationEnd={() => setToast(null)}><span>{toast.type === 'success' ? '✓' : '!'}</span>{toast.message}</div>}
    </div>
  )
}
