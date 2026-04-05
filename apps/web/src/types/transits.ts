export type TransitEvent = {
  transit_key: string
  transit_label: string
  natal_key: string
  natal_label: string
  aspect_key: string
  aspect_label: string
  color: string
  from_date: string
  to_date: string
  exact_date: string
  active_days: number
  min_orb: number
  retrograde_on_exact: boolean
  score: number
  stars: number
  text: string | null
  source: string | null
}

export type TransitPeriodResponse = {
  input: {
    birth_date: string
    birth_time: string
    timezone: string
    latitude: number
    longitude: number
    from_date: string
    to_date: string
    exclude_moon: boolean
  }
  summary: {
    total_events: number
    events_with_text: number
    days_total: number
  }
  events: TransitEvent[]
}
