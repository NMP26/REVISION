import { FormEvent, useState } from 'react'
import { ApiError, ensureCsrf, login } from '../lib/api'

export function LoginPage({ onLogin }: { onLogin: () => Promise<void> }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault(); setError(''); setLoading(true)
    try { await ensureCsrf(); await login(email, password); await onLogin() }
    catch (caught) { setError(caught instanceof ApiError ? caught.message : 'Connexion impossible.') }
    finally { setLoading(false) }
  }

  return <main className="auth-shell"><form className="card form-card" onSubmit={submit}>
    <p className="eyebrow">REVISIONPRIX · LOT 1A</p><h1>Connexion</h1>
    <p className="muted">Accédez à vos sociétés autorisées.</p>
    {error && <div className="alert error" role="alert">{error}</div>}
    <label>Email<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" required /></label>
    <label>Mot de passe<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required /></label>
    <button className="primary" disabled={loading}>{loading ? 'Connexion…' : 'Se connecter'}</button>
  </form></main>
}
