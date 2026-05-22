/**
 * Backend API base URL.
 *
 * - Local development: leave empty, proxied by Vite to http://localhost:7860
 * - Docker production: leave empty, proxied by nginx to backend:7860
 * - Vercel / Standalone frontend: set VITE_API_BASE_URL=https://your-backend.example.com
 */
export const API_BASE: string = (import.meta.env.VITE_API_BASE_URL as string) ?? ''
