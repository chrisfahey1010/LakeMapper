import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

type LakeMeta = {
  dowlknum: string
  lake_name?: string
  acres?: number
  city_name?: string
  survey_url?: string
  fish_survey?: {
    fish_species: { species_name: string; count: number; cpue?: number | null }[]
    total_fish_caught: number
    survey_date?: string | null
    survey_type?: string | null
  } | null
}

export default function LakeDetailPage() {
  const { dowlknum = '' } = useParams()
  const [meta, setMeta] = useState<LakeMeta | null>(null)
  const [merged, setMerged] = useState<any | null>(null)
  const [contours, setContours] = useState<any | null>(null)

  useEffect(() => {
    if (!dowlknum) return
    fetch(`/output/metadata/lake_${dowlknum}.json`).then(r => r.json()).then(setMeta).catch(() => setMeta(null))
    fetch(`/output/geojson/lake_${dowlknum}.geojson`).then(r => r.json()).then(setMerged).catch(() => setMerged(null))
    fetch(`/output/contours/contours_${dowlknum}.geojson`).then(r => r.json()).then(setContours).catch(() => setContours(null))
  }, [dowlknum])

  const bounds = useMemo(() => {
    const g = (merged?.features?.[0]?.geometry) || (contours?.features?.[0]?.geometry)
    return g ? undefined : undefined
  }, [merged, contours])

  const species = meta?.fish_survey?.fish_species || []

  return (
    <section className="lake-detail">
      <h1>{meta?.lake_name || 'Lake'} <span className="muted">({dowlknum})</span></h1>
      <div className="grid">
        <div className="panel map-panel">
          <MapContainer style={{ height: 480, width: '100%' }} center={[46.3, -94.2]} zoom={9} scrollWheelZoom>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {merged && <GeoJSON data={merged} style={{ color: '#1d4ed8', weight: 2, fillOpacity: 0.15 }} />}
            {contours && <GeoJSON data={contours} style={{ color: '#0f766e', weight: 1 }} />}
          </MapContainer>
        </div>
        <div className="panel">
          <h2>Lake info</h2>
          <div className="kv">
            <div>Acres</div>
            <div>{meta?.acres ? Math.round(meta.acres).toLocaleString() : '—'}</div>
            <div>City</div>
            <div>{meta?.city_name || '—'}</div>
            <div>Survey</div>
            <div>{meta?.survey_url ? <a href={meta.survey_url} target="_blank" rel="noreferrer">DNR report</a> : '—'}</div>
          </div>
          <h2>Species</h2>
          {species.length === 0 && <div className="muted">No fish survey data.</div>}
          {species.length > 0 && (
            <div className="table">
              <div className="table__head">
                <div>Species</div>
                <div>Count</div>
                <div>CPUE</div>
              </div>
              <div className="table__body">
                {species.map(s => (
                  <div className="row" key={s.species_name}>
                    <div>{s.species_name}</div>
                    <div>{s.count}</div>
                    <div>{s.cpue ?? '—'}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}


