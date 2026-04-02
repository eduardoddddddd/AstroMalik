/**
 * Base URL para llamadas al API. En desarrollo, Vite reenvía /api al backend local.
 * En producción puedes definir VITE_API_BASE (p. ej. https://tu-servidor).
 */
export const API_BASE = import.meta.env.VITE_API_BASE ?? ''
