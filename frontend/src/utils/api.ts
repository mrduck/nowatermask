const API_BASE = import.meta.env.PROD
  ? (import.meta.env.VITE_API_BASE || 'https://nowatermask.onrender.com/api')
  : '/api'

async function apiFetch(path: string, body: FormData): Promise<Blob> {
  const res = await fetch(`${API_BASE}${path}`, { method: 'POST', body })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`API ${res.status}: ${text || res.statusText}`)
  }
  return res.blob()
}

export async function removeWatermarkManual(
  file: File,
  maskBlob: Blob,
  onProgress?: (pct: number) => void
): Promise<Blob> {
  onProgress?.(10)
  const formData = new FormData()
  formData.append('file', file)
  formData.append('mask', maskBlob, 'mask.png')
  onProgress?.(30)
  const blob = await apiFetch('/remove/manual', formData)
  onProgress?.(80)
  onProgress?.(100)
  return blob
}

export async function cropPhoto(
  file: File,
  x: number, y: number, w: number, h: number,
  targetW: number, targetH: number
): Promise<Blob> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('x', String(x))
  formData.append('y', String(y))
  formData.append('w', String(w))
  formData.append('h', String(h))
  formData.append('target_w', String(targetW))
  formData.append('target_h', String(targetH))
  return apiFetch('/crop', formData)
}

export async function generateLayout(file: File, spec: string): Promise<Blob> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('spec', spec)
  return apiFetch('/layout', formData)
}

export async function compressImage(file: File, quality: number, format: string): Promise<Blob> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('quality', String(quality))
  formData.append('fmt', format)
  return apiFetch('/compress', formData)
}