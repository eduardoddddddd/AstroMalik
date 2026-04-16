# AstroMalik — Contexto del Proyecto

**Archivo de estado para colaboración Claude ↔ Codex (GPT), con Eduardo como árbitro.**

Actualizar este archivo al final de cada sesión. Es la memoria del proyecto.

---

## Descripción General

Aplicación web de astrología completa, en castellano, con:
- Cartas natales con interpretaciones de alta calidad
- Tránsitos por intensidad y rango de fechas (estilo Grupo Venus)
- Sinastría (pendiente)
- Corpus de textos scrapeado de internet, multiautor, en castellano — **1766 filas**

**Nombre:** AstroMalik
**Repositorio GitHub:** https://github.com/eduardoddddddd/AstroMalik
**HuggingFace Space:** pendiente crear
**Inicio del proyecto:** 2026-03-29

---

## Requisitos No Negociables

1. **Gratuito y siempre online** — GitHub Pages (frontend) + HuggingFace Spaces Docker (backend)
2. **Responsive completo** — desde móvil 6" hasta monitor 4K 32", orientación horizontal y vertical
3. **Textos en castellano** — si la fuente es inglés, traducir al importar al corpus
4. **Multiautor** — cada interpretación lleva fuente; la misma clave puede tener múltiples entradas de distintos autores
5. **Rueda SVG interactiva** — viewBox relativo, touch-friendly, tap en planeta muestra aspectos
6. **Sin base de datos de servidor** — corpus.db SQLite empaquetado en Docker; cartas de usuario en user.db local

---

## Stack Tecnológico (REAL)

```
FRONTEND  → apps/web/
           React 18 + TypeScript
           Vite (dev server + build)
           CSS Modules por componente
           Sin framework CSS externo

BACKEND   → backend/ (FastAPI + uvicorn, puerto 8765)
           Python 3.11
           FastAPI + Pydantic
           pyswisseph (efemérides Swiss Ephemeris)
           SQLite read-only (corpus.db) + SQLite write (user.db)

DATOS USUARIO → user.db local (SQLite en backend/data/)

SCRAPER   → scraper/ — Scripts Python locales (no se despliegan)
           requests + BeautifulSoup4
           deep-translator (Google Translate, sin cuota)
           Ejecutar localmente, generar corpus.db
```

---

## Estructura del Repositorio (REAL)

```
AstroMalik/
├── CONTEXT.md              ← ESTE ARCHIVO (actualizar siempre)
├── README.md               ← Resumen para humanos/GitHub
├── .gitignore
├── apps/
│   └── web/               ← Frontend React + Vite
│       ├── src/
│       │   ├── App.tsx
│       │   ├── config.ts  ← API_BASE (VITE_API_BASE env)
│       │   ├── index.css
│       │   ├── api/
│       │   │   └── astromalik.ts  ← cliente REST
│       │   ├── components/
│       │   │   ├── BirthChartForm.tsx
│       │   │   ├── NatalPreview.tsx
│       │   │   ├── Interpretaciones.tsx
│       │   │   ├── PlaceSearch.tsx
│       │   │   ├── SavedChartsList.tsx
│       │   │   └── ApiStatus.tsx
│       │   └── types/
│       │       ├── natal.ts
│       │       └── chart.ts
│       ├── index.html
│       ├── vite.config.ts  ← proxy /api → localhost:8765
│       └── package.json
├── backend/
│   ├── app/
│   │   ├── config.py       ← CORPUS_DB, USER_DB (rutas centralizadas)
│   │   ├── main.py         ← FastAPI app + lifespan + endpoints generales
│   │   ├── astro_core.py   ← motor pyswisseph (NO TOCAR sin revisar AstroBot)
│   │   ├── jd_local.py     ← hora local IANA → Julian Day UT
│   │   ├── transits.py     ← algoritmo tránsitos + intensidad + corpus
│   │   ├── user_store.py   ← CRUD SQLite user.db
│   │   ├── places.py       ← búsqueda de lugar (seed + Nominatim)
│   │   └── routers/
│   │       └── charts.py   ← /api/charts/natal y /api/charts/transits
│   ├── data/
│   │   ├── corpus.db       ← 1766 interpretaciones (read-only)
│   │   ├── user.db         ← cartas guardadas (write, excluido de git)
│   │   └── cities_seed.json
│   └── requirements.txt
├── corpus/
│   └── schema.sql          ← definición de tablas
├── scraper/                ← scrapers Python (ejecución local, no se despliegan)
│   ├── sources/
│   │   ├── astrology_king.py
│   │   ├── astrolibrary.py
│   │   └── grupo_venus.py
│   └── ...
└── scripts/
    └── dev/               ← scripts de debug/análisis/prueba (excluidos de git)
```

---

## Esquema Base de Datos — corpus.db

```sql
CREATE TABLE interpretaciones (
    id           INTEGER PRIMARY KEY,
    tipo         TEXT NOT NULL,
    -- valores: natal_planeta_signo | natal_planeta_casa |
    --          aspecto_natal | transito | sinastria
    clave        TEXT NOT NULL,
    -- formato por tipo:
    --   natal_planeta_signo:  SOL_ARIES
    --   natal_planeta_casa:   SOL_CASA_1
    --   aspecto_natal:        SOL_LUNA_CONJUNCION
    --   transito:             SATURNO_tr_SOL_CONJUNCION
    --   sinastria:            SYN_SOL_LUNA_CONJUNCION
    autor        TEXT,
    fuente_url   TEXT,
    fuente_nombre TEXT,
    idioma_origen TEXT DEFAULT 'es',
    texto_corto  TEXT,
    texto_largo  TEXT NOT NULL,
    calidad      INTEGER DEFAULT 3,
    fecha_scrape TEXT,
    UNIQUE(clave, fuente_url)   -- permite multiautor, no duplicados
);

CREATE INDEX idx_tipo_clave ON interpretaciones(tipo, clave);
CREATE INDEX idx_clave ON interpretaciones(clave);
```

---

## Corpus — Estado Actual (1766 filas)

| Tipo | Filas | Fuentes | Cobertura |
|------|-------|---------|-----------|
| `transito` | 745 | Grupo Venus + Astrology King | 99% |
| `sinastria` | 420 | Grupo Venus | 93% |
| `aspecto_natal` | 368 | Astrology King + Café Astrology | 92% |
| `natal_planeta_signo` | 113 | Astrolibrary | 100% real |
| `natal_planeta_casa` | 120 | Astro-seek | 100% |

---

## Módulo de Tránsitos — Algoritmo de Intensidad

```python
PLANET_WEIGHTS = {
    'PLUTON': 10, 'NEPTUNO': 9, 'URANO': 8,
    'SATURNO': 7, 'JUPITER': 6,
    'MARTE': 4, 'VENUS': 2, 'MERCURIO': 2, 'SOL': 2, 'LUNA': 1,
}
ASPECT_WEIGHTS = {
    'CONJUNCION': 5, 'OPOSICION': 4.5, 'CUADRADO': 4,
    'TRIGONO': 3, 'SEXTIL': 2,
}
# Score = planet_weight × aspect_weight × orb_factor
# Stars: ≥25 → 5★, ≥15 → 4★, ≥8 → 3★, ≥3 → 2★, else → 1★
```

---

## Decisiones de Diseño Tomadas

| Decisión | Elección | Motivo |
|----------|----------|--------|
| Frontend | React + TypeScript + Vite | Componentes, tipado fuerte, hot-reload |
| Backend | FastAPI + uvicorn | Async, documentación automática, HF-friendly |
| Corpus | SQLite empaquetado | Sin servidor BD, portable, read-only |
| Cartas usuario | SQLite local (user.db) | Sin infraestructura, MVP rápido |
| Zona horaria | `zoneinfo` + `tzdata` | Estándar Python 3.9+, sin pytz |
| Casas | Placidus para natal | Igual que AstroBot original |
| Textos | Multiautor por clave | UNIQUE(clave, fuente_url) |
| Config rutas | `app/config.py` | CORPUS_DB/USER_DB centralizados |

---

## Notas Críticas para el Motor de Cálculo

- **NO modificar** `backend/app/astro_core.py` sin comparar contra el AstroBot original
- Hora de nacimiento es **LOCAL**, nunca UTC — `jd_local.py` aplica el offset via `zoneinfo`
- Sistema de casas: **Placidus** (`b'P'`) para natal, Regiomontanus (`b'R'`) para horaria
- **Carta de referencia:** `1976-10-11 20:33 Europe/Madrid` → Saturno Casa 4, ASC Géminis ~0°
- `CORPUS_DB` y `USER_DB` → importar siempre desde `app.config`, nunca redefinir en módulos

---

## Estado del Proyecto

### ✅ Completado
- Corpus de 1766 textos (transito, sinastria, aspecto_natal, natal_planeta_signo, natal_planeta_casa)
- Backend FastAPI: carta natal (`/api/charts/natal`) con posiciones + interpretaciones
- Backend FastAPI: tránsitos (`/api/charts/transits`) con scoring + textos corpus
- Backend FastAPI: places search (seed + Nominatim), saved-charts CRUD, health, corpus/stats
- Frontend React: BirthChartForm, NatalPreview, Interpretaciones, PlaceSearch, SavedChartsList
- Motor pyswisseph: cálculo natal completo (planetas, casas Placidus, ASC/MC)
- Motor de tránsitos: scoring por intensidad, agrupación de eventos
- Limpieza arquitectural: carpetas vacías eliminadas, scripts a `scripts/dev/`, config.py centralizado

### 🔄 En Progreso / Próximos pasos
- [ ] Rueda SVG interactiva (el feature bandera)
- [ ] Dark mode + transiciones suaves
- [ ] Selector de zona horaria inteligente (por lugar/coordenadas)
- [ ] Módulo de sinastría (endpoints + UI)
- [ ] ErrorBoundary en frontend
- [ ] Tests unitarios (jd_local, carta de referencia, tránsitos)
- [ ] Logging básico en backend
- [ ] Deploy: HuggingFace Spaces (backend) + GitHub Pages (frontend)

---

## Historial de Sesiones

### 2026-03-29 — Sesión 1 (Claude)
- Diseño completo de arquitectura
- Decisión stack: FastAPI + HF Spaces + GitHub Pages
- Esquema corpus.db con soporte multiautor
- Sistema de claves de interpretación definido
- Algoritmo de intensidad de tránsitos diseñado
- Creación estructura de carpetas y repo git

### 2026-03-29 — Sesión 2 (Codex)
- Auditoría del estado real del repo local
- Validación de `Grupo Venus` (transiaw OK, tracompu OK, starsolu descartado)
- Carga inicial: transito 354 filas GV, sinastria 375 filas GV
- Implementado scraper Astrology King
- Carga adicional: aspecto_natal 334 filas AK, transito 391 filas AK
- Total: 1488 filas

### 2026-03-30 — Sesión 3 (Claude)
- Verificación cobertura corpus.db
- Sinastría: ejecutado fill_sinastria.py → 420/450 (93%) — efectivamente completa
- Elegidas fuentes para natal: astrolibrary.org (signos), astro-seek.com (casas)

### 2026-03-30 — Sesión 4 (Claude)
- Cobertura verificada: transito 99%, sinastria 93%, aspecto_natal 92%
- Implementado scraper astrolibrary.py (signos + casas)
- Traducción con deep-translator (Google Translate, sin cuota)

### 2026-03-30 — Sesión 5 (Claude)
- **CORPUS COMPLETADO** — 1766 filas totales
  - natal_planeta_signo: 113 filas (astrolibrary, traducido)
  - natal_planeta_casa: 120 filas (astro-seek, traducido)
- **Próximo paso:** backend FastAPI

### 2026-04-05 — Sesión 6 (Claude/Codex)
- Backend FastAPI implementado: main.py, astro_core.py, jd_local.py, transits.py
- Frontend React: BirthChartForm, NatalPreview, Interpretaciones, PlaceSearch
- Motor de tránsitos con scoring por intensidad operativo
- Deploy en GCP VM (contenedor `astro-api`, puerto 8765)

### 2026-04-16 — Sesión 7 (Claude)
- Revisión arquitectural completa: identificados 17 puntos de mejora
- **Fase 1 (Limpieza) ejecutada:**
  - Eliminadas 7 carpetas vacías fantasma (frontend/, backend/api/, backend/engine/, etc.)
  - 18 scripts/archivos de debug movidos a `scripts/dev/`
  - `.gitignore` actualizado (apps/web/dist/, scripts/dev/)
  - `backend/app/config.py` creado — CORPUS_DB y USER_DB centralizados
  - `main.py`, `charts.py`, `transits.py` actualizados para importar de config.py
  - `CONTEXT.md` reescrito para reflejar el stack real (React + Vite, no Alpine.js)
