import { useEffect } from 'react'
import { useMap } from 'react-leaflet'
import { valueAt } from '../../lib/rasterize'
import type { ForecastGrid } from '../../types/forecast'

const MAX_DROPS = 2000
const DROPS_PER_SPOT = 0.9 // density relative to rainy screen area
const SPOT_PX = 10 // coarse screen lookup cell
const MIN_RAIN_MM = 2.5 // below IMD "light": no streaks
const WIND_SLANT = 0.22 // horizontal drift per unit fall
const ALPHA_LEVELS = 4 // batched stroke passes

interface Drop {
  x: number
  y: number
  speed: number
  length: number
  level: number
  life: number
}

/** 0..1 intensity from rainfall (mm): drizzle ~0.1, heavy (64.5) ~0.8, very heavy+ 1. */
const intensity = (mm: number) => Math.min(1, Math.log1p(mm - MIN_RAIN_MM + 1) / Math.log1p(100))

/**
 * Screen-space rain streaks on a canvas above the map. Drops spawn only where the forecast
 * has rain (weighted by intensity); length and speed scale with intensity.
 */
export function RainAnimation({ grid }: { grid: ForecastGrid }) {
  const map = useMap()

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return

    const container = map.getContainer()
    const canvas = document.createElement('canvas')
    canvas.className = 'rain-canvas'
    container.appendChild(canvas)
    const ctx = canvas.getContext('2d')!
    const dpr = Math.min(window.devicePixelRatio || 1, 2)

    // Weighted spawn table over coarse screen cells: [x, y, intensity] + cumulative weights
    let spots: Float32Array = new Float32Array(0)
    let cumulative: Float32Array = new Float32Array(0)
    let target = 0
    // Coarse rainy/dry mask so drops vanish when they leave the rain area
    let mask = new Uint8Array(0)
    let maskCols = 0
    let maskRows = 0

    const isRainy = (x: number, y: number) => {
      const cx = Math.floor(x / SPOT_PX)
      const cy = Math.floor(y / SPOT_PX)
      return cx >= 0 && cy >= 0 && cx < maskCols && cy < maskRows && mask[cy * maskCols + cx] === 1
    }

    const rebuild = () => {
      const { x: w, y: h } = map.getSize()
      canvas.width = w * dpr
      canvas.height = h * dpr
      canvas.style.width = `${w}px`
      canvas.style.height = `${h}px`
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

      const found: number[] = []
      const weights: number[] = []
      let total = 0
      maskCols = Math.ceil(w / SPOT_PX)
      maskRows = Math.ceil(h / SPOT_PX)
      mask = new Uint8Array(maskCols * maskRows)
      for (let cy = 0; cy < maskRows; cy++) {
        for (let cx = 0; cx < maskCols; cx++) {
          const x = (cx + 0.5) * SPOT_PX
          const y = (cy + 0.5) * SPOT_PX
          const ll = map.containerPointToLatLng([x, y])
          const mm = valueAt(grid, ll.lat, ll.lng) ?? 0
          if (mm < MIN_RAIN_MM) continue
          mask[cy * maskCols + cx] = 1
          const k = intensity(mm)
          found.push(x, y, k)
          total += 0.15 + 0.85 * k
          weights.push(total)
        }
      }
      spots = Float32Array.from(found)
      cumulative = Float32Array.from(weights)
      target = Math.min(MAX_DROPS, Math.round(weights.length * DROPS_PER_SPOT))
      drops.length = 0
    }

    const spawn = (): Drop | null => {
      const n = cumulative.length
      if (n === 0) return null
      const r = Math.random() * cumulative[n - 1]
      let lo = 0
      let hi = n - 1
      while (lo < hi) {
        const mid = (lo + hi) >> 1
        if (cumulative[mid] < r) lo = mid + 1
        else hi = mid
      }
      const k = spots[lo * 3 + 2]
      return {
        x: spots[lo * 3] + (Math.random() - 0.5) * SPOT_PX,
        y: spots[lo * 3 + 1] + (Math.random() - 0.5) * SPOT_PX,
        speed: 5 + 9 * k + Math.random() * 3,
        length: 7 + 16 * k + Math.random() * 5,
        level: Math.min(ALPHA_LEVELS - 1, Math.floor(k * ALPHA_LEVELS)),
        life: 8 + Math.random() * 14,
      }
    }

    const drops: Drop[] = []
    rebuild()

    let frame = 0
    const tick = () => {
      const { x: w, y: h } = map.getSize()
      ctx.clearRect(0, 0, w, h)

      while (drops.length < target) {
        const d = spawn()
        if (!d) break
        drops.push(d)
      }

      ctx.lineCap = 'round'
      ctx.lineWidth = 1.1
      for (let level = 0; level < ALPHA_LEVELS; level++) {
        ctx.strokeStyle = `rgba(210, 235, 255, ${0.2 + 0.16 * level})`
        ctx.beginPath()
        for (let i = 0; i < drops.length; i++) {
          const d = drops[i]
          if (d.level !== level) continue
          ctx.moveTo(d.x, d.y)
          ctx.lineTo(d.x - d.length * WIND_SLANT, d.y - d.length)
        }
        ctx.stroke()
      }

      for (let i = 0; i < drops.length; i++) {
        const d = drops[i]
        d.x += d.speed * WIND_SLANT
        d.y += d.speed
        d.life -= 1
        if (d.life <= 0 || d.y > h || !isRainy(d.x, d.y)) {
          const fresh = spawn()
          if (fresh) drops[i] = fresh
        }
      }
      frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)

    // Streaks are screen-space: hide while the map moves, rebuild the spawn table after
    const hide = () => (canvas.style.opacity = '0')
    const show = () => {
      rebuild()
      canvas.style.opacity = '1'
    }
    map.on('movestart zoomstart', hide)
    map.on('moveend zoomend resize', show)

    return () => {
      cancelAnimationFrame(frame)
      map.off('movestart zoomstart', hide)
      map.off('moveend zoomend resize', show)
      canvas.remove()
    }
  }, [map, grid])

  return null
}
