# AstroMalik — frontend (`astromalik-web`)

## Desarrollo

1. **API** (desde `../backend`, puerto **8765**):

   ```powershell
   cd ..\backend
   .\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8765
   ```

   Tras cambiar el backend, **reinicia uvicorn** para cargar rutas nuevas.

2. **Frontend** (proxy `/api` → `8765`):

   ```powershell
   npm run dev
   ```

3. **http://127.0.0.1:5173/** — **Calcular carta** → `POST /api/charts/natal` (Placidus, núcleo alineado con AstroBot). También lugar, **Guardar carta** (`backend/data/user.db`).

En el **backend**, instala dependencias incluida **`tzdata`** (necesaria en Windows para `Europe/Madrid` y otras IANA).

---

Plantilla: React + TypeScript + Vite.
