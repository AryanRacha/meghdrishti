// Mirrors backend/app/schemas/forecast.py

export type Variable = 'rain' | 'temp' | 'wind'
export type Layer = 'blended' | 'gfs' | 'ai' | 'trust'
export type DataSource = 'processed' | 'synthetic' | 'live_noaa_s3'
export type WeightsMode = 'trained' | 'untrained'
export type ImdCategory = 'heavy' | 'very_heavy' | 'extremely_heavy'
export type WindCategory = 'strong_wind' | 'gale' | 'storm'
export type HeatCategory = 'heat_watch' | 'heatwave' | 'severe_heatwave'
export type ThreatCategory = ImdCategory | WindCategory | HeatCategory
export type ThreatLevel = 1 | 2 | 3

export interface RunInfo {
  date: string
  lead_time: number
  lead_time_validated: boolean
  data_source: DataSource
  weights: WeightsMode
}

export interface LayerMetadata extends RunInfo {
  variable: Variable
  layer: Layer
  units: string
  min: number
  max: number
  stride: number
  cell_count: number
}

export interface ForecastGrid {
  metadata: LayerMetadata
  lat_north: number
  lat_south: number
  lon_west: number
  lon_east: number
  rows: number
  cols: number
  values: number[] // row-major, row 0 = north
}

export interface Threat {
  id: string
  variable: Variable
  units: string // mm (rain), km/h (wind), °C (temp)
  district: string
  state: string
  distance_km: number
  lat: number
  lon: number
  peak: number
  mean: number
  area_km2: number
  category: ThreatCategory
  level: ThreatLevel // 1-3 within the hazard's scale
  severity_rank: number
  gfs_value: number
  ai_value: number
  gfs_trust: number
  population_exposed: number
  risk_index: number
}

export interface AlertsResponse {
  metadata: RunInfo
  threats: Threat[]
}

export interface VariableInfo {
  id: Variable
  label: string
  units: string
}

export interface MetaResponse {
  dates: string[]
  lead_times: number[]
  trained_lead_times: number[]
  variables: VariableInfo[]
  layers: Layer[]
  bbox: [number, number, number, number] // [south, west, north, east]
  data_source: DataSource
  weights: WeightsMode
}

export interface ForecastQuery {
  date: string
  leadTime: number
  variable: Variable
  layer: Layer
}
