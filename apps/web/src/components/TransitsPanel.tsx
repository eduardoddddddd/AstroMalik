import { useEffect, useMemo, useState, type CSSProperties } from 'react'
import { fetchTransitPeriod } from '../api/astromalik'
import type { NatalChartResponse } from '../types/natal'
import type { TransitEvent, TransitPeriodResponse } from '../types/transits'
import './TransitsPanel.css'

type Props = {
  natal: NatalChartResponse | null
}

type PeriodDraft = {
  fromDate: string
  toDate: string
  excludeMoon: boolean
}

function formatDate(isoDate: string): string {
  const [year, month, day] = isoDate.split('-')
  if (!year || !month || !day) return isoDate
  return `${day}/${month}/${year}`
}

function addMonths(isoDate: string, months: number): string {
  const base = new Date(`${isoDate}T12:00:00`)
  if (Number.isNaN(base.getTime())) return isoDate
  base.setMonth(base.getMonth() + months)
  return base.toISOString().slice(0, 10)
}

function daysFromStart(startDate: string, targetDate: string): number {
  const start = new Date(`${startDate}T00:00:00`)
  const target = new Date(`${targetDate}T00:00:00`)
  return Math.round((target.getTime() - start.getTime()) / 86400000)
}

function buildStarString(stars: number): string {
  return `${'★'.repeat(stars)}${'☆'.repeat(Math.max(0, 5 - stars))}`
}

export function TransitsPanel({ natal }: Props) {
  const today = useMemo(() => new Date().toISOString().slice(0, 10), [])
  const [draft, setDraft] = useState<PeriodDraft>(() => ({
    fromDate: today,
    toDate: addMonths(today, 3),
    excludeMoon: true,
  }))
  const [status, setStatus] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<TransitPeriodResponse | null>(null)
  const [minStars, setMinStars] = useState(1)

  useEffect(() => {
    setResult(null)
    setStatus('')
  }, [natal])

  const filteredEvents = useMemo(() => {
    if (!result) return []
    return result.events.filter((event) => event.stars >= minStars)
  }, [minStars, result])

  async function handleCalculate() {
    if (!natal) {
      setStatus('Primero calcula una carta natal.')
      return
    }
    if (!draft.fromDate || !draft.toDate) {
      setStatus('Indica ambas fechas del periodo.')
      return
    }

    setLoading(true)
    setStatus('')
    try {
      const next = await fetchTransitPeriod({
        birthDate: natal.input.birth_date,
        birthTime: natal.input.birth_time,
        timezone: natal.input.timezone,
        latitude: natal.input.latitude,
        longitude: natal.input.longitude,
        fromDate: draft.fromDate,
        toDate: draft.toDate,
        excludeMoon: draft.excludeMoon,
      })
      setResult(next)
      setMinStars(1)
      setStatus(
        `${next.summary.total_events} eventos, ${next.summary.events_with_text} con texto del corpus.`,
      )
    } catch (error) {
      setResult(null)
      setStatus(
        error instanceof Error ? error.message : 'No se pudo calcular el periodo.',
      )
    } finally {
      setLoading(false)
    }
  }

  function applyPreset(months: number) {
    setDraft((current) => ({
      ...current,
      toDate: addMonths(current.fromDate || today, months),
    }))
  }

  const topTimeline = filteredEvents.slice(0, 18)

  return (
    <section className="transits-panel" aria-labelledby="transits-title">
      <div className="transits-panel__head">
        <div>
          <h3 id="transits-title" className="transits-panel__title">
            Transitos por periodo
          </h3>
          <p className="transits-panel__subtitle">
            Rango diario con importancia, fecha exacta y timeline visual de los
            eventos mas fuertes.
          </p>
        </div>
      </div>

      {!natal ? (
        <p className="transits-panel__placeholder">
          Este panel se activa despues de calcular la carta natal.
        </p>
      ) : (
        <>
          <div className="transits-panel__form">
            <label className="transits-panel__field">
              <span>Desde</span>
              <input
                type="date"
                value={draft.fromDate}
                onChange={(event) =>
                  setDraft((current) => ({
                    ...current,
                    fromDate: event.target.value,
                  }))
                }
              />
            </label>
            <label className="transits-panel__field">
              <span>Hasta</span>
              <input
                type="date"
                value={draft.toDate}
                onChange={(event) =>
                  setDraft((current) => ({
                    ...current,
                    toDate: event.target.value,
                  }))
                }
              />
            </label>
            <label className="transits-panel__checkbox">
              <input
                type="checkbox"
                checked={draft.excludeMoon}
                onChange={(event) =>
                  setDraft((current) => ({
                    ...current,
                    excludeMoon: event.target.checked,
                  }))
                }
              />
              <span>Excluir Luna</span>
            </label>
            <button
              type="button"
              className="transits-panel__button transits-panel__button--primary"
              onClick={handleCalculate}
              disabled={loading}
            >
              {loading ? 'Calculando...' : 'Calcular periodo'}
            </button>
          </div>

          <div className="transits-panel__presets">
            {[1, 3, 6, 12, 36].map((months) => (
              <button
                key={months}
                type="button"
                className="transits-panel__button"
                onClick={() => applyPreset(months)}
              >
                {months === 1 ? '1 mes' : months === 12 ? '1 ano' : `${months} meses`}
              </button>
            ))}
          </div>

          <p className="transits-panel__status">{status}</p>

          {result && (
            <>
              <div className="transits-panel__summary">
                <span>
                  {formatDate(result.input.from_date)} {'->'}{' '}
                  {formatDate(result.input.to_date)}
                </span>
                <span>{result.summary.days_total} dias</span>
                <span>{result.summary.total_events} eventos</span>
                <span>{result.summary.events_with_text} con texto</span>
              </div>

              <div className="transits-panel__filters">
                <span>Mostrar:</span>
                {[1, 2, 3, 4, 5].map((stars) => (
                  <button
                    key={stars}
                    type="button"
                    className={`transits-panel__filter${
                      minStars === stars ? ' transits-panel__filter--active' : ''
                    }`}
                    onClick={() => setMinStars(stars)}
                  >
                    {stars}+ estrellas
                  </button>
                ))}
              </div>

              {topTimeline.length > 0 && (
                <div className="transits-timeline">
                  <div className="transits-timeline__header">
                    <span>Timeline de importancia</span>
                    <span>Top {topTimeline.length}</span>
                  </div>
                  <div className="transits-timeline__list">
                    {topTimeline.map((event) => {
                      const startOffset = daysFromStart(
                        result.input.from_date,
                        event.from_date,
                      )
                      const endOffset = daysFromStart(
                        result.input.from_date,
                        event.to_date,
                      )
                      const exactOffset = daysFromStart(
                        result.input.from_date,
                        event.exact_date,
                      )
                      const totalDays = Math.max(result.summary.days_total, 1)
                      const left = `${(startOffset / totalDays) * 100}%`
                      const width = `${Math.max(
                        2,
                        ((endOffset - startOffset + 1) / totalDays) * 100,
                      )}%`
                      const exact = `${(exactOffset / totalDays) * 100}%`

                      return (
                        <div key={`${event.transit_key}-${event.exact_date}`} className="transits-timeline__row">
                          <div className="transits-timeline__label">
                            <strong>{event.transit_label}</strong>{' '}
                            {event.aspect_label} {event.natal_label}
                          </div>
                          <div className="transits-timeline__track">
                            <div
                              className="transits-timeline__bar"
                              style={{ left, width, backgroundColor: event.color }}
                            />
                            <div
                              className="transits-timeline__exact"
                              style={{ left: exact }}
                            />
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              <div className="transits-results">
                {filteredEvents.length === 0 ? (
                  <p className="transits-panel__placeholder">
                    No hay eventos para el filtro actual.
                  </p>
                ) : (
                  filteredEvents.map((event) => (
                    <TransitCard key={cardKey(event)} event={event} />
                  ))
                )}
              </div>
            </>
          )}
        </>
      )}
    </section>
  )
}

function cardKey(event: TransitEvent): string {
  return [
    event.transit_key,
    event.aspect_key,
    event.natal_key,
    event.exact_date,
    event.from_date,
  ].join(':')
}

function TransitCard({ event }: { event: TransitEvent }) {
  return (
    <article
      className="transit-card"
      style={{ '--transit-accent': event.color } as CSSProperties}
    >
      <div className="transit-card__top">
        <div>
          <p className="transit-card__eyebrow">
            {buildStarString(event.stars)} · score {event.score.toFixed(1)}
          </p>
          <h4 className="transit-card__title">
            {event.transit_label}
            {event.retrograde_on_exact ? ' R' : ''} {event.aspect_label}{' '}
            {event.natal_label}
          </h4>
        </div>
        <div className="transit-card__orb">orbe {event.min_orb.toFixed(2)}°</div>
      </div>

      <p className="transit-card__dates">
        Exacto <strong>{formatDate(event.exact_date)}</strong> · activo{' '}
        {formatDate(event.from_date)} {'->'} {formatDate(event.to_date)} (
        {event.active_days} dias)
      </p>

      {event.text ? (
        <div className="transit-card__text">
          {event.text.split('\n').filter(Boolean).map((paragraph, index) => (
            <p key={`${event.exact_date}-${index}`}>{paragraph}</p>
          ))}
          {event.source && (
            <p className="transit-card__source">Fuente: {event.source}</p>
          )}
        </div>
      ) : (
        <p className="transit-card__missing">
          Sin texto asociado en el corpus para esta combinacion.
        </p>
      )}
    </article>
  )
}
