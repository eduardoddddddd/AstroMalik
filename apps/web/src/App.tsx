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
        <div>
          <h1 className="app-brand">AstroMalik</h1>
          <p className="app-tagline">
            Cartas natales, tránsitos y sinastría — corpus en castellano
          </p>
        </div>
        <ApiStatus />
      </header>

      <main className="app-main">
        <section className="panel" aria-labelledby="panel-datos">
          <h2 id="panel-datos" className="panel__title">
            Datos de nacimiento
          </h2>
          <p className="panel__subtitle">
            Introduce los datos para calcular posiciones y enlazar textos del
            corpus.
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
            Posiciones y casas (motor AstroBot / pyswisseph). Los textos del
            corpus se enlazan en un siguiente paso.
          </p>
          <NatalPreview data={natal} />
        </section>
      </main>
    </div>
  )
}

export default App
