import { useCallback, useEffect, useRef, useState } from 'react'
import { searchPlaces, type PlaceResult } from '../api/astromalik'
import './PlaceSearch.css'

type Props = {
  onPick: (p: PlaceResult) => void
  placeLabel: string
  onPlaceLabelChange: (v: string) => void
}

export function PlaceSearch({
  onPick,
  placeLabel,
  onPlaceLabelChange,
}: Props) {
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<PlaceResult[]>([])
  const wrapRef = useRef<HTMLDivElement>(null)

  const runSearch = useCallback(async (q: string) => {
    const t = q.trim()
    if (t.length < 2) {
      setResults([])
      return
    }
    setLoading(true)
    try {
      const list = await searchPlaces(t)
      setResults(list)
      setOpen(true)
    } catch {
      setResults([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const t = placeLabel.trim()
    if (t.length < 2) {
      setResults([])
      return
    }
    const id = window.setTimeout(() => {
      runSearch(t)
    }, 380)
    return () => window.clearTimeout(id)
  }, [placeLabel, runSearch])

  useEffect(() => {
    function close(e: MouseEvent) {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('click', close)
    return () => document.removeEventListener('click', close)
  }, [])

  function handlePick(p: PlaceResult) {
    onPlaceLabelChange(p.label)
    onPick(p)
    setOpen(false)
  }

  return (
    <div className="place-search" ref={wrapRef}>
      <label className="place-search__label" htmlFor="placeLabel">
        Lugar de nacimiento
      </label>
      <input
        id="placeLabel"
        className="place-search__input"
        type="text"
        autoComplete="off"
        placeholder="Escribe ciudad o país y elige de la lista"
        value={placeLabel}
        onChange={(e) => onPlaceLabelChange(e.target.value)}
        onFocus={() => {
          if (results.length > 0) setOpen(true)
        }}
        aria-autocomplete="list"
        aria-expanded={open}
        aria-controls="place-search-listbox"
      />
      {loading && (
        <span className="place-search__loading" aria-live="polite">
          Buscando…
        </span>
      )}
      {open && results.length > 0 && (
        <ul
          id="place-search-listbox"
          className="place-search__list"
          role="listbox"
        >
          {results.map((p, i) => (
            <li key={`${p.label}-${p.lat}-${i}`} role="option">
              <button
                type="button"
                className="place-search__opt"
                onClick={() => handlePick(p)}
              >
                <span className="place-search__opt-title">{p.label}</span>
                <span className="place-search__opt-meta">
                  {p.lat.toFixed(4)}°, {p.lon.toFixed(4)}° · {p.source}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
      <p className="place-search__hint">
        Lista local + OpenStreetMap (Nominatim). Elige una fila para fijar latitud
        y longitud.
      </p>
    </div>
  )
}
