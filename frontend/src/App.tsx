import { useEffect, useState } from 'react'
import { Link, Navigate, Outlet, Route, Routes, useNavigate } from 'react-router-dom'
import { ApiError, currentUser, ensureCsrf, logout, User } from './lib/api'
import { LoginPage } from './auth/LoginPage'
import { CompaniesPage, CompanyCreatePage, CompanyDetailPage } from './companies/CompaniesPage'
import { MarketCreatePage, MarketDetailPage, MarketsPage } from './markets/MarketsPage'

function Protected({ user }: { user: User | null }) { return user ? <Outlet /> : <Navigate to="/login" replace /> }

function Layout({ user, onLogout }: { user: User; onLogout: () => Promise<void> }) {
  const navigate = useNavigate(); return <div className="app-shell"><header className="topbar"><div className="topbar-main"><Link to="/app/companies" className="brand">Révision<span>Prix</span></Link><nav><Link to="/app/companies">Sociétés</Link><Link to="/app/markets">Marchés</Link></nav></div><div className="user-menu"><span>{user.first_name} {user.last_name}</span><button className="link-button" onClick={async () => { await onLogout(); navigate('/login') }}>Déconnexion</button></div></header><main className="content"><Outlet /></main></div>
}

export default function App() {
  const [user, setUser] = useState<User | null>(null); const [loading, setLoading] = useState(true)
  useEffect(() => {
    const expire = () => setUser(null)
    window.addEventListener('auth-expired', expire)
    ensureCsrf().then(() => currentUser()).then(setUser).catch((error) => { if (!(error instanceof ApiError && error.status === 401)) console.error(error) }).finally(() => setLoading(false))
    return () => window.removeEventListener('auth-expired', expire)
  }, [])
  if (loading) return <p className="state">Chargement…</p>
  return <Routes><Route path="/login" element={user ? <Navigate to="/app/companies" replace /> : <LoginPage onLogin={async () => setUser(await currentUser())} />} /><Route element={<Protected user={user} />}><Route element={<Layout user={user!} onLogout={async () => { await logout(); setUser(null) }} />}><Route path="/app/companies" element={<CompaniesPage />} /><Route path="/app/companies/new" element={<CompanyCreatePage />} /><Route path="/app/companies/:id" element={<CompanyDetailPage />} /><Route path="/app/companies/:id/edit" element={<CompanyDetailPage />} /><Route path="/app/markets" element={<MarketsPage />} /><Route path="/app/markets/new" element={<MarketCreatePage />} /><Route path="/app/markets/:id" element={<MarketDetailPage />} /><Route path="/app/markets/:id/edit" element={<MarketDetailPage />} /></Route></Route><Route path="*" element={<Navigate to={user ? '/app/companies' : '/login'} replace />} /></Routes>
}
