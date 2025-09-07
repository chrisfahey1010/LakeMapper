import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { indexJsonPath } from '@/lib/dataPaths'

type LakeIndexRecord = {
  dowlknum: string
  lake_name: string
  acres: number
  city_name: string
  contour_count: number
  min_depth: number
  max_depth: number
}

export default function LakeListPage() {
  const [records, setRecords] = useState<LakeIndexRecord[]>([])
  const [query, setQuery] = useState('')

  useEffect(() => {
    fetch(indexJsonPath())
      .then(r => r.json())
      .then(setRecords)
      .catch(() => setRecords([]))
  }, [])

  const filtered = useMemo(() => {
    if (!query) return records
    const q = query.toLowerCase()
    return records.filter(r =>
      (r.lake_name || '').toLowerCase().includes(q) ||
      r.dowlknum.includes(q) ||
      (r.city_name || '').toLowerCase().includes(q)
    )
  }, [records, query])

  return (
    <section>
      <div className="toolbar">
        <input
          placeholder="Search by name, DOWLKNUM, or city"
          value={query}
          onChange={e => setQuery(e.target.value)}
          className="input"
        />
        <div className="hint">{filtered.length} lakes</div>
      </div>

      <div className="table">
        <div className="table__head">
          <div>Name</div>
          <div>DOWLKNUM</div>
          <div>Acres</div>
          <div>City</div>
          <div>Contours</div>
          <div>Depth (min/max)</div>
        </div>
        <div className="table__body">
          {filtered.map(r => (
            <Link to={`/lake/${r.dowlknum}`} className="row" key={r.dowlknum}>
              <div>{r.lake_name || 'Unknown'}</div>
              <div>{r.dowlknum}</div>
              <div>{Math.round(r.acres).toLocaleString()}</div>
              <div>{r.city_name || '—'}</div>
              <div>{r.contour_count}</div>
              <div>{r.min_depth} / {r.max_depth} ft</div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  )
}


