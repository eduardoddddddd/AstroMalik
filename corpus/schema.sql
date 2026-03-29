-- corpus/schema.sql
-- Esquema completo de corpus.db para AstroMalik

CREATE TABLE IF NOT EXISTS interpretaciones (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo          TEXT NOT NULL CHECK(tipo IN (
                    'natal_planeta_signo',
                    'natal_planeta_casa',
                    'aspecto_natal',
                    'transito',
                    'sinastria'
                  )),
    clave         TEXT NOT NULL,
    autor         TEXT,
    fuente_url    TEXT,
    fuente_nombre TEXT,
    idioma_origen TEXT DEFAULT 'es',
    texto_corto   TEXT,
    texto_largo   TEXT NOT NULL,
    calidad       INTEGER DEFAULT 3 CHECK(calidad BETWEEN 1 AND 5),
    fecha_scrape  TEXT DEFAULT (date('now')),
    UNIQUE(clave, fuente_url)
);

CREATE INDEX IF NOT EXISTS idx_tipo_clave ON interpretaciones(tipo, clave);
CREATE INDEX IF NOT EXISTS idx_clave ON interpretaciones(clave);

-- Vista útil para ver cobertura del corpus
CREATE VIEW IF NOT EXISTS cobertura AS
SELECT tipo, clave, COUNT(*) as num_fuentes, GROUP_CONCAT(fuente_nombre, ' | ') as fuentes
FROM interpretaciones
GROUP BY tipo, clave
ORDER BY tipo, clave;
