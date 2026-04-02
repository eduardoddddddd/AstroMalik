import { type FormEvent, useState } from 'react'
import { fetchNatalChart, saveChart } from '../api/astromalik'
import type { NatalChartResponse } from '../types/natal'
import type { BirthChartDraft, SavedChartRow } from '../types/chart'
import { initialDraft } from '../types/chart'
import { PlaceSearch } from './PlaceSearch'
import { SavedChartsList } from './SavedChartsList'
import './BirthChartForm.css'

export type { BirthChartDraft } from '../types/chart'

type Props = {
  onChartComputed?: (data: NatalChartResponse | null) => void
}
type BirthDateParts = { y: string; m: string; d: string }

const HOURS_24 = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, '0'))
const MINUTES_60 = Array.from({ length: 60 }, (_, i) => String(i).padStart(2, '0'))
const DAYS_31 = Array.from({ length: 31 }, (_, i) => String(i + 1).padStart(2, '0'))
const MONTHS_12 = Array.from({ length: 12 }, (_, i) => String(i + 1).padStart(2, '0'))
const YEARS = Array.from({ length: 141 }, (_, i) => String(2100 - i))

/** Normaliza "HH:MM" o "HH:MM:SS" desde BD. */
function parseTime24(s: string): { h: string; m: string } {
  const parts = s.trim().split(':')
  let h = parseInt(parts[0] ?? '12', 10)
  let m = parseInt(parts[1] ?? '0', 10)
  if (Number.isNaN(h)) h = 12
  if (Number.isNaN(m)) m = 0
  h = Math.min(23, Math.max(0, h))
  m = Math.min(59, Math.max(0, m))
  return { h: String(h).padStart(2, '0'), m: String(m).padStart(2, '0') }
}

function parseBirthDateIso(s: string): { y: string; m: string; d: string } {
  const p = s.trim().split('-')
  if (p.length === 3 && p[0] && p[1] && p[2]) {
    return { y: p[0], m: p[1], d: p[2] }
  }
  return { y: '', m: '', d: '' }
}

function composeBirthDateIso(y: string, m: string, d: string): string {
  if (!y || !m || !d) return ''
  return `${y}-${m}-${d}`
}

export function BirthChartForm({ onChartComputed }: Props) {
  const [draft, setDraft] = useState<BirthChartDraft>(initialDraft)
  const [birthDateParts, setBirthDateParts] = useState<BirthDateParts>(
    parseBirthDateIso(initialDraft.birthDate),
  )
  const [status, setStatus] = useState('')
  const [savedRefreshKey, setSavedRefreshKey] = useState(0)
  const [computing, setComputing] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setStatus('')
    if (!draft.birthDate.trim()) {
      setStatus('Indica la fecha de nacimiento.')
      onChartComputed?.(null)
      return
    }
    if (draft.latitude == null || draft.longitude == null) {
      setStatus('Elige un lugar con coordenadas en la lista.')
      onChartComputed?.(null)
      return
    }
    if (!draft.timezone.trim()) {
      setStatus('Indica la zona horaria IANA (ej. Europe/Madrid).')
      onChartComputed?.(null)
      return
    }
    setComputing(true)
    try {
      const res = await fetchNatalChart(draft)
      onChartComputed?.(res)
      setStatus('Carta calculada (Placidus, UT vía zoneinfo + tzdata).')
    } catch (err) {
      onChartComputed?.(null)
      setStatus(err instanceof Error ? err.message : 'Error al calcular la carta.')
    } finally {
      setComputing(false)
    }
  }

  function handleReset() {
    setDraft(initialDraft)
    setBirthDateParts(parseBirthDateIso(initialDraft.birthDate))
    setStatus('')
    onChartComputed?.(null)
  }

  async function handleSaveCard() {
    setStatus('')
    if (!draft.birthDate.trim()) {
      setStatus('Indica la fecha de nacimiento antes de guardar.')
      return
    }
    if (draft.latitude == null || draft.longitude == null) {
      setStatus(
        'Busca el lugar y elige una ciudad de la lista para fijar latitud y longitud.',
      )
      return
    }
    try {
      await saveChart(draft)
      setStatus('Carta guardada correctamente.')
      setSavedRefreshKey((k) => k + 1)
    } catch (e) {
      setStatus(e instanceof Error ? e.message : 'No se pudo guardar.')
    }
  }

  function handleLoadSaved(row: SavedChartRow) {
    const nextParts = parseBirthDateIso(row.birth_date)
    setDraft({
      profileName: row.profile_name,
      birthDate: row.birth_date,
      birthTime: row.birth_time,
      timezone: row.timezone,
      placeLabel: row.place_label,
      latitude: row.latitude,
      longitude: row.longitude,
    })
    setBirthDateParts(nextParts)
    setStatus('Carta cargada desde la base local (user.db).')
  }

  return (
    <div className="birth-chart-block">
      <form className="birth-form" onSubmit={handleSubmit} noValidate>
        <div className="birth-form__field">
          <label className="birth-form__label" htmlFor="profileName">
            Nombre del perfil
          </label>
          <input
            id="profileName"
            className="birth-form__input"
            type="text"
            autoComplete="name"
            placeholder="Ej. María — consulta trabajo"
            value={draft.profileName}
            onChange={(e) =>
              setDraft((d) => ({ ...d, profileName: e.target.value }))
            }
          />
        </div>

        <div className="birth-form__row">
          <div className="birth-form__field">
            <span className="birth-form__label" id="birthDate-label">
              Fecha de nacimiento
            </span>
            <div className="birth-form__time24" role="group" aria-labelledby="birthDate-label">
              <select
                id="birthDay"
                className="birth-form__input birth-form__select"
                aria-label="Día"
                value={birthDateParts.d}
                onChange={(e) => {
                  const d0 = e.target.value
                  setBirthDateParts((parts) => {
                    const next = { ...parts, d: d0 }
                    setDraft((curr) => ({
                      ...curr,
                      birthDate: composeBirthDateIso(next.y, next.m, next.d),
                    }))
                    return next
                  })
                }}
              >
                <option value="">DD</option>
                {DAYS_31.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
              <span className="birth-form__time-sep" aria-hidden>
                /
              </span>
              <select
                id="birthMonth"
                className="birth-form__input birth-form__select"
                aria-label="Mes"
                value={birthDateParts.m}
                onChange={(e) => {
                  const m0 = e.target.value
                  setBirthDateParts((parts) => {
                    const next = { ...parts, m: m0 }
                    setDraft((curr) => ({
                      ...curr,
                      birthDate: composeBirthDateIso(next.y, next.m, next.d),
                    }))
                    return next
                  })
                }}
              >
                <option value="">MM</option>
                {MONTHS_12.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
              <span className="birth-form__time-sep" aria-hidden>
                /
              </span>
              <select
                id="birthYear"
                className="birth-form__input birth-form__select"
                aria-label="Año"
                value={birthDateParts.y}
                onChange={(e) => {
                  const y0 = e.target.value
                  setBirthDateParts((parts) => {
                    const next = { ...parts, y: y0 }
                    setDraft((curr) => ({
                      ...curr,
                      birthDate: composeBirthDateIso(next.y, next.m, next.d),
                    }))
                    return next
                  })
                }}
              >
                <option value="">YYYY</option>
                {YEARS.map((y) => (
                  <option key={y} value={y}>
                    {y}
                  </option>
                ))}
              </select>
            </div>
            <p className="birth-form__hint">
              Formato fijo sin ambigüedad: <code>DD/MM/YYYY</code> (internamente se guarda en{' '}
              <code>YYYY-MM-DD</code>).
            </p>
          </div>
          <div className="birth-form__field">
            <span className="birth-form__label" id="birthTime-label">
              Hora local (24 h)
            </span>
            <div
              className="birth-form__time24"
              role="group"
              aria-labelledby="birthTime-label"
            >
              <select
                id="birthHour"
                className="birth-form__input birth-form__select"
                aria-label="Hora en formato 24 horas"
                value={parseTime24(draft.birthTime).h}
                onChange={(e) => {
                  const h = e.target.value
                  setDraft((d) => {
                    const { m } = parseTime24(d.birthTime)
                    return { ...d, birthTime: `${h}:${m}` }
                  })
                }}
              >
                {HOURS_24.map((h) => (
                  <option key={h} value={h}>
                    {h}
                  </option>
                ))}
              </select>
              <span className="birth-form__time-sep" aria-hidden>
                :
              </span>
              <select
                id="birthMinute"
                className="birth-form__input birth-form__select"
                aria-label="Minutos"
                value={parseTime24(draft.birthTime).m}
                onChange={(e) => {
                  const m = e.target.value
                  setDraft((d) => {
                    const { h } = parseTime24(d.birthTime)
                    return { ...d, birthTime: `${h}:${m}` }
                  })
                }}
              >
                {MINUTES_60.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>
            <p className="birth-form__hint">
              Formato fijo 24 h (no depende del idioma del sistema).
            </p>
          </div>
        </div>

        <div className="birth-form__field">
          <label className="birth-form__label" htmlFor="timezone">
            Zona horaria (IANA)
          </label>
          <input
            id="timezone"
            className="birth-form__input"
            type="text"
            placeholder="Europe/Madrid"
            value={draft.timezone}
            onChange={(e) =>
              setDraft((d) => ({ ...d, timezone: e.target.value.trim() }))
            }
          />
          <p className="birth-form__hint">
            Identificador estándar (ej. <code>America/Bogota</code>) para el
            offset histórico correcto.
          </p>
        </div>

        <PlaceSearch
          placeLabel={draft.placeLabel}
          onPlaceLabelChange={(v) =>
            setDraft((d) => ({
              ...d,
              placeLabel: v,
              latitude: null,
              longitude: null,
            }))
          }
          onPick={(p) =>
            setDraft((d) => ({
              ...d,
              placeLabel: p.label,
              latitude: p.lat,
              longitude: p.lon,
            }))
          }
        />

        {draft.latitude != null && draft.longitude != null && (
          <p className="birth-form__coords">
            Coordenadas:{' '}
            <strong>
              {draft.latitude.toFixed(5)}° lat · {draft.longitude.toFixed(5)}°
              lon
            </strong>
          </p>
        )}

        <div className="birth-form__actions">
          <button
            type="submit"
            className="birth-form__btn birth-form__btn--primary"
            disabled={computing}
          >
            {computing ? 'Calculando…' : 'Calcular carta'}
          </button>
          <button
            type="button"
            className="birth-form__btn birth-form__btn--accent"
            onClick={handleSaveCard}
          >
            Guardar carta
          </button>
          <button
            type="button"
            className="birth-form__btn"
            onClick={handleReset}
          >
            Limpiar
          </button>
        </div>
        <p className="birth-form__status" role="status">
          {status}
        </p>
      </form>

      <div className="birth-chart-block__saved">
        <h3 className="birth-chart-block__saved-title">Cartas guardadas</h3>
        <SavedChartsList
          refreshKey={savedRefreshKey}
          onLoad={handleLoadSaved}
        />
      </div>
    </div>
  )
}
