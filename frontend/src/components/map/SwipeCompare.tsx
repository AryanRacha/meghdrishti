import { useEffect } from 'react'
import { Pane, useMap } from 'react-leaflet'
import type { Scale } from '../../lib/colorScales'
import type { ForecastGrid } from '../../types/forecast'
import { RasterLayer } from './RasterLayer'

const LEFT_PANE = 'swipe-left'
const RIGHT_PANE = 'swipe-right'

interface SwipeCompareProps {
  left: ForecastGrid
  right: ForecastGrid
  scale: Scale
  position: number // 0..1 across the map container
}

/** Two heatmaps in separate panes, clipped either side of a vertical divider (leaflet-side-by-side technique). */
export function SwipeCompare({ left, right, scale, position }: SwipeCompareProps) {
  const map = useMap()

  useEffect(() => {
    const update = () => {
      const leftPane = map.getPane(LEFT_PANE)
      const rightPane = map.getPane(RIGHT_PANE)
      if (!leftPane || !rightPane) return
      const size = map.getSize()
      const nw = map.containerPointToLayerPoint([0, 0])
      const se = map.containerPointToLayerPoint(size)
      const x = nw.x + size.x * position
      leftPane.style.clip = `rect(${nw.y}px, ${x}px, ${se.y}px, ${nw.x}px)`
      rightPane.style.clip = `rect(${nw.y}px, ${se.x}px, ${se.y}px, ${x}px)`
    }
    update()
    map.on('move zoom resize viewreset zoomanim', update)
    return () => {
      map.off('move zoom resize viewreset zoomanim', update)
    }
  }, [map, position, left, right])

  return (
    <>
      <Pane name={LEFT_PANE} style={{ zIndex: 401 }}>
        <RasterLayer grid={left} scale={scale} pane={LEFT_PANE} tooltip={false} />
      </Pane>
      <Pane name={RIGHT_PANE} style={{ zIndex: 402 }}>
        <RasterLayer grid={right} scale={scale} pane={RIGHT_PANE} />
      </Pane>
    </>
  )
}
