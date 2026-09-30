import L from 'leaflet'
import { useEffect, useMemo } from 'react'
import { CircleMarker, Marker, Tooltip, useMap } from 'react-leaflet'
import { CATEGORY_COLORS, CATEGORY_LABELS } from '../../lib/format'
import type { Threat } from '../../types/forecast'

interface ThreatMarkersProps {
  threats: Threat[]
  selectedId: string | null
  onSelect: (id: string) => void
}

const FOCUS_ZOOM = 7

function pulseIcon(color: string): L.DivIcon {
  return L.divIcon({
    className: '',
    html: `<div class="threat-pulse" style="--pulse-color:${color};width:44px;height:44px"><span></span><span></span><i></i></div>`,
    iconSize: [44, 44],
    iconAnchor: [22, 22],
  })
}

export function ThreatMarkers({ threats, selectedId, onSelect }: ThreatMarkersProps) {
  const map = useMap()
  const selected = threats.find((t) => t.id === selectedId) ?? null
  const icon = useMemo(() => (selected ? pulseIcon(CATEGORY_COLORS[selected.category]) : null), [selected])

  useEffect(() => {
    if (!selected) return
    map.flyTo([selected.lat, selected.lon], Math.max(map.getZoom(), FOCUS_ZOOM), { duration: 1.2 })
  }, [selected, map])

  return (
    <>
      {threats.map((t) => (
        <CircleMarker
          key={t.id}
          center={[t.lat, t.lon]}
          radius={t.id === selectedId ? 0 : 7}
          pathOptions={{ color: CATEGORY_COLORS[t.category], weight: 2, fillOpacity: 0.2 }}
          eventHandlers={{ click: () => onSelect(t.id) }}
        >
          <Tooltip className="cell-tooltip" direction="top" offset={[0, -6]}>
            #{t.severity_rank} {t.district} · {t.peak_mm} mm · {CATEGORY_LABELS[t.category]}
          </Tooltip>
        </CircleMarker>
      ))}
      {selected && icon && <Marker position={[selected.lat, selected.lon]} icon={icon} interactive={false} />}
    </>
  )
}
