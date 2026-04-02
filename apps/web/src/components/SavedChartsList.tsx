import { useCallback, useEffect, useState } from 'react'
import { deleteSavedChart, fetchSavedCharts } from '../api/astromalik'
import type { SavedChartRow } from '../types/chart'
import './SavedChartsList.css'

type Props = {
  refreshKey: number
  onLoad: (row: SavedChartRow) => void
}

export function SavedChartsList({ refreshKey, onLoad }: Props) {
  const [rows, setRows] = useState<SavedChartRow[]>([])
  const [err, setErr] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      setErr(null)
      const list = await fetchSavedCharts()
      setRows(list)
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Error al cargar')
      setRows([])
    }
  }, [])

  useEffect(() => {
    load()
  }, [load, refreshKey])

  async function handleDelete(id: number) {
    if (!window.confirm('¿Eliminar esta carta guardada?')) return
    try {
      await deleteSavedChart(id)
      await load()
    } catch {
      setErr('No se pudo eliminar')
    }
  }

  if (err) {
    return <p className="saved-list__err">{err}</p>
  }

  if (rows.length === 0) {
    return (
      <p className="saved-list__empty">
        Aún no hay cartas guardadas. Completa el formulario, elige lugar con
        coordenadas y pulsa <strong>Guardar carta</strong>.
      </p>
    )
  }

  return (
    <ul className="saved-list" aria-label="Cartas guardadas">
      {rows.map((row) => (
        <li key={row.id} className="saved-list__item">
          <div className="saved-list__text">
            <span className="saved-list__name">
              {row.profile_name || `Carta #${row.id}`}
            </span>
            <span className="saved-list__meta">
              {row.birth_date} · {row.place_label || 'sin lugar'}
            </span>
          </div>
          <div className="saved-list__actions">
            <button
              type="button"
              className="saved-list__btn"
              onClick={() => onLoad(row)}
            >
              Cargar
            </button>
            <button
              type="button"
              className="saved-list__btn saved-list__btn--danger"
              onClick={() => handleDelete(row.id)}
            >
              Borrar
            </button>
          </div>
        </li>
      ))}
    </ul>
  )
}
