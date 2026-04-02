import { useEffect, useState } from 'react'
import './ApiStatus.css'

type Health = { status: string; service: string; corpus_db: boolean }
type Stats = { total?: number; by_type?: Record<string, number>; error?: string }

export function ApiStatus() {
  const [health, setHealth] = useState<Health | null>(null)
  const [stats, setStats] = useState<Stats | null>(null)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const [h, s] = await Promise.all([
          fetch('/api/health').then((r) => r.json()),
          fetch('/api/corpus/stats').then((r) => r.json()),
        ])
        if (!cancelled) {
          setHealth(h as Health)
          setStats(s as Stats)
          setErr(null)
        }
      } catch (e) {
        if (!cancelled) {
          setErr(e instanceof Error ? e.message : 'Error de red')
          setHealth(null)
          setStats(null)
        }
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [])

  if (err) {
    return (
      <div className="api-status api-status--error" role="status">
        API no disponible ({err}). ¿Está uvicorn en el puerto configurado?
      </div>
    )
  }

  if (!health) {
    return (
      <div className="api-status api-status--pending" role="status">
        Conectando con la API…
      </div>
    )
  }

  return (
    <div className="api-status api-status--ok" role="status">
      <span className="api-status__dot" aria-hidden />
      API <strong>{health.status}</strong>
      {stats?.total != null && (
        <>
          {' · '}
          corpus <strong>{stats.total}</strong> textos
        </>
      )}
      {health.corpus_db === false && ' · aviso: corpus.db no localizado'}
    </div>
  )
}
