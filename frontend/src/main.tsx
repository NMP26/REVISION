import { StrictMode, useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'

type Health = { status: string; database?: { status: string }; migrations?: { status: string } }

function App() {
  const [health, setHealth] = useState<Health | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    fetch('/api/health/').then((response) => response.json()).then(setHealth).catch(() => setError(true))
  }, [])

  const operational = health?.status === 'ok' && health.database?.status === 'ok'
  return (
    <main className="page-shell">
      <section className="status-card" aria-labelledby="page-title">
        <div className="eyebrow">LOT 0 · FONDATION</div>
        <h1 id="page-title">Révision des Prix</h1>
        <p className="intro">Fondation technique de l’application de gestion des révisions de prix.</p>
        <div className="status-list">
          <div className="status-row"><span>État de l’application</span><strong className={operational ? 'ok' : 'pending'}>{operational ? 'opérationnelle' : 'vérification…'}</strong></div>
          <div className="status-row"><span>Backend</span><strong className={health ? 'ok' : error ? 'error' : 'pending'}>{health ? 'opérationnel' : error ? 'indisponible' : 'vérification…'}</strong></div>
          <div className="status-row"><span>Base de données</span><strong className={health?.database?.status === 'ok' ? 'ok' : 'pending'}>{health?.database?.status === 'ok' ? 'opérationnelle' : 'vérification…'}</strong></div>
        </div>
      </section>
    </main>
  )
}

createRoot(document.getElementById('root')!).render(<StrictMode><App /></StrictMode>)
