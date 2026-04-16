# AstroMalik

Aplicación web de astrología completa en castellano. Cartas natales con interpretaciones del corpus, tránsitos por intensidad y sinastría.

**Repo:** https://github.com/eduardoddddddd/AstroMalik  
**Stack:** React + TypeScript + Vite · FastAPI + pyswisseph · SQLite

---

## Lo que hay ahora mismo

### Frontend (`apps/web`)
- Formulario de carta natal — fecha (DD/MM/YYYY) · hora 24h · zona IANA · lugar con coordenadas
- Búsqueda de lugar: base local `cities_seed.json` + Nominatim/OpenStreetMap
- Motor de cálculo: **misma lógica que AstroBot** (pyswisseph, Placidus)
- Tabla de posiciones: planetas, grado, signo, casa, retrogradación
- **Interpretaciones del corpus** en acordeón:
  - Planetas en signo y casa agrupados por planeta (un ítem = signo + casa juntos)
  - Aspectos natales separados
- Guardar / recuperar cartas en base local (`user.db`, SQLite)
- Diseño crema/papel tipo Claude Desktop

### Backend (`backend/`)
- FastAPI + uvicorn, puerto 8765
- `POST /api/charts/natal` — calcula carta natal y devuelve posiciones + interpretaciones
- `POST /api/charts/transits` — tránsitos por periodo con scoring de intensidad (1-5 ★)
- `GET  /api/places/search` — búsqueda de lugar (seed + Nominatim)
- `GET/POST/DELETE /api/saved-charts` — CRUD de cartas guardadas en `user.db`
- `GET /api/health` + `GET /api/corpus/stats`
- Zona horaria correcta: `zoneinfo` + `tzdata` — hora local → UT antes de pyswisseph

### Corpus (`backend/data/corpus.db`) — 1766 filas
| Tipo | Filas | Fuentes | Cobertura |
|---|---|---|---|
| `transito` | 745 | Grupo Venus + Astrology King | 99% |
| `sinastria` | 420 | Grupo Venus | 93% |
| `aspecto_natal` | 368 | Astrology King + Café Astrology | 92% |
| `natal_planeta_signo` | 113 | Astrolibrary | 100% real |
| `natal_planeta_casa` | 120 | Astro-seek | 100% |

---

## Estructura del repositorio

```
AstroMalik/
├── apps/
│   └── web/                   ← React + Vite (frontend)
│       └── src/
│           ├── components/    ← BirthChartForm, NatalPreview, Interpretaciones,
│           │                     PlaceSearch, SavedChartsList, ApiStatus
│           ├── api/           ← astromalik.ts (cliente REST)
│           └── types/         ← natal.ts, chart.ts
├── backend/
│   ├── app/
│   │   ├── config.py          ← CORPUS_DB y USER_DB centralizados (fuente única)
│   │   ├── main.py            ← FastAPI app + lifespan + endpoints generales
│   │   ├── astro_core.py      ← motor pyswisseph (NO TOCAR sin revisar AstroBot)
│   │   ├── jd_local.py        ← hora local IANA → Julian Day UT
│   │   ├── transits.py        ← algoritmo tránsitos + scoring + textos corpus
│   │   ├── user_store.py      ← CRUD SQLite user.db
│   │   ├── places.py          ← búsqueda de lugar
│   │   └── routers/
│   │       └── charts.py      ← /api/charts/natal + /api/charts/transits
│   ├── data/
│   │   ├── corpus.db          ← 1766 interpretaciones (read-only)
│   │   └── cities_seed.json   ← ciudades para búsqueda offline
│   └── requirements.txt
├── scraper/                   ← scrapers Python (ejecución local, no se despliegan)
├── corpus/
│   └── schema.sql
├── scripts/
│   └── dev/                   ← scripts de análisis/debug (excluidos de git)
└── CONTEXT.md                 ← estado del proyecto para IA
```

---

## Desarrollo local

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8765 --reload
```

### Frontend
```bash
cd apps/web
npm install
npm run dev                     # http://localhost:5173
```

El frontend hace proxy de `/api` → `http://127.0.0.1:8765` (configurado en `vite.config.ts`).

---

## Notas críticas para el motor de cálculo

- **NO modificar** `backend/app/astro_core.py` sin comparar contra el AstroBot original
- Hora de nacimiento es **LOCAL**, nunca UTC — `jd_local.py` aplica el offset via `zoneinfo`
- Sistema de casas: **Placidus** (`b'P'`) para natal, Regiomontanus (`b'R'`) para horaria
- Carta de referencia para sanity check: `1976-10-11 20:33 Europe/Madrid` → Saturno Casa 4, ASC Géminis ~0°
- Rutas de BD centralizadas en `backend/app/config.py` — nunca redefinir `CORPUS_DB` en otros módulos

---

## Próximos pasos

- [x] Módulo de tránsitos (cálculo de intensidad + textos del corpus)
- [ ] Rueda SVG interactiva
- [ ] Dark mode + transiciones suaves
- [ ] Selector de zona horaria por lugar (deducir automáticamente de coordenadas)
- [ ] Sinastría (endpoints + UI)
- [ ] ErrorBoundary en frontend
- [ ] Tests unitarios (jd_local, carta de referencia, tránsitos)
- [ ] Deploy: GitHub Pages (frontend) + HuggingFace Spaces Docker (backend)
