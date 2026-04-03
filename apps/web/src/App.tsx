import { useState } from 'react'
import { ApiStatus } from './components/ApiStatus'
import { BirthChartForm } from './components/BirthChartForm'
import { NatalPreview } from './components/NatalPreview'
import type { NatalChartResponse } from './types/natal'

function App() {
  const [natal, setNatal] = useState<NatalChartResponse | null>(null)

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-shell app-header__row">
          <div>
            <h1 className="app-brand">AstroMalik</h1>
            <p className="app-tagline">
              Cartas natales, tránsitos y sinastría — corpus en castellano
            </p>
          </div>
          <ApiStatus />
        </div>
      </header>

      <main className="app-main app-shell">
        <section className="panel panel--form" aria-labelledby="panel-datos">
          <h2 id="panel-datos" className="panel__title">
            Datos de nacimiento
          </h2>
          <p className="panel__subtitle">
            Introduce los datos y pulsa calcular: el servidor devuelve posiciones
            y textos del corpus (planeta en signo/casa y aspectos natales).
          </p>
          <BirthChartForm onChartComputed={setNatal} />
        </section>

        <section
          className="panel panel--preview"
          aria-labelledby="panel-vista"
        >
          <h2 id="panel-vista" className="panel__title">
            Carta e interpretaciones
          </h2>
          <p className="panel__subtitle">
            Tras calcular verás la tabla de posiciones (Placidus, pyswisseph) y
            abajo las interpretaciones disponibles en la base local.
          </p>
          <NatalPreview data={natal} />
        </section>
      </main>
    </div>
  )
}

export default App
