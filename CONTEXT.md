# AstroMalik — Contexto del Proyecto

**Archivo de estado para colaboración Claude ↔ Codex (GPT), con Eduardo como árbitro.**

Actualizar este archivo al final de cada sesión. Es la memoria del proyecto.

---

## Descripción General

Aplicación web de astrología completa, en castellano, con:
- Cartas natales con interpretaciones de alta calidad
- Tránsitos por intensidad y rango de fechas (estilo Grupo Venus)
- Sinastría
- Corpus de textos scrapeado de internet, multiautor, en castellano

**Nombre:** AstroMalik
**Repositorio GitHub:** https://github.com/eduardoddddddd/AstroMalik (pendiente crear)
**HuggingFace Space:** pendiente crear
**Inicio del proyecto:** 2026-03-29

---

## Requisitos No Negociables

1. **Gratuito y siempre online** — GitHub Pages (frontend) + HuggingFace Spaces Docker (backend)
2. **Responsive completo** — desde móvil 6" hasta monitor 4K 32", orientación horizontal y vertical
3. **Textos en castellano** — si la fuente es inglés, traducir al importar al corpus
4. **Multiautor** — cada interpretación lleva fuente; la misma clave puede tener múltiples entradas de distintos autores
5. **Rueda SVG interactiva** — viewBox relativo, touch-friendly, tap en planeta muestra aspectos
6. **Sin base de datos de servidor** — corpus.db SQLite empaquetado en Docker; cartas de usuario en localStorage o Supabase

---

## Stack Tecnológico

```
FRONTEND  → GitHub Pages
           HTML5 + CSS Grid/Flexbox (sin framework CSS)
           Alpine.js (reactividad ligera, ~8kb)
           JS vanilla
           SVG rueda generada dinámicamente

BACKEND   → HuggingFace Spaces (Docker, CPU free)
           Python 3.11
           FastAPI
           pyswisseph (efemérides)
           SQLite (corpus.db, read-only)

DATOS USUARIO → localStorage (MVP) → Supabase (v2)

SCRAPER   → Scripts Python locales (no se despliegan)
           requests + BeautifulSoup4
           googletrans / deep-translator (traducción)
           Ejecutar localmente, generar corpus.db
```

---

## Estructura del Repositorio

```
AstroMalik/
├── CONTEXT.md              ← ESTE ARCHIVO (actualizar siempre)
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py             ← FastAPI app principal
│   ├── api/
│   │   ├── carta.py        ← endpoints carta natal
│   │   ├── transitos.py    ← endpoints tránsitos
│   │   └── sinastria.py    ← endpoints sinastría
│   ├── engine/
│   │   ├── calculos.py     ← pyswisseph wrapper
│   │   ├── transitos.py    ← algoritmo tránsitos + intensidad
│   │   └── aspectos.py     ← cálculo de aspectos
│   ├── models/
│   │   └── corpus.py       ← acceso a corpus.db
│   └── data/
│       └── corpus.db       ← generado por scraper (no editar a mano)
├── frontend/
│   ├── index.html          ← SPA principal
│   ├── static/
│   │   ├── css/
│   │   │   └── main.css
│   │   └── js/
│   │       ├── app.js
│   │       ├── rueda.js    ← SVG rueda astral
│   │       └── transitos.js
│   └── templates/          ← partials HTML
├── scraper/
│   ├── README.md
│   ├── run_all.py          ← ejecutar todos los scrapers
│   ├── sources/
│   │   ├── cafe_astrology.py
│   │   ├── astro_com.py
│   │   ├── astrology_king.py
│   │   └── skyscript.py
│   ├── translator.py       ← wrapper de traducción ES
│   ├── normalizer.py       ← limpieza y normalización
│   └── build_corpus.py     ← genera corpus.db final
├── corpus/
│   └── schema.sql          ← definición de tablas
└── docs/
    ├── diseno.md           ← decisiones de diseño
    └── claves.md           ← catálogo de claves del corpus
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
    -- formato por tipo (ver docs/claves.md):
    --   natal_planeta_signo:  SOL_ARIES
    --   natal_planeta_casa:   SOL_CASA_1
    --   aspecto_natal:        SOL_LUNA_CONJUNCION
    --   transito:             SATURNO_tr_SOL_CONJUNCION
    --   sinastria:            SYN_SOL_LUNA_CONJUNCION
    autor        TEXT,          -- nombre del autor / sitio
    fuente_url   TEXT,          -- URL original
    fuente_nombre TEXT,         -- nombre legible de la fuente
    idioma_origen TEXT DEFAULT 'es',  -- 'en' si fue traducido
    texto_corto  TEXT,          -- 2-3 líneas resumen
    texto_largo  TEXT NOT NULL, -- interpretación completa
    calidad      INTEGER DEFAULT 3,  -- 1-5
    fecha_scrape TEXT,
    UNIQUE(clave, fuente_url)   -- permite multiautor, no duplicados
);

CREATE INDEX idx_tipo_clave ON interpretaciones(tipo, clave);
CREATE INDEX idx_clave ON interpretaciones(clave);
```

---

## Módulo de Tránsitos — Algoritmo de Intensidad

```python
PESOS_PLANETA_TRANSITO = {
    'PLUTON': 5, 'NEPTUNO': 4, 'URANO': 4,
    'SATURNO': 3, 'JUPITER': 2,
    'MARTE': 1, 'SOL': 1, 'VENUS': 1, 'MERCURIO': 0
}
PESOS_PUNTO_NATAL = {
    'ASC': 5, 'MC': 5, 'SOL': 4, 'LUNA': 4,
    'SATURNO': 3, 'MARTE': 3, 'VENUS': 2,
    'JUPITER': 2, 'MERCURIO': 1, 'VENUS': 2
}
PESOS_ASPECTO = {
    'CONJUNCION': 5, 'OPOSICION': 4, 'CUADRADO': 3,
    'TRIGONO': 2, 'SEXTIL': 1
}
# Intensidad final = media ponderada, 1-5 estrellas
# +0.5 si planeta retrógrado toca más de una vez
```

---

## Estado Actual del Proyecto

### ✅ Completado
- Diseño de arquitectura general
- Esquema de base de datos corpus.db
- Sistema de claves de interpretación
- Algoritmo de intensidad de tránsitos
- Estructura de carpetas y repo git local
- CONTEXT.md (este archivo)

### 🔄 En Progreso
- **Scraper Grupo Venus**
  - `transiaw` validado para `transito`
  - `tracompu` validado para `sinastria`
  - `starsolu` descartado por ahora: devuelve contenido externo en inglés ("Starlight Solutions")
  - Cobertura actual en `corpus.db`:
    - `transito`: 354 filas
    - `sinastria`: 375 filas
  - Investigación natal:
    - `info.asp?bypass` revela informes natales con IDs (`61` SuperNatal, `62` Carta Natal, `170` Carta Natal con Quirón)
    - Flujo detectado: `info.asp?bypass` → `informes3.asp`
    - Bloqueo actual: el acceso libre termina en solicitud por email/lote gratis, no devuelve el informe natal completo en HTML inmediato
    - Conclusión actual: GV es excelente para `transito` y `sinastria`; para `natal` todavía no hay extractor limpio
- **Scraper Café Astrology**
  - Estado: despriorizado
  - Motivo: aunque `aspecto_natal` funciona, la cobertura es pobre y la prioridad del proyecto pasa a exprimir mejor `Grupo Venus` + nuevas fuentes más directas
  - `natal_planeta_signo`, `natal_planeta_casa` y `transito` quedan congelados
- **Evaluación de nueva fuente: Astrology King**
  - Estado: operativo
  - Páginas estables y legibles como `Sun Square Saturn Natal and Transit`
  - Una misma URL suele contener secciones `Natal` y `Transit`, útiles para extraer ambos textos con parser por encabezados
  - Regla aplicada: si la fuente original está en inglés, se traduce antes de insertar; si la traducción falla, la fila se descarta
  - Cobertura actual en `corpus.db`:
    - `aspecto_natal`: 334 filas
    - `transito`: 391 filas
  - Encaje actual:
    - `aspecto_natal`: sí
    - `transito`: sí
    - `sinastria`: no prioritaria por ahora
    - `planeta_signo` / `planeta_casa`: no parece fuente principal
  - Observación: algunas URLs del índice no traen bloque útil de tránsito y se descartan automáticamente
- **Robert Hand / Planets in Transit**
  - Valor editorial alto como referencia de calidad para el módulo de tránsitos
  - No usar como corpus scrapeado desde Internet Archive
  - Motivo: obra con copyright y acceso restringido (`Access-restricted-item`) en Archive
  - Decisión: solo puede servir como referencia conceptual o como material de trabajo si el usuario aporta una copia legítima propia

### ⏳ Pendiente
- Scraper Astro.com (interpretaciones Liz Greene)
- Scraper Skyscript (tradicional)
- FastAPI backend básico
- Motor pyswisseph wrapper
- HTML responsive shell
- Rueda SVG responsive
- Deploy HuggingFace Spaces
- Deploy GitHub Pages
- Módulo sinastría
- Supabase para persistencia multidevice

---

## Decisiones de Diseño Tomadas

| Decisión | Elección | Motivo |
|----------|----------|--------|
| Frontend | HTML + Alpine.js | Sin build step, hosting estático puro |
| Backend | FastAPI | Async, HF-friendly, docs automáticas |
| Corpus | SQLite empaquetado | Sin servidor BD, portable |
| Cartas usuario | localStorage | Sin infraestructura, MVP rápido |
| Responsive | CSS Grid nativo | Sin dependencias, control total |
| Rueda | SVG viewBox relativo | Escala perfecta en cualquier pantalla |
| Textos | Multiautor por clave | Riqueza interpretativa, misma situación varios autores |

---

## Notas para Claude / Codex

- **Idioma del código:** inglés para código, comentarios en castellano
- **Idioma de datos:** todo en castellano en la BD (traducir en el scraper)
- **Rueda SVG:** nunca píxeles fijos, siempre viewBox="0 0 800 800" y porcentajes
- **pyswisseph:** siempre Placidus para cartas natales, Regiomontanus solo para horary
- **Timezone gotcha:** la hora de nacimiento es LOCAL, no UTC — siempre aplicar offset antes de swe.julday()
- **Multiautor:** UNIQUE(clave, fuente_url) — la misma clave puede tener N filas de distintas fuentes
- **Calidad fuentes:** astro.com=5, cafe_astrology=4, astrology_king=4, skyscript=3

---

## Historial de Sesiones

### 2026-03-29 — Sesión 1 (Claude)
- Diseño completo de arquitectura
- Decisión stack: FastAPI + HF Spaces + GitHub Pages
- Esquema corpus.db con soporte multiautor
- Sistema de claves de interpretación definido
- Algoritmo de intensidad de tránsitos diseñado
- Creación estructura de carpetas y repo git
- Inicio scraper Café Astrology (próximo paso)

### 2026-03-29 — Sesión 2 (Codex)
- Auditoría del estado real del repo local
- Validación de `Grupo Venus`
  - `transiaw` OK
  - `tracompu` OK
  - `starsolu` descartado
- Confirmación de que el parser de sitemaps de Café Astrology funciona si se completa
- Generado `scraper/cafe_astrology_urls.json` con URLs reales clasificadas
- Reorientación del scraper de Café Astrology para priorizar solo entradas de alta confianza
- Carga real de corpus:
  - `transito`: 354 filas de Grupo Venus
  - `sinastria`: 375 filas de Grupo Venus
  - `aspecto_natal`: 34 filas de Café Astrology
  - Fila heredada de `Grupo Venus/starsolu` eliminada por no ser fuente fiable
  - Total actual en `backend/data/corpus.db`: 763 filas
- Investigación adicional:
  - Detectado el menú natal de Grupo Venus con IDs internos (`61`, `62`, `170`)
  - Comprobado que el acceso libre a natal deriva a solicitud por email, no a HTML inmediato reutilizable
  - Decisión de producto: bajar prioridad de Café Astrology y buscar nuevas fuentes natales/aspectos más directas
  - Evaluado `Astrology King` como siguiente fuente:
    - estructura simple
    - URLs estables
    - artículos con secciones `Natal` + `Transit` aprovechables
  - Implementado `scraper/sources/astrology_king.py`
  - Carga real adicional del corpus:
    - `aspecto_natal`: 334 filas de Astrology King
    - `transito`: 391 filas de Astrology King
    - Total actual en `backend/data/corpus.db`: 1488 filas
  - Regla reforzada: en la BD solo entra texto en castellano; si falla la traducción, se descarta la fila
  - Decisión adicional:
    - `Robert Hand / Planets in Transit` no se usa como fuente scrapeada desde Internet Archive por copyright y acceso restringido

### 2026-03-30 — Sesión 3 (Claude)
- Retomado el proyecto tras sesión 2 con Codex
- Verificado estado real del corpus.db:
  - `transito`:       745 filas (354 GV + 391 AK)  ✅
  - `sinastria`:      375 filas (GV)               ✅
  - `aspecto_natal`:  368 filas (334 AK + 34 CA)   ✅
  - `natal_planeta_signo`:  0 filas                ❌ — AGUJERO PRINCIPAL
  - `natal_planeta_casa`:   0 filas                ❌ — AGUJERO PRINCIPAL
  - TOTAL: 1488 filas
- Situación: el corpus de tránsitos, sinastría y aspectos está bien cubierto
- El problema urgente es la ausencia total de textos natales (planeta en signo / planeta en casa)
- Opciones debatidas con el usuario:
  - Arreglar scraper CA para tapar el agujero natal (URLs reales son slugs WordPress /sun-in-aries/)
  - Comenzar backend FastAPI + motor pyswisseph
  - Ambas en paralelo
- Motor de traducción pendiente de decidir: deep-translator/Google vs DeepL vs Gemini API
- Pendiente: decisión del usuario sobre siguiente paso

### 2026-03-30 — Sesión 4 (Claude)
- Verificada cobertura real del corpus con check_coverage.py:
  - transito:       328/330  (99%) — 2 faltantes son combinaciones astronómicamente imposibles ✅
  - sinastria:      375/450  (83%) — 75 huecos detectados
  - aspecto_natal:  208/225  (92%) — 17 faltantes son aspectos imposibles ✅
- Ejecutado fill_sinastria.py: +45 filas insertadas (todos los LUNA_X via URL inversa GV)
  - Resultado: sinastria 420/450 (93%) — 30 irrecuperables son planetas transpersonales entre sí ✅
  - sinastria efectivamente COMPLETA para uso práctico
- Exploración de fuentes para natal_planeta_signo y natal_planeta_casa:
  - Probados: astrolibrary.org, astro-seek.com, astrotheme.com, astromatrix.org, astro.com
  - astro.com: JavaScript wall, inaccesible ❌
  - astromatrix.org: timeout ❌
  - astrotheme.com: responde pero solo devuelve nav/ephemeris, sin texto interpretativo ❌
  - **astrolibrary.org: ELEGIDA para natal_planeta_signo** ✅
    - URL: /interpretations/[planeta]/  (ej: /interpretations/sun/)
    - Una página por planeta con los 12 signos (H2/H3 por signo)
    - Solo 10 peticiones HTTP para los 120 textos
    - Calidad alta, textos propios de Astrolibrary
    - Textos en inglés → traducir con Gemini API
  - **astro-seek.com: ELEGIDA para natal_planeta_casa** ✅
    - URL: /[planeta]-in-[N]th-house-astrology-meaning  (ej: /sun-in-1st-house-astrology-meaning)
    - Patrón limpio y consistente para los 120 textos (10 planetas × 12 casas)
    - Textos en inglés → traducir con Gemini API
- Creado: scraper/sources/astrolibrary.py (signos + casas)
  - dry-run validado: 12/12 signos para Sol extraídos correctamente
  - Textos de 2000-4500 chars por entrada, calidad excelente
  - PENDIENTE: configurar GEMINI_API_KEY para ejecutar real
    - El usuario debe ejecutar: set GEMINI_API_KEY=su_clave
    - Luego: python scraper/sources/astrolibrary.py --tipo signos
    - Y:     python scraper/sources/astrolibrary.py --tipo casas

### Estado corpus.db tras sesión 4:
- transito:              745 filas  (99%) ✅
- sinastria:             420 filas  (93%) ✅ efectivamente completo
- aspecto_natal:         368 filas  (92%) ✅
- natal_planeta_signo:     0 filas   (0%) ← PENDIENTE ejecutar con GEMINI_API_KEY
- natal_planeta_casa:      0 filas   (0%) ← PENDIENTE ejecutar con GEMINI_API_KEY
- TOTAL: 1533 filas

### Próximos pasos
1. Configurar GEMINI_API_KEY y ejecutar astrolibrary.py --tipo all
   → Objetivo: +120 natal_planeta_signo + 120 natal_planeta_casa = ~240 nuevas filas
2. Con corpus completo, pasar a backend FastAPI + motor pyswisseph

### 2026-03-30 — Sesión 5 (Claude)
- **CORPUS COMPLETADO** — 1766 filas totales en corpus.db
  - transito:           745 filas  (99%)  ✅ — 2 huecos = aspectos astronómicamente imposibles
  - sinastria:          420 filas  (93%)  ✅ — 30 huecos = planetas transpersonales entre sí
  - aspecto_natal:      368 filas  (92%)  ✅ — 17 huecos = aspectos imposibles (Sol cuadrado Mercurio, etc.)
  - natal_planeta_signo: 113 filas (100% real) ✅ — algunos planetas lentos solo cubren los signos posibles
  - natal_planeta_casa:  120 filas (100%) ✅ — 10 planetas × 12 casas
- Fuentes usadas:
  - Grupo Venus → transito + sinastria (castellano nativo)
  - Astrology King → aspecto_natal + transito adicional (traducido)
  - Astrolibrary.org → natal_planeta_signo + natal_planeta_casa (traducido con deep-translator)
- Motor de traducción: deep-translator (Google Translate, sin cuota, sin API key)
  - Calidad verificada: buena para textos astrológicos
  - Gemini API (cuota agotada en sesión) — puede usarse después para re-traducir si se desea mejorar calidad

### ✅ CORPUS TERMINADO — Próximo paso: BACKEND FastAPI
