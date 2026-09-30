import type { Scale } from './colorScales'
import type { ForecastGrid } from '../types/forecast'

const OUTPUT_WIDTH = 1400 // px; height follows the Mercator aspect ratio (sharp contours when zoomed to a district)
// Feather the grid boundary (in cells, ~26 km each); full-coverage fields get a wider, rounder fade
const EDGE_FADE_RAIN = 6
const EDGE_FADE_FIELD = 14

const toMercY = (lat: number) => Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360))
const fromMercY = (y: number) => (360 / Math.PI) * Math.atan(Math.exp(y)) - 90

const smoothstep = (e0: number, e1: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - e0) / (e1 - e0)))
  return t * t * (3 - 2 * t)
}

export interface GridGeometry {
  bounds: [[number, number], [number, number]] // [[south, west], [north, east]] of cell edges
  latStep: number
  lonStep: number
}

export function gridGeometry(g: ForecastGrid): GridGeometry {
  const latStep = (g.lat_north - g.lat_south) / (g.rows - 1)
  const lonStep = (g.lon_east - g.lon_west) / (g.cols - 1)
  return {
    latStep,
    lonStep,
    bounds: [
      [g.lat_south - latStep / 2, g.lon_west - lonStep / 2],
      [g.lat_north + latStep / 2, g.lon_east + lonStep / 2],
    ],
  }
}

/** Bilinear sample at fractional (row, col); rows run north -> south. */
function sample(g: ForecastGrid, fi: number, fj: number): number {
  const i0 = Math.max(0, Math.min(g.rows - 1, Math.floor(fi)))
  const j0 = Math.max(0, Math.min(g.cols - 1, Math.floor(fj)))
  const i1 = Math.min(g.rows - 1, i0 + 1)
  const j1 = Math.min(g.cols - 1, j0 + 1)
  const di = Math.min(1, Math.max(0, fi - i0))
  const dj = Math.min(1, Math.max(0, fj - j0))
  const v = g.values
  const top = v[i0 * g.cols + j0] * (1 - dj) + v[i0 * g.cols + j1] * dj
  const bottom = v[i1 * g.cols + j0] * (1 - dj) + v[i1 * g.cols + j1] * dj
  return top * (1 - di) + bottom * di
}

/** Value at a lat/lon (nearest cell), or null outside the grid. */
export function valueAt(g: ForecastGrid, lat: number, lon: number): number | null {
  const { latStep, lonStep } = gridGeometry(g)
  const i = Math.round((g.lat_north - lat) / latStep)
  const j = Math.round((lon - g.lon_west) / lonStep)
  if (i < 0 || j < 0 || i >= g.rows || j >= g.cols) return null
  return g.values[i * g.cols + j]
}

/**
 * Renders the grid to a PNG data URL in Web Mercator pixel space: bilinear-smoothed values,
 * coloured *after* interpolation (crisp category contours), with feathered edges.
 */
export function rasterize(g: ForecastGrid, scale: Scale): string {
  const { bounds, latStep, lonStep } = gridGeometry(g)
  const [[south, west], [north, east]] = bounds
  const fade = scale.kind === 'stepped' ? EDGE_FADE_RAIN : EDGE_FADE_FIELD
  const yTop = toMercY(north)
  const yBottom = toMercY(south)
  const width = OUTPUT_WIDTH
  const height = Math.round((width * (yTop - yBottom)) / (((east - west) * Math.PI) / 180))

  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const ctx = canvas.getContext('2d')!
  const img = ctx.createImageData(width, height)
  const px = img.data

  for (let y = 0; y < height; y++) {
    const lat = fromMercY(yTop - ((y + 0.5) / height) * (yTop - yBottom))
    const fi = (g.lat_north - lat) / latStep
    const fadeI = smoothstep(0, fade, Math.min(fi + 0.5, g.rows - 0.5 - fi))
    if (fadeI <= 0) continue
    for (let x = 0; x < width; x++) {
      const lon = west + ((x + 0.5) / width) * (east - west)
      const fj = (lon - g.lon_west) / lonStep
      // Multiplying the two axes rounds the corners instead of leaving a hard box
      const edgeFade = fadeI * smoothstep(0, fade, Math.min(fj + 0.5, g.cols - 0.5 - fj))
      if (edgeFade <= 0) continue

      const v = sample(g, fi, fj)
      const rgb = scale.rgb(v)
      if (!rgb) continue
      const alpha = scale.alpha(v) * edgeFade
      const o = (y * width + x) * 4
      px[o] = rgb[0]
      px[o + 1] = rgb[1]
      px[o + 2] = rgb[2]
      px[o + 3] = Math.round(alpha * 255)
    }
  }

  ctx.putImageData(img, 0, 0)
  return canvas.toDataURL('image/png')
}
