import type { BirthChartDraft, SavedChartRow } from '../types/chart'
import type { NatalChartResponse } from '../types/natal'
import type { TransitPeriodResponse } from '../types/transits'

export type PlaceResult = {
  label: string
  lat: number
  lon: number
  source: string
}

export async function searchPlaces(q: string): Promise<PlaceResult[]> {
  const params = new URLSearchParams({ q })
  const r = await fetch(`/api/places/search?${params}`)
  if (!r.ok) throw new Error(`places ${r.status}`)
  const data = (await r.json()) as { results: PlaceResult[] }
  return data.results ?? []
}

export async function fetchSavedCharts(): Promise<SavedChartRow[]> {
  const r = await fetch('/api/saved-charts')
  if (!r.ok) throw new Error(`saved ${r.status}`)
  return r.json()
}

export async function saveChart(d: BirthChartDraft): Promise<SavedChartRow> {
  const r = await fetch('/api/saved-charts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      profile_name: d.profileName,
      birth_date: d.birthDate,
      birth_time: d.birthTime,
      timezone: d.timezone,
      place_label: d.placeLabel,
      latitude: d.latitude,
      longitude: d.longitude,
    }),
  })
  if (!r.ok) {
    const err = await r.text()
    throw new Error(err || `save ${r.status}`)
  }
  return r.json()
}

export async function deleteSavedChart(id: number): Promise<void> {
  const r = await fetch(`/api/saved-charts/${id}`, { method: 'DELETE' })
  if (!r.ok) throw new Error(`delete ${r.status}`)
}

export async function fetchNatalChart(
  d: BirthChartDraft,
): Promise<NatalChartResponse> {
  if (d.latitude == null || d.longitude == null) {
    throw new Error('Faltan coordenadas')
  }
  const r = await fetch('/api/charts/natal', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      birth_date: d.birthDate,
      birth_time: d.birthTime,
      timezone: d.timezone,
      latitude: d.latitude,
      longitude: d.longitude,
    }),
  })
  if (!r.ok) {
    let msg = `natal ${r.status}`
    try {
      const err = await r.json()
      if (err.detail) msg = String(err.detail)
    } catch {
      /* ignore */
    }
    throw new Error(msg)
  }
  return r.json()
}

export async function fetchTransitPeriod(input: {
  birthDate: string
  birthTime: string
  timezone: string
  latitude: number
  longitude: number
  fromDate: string
  toDate: string
  excludeMoon: boolean
}): Promise<TransitPeriodResponse> {
  const r = await fetch('/api/charts/transits', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      birth_date: input.birthDate,
      birth_time: input.birthTime,
      timezone: input.timezone,
      latitude: input.latitude,
      longitude: input.longitude,
      from_date: input.fromDate,
      to_date: input.toDate,
      exclude_moon: input.excludeMoon,
    }),
  })
  if (!r.ok) {
    let msg = `transits ${r.status}`
    try {
      const err = await r.json()
      if (err.detail) msg = String(err.detail)
    } catch {
      /* ignore */
    }
    throw new Error(msg)
  }
  return r.json()
}
