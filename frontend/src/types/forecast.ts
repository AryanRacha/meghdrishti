// Mirrors backend/app/schemas/forecast.py

export type Variable = 'rain' | 'temp' | 'wind'
export type Layer = 'blended' | 'gfs' | 'ai' | 'trust'
export type DataSource = 'processed' | 'synthetic'
export type WeightsMode = 'trained' | 'untrained'
export type ImdCategory = 'heavy' | 'very_heavy' | 'extremely_heavy'

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
  district: string
  state: string
  distance_km: number
  lat: number
  lon: number
  peak_mm: number
  mean_mm: number
  area_km2: number
  category: ImdCategory
  severity_rank: number
  gfs_mm: number
  ai_mm: number
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
