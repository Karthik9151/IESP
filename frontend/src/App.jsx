import { useEffect, useState } from 'react'
import { api } from './api'
import LoginPage from './features/auth/LoginPage'
import AnalyzePage from './features/analysis/AnalyzePage'
import DashboardPage from './features/dashboard/DashboardPage'
import AnalysisDetailPage from './features/history/AnalysisDetailPage'
import HistoryPage from './features/history/HistoryPage'
import ReportsPage from './features/reports/ReportsPage'
import SettingsPage from './features/settings/SettingsPage'

const NAV = [
  { id: 'overview', label: 'Overview' },
  { id: 'analyze', label: 'Analyze' },
  { id: 'history', label: 'History' },
  { id: 'reports', label: 'Reports' },
  { id: 'settings', label: 'Settings' },
]

export default function App() {
  const [session, setSession] = useState(null)
  const [authLoading, setAuthLoading] = useState(true)
  const [page, setPage] = useState('overview')
  const [detailId, setDetailId] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    api.me().then(setSession).catch(() => setSession(null)).finally(() => setAuthLoading(false))
  }, [])

  if (authLoading) return <main className="auth-shell"><div className="loading-panel panel" role="status">Checking your session…</div></main>
  if (!session) return <LoginPage onAuthenticated={setSession} />

  const navigate = (nextPage) => {
    setDetailId(null)
    setPage(nextPage)
  }
  const openAnalysis = (messageId) => {
    setDetailId(messageId)
    setPage('detail')
  }
  const analyzed = () => setRefreshKey((value) => value + 1)

  const logout = async () => {
    try { await api.logout() } finally { setSession(null); setPage('overview'); setDetailId(null) }
  }

  const currentPage = page === 'detail' ? 'history' : page

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-brand"><div className="brand-mark small">IESP</div><div><strong>IESP</strong><span>Intelligent Email Security Platform</span></div></div>
        <div className="topbar-actions"><span className="desktop-user">{session.user.email}</span><button className="button secondary compact-button" onClick={logout}>Logout</button></div>
      </header>
      <div className="app-layout">
        <aside className="sidebar">
          <div className="workspace-card"><span className="eyebrow">Workspace</span><strong>{session.workspace.name}</strong><span className="microcopy">{session.workspace.role}</span></div>
          <nav className="primary-nav" aria-label="Primary navigation">
            {NAV.map((item) => <button key={item.id} className={currentPage === item.id ? 'active' : ''} aria-current={currentPage === item.id ? 'page' : undefined} onClick={() => navigate(item.id)}>{item.label}</button>)}
          </nav>
          <div className="sidebar-note"><span className="eyebrow">Trust boundary</span><p>Email bodies, HTML, URLs, and attachment names are treated as untrusted analysis data.</p></div>
        </aside>
        <main className="content-shell">
          {page === 'overview' && <DashboardPage refreshKey={refreshKey} onOpenAnalysis={openAnalysis} />}
          {page === 'analyze' && <AnalyzePage onAnalyzed={analyzed} />}
          {page === 'history' && <HistoryPage onOpenAnalysis={openAnalysis} />}
          {page === 'detail' && <AnalysisDetailPage messageId={detailId} onBack={() => navigate('history')} />}
          {page === 'reports' && <ReportsPage />}
          {page === 'settings' && <SettingsPage session={session} />}
        </main>
      </div>
    </div>
  )
}
