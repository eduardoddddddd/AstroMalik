import { useState } from 'react'
import type { Interpretation } from '../types/natal'
import './Interpretaciones.css'

type Props = {
  items: Interpretation[]
}

// Orden canónico de planetas (igual que en astro_core.py)
const PLANET_KEYS = [
  'SOL', 'LUNA', 'MERCURIO', 'VENUS', 'MARTE',
  'JUPITER', 'SATURNO', 'URANO', 'NEPTUNO', 'PLUTON',
]

type PlanetGroup = {
  pk: string
  planetLabel: string   // ej. "☉ Sol"
  signoLabel: string    // ej. "♎ Libra"
  casaLabel: string     // ej. "Casa 6"
  signo: Interpretation | null
  casa: Interpretation | null
}

function buildPlanetGroups(items: Interpretation[]): PlanetGroup[] {
  const planetItems = items.filter(
    (i) => i.tipo === 'natal_planeta_signo' || i.tipo === 'natal_planeta_casa',
  )
  return PLANET_KEYS.flatMap((pk) => {
    const signo = planetItems.find(
      (i) => i.tipo === 'natal_planeta_signo' && i.clave.startsWith(pk + '_'),
    ) ?? null
    const casa = planetItems.find(
      (i) => i.tipo === 'natal_planeta_casa' && i.clave.startsWith(pk + '_'),
    ) ?? null
    if (!signo && !casa) return []
    const ref = signo ?? casa!
    // titulo: "☉ Sol en ♎ Libra"  →  part before " en " is the planet label
    const parts = ref.titulo.split(' en ')
    const planetLabel = parts[0] ?? pk
    const signoLabel = signo ? (signo.titulo.split(' en ')[1] ?? '') : ''
    const casaLabel  = casa  ? (casa.titulo.split(' en ')[1] ?? '') : ''
    return [{ pk, planetLabel, signoLabel, casaLabel, signo, casa }]
  })
}

function TextBlock({ interp, subheading }: { interp: Interpretation; subheading: string }) {
  return (
    <div className="interp__sub">
      <p className="interp__sub-heading">{subheading}</p>
      {interp.texto.split('\n').filter(Boolean).map((p, i) => (
        <p key={i}>{p}</p>
      ))}
      {interp.fuente && (
        <p className="interp__item-credit">Fuente: {interp.fuente}</p>
      )}
    </div>
  )
}

export function Interpretaciones({ items }: Props) {
  const [openGroup, setOpenGroup] = useState<string>('planetas')
  const [openItem,  setOpenItem]  = useState<string | null>(null)

  if (!items.length) return null

  const planetGroups  = buildPlanetGroups(items)
  const aspectItems   = items.filter((i) => i.tipo === 'aspecto_natal')

  function toggle(id: string) {
    setOpenItem(openItem === id ? null : id)
  }

  return (
    <div className="interp">
      <h3 className="interp__heading">Interpretaciones del corpus</h3>

      {/* ── SECCIÓN: Planetas ── */}
      {planetGroups.length > 0 && (
        <section className="interp__group">
          <button
            className={`interp__group-btn${openGroup === 'planetas' ? ' interp__group-btn--open' : ''}`}
            onClick={() => setOpenGroup(openGroup === 'planetas' ? '' : 'planetas')}
            aria-expanded={openGroup === 'planetas'}
          >
            <span className="interp__group-icon">♈</span>
            <span className="interp__group-label">Planetas — signo y casa</span>
            <span className="interp__group-count">{planetGroups.length}</span>
            <span className="interp__chevron">{openGroup === 'planetas' ? '▲' : '▼'}</span>
          </button>

          {openGroup === 'planetas' && (
            <ul className="interp__list">
              {planetGroups.map((pg) => {
                const isOpen = openItem === pg.pk
                // Cabecera: "☉ Sol — ♎ Libra · Casa 6"
                const subtitle = [pg.signoLabel, pg.casaLabel].filter(Boolean).join(' · ')
                return (
                  <li key={pg.pk} className={`interp__item${isOpen ? ' interp__item--open' : ''}`}>
                    <button
                      className="interp__item-btn"
                      onClick={() => toggle(pg.pk)}
                      aria-expanded={isOpen}
                    >
                      <span className="interp__item-titulo">
                        <strong>{pg.planetLabel}</strong>
                        {subtitle && <span className="interp__item-subtitle"> — {subtitle}</span>}
                      </span>
                      <span className="interp__item-chevron">{isOpen ? '▲' : '▼'}</span>
                    </button>
                    {isOpen && (
                      <div className="interp__item-body">
                        {pg.signo && (
                          <TextBlock
                            interp={pg.signo}
                            subheading={`En ${pg.signoLabel}`}
                          />
                        )}
                        {pg.signo && pg.casa && <hr className="interp__divider" />}
                        {pg.casa && (
                          <TextBlock
                            interp={pg.casa}
                            subheading={pg.casaLabel}
                          />
                        )}
                      </div>
                    )}
                  </li>
                )
              })}
            </ul>
          )}
        </section>
      )}

      {/* ── SECCIÓN: Aspectos natales ── */}
      {aspectItems.length > 0 && (
        <section className="interp__group">
          <button
            className={`interp__group-btn${openGroup === 'aspectos' ? ' interp__group-btn--open' : ''}`}
            onClick={() => setOpenGroup(openGroup === 'aspectos' ? '' : 'aspectos')}
            aria-expanded={openGroup === 'aspectos'}
          >
            <span className="interp__group-icon">△</span>
            <span className="interp__group-label">Aspectos natales</span>
            <span className="interp__group-count">{aspectItems.length}</span>
            <span className="interp__chevron">{openGroup === 'aspectos' ? '▲' : '▼'}</span>
          </button>

          {openGroup === 'aspectos' && (
            <ul className="interp__list">
              {aspectItems.map((item) => {
                const isOpen = openItem === item.clave
                return (
                  <li key={item.clave} className={`interp__item${isOpen ? ' interp__item--open' : ''}`}>
                    <button
                      className="interp__item-btn"
                      onClick={() => toggle(item.clave)}
                      aria-expanded={isOpen}
                    >
                      <span className="interp__item-titulo">{item.titulo}</span>
                      {item.fuente && (
                        <span className="interp__item-fuente">{item.fuente}</span>
                      )}
                      <span className="interp__item-chevron">{isOpen ? '▲' : '▼'}</span>
                    </button>
                    {isOpen && (
                      <div className="interp__item-body">
                        {item.texto.split('\n').filter(Boolean).map((p, i) => (
                          <p key={i}>{p}</p>
                        ))}
                        {item.fuente && (
                          <p className="interp__item-credit">Fuente: {item.fuente}</p>
                        )}
                      </div>
                    )}
                  </li>
                )
              })}
            </ul>
          )}
        </section>
      )}
    </div>
  )
}
