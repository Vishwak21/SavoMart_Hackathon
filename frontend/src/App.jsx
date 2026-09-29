import { useEffect, useState } from 'react'
import './App.css'

const icons = {
  Overview: '#',
  'Area intelligence': '?',
  'Property pipeline': '$',
  'Catchment studies': 'o',
  'My assignments': '+',
  'Captured properties': '@',
  'Catchment requests': 'o',
  'Survey assignments': '+',
  'Field team': '&',
  'My survey work': '+',
  'Submitted observations': 'v',
}

const demoUsers = [
  { id: 'bd-manager', name: 'Arjun Raman', role: 'BD Manager', initials: 'AR' },
  { id: 'bd-executive', name: 'Meera Kumar', role: 'BD Executive', initials: 'MK' },
  { id: 'survey-manager', name: 'Nila Shankar', role: 'Survey Manager', initials: 'NS' },
  { id: 'survey-executive', name: 'Kavin Raj', role: 'Survey Executive', initials: 'KR' },
]

const roleViews = {
  'BD Manager': {
    title: 'Expansion overview',
    description: 'Area intelligence, property decisions, and catchment validation in one place.',
    items: [
      { label: 'Area intelligence' },
      { label: 'Property pipeline' },
      { label: 'Catchment studies' },
    ],
    metrics: ['Areas analysed', 'Properties in review', 'Catchment studies'],
    workTitle: 'Decision workspace',
    emptyTitle: 'Your expansion workspace is ready',
    emptyDescription: 'Area reports, property reviews, and survey findings will appear here as the team works.',
  },
  'BD Executive': {
    title: 'Scouting workspace',
    description: 'Your assigned locations and candidate properties, ready for field work.',
    items: [
      { label: 'My assignments' },
      { label: 'Captured properties' },
    ],
    metrics: ['Open assignments', 'Properties captured', 'Awaiting review'],
    workTitle: 'My field work',
    emptyTitle: 'No scouting assignments yet',
    emptyDescription: 'When a manager assigns a hotspot, it will show up here.',
  },
  'Survey Manager': {
    title: 'Survey operations',
    description: 'Coordinate catchment requests and keep field survey work moving.',
    items: [
      { label: 'Catchment requests' },
      { label: 'Survey assignments' },
      { label: 'Field team' },
    ],
    metrics: ['Pending requests', 'Active assignments', 'Completed surveys'],
    workTitle: 'Survey queue',
    emptyTitle: 'No survey requests in the queue',
    emptyDescription: 'New catchment requests from the business development team will appear here.',
  },
  'Survey Executive': {
    title: 'Field surveys',
    description: 'Your assigned survey sections and the latest ground observations.',
    items: [
      { label: 'My survey work' },
      { label: 'Submitted observations' },
    ],
    metrics: ['Assigned sections', 'In progress', 'Submitted'],
    workTitle: 'My survey assignments',
    emptyTitle: 'No survey sections assigned',
    emptyDescription: 'Your survey manager will assign a work area when a catchment study is planned.',
  },
}

function AreaIntelligence() {
  const [query, setQuery] = useState('')
  const [matchResult, setMatchResult] = useState({ query: '', areas: [] })
  const [selectedArea, setSelectedArea] = useState(null)
  const [report, setReport] = useState(null)
  const [reports, setReports] = useState([])
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let isMounted = true

    fetch('/api/areas/reports')
      .then((response) => {
        if (!response.ok) throw new Error('Could not load saved reports')
        return response.json()
      })
      .then((savedReports) => {
        if (isMounted) setReports(savedReports)
      })
      .catch(() => {
        if (isMounted) setError('Saved reports are temporarily unavailable.')
      })

    return () => {
      isMounted = false
    }
  }, [])

  useEffect(() => {
    const searchTerm = query.trim()
    if (searchTerm.length < 2 || selectedArea?.name === searchTerm) {
      return undefined
    }

    let isCurrent = true
    const timer = window.setTimeout(() => {
      fetch(`/api/areas/search?q=${encodeURIComponent(searchTerm)}`)
        .then((response) => response.json())
        .then((results) => {
          if (isCurrent) setMatchResult({ query: searchTerm, areas: results })
        })
        .catch(() => {
          if (isCurrent) setMatchResult({ query: searchTerm, areas: [] })
        })
    }, 180)

    return () => {
      isCurrent = false
      window.clearTimeout(timer)
    }
  }, [query, selectedArea])

  function chooseArea(area) {
    setSelectedArea(area)
    setQuery(area.name)
    setError('')
  }

  async function analyzeSelectedArea(event) {
    event.preventDefault()
    if (!selectedArea) return

    setIsAnalyzing(true)
    setError('')
    try {
      const response = await fetch('/api/areas/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ locality_id: selectedArea.id }),
      })
      const result = await response.json()
      if (!response.ok) throw new Error(result.detail || 'Area analysis failed')
      setReport(result)
      setReports((currentReports) => [result, ...currentReports.filter((item) => item.id !== result.id)])
    } catch (requestError) {
      setError(requestError.message || 'Area analysis is unavailable. Try again shortly.')
    } finally {
      setIsAnalyzing(false)
    }
  }

  const mapUrl = report
    ? `https://www.openstreetmap.org/export/embed.html?bbox=${report.longitude - 0.018}%2C${report.latitude - 0.014}%2C${report.longitude + 0.018}%2C${report.latitude + 0.014}&layer=mapnik&marker=${report.latitude}%2C${report.longitude}`
    : null
  const matches = matchResult.query === query.trim() && selectedArea?.name !== query.trim()
    ? matchResult.areas
    : []
  const scoreLabels = {
    residential_potential: 'Residential potential',
    commercial_demand: 'Commercial demand',
    amenities: 'Nearby amenities',
    road_accessibility: 'Road accessibility',
    transit_accessibility: 'Transit access',
    competition: 'Competition',
    savomart_proximity: 'Savomart proximity',
  }

  return (
    <div className="area-workspace">
      <section className="area-toolbar">
        <form className="locality-search" onSubmit={analyzeSelectedArea}>
          <label htmlFor="locality-search">Chennai locality</label>
          <div className="search-row">
            <div className="search-input-wrap">
              <input
                autoComplete="off"
                id="locality-search"
                onChange={(event) => {
                  setQuery(event.target.value)
                  setSelectedArea(null)
                  setReport(null)
                }}
                placeholder="Search T. Nagar, Anna Nagar, Adyar..."
                value={query}
              />
              {matches.length > 0 && (
                <ul className="search-suggestions">
                  {matches.map((area) => (
                    <li key={area.id}>
                      <button onClick={() => chooseArea(area)} type="button">
                        <span>{area.name}</span><small>Chennai</small>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <button className="analyze-button" disabled={!selectedArea || isAnalyzing} type="submit">
              {isAnalyzing ? 'Analyzing...' : 'Analyze area'}
            </button>
          </div>
          <p className="search-hint">Analysis covers a 1.2 km radius around the selected locality.</p>
          {error && <p className="area-error" role="alert">{error}</p>}
        </form>
        <div className="source-note">
          <span className="source-dot" />
          <span>OpenStreetMap signals</span>
        </div>
      </section>

      {report ? (
        <>
          <section className="area-result-heading">
            <div>
              <p className="eyebrow">FITNESS REPORT</p>
              <h2>{report.area_name}</h2>
              <p>{report.radius_m.toLocaleString()} m catchment · {report.data_source}</p>
            </div>
            <div className={`data-badge ${report.data_source.includes('Demo') ? 'demo' : ''}`}>
              {report.data_source.includes('Demo') ? 'DEMO DATA' : 'LIVE OSM DATA'}
            </div>
          </section>

          <section className="area-result-grid">
            <div className="area-map-panel">
              <div className="map-panel-heading">
                <h3>Catchment map</h3>
                <span>1.2 KM RADIUS</span>
              </div>
              <iframe
                className="catchment-map"
                loading="lazy"
                referrerPolicy="no-referrer"
                src={mapUrl}
                title={`${report.area_name} catchment map`}
              />
              <p className="map-caption">Map data © OpenStreetMap contributors</p>
            </div>

            <div className="fitness-panel">
              <div className="fitness-score-row">
                <div>
                  <p className="eyebrow">AREA FITNESS</p>
                  <strong>{report.fitness_score}<span>/100</span></strong>
                </div>
                <span className="score-status">{report.fitness_score >= 70 ? 'Promising' : report.fitness_score >= 50 ? 'Needs review' : 'Low signal'}</span>
              </div>
              <div className="score-breakdown">
                {Object.entries(report.metrics.score_breakdown).map(([key, item]) => (
                  <div className="score-line" key={key}>
                    <div className="score-line-label"><span>{scoreLabels[key]}</span><small>{item.score} · {item.weight}%</small></div>
                    <div className="score-track"><span style={{ width: `${item.score}%` }} /></div>
                  </div>
                ))}
              </div>
              <div className="signal-counts">
                <span>{report.metrics.counts.residential_features} residential signals</span>
                <span>{report.metrics.counts.commercial_features} shops and businesses</span>
                <span>{report.metrics.counts.competitors} grocery competitors</span>
              </div>
            </div>
          </section>

          <section className="area-insights-grid">
            <div>
              <p className="eyebrow">POSITIVE SIGNAL</p>
              {report.highlights.map((highlight) => <p className="insight-line" key={highlight}>{highlight}</p>)}
            </div>
            <div>
              <p className="eyebrow">TO VALIDATE</p>
              {report.risks.map((risk) => <p className="insight-line" key={risk}>{risk}</p>)}
            </div>
          </section>
        </>
      ) : (
        <section className="area-empty-state">
          <span className="area-empty-mark">A</span>
          <h2>Start with a Chennai locality</h2>
          <p>Search for an area to review its residential, commercial, access, transit, and competition signals.</p>
        </section>
      )}

      <section className="saved-reports">
        <div className="saved-reports-heading">
          <div><p className="eyebrow">HISTORY</p><h3>Recent area reports</h3></div>
          <span>{reports.length} saved</span>
        </div>
        {reports.length === 0 ? (
          <p className="history-empty">Saved analyses will appear here.</p>
        ) : (
          <div className="report-list">
            {reports.map((savedReport) => (
              <button
                className={`report-row ${report?.id === savedReport.id ? 'is-selected' : ''}`}
                key={savedReport.id}
                onClick={() => setReport(savedReport)}
                type="button"
              >
                <span className="report-name">{savedReport.area_name}<small>{savedReport.data_source}</small></span>
                <span className="report-score">{savedReport.fitness_score}<small>/100</small></span>
              </button>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

function PropertyPipeline() {
  const [properties, setProperties] = useState([])
  const [error, setError] = useState('')
  const [form, setForm] = useState({
    locality_id: 'anna-nagar',
    address: '12th Main Road, Anna Nagar',
    latitude: 13.085,
    longitude: 80.2101,
    monthly_rent: 420000,
    property_area_sqft: 1400,
    frontage_m: 16,
    road_width_m: 12,
    parking_slots: 2,
    visibility: 8,
    condition: 'good',
    notes: 'Near residential cluster and daily retail traffic.',
  })

  useEffect(() => {
    fetch('/api/properties')
      .then((response) => response.json())
      .then((items) => setProperties(items))
      .catch(() => setError('Property pipeline is temporarily unavailable.'))
  }, [])

  async function submitProperty(event) {
    event.preventDefault()
    try {
      const response = await fetch('/api/properties', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      const result = await response.json()
      if (!response.ok) throw new Error(result.detail || 'Property save failed')
      setProperties((current) => [result, ...current])
      setError('')
    } catch (requestError) {
      setError(requestError.message || 'Could not save property.')
    }
  }

  return (
    <div className="area-workspace">
      <section className="area-toolbar">
        <form className="locality-search" onSubmit={submitProperty}>
          <label htmlFor="property-address">Candidate property</label>
          <div className="search-row" style={{ alignItems: 'flex-end' }}>
            <div className="search-input-wrap" style={{ width: '100%' }}>
              <input
                id="property-address"
                onChange={(event) => setForm((current) => ({ ...current, address: event.target.value }))}
                placeholder="Enter property address"
                value={form.address}
              />
            </div>
            <button className="analyze-button" type="submit">Capture property</button>
          </div>
          {error && <p className="area-error" role="alert">{error}</p>}
        </form>
      </section>

      <section className="area-result-grid">
        <div className="area-map-panel">
          <div className="map-panel-heading">
            <h3>Property inputs</h3>
            <span>FIELD FIT</span>
          </div>
          <div className="score-breakdown" style={{ padding: '18px' }}>
            <div className="score-line">
              <div className="score-line-label"><span>Area</span><small>{form.locality_id}</small></div>
            </div>
            <div className="score-line">
              <div className="score-line-label"><span>Monthly rent</span><small>₹{Number(form.monthly_rent).toLocaleString()}</small></div>
            </div>
            <div className="score-line">
              <div className="score-line-label"><span>Area size</span><small>{form.property_area_sqft} sqft</small></div>
            </div>
            <div className="score-line">
              <div className="score-line-label"><span>Frontage</span><small>{form.frontage_m} m</small></div>
            </div>
            <div className="score-line">
              <div className="score-line-label"><span>Road width</span><small>{form.road_width_m} m</small></div>
            </div>
          </div>
        </div>

        <div className="fitness-panel">
          <div className="fitness-score-row">
            <div>
              <p className="eyebrow">PROPERTY SCREEN</p>
              <strong>{properties[0]?.score ?? 0}<span>/100</span></strong>
            </div>
            <span className="score-status">{properties[0]?.status ?? 'SCOUTED'}</span>
          </div>
          <div className="signal-counts">
            <span>{form.parking_slots} parking slots</span>
            <span>{form.visibility}/10 visibility</span>
            <span>{form.condition}</span>
          </div>
        </div>
      </section>

      <section className="saved-reports">
        <div className="saved-reports-heading">
          <div><p className="eyebrow">PIPELINE</p><h3>Candidate properties</h3></div>
          <span>{properties.length} records</span>
        </div>
        {properties.length === 0 ? (
          <p className="history-empty">No captured properties yet.</p>
        ) : (
          <div className="report-list">
            {properties.map((property) => (
              <div className="report-row" key={property.id}>
                <span className="report-name">{property.address}<small>{property.area_name}</small></span>
                <span className="report-score">{property.score}<small>/100</small></span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

function CatchmentStudies() {
  const [requests, setRequests] = useState([])

  useEffect(() => {
    fetch('/api/catchment-requests')
      .then((response) => response.json())
      .then((items) => setRequests(items))
      .catch(() => setRequests([]))
  }, [])

  async function requestCatchment() {
    const payload = {
      locality_id: 'anna-nagar',
      area_name: 'Anna Nagar',
      target_type: 'area',
      reason: 'Need lane validation before opening a new store cluster.',
    }

    const response = await fetch('/api/catchment-requests', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })

    if (response.ok) {
      const created = await response.json()
      setRequests((current) => [created, ...current])
    }
  }

  return (
    <div className="area-workspace">
      <section className="area-toolbar">
        <div className="locality-search">
          <label>Catchment request</label>
          <div className="search-row">
            <div className="search-input-wrap" style={{ width: '100%' }}>
              <input value="Anna Nagar" readOnly />
            </div>
            <button className="analyze-button" onClick={requestCatchment} type="button">Request study</button>
          </div>
        </div>
      </section>

      <section className="saved-reports">
        <div className="saved-reports-heading">
          <div><p className="eyebrow">QUEUE</p><h3>Catchment requests</h3></div>
          <span>{requests.length} items</span>
        </div>
        {requests.length === 0 ? (
          <p className="history-empty">No catchment requests yet.</p>
        ) : (
          <div className="report-list">
            {requests.map((request) => (
              <div className="report-row" key={request.id}>
                <span className="report-name">{request.area_name}<small>{request.target_type}</small></span>
                <span className="report-score">{request.status}<small>{request.reason}</small></span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

function App() {
  const [selectedUserId, setSelectedUserId] = useState(demoUsers[0].id)
  const [activeSection, setActiveSection] = useState('Overview')
  const [apiStatus, setApiStatus] = useState('checking')
  const selectedUser = demoUsers.find((user) => user.id === selectedUserId)
  const roleView = roleViews[selectedUser.role]

  useEffect(() => {
    let isMounted = true

    fetch('/api/health')
      .then((response) => {
        if (!response.ok) throw new Error('API is unavailable')
        return response.json()
      })
      .then(() => {
        if (isMounted) setApiStatus('online')
      })
      .catch(() => {
        if (isMounted) setApiStatus('offline')
      })

    return () => {
      isMounted = false
    }
  }, [])

  function changeRole(event) {
    setSelectedUserId(event.target.value)
    setActiveSection('Overview')
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="/" aria-label="Savo SiteScout home">
          <span className="brand-mark">S</span>
          <span className="brand-name">savo<span>scout</span></span>
        </a>

        <div className="workspace-label">WORKSPACE</div>
        <nav className="sidebar-nav" aria-label="Main navigation">
          <button
            className={`nav-item ${activeSection === 'Overview' ? 'is-active' : ''}`}
            onClick={() => setActiveSection('Overview')}
            type="button"
          >
            <span className="nav-icon" aria-hidden="true">{icons.Overview}</span>
            <span>Overview</span>
          </button>
          {roleView.items.map(({ label }) => (
            <button
              className={`nav-item ${activeSection === label ? 'is-active' : ''}`}
              key={label}
              onClick={() => setActiveSection(label)}
              type="button"
            >
              <span className="nav-icon" aria-hidden="true">{icons[label]}</span>
              <span>{label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <span className={`status-dot ${apiStatus}`} />
          <span>{apiStatus === 'checking' ? 'Connecting to API' : apiStatus === 'online' ? 'API connected' : 'API not connected'}</span>
        </div>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div className="breadcrumb">Savomart <span>/</span> {activeSection}</div>
          <label className="role-switcher">
            <span>Demo role</span>
            <select aria-label="Switch demo role" onChange={changeRole} value={selectedUserId}>
              {demoUsers.map((user) => (
                <option key={user.id} value={user.id}>{user.role}</option>
              ))}
            </select>
          </label>
          <div className="user-chip">
            <span className="avatar">{selectedUser.initials}</span>
            <span className="user-copy"><strong>{selectedUser.name}</strong><small>{selectedUser.role}</small></span>
          </div>
        </header>

        <div className="page-content">
          <section className="page-heading">
            <div>
              <p className="eyebrow">CHENNAI OPERATIONS</p>
              <h1>{activeSection === 'Overview' ? roleView.title : activeSection}</h1>
              <p className="page-description">{roleView.description}</p>
            </div>
            <div className="date-stamp">
              <span className="date-indicator" />
              Demo workspace
            </div>
          </section>

          {activeSection === 'Area intelligence' && selectedUser.role === 'BD Manager' ? (
            <AreaIntelligence />
          ) : null}

          {activeSection === 'Property pipeline' && selectedUser.role === 'BD Manager' ? (
            <PropertyPipeline />
          ) : null}

          {activeSection === 'Catchment studies' && selectedUser.role === 'BD Manager' ? (
            <CatchmentStudies />
          ) : null}

          {activeSection !== 'Area intelligence' &&
            activeSection !== 'Property pipeline' &&
            activeSection !== 'Catchment studies' ? (
              <>
                <section className="metric-grid" aria-label="Workspace summary">
                  {roleView.metrics.map((metric) => (
                    <article className="metric-panel" key={metric}>
                      <span className="metric-label">{metric}</span>
                      <strong className="metric-value">0</strong>
                      <span className="metric-note">Nothing to review yet</span>
                    </article>
                  ))}
                </section>

                <section className="work-section">
                  <div className="section-heading">
                    <div>
                      <p className="eyebrow">YOUR QUEUE</p>
                      <h2>{activeSection === 'Overview' ? roleView.workTitle : activeSection}</h2>
                    </div>
                    <span className="queue-count">0 items</span>
                  </div>
                  <div className="empty-state">
                    <span className="empty-icon" aria-hidden="true">{icons['My assignments']}</span>
                    <h3>{roleView.emptyTitle}</h3>
                    <p>{roleView.emptyDescription}</p>
                  </div>
                </section>
              </>
            ) : null}
        </div>
      </main>
    </div>
  )
}

export default App
