import type { NatalChartResponse } from '../types/natal'
import { Interpretaciones } from './Interpretaciones'
import './NatalPreview.css'

type Props = {
  data: NatalChartResponse | null
}

export function NatalPreview({ data }: Props) {
  if (!data) {
    return (
      <p className="natal-preview__placeholder">
        Pulsa <strong>Calcular carta</strong> con fecha, hora local, zona IANA y
        lugar con coordenadas. Verás posiciones (Placidus, pyswisseph) y debajo
        las interpretaciones del corpus cuando existan claves en la base.
      </p>
    )
  }

  const { chart, time, jd, input, interpretations } = data

  return (
    <div className="natal-preview">
      <div className="natal-preview__meta">
        <span>
          JD <code>{jd.toFixed(5)}</code>
        </span>
        <span className="natal-preview__muted">{chart.house_system}</span>
      </div>
      <p className="natal-preview__angles">
        <strong>ASC</strong> {chart.ascendant.formatted}
        <span className="natal-preview__sep">·</span>
        <strong>MC</strong> {chart.mc.formatted}
      </p>
      <p className="natal-preview__utc">
        <strong>Hora local</strong> (servidor, IANA): <code>{time.local_iso}</code>
      </p>
      <p className="natal-preview__utc">
        <strong>UT efemérides</strong> (lo usa pyswisseph): <code>{time.utc_iso}</code> ·{' '}
        fracción diaria UT <code>{String(time.ut_fractional_hours)}</code> h
      </p>
      <p className="natal-preview__utc">
        Petición API: fecha <code>{input.birth_date}</code>, hora local{' '}
        <code>{input.birth_time}</code>, zona <code>{input.timezone}</code> · lat{' '}
        <code>{input.latitude.toFixed(5)}</code> · lon <code>{input.longitude.toFixed(5)}</code>
      </p>

      <div className="natal-preview__scroll">
        <table className="natal-preview__table">
          <thead>
            <tr>
              <th>Cuerpo</th>
              <th>Posición</th>
              <th>Casa</th>
              <th>℞</th>
            </tr>
          </thead>
          <tbody>
            {chart.bodies.map((b) => (
              <tr key={b.key}>
                <td>{b.label}</td>
                <td>{b.formatted}</td>
                <td>{b.house}</td>
                <td>{b.retrograde ? '℞' : ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {interpretations && interpretations.length > 0 && (
        <Interpretaciones items={interpretations} />
      )}
    </div>
  )
}
