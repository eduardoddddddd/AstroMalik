export type BirthChartDraft = {
  profileName: string
  birthDate: string
  birthTime: string
  timezone: string
  placeLabel: string
  latitude: number | null
  longitude: number | null
}

export type SavedChartRow = {
  id: number
  profile_name: string
  birth_date: string
  birth_time: string
  timezone: string
  place_label: string
  latitude: number
  longitude: number
  created_at: string
}

export const initialDraft: BirthChartDraft = {
  profileName: '',
  birthDate: '',
  birthTime: '12:00',
  timezone: 'Europe/Madrid',
  placeLabel: '',
  latitude: null,
  longitude: null,
}
