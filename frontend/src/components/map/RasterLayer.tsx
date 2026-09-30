import L from 'leaflet'
import { useEffect, useMemo, useRef } from 'react'
import { useMap } from 'react-leaflet'
import type { Scale } from '../../lib/colorScales'
import { formatValue } from '../../lib/format'
import { gridGeometry, rasterize, valueAt } from '../../lib/rasterize'
import type { ForecastGrid } from '../../types/forecast'

interface RasterLayerProps {
  grid: ForecastGrid
  scale: Scale
  pane?: string
  /** Show a hover tooltip with the cell value (only one layer should, in swipe mode). */
  tooltip?: boolean
}

export function RasterLayer({ grid, scale, pane = 'overlayPane', tooltip = true }: RasterLayerProps) {
  const map = useMap()
  const url = useMemo(() => rasterize(grid, scale), [grid, scale])
  const overlays = useRef<L.ImageOverlay[]>([])

  // Swap images without a blank frame: add the new overlay, drop older ones once it has loaded
  useEffect(() => {
    const next = L.imageOverlay(url, gridGeometry(grid).bounds, { pane, className: 'forecast-raster' })
    next.once('load', () => {
      // Ignore late loads from overlays that were already removed (e.g. StrictMode remount)
      if (!overlays.current.includes(next)) return
      overlays.current = overlays.current.filter((o) => {
        if (o === next) return true
        o.remove()
        return false
      })
    })
    overlays.current.push(next)
    next.addTo(map)
  }, [url, grid, map, pane])

  useEffect(
    () => () => {
      overlays.current.forEach((o) => o.remove())
      overlays.current = []
    },
    [],
  )

  useEffect(() => {
    if (!tooltip) return
    const tip = L.tooltip({ className: 'cell-tooltip', direction: 'top', offset: [0, -8] })
    const { layer, units } = grid.metadata
    const onMove = (e: L.LeafletMouseEvent) => {
      const v = valueAt(grid, e.latlng.lat, e.latlng.lng)
      if (v === null || (layer !== 'trust' && grid.metadata.variable === 'rain' && v < 1)) {
        tip.remove()
        return
      }
      tip.setLatLng(e.latlng).setContent(formatValue(v, layer, units))
      if (!map.hasLayer(tip)) tip.addTo(map)
    }
    const onOut = () => tip.remove()
    map.on('mousemove', onMove)
    map.on('mouseout', onOut)
    return () => {
      map.off('mousemove', onMove)
      map.off('mouseout', onOut)
      tip.remove()
    }
  }, [grid, map, tooltip])

  return null
}
