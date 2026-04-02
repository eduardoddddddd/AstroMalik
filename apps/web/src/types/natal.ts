export type Interpretation = {
  clave: string
  tipo: 'natal_planeta_signo' | 'natal_planeta_casa' | 'aspecto_natal'
  titulo: string
  texto: string
  fuente: string
  orden: number
}

export type NatalChartResponse = {
  input: {
    birth_date: string
    birth_time: string
    timezone: string
    latitude: number
    longitude: number
  }
  jd: number
  time: {
    timezone_iana: string
    local_iso: string
    utc_iso: string
    ut_fractional_hours: number
  }
  chart: {
    house_system: string
    ascendant: { longitude: number; formatted: string }
    mc: { longitude: number; formatted: string }
    cusps: number[]
    bodies: Array<{
      key: string
      label: string
      longitude: number
      formatted: string
      house: number
      retrograde: boolean
    }>
  }
  interpretations: Interpretation[]
}
