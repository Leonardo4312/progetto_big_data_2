import { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './App.css'
import {
  Car, Download, Printer, History, ChevronLeft, ChevronRight,
  Zap, Battery, TrendingUp, RefreshCw,
  Compass, Database, BarChart3, ShieldCheck, Layers, Copy, Check,
  FlaskConical, Play, Bot, LayoutDashboard, Terminal, Circle
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, ScatterChart, Scatter, ZAxis,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts'

const API_BASE = "http://localhost:8000"
const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316'];

const SUGGESTED_QUERIES = [
  "What is the ratio between registered Tesla cars and the availability of fast charging stations?",
  "What are the top 5 counties with the most registered electric vehicles?",
  "Which charging networks are most prevalent in Washington State?",
  "What is the average electric range of vehicles by make?",
  "How many charging stations are there in Seattle compared to Bellevue?",
  "What is the most popular electric vehicle model across the state?"
]

// ---------------------------------------------------------------------------
// Componenti Dashboard
// ---------------------------------------------------------------------------

const KpiCard = ({ icon: Icon, label, value, accent }) => (
  <div className="glass-card kpi-card">
    <div className="card-header">
      <Icon className="card-icon" style={{ color: accent }} size={20} />
      <span className="card-desc">{label}</span>
    </div>
    <div className="kpi-value">{value}</div>
  </div>
)

const ChartCard = ({ title, children, wide }) => (
  <div className={`glass-card chart-card ${wide ? 'grid-col-2' : ''}`}>
    <h3 className="chart-title">{title}</h3>
    <div style={{ height: 280 }}>
      <ResponsiveContainer>{children}</ResponsiveContainer>
    </div>
  </div>
)

const tooltipStyle = { backgroundColor: 'rgba(15, 23, 42, 0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }

function Dashboard({ data, loading, error, onRetry, activeTab, setActiveTab, onBack }) {
  if (loading) {
    return (
      <div className="glass-card" style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>
        <RefreshCw size={24} className="animate-spin" style={{ margin: '0 auto 1rem auto', color: '#3b82f6' }} />
        Loading aggregate data and computing Big Data calculations...
      </div>
    )
  }

  if (error) {
    return (
      <div className="glass-card" style={{ padding: '2rem', textAlign: 'center' }}>
        <p style={{ color: '#f87171', marginBottom: '1rem' }}>
          Unable to load dashboard: {error}
        </p>
        <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginBottom: '1rem' }}>
          Verify that the backend is reachable at {API_BASE}.
        </p>
        <button className="export-btn" onClick={onRetry}>
          <RefreshCw size={16} /> Retry
        </button>
      </div>
    )
  }

  if (!data) return null

  const {
    kpis,
    top_makes,
    range_distribution,
    ev_by_county,
    registration_trends,
    range_vs_manufacturer,
    network_share,
    infrastructure_deficit,
    income_vs_ev,
    marketing_adoption
  } = data

  const tabs = [
    { id: 'overview', label: 'Basic Overview (SQL Only)' },
    { id: 'marketing', label: 'Marketing & Adoption (CSV + SQL)' },
    { id: 'infrastructure', label: 'Infrastructure & Charging (JSON + SQL)' },
    { id: 'range', label: 'Range Evolution (SQL Only)' }
  ];


  const worstCounties = (infrastructure_deficit || []).slice(0, 3).map(item => item.county);


  const yearsMap = {};
  (range_vs_manufacturer || []).forEach(item => {
    if (!yearsMap[item.model_year]) {
      yearsMap[item.model_year] = { name: item.model_year };
    }
    yearsMap[item.model_year][item.make] = item.avg_range;
  });
  const rangeEvolutionData = Object.values(yearsMap).sort((a, b) => a.name - b.name);
  const distinctMakes = Array.from(new Set((range_vs_manufacturer || []).map(item => item.make)));

  return (
    <div className="post-report-dashboard" style={{ marginTop: '2.5rem' }}>
      <div className="dashboard-header" style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '1rem', marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2 className="chart-title" style={{ fontSize: '1.5rem', margin: 0, color: '#e2e8f0' }}>Dashboard EV-Nexus Analysis</h2>
          <p className="card-desc" style={{ margin: '0.25rem 0 0 0' }}>
            Explore insights by cross-referencing SQL, semi-structured JSON, and Kaggle geographical data.
          </p>
        </div>
        {onBack && (
          <button className="export-btn" onClick={onBack} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
            <ChevronLeft size={16} /> Back to Search
          </button>
        )}
      </div>

      {/* Navigazione Tab */}
      <div className="dashboard-tabs" style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1.5rem' }}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`export-btn ${activeTab === tab.id ? 'active-tab' : ''}`}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '0.6rem 1.2rem',
              borderRadius: '6px',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              background: activeTab === tab.id ? 'linear-gradient(90deg, #3b82f6, #8b5cf6)' : 'rgba(15, 23, 42, 0.5)',
              color: activeTab === tab.id ? '#ffffff' : '#94a3b8',
              fontWeight: '600',
              cursor: 'pointer',
              boxShadow: activeTab === tab.id ? '0 0 10px rgba(59, 130, 246, 0.4)' : 'none',
              transition: 'all 0.2s ease-in-out'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* KPI Cards */}
      <div className="dashboard-grid kpi-grid" style={{ marginBottom: '2rem' }}>
        <KpiCard icon={Car} label="Electric Vehicles (Volume)" value={kpis.total_ev.toLocaleString('it-IT')} accent="#3b82f6" />
        <KpiCard icon={TrendingUp} label="Average Range (miles)" value={kpis.avg_range.toLocaleString('it-IT')} accent="#8b5cf6" />
        <KpiCard
          icon={Zap}
          label="Charging Stations"
          value={kpis.total_stations > 0 ? kpis.total_stations.toLocaleString('it-IT') : "N/A (Requires JSON)"}
          accent="#10b981"
        />
        <KpiCard
          icon={Battery}
          label="DC Fast Chargers"
          value={kpis.dc_fast_chargers > 0 ? kpis.dc_fast_chargers.toLocaleString('it-IT') : "N/A (Requires JSON)"}
          accent="#f59e0b"
        />
      </div>

      {/* Render delle Viste Condizionali */}
      {activeTab === 'overview' && (
        <div className="dashboard-grid">
          <ChartCard title="Top Brands by Registrations (SQL)">
            <BarChart data={top_makes}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="name" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {top_makes.map((entry, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ChartCard>

          <ChartCard title="Range Distribution (miles) (SQL)">
            <BarChart data={range_distribution}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="name" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="value" fill="#06b6d4" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ChartCard>

          <ChartCard title="Top 10 Counties by EV Count (SQL)">
            <BarChart data={ev_by_county} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis type="number" stroke="#94a3b8" />
              <YAxis dataKey="name" type="category" stroke="#94a3b8" width={90} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="value" fill="#ec4899" radius={[0, 6, 6, 0]} />
            </BarChart>
          </ChartCard>

          <ChartCard title="EV Registrations Trend by Year (SQL)">
            <LineChart data={registration_trends}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="name" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip contentStyle={tooltipStyle} />
              <Line type="monotone" dataKey="value" name="Registrations" stroke="#3b82f6" strokeWidth={3} dot={{ r: 5 }} />
            </LineChart>
          </ChartCard>
        </div>
      )}

      {activeTab === 'marketing' && (
        <div className="dashboard-grid">
          <ChartCard title="Marketing & Adoption: Income vs Premium EV Penetration" wide>
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="mean_income" name="Average income" stroke="#94a3b8" tickFormatter={v => `$${(v / 1000).toFixed(0)}k`} label={{ value: 'Average Income ($)', position: 'insideBottom', offset: -5, fill: '#94a3b8' }} />
              <YAxis dataKey="premium_ev_penetration" name="Premium Penetration (%)" stroke="#94a3b8" unit="%" label={{ value: 'Premium Penetration (%)', angle: -90, position: 'insideLeft', fill: '#94a3b8' }} />
              <Tooltip contentStyle={tooltipStyle} cursor={{ strokeDasharray: '3 3' }} formatter={(value, name) => {
                if (name === "Average income") return [`$${value.toLocaleString('it-IT')}`, name];
                if (name === "Premium Penetration (%)") return [`${value}%`, name];
                return [value, name];
              }} />
              <ZAxis dataKey="county" name="County" />
              <Scatter data={marketing_adoption} fill="#10b981">
                {marketing_adoption.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.premium_ev_penetration > 40 ? '#ef4444' : '#10b981'} />
                ))}
              </Scatter>
            </ScatterChart>
          </ChartCard>

          <div className="glass-card chart-card grid-col-2" style={{ padding: '1.5rem' }}>
            <h3 className="chart-title" style={{ color: '#bae6fd', marginBottom: '1rem' }}>Market Opportunity Identification</h3>
            <p className="card-desc" style={{ marginBottom: '1rem' }}>
              This view cross-references the <strong>average county income (Kaggle CSV)</strong> with the percentage penetration of <strong>Tesla, Lucid, and Rivian</strong> on the total electric vehicles registered in the county.
            </p>
            <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', color: '#cbd5e1', fontSize: '0.9rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', textAlign: 'left' }}>
                    <th style={{ padding: '0.5rem' }}>Contea</th>
                    <th style={{ padding: '0.5rem' }}>Average Income</th>
                    <th style={{ padding: '0.5rem' }}>Total EVs</th>
                    <th style={{ padding: '0.5rem' }}>Premium EVs</th>
                    <th style={{ padding: '0.5rem' }}>Penetration %</th>
                  </tr>
                </thead>
                <tbody>
                  {marketing_adoption && marketing_adoption.slice(0, 8).map((item, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                      <td style={{ padding: '0.5rem', fontWeight: '500' }}>{item.county}</td>
                      <td style={{ padding: '0.5rem' }}>${item.mean_income.toLocaleString('it-IT')}</td>
                      <td style={{ padding: '0.5rem' }}>{item.total_ev_count.toLocaleString('it-IT')}</td>
                      <td style={{ padding: '0.5rem', color: '#3b82f6' }}>{item.premium_ev_count.toLocaleString('it-IT')}</td>
                      <td style={{ padding: '0.5rem', color: item.premium_ev_penetration > 40 ? '#ef4444' : '#10b981', fontWeight: 'bold' }}>
                        {item.premium_ev_penetration}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'infrastructure' && (
        <div className="dashboard-grid">
          <ChartCard title="Infrastructure & Under-Service: EVs per Fast Charger (Charging Deficit)" wide>
            <BarChart data={infrastructure_deficit.slice(0, 10)}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="county" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" label={{ value: 'EV / DC Fast Charger Ratio', angle: -90, position: 'insideLeft', fill: '#94a3b8', offset: 10 }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="ev_per_charger" fill="#3b82f6" radius={[6, 6, 0, 0]}>
                {infrastructure_deficit.slice(0, 10).map((entry, index) => {
                  const isWorst = worstCounties.includes(entry.county);
                  return <Cell key={`cell-${index}`} fill={isWorst ? '#ef4444' : '#3b82f6'} />;
                })}
              </Bar>
            </BarChart>
          </ChartCard>

          <div className="glass-card chart-card grid-col-2" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <h3 className="chart-title" style={{ color: '#ef4444', margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                ⚠️ Critical Under-Served Areas (Worst Deficit)
              </h3>
              <p className="card-desc" style={{ marginBottom: '1rem' }}>
                Numerical ratio between vehicles registered in the county and DC Fast (Level 3) chargers surveyed in the JSON dataset. Red bars represent the 3 markets with the worst infrastructure deficit.
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {infrastructure_deficit && infrastructure_deficit.slice(0, 3).map((item, index) => (
                  <div key={index} style={{ padding: '0.75rem', borderRadius: '6px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 'bold', color: '#f87171' }}>
                      <span>{index + 1}. County of {item.county}</span>
                      <span>{item.ev_per_charger} EV/DC Fast</span>
                    </div>
                    <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '0.25rem' }}>
                      {item.ev_count.toLocaleString('it-IT')} EV registered vs only {item.dc_fast} fast stations.
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ marginTop: '1rem' }}>
              <ChartCard title="Charging Network Share (JSON)">
                <PieChart>
                  <Tooltip contentStyle={tooltipStyle} />
                  <Legend />
                  <Pie data={network_share} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} label>
                    {network_share.map((entry, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                </PieChart>
              </ChartCard>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'range' && (
        <div className="dashboard-grid">
          <ChartCard title="Average Range Evolution (Miles) by Manufacturer over Years" wide>
            <LineChart data={rangeEvolutionData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="name" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" unit=" mi" />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend />
              {distinctMakes.map((make, index) => (
                <Line
                  key={make}
                  type="monotone"
                  dataKey={make}
                  name={make}
                  stroke={COLORS[index % COLORS.length]}
                  strokeWidth={3}
                  dot={{ r: 4 }}
                  connectNulls
                />
              ))}
            </LineChart>
          </ChartCard>

          <div className="glass-card chart-card grid-col-2" style={{ padding: '1.5rem' }}>
            <h3 className="chart-title" style={{ color: '#bae6fd', marginBottom: '1rem' }}>Battery Technology Evolution</h3>
            <p className="card-desc">
              Analysis of the real efficiency of battery packs of vehicles filtered by year from 2012 onwards. This view allows identifying manufacturers with the best technological evolution and consistency over time.
              <br /><br />
              <em>Note:</em> Range data exclusively consider vehicles with a certified real range greater than zero, excluding null estimates to avoid distortions in the average calculation.
            </p>
          </div>
        </div>
      )}

      <ExperimentPanel />
    </div>
  )
}

// ---------------------------------------------------------------------------
// Pannello di Experimental Evaluation (on-demand: latenza + accuratezza)
// ---------------------------------------------------------------------------

function ExperimentPanel() {
  const [effectiveness, setEffectiveness] = useState(null)
  const [runningEff, setRunningEff] = useState(false)
  const [scalability, setScalability] = useState(null)
  const [runningScalability, setRunningScalability] = useState(false)
  const [error, setError] = useState(null)

  const runScalability = () => {
    setRunningScalability(true)
    setError(null)
    fetch(`${API_BASE}/api/evaluation/scalability`)
      .then(res => res.json())
      .then(json => {
        if (json.error) throw new Error(json.error)
        setScalability(json.results || json)
      })
      .catch(err => setError(err.message))
      .finally(() => setRunningScalability(false))
  }

  const runEffectiveness = () => {
    setRunningEff(true)
    setError(null)
    fetch(`${API_BASE}/api/evaluation/effectiveness`)
      .then(res => res.json())
      .then(json => {
        if (json.error) throw new Error(json.error)
        setEffectiveness(json)
      })
      .catch(err => setError(err.message))
      .finally(() => setRunningEff(false))
  }

  return (
    <div className="post-report-dashboard" style={{ marginTop: '4rem', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
      <div className="dashboard-header" style={{ marginBottom: '1rem' }}>
        <h3 className="chart-title" style={{ margin: 0 }}>
          <FlaskConical size={16} style={{ display: 'inline', marginRight: 6, verticalAlign: 'text-bottom' }} />
          Experimental Evaluation
        </h3>
      </div>
      <p className="card-desc" style={{ marginBottom: '1.25rem' }}>
        On-demand benchmark: compares the crew's Text-to-SQL answers against a set of questions with a known,
        pre-verified ground truth.
      </p>

      {error && <p style={{ color: '#f87171', marginBottom: '1rem' }}>{error}</p>}

      <div className="dashboard-grid">
        <div className="glass-card chart-card">
          <div className="dashboard-header" style={{ marginBottom: '0.75rem' }}>
            <span className="chart-title" style={{ margin: 0 }}>Pandas vs PySpark as Volume grows</span>
            <button className="export-btn" onClick={runScalability} disabled={runningScalability}>
              <Play size={16} /> {runningScalability ? "Running..." : "Run"}
            </button>
          </div>
          {scalability ? (
            <div style={{ height: 260 }}>
              <ResponsiveContainer>
                <LineChart data={scalability}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis dataKey="scenario" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" unit="s" />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Legend />
                  <Line type="monotone" dataKey="pandas_time" name="Pandas" stroke="#3b82f6" strokeWidth={3} dot={{ r: 5 }} />
                  <Line type="monotone" dataKey="pyspark_time" name="PySpark" stroke="#f59e0b" strokeWidth={3} dot={{ r: 5 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="card-desc">
              Click "Run" to replicate the dataset (1x/5x/10x) and benchmark the aggregation execution times.
              It may take a few tens of seconds (Spark startup included).
            </p>
          )}
        </div>

        <div className="glass-card chart-card">
          <div className="dashboard-header" style={{ marginBottom: '0.75rem' }}>
            <span className="chart-title" style={{ margin: 0 }}>Text-to-SQL Accuracy (Effectiveness)</span>
            <button className="export-btn" onClick={runEffectiveness} disabled={runningEff}>
              <Play size={16} /> {runningEff ? "Running..." : "Run"}
            </button>
          </div>
          {effectiveness ? (
            <div>
              <div className="fivev-score" style={{ marginBottom: '0.75rem' }}>
                {effectiveness.accuracy}<span>%</span>
              </div>
              <ul className="fivev-list">
                {effectiveness.cases.map((c, i) => (
                  <li key={i} style={{ gridTemplateColumns: '1fr 60px' }}>
                    <span className="fivev-label" style={{ whiteSpace: 'normal' }}>{c.question}</span>
                    <span className="fivev-num" style={{ color: c.correct ? '#10b981' : '#ef4444' }}>
                      {c.correct ? "Correct" : "Incorrect"}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="card-desc">Click "Run" to compare the agent's answers against pre-verified golden SQL queries. It may take 1-3 minutes.</p>
          )}
        </div>

      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Chat esistente (Text-to-SQL)
// ---------------------------------------------------------------------------

const FiveVRadar = ({ evaluation }) => {
  if (!evaluation) return null;
  const metrics = ["Volume", "Velocity", "Variety", "Veracity", "Value"];
  const data = metrics.map(m => ({ metric: m, value: evaluation[m] || 0 }));
  const avg = (data.reduce((s, d) => s + d.value, 0) / data.length).toFixed(1);
  const veridicita = evaluation["Veracity"] || 0;
  const confidence = veridicita >= 4
    ? { label: "High", color: "#10b981" }
    : veridicita >= 3
      ? { label: "Medium", color: "#f59e0b" }
      : { label: "Low", color: "#ef4444" };

  return (
    <div className="fivev-panel">
      <h3 className="fivev-title">Query Evaluation — The 5 Vs of Big Data</h3>
      <div className="fivev-body">
        <div className="fivev-radar">
          <ResponsiveContainer width="100%" height={260}>
            <RadarChart data={data} outerRadius="75%">
              <PolarGrid stroke="rgba(255,255,255,0.15)" />
              <PolarAngleAxis dataKey="metric" tick={{ fill: '#cbd5e1', fontSize: 12 }} />
              <PolarRadiusAxis angle={90} domain={[0, 5]} tick={false} axisLine={false} />
              <Radar dataKey="value" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.35} strokeWidth={2} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
        <div className="fivev-side">
          <div className="fivev-score">{avg}<span>/5</span></div>
          <div className="card-desc">Average score across 5 dimensions</div>
          <ul className="fivev-list">
            {data.map(d => (
              <li key={d.metric}>
                <span className="fivev-label">{d.metric}</span>
                <div className="fivev-bar-track"><div className="fivev-bar-fill" style={{ width: `${d.value / 5 * 100}%` }} /></div>
                <span className="fivev-num">{d.value}/5</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}

// Configurazione dei 4 agenti per il Live Agent Monitor (griglia 2x2 in fase di polling)
const AGENT_CONFIG = [
  { key: 'architect', name: 'The Architect', icon: Compass, color: '#3b82f6', match: /architect/i, range: [0, 25] },
  { key: 'sql', name: 'SQL Engineer', icon: Database, color: '#10b981', match: /sql|engineer|postgres/i, range: [26, 50] },
  { key: 'analyst', name: 'Data Analyst', icon: BarChart3, color: '#f59e0b', match: /analyst|pyspark|charging/i, range: [51, 75] },
  { key: 'guardian', name: 'Veracity Guardian', icon: ShieldCheck, color: '#8b5cf6', match: /guardian|veracity|veridic/i, range: [76, 100] },
]

const makeInitialAgentState = () =>
  AGENT_CONFIG.reduce((acc, a) => { acc[a.key] = { status: 'idle', logs: [] }; return acc }, {})

// Determina quale agente è "attivo" in base al progress numerico generato dal backend
const resolveActiveAgentIndex = (progress) => {
  const byProgress = AGENT_CONFIG.findIndex(a => progress <= a.range[1])
  return byProgress === -1 ? AGENT_CONFIG.length - 1 : byProgress
}

// ---------------------------------------------------------------------------
// Live Agent Monitor: griglia 2x2 con badge di stato e micro-terminale per agente
// ---------------------------------------------------------------------------

function AgentMonitor({ agents }) {
  return (
    <div className="agent-monitor-grid">
      {AGENT_CONFIG.map(cfg => {
        const state = agents[cfg.key] || { status: 'idle', logs: [] }
        const Icon = cfg.icon
        return <AgentCard key={cfg.key} cfg={cfg} state={state} Icon={Icon} />
      })}
    </div>
  )
}

function AgentCard({ cfg, state, Icon }) {
  const terminalRef = useRef(null)

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight
    }
  }, [state.logs.length])

  return (
    <div className={`agent-card status-${state.status}`} style={{ '--agent-color': cfg.color }}>
      <div className="agent-card-header">
        <div className="agent-icon-wrap">
          <Icon size={18} />
        </div>
        <span className="agent-name">{cfg.name}</span>
        <span className={`agent-badge badge-${state.status}`}>
          {state.status === 'running' && <span className="badge-dot" />}
          {state.status === 'completed' && <Check size={12} />}
          {state.status === 'idle' && <Circle size={8} fill="currentColor" />}
          {state.status === 'completed' ? 'Completed' : state.status === 'running' ? 'Running' : 'Idle'}
        </span>
      </div>
      <div className="agent-terminal" ref={terminalRef}>
        <div className="agent-terminal-label">
          <Terminal size={12} /> live log
        </div>
        {state.logs.length === 0 ? (
          <div className="terminal-line dim">awaiting task assignment...</div>
        ) : (
          state.logs.map((l, i) => (
            <div key={i} className="terminal-line">
              <span className="terminal-caret">&gt;</span> {l}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

// Metadati visivi per il reasoning multi-agente (Architetto, SQL Engineer, Analista, Guardian)
const AGENT_META = [
  { test: /architett/i, icon: Compass, color: '#3b82f6', label: 'Planning' },
  { test: /sql|ingegner/i, icon: Database, color: '#10b981', label: 'Data extraction' },
  { test: /analist|dati/i, icon: BarChart3, color: '#f59e0b', label: 'Analysis' },
  { test: /guardian|veridic|veracity/i, icon: ShieldCheck, color: '#ef4444', label: 'Validation' },
]

const flattenText = (children) => {
  if (typeof children === 'string') return children
  if (Array.isArray(children)) return children.map(flattenText).join('')
  if (children?.props?.children) return flattenText(children.props.children)
  return ''
}

const matchAgent = (text) => AGENT_META.find(a => a.test.test(text))

// h2: intercetta il titolo "Il Lavoro degli Agenti" e apre la timeline via marker CSS
const Heading2 = ({ children }) => {
  const text = flattenText(children)
  if (/lavoro.*agent|reasoning|pipeline agent/i.test(text)) {
    return (
      <>
        <h2 className="agents-section-title"><Layers size={18} /> {children}</h2>
        <div className="agent-timeline-marker" />
      </>
    )
  }
  return <h2>{children}</h2>
}

// h3: se il titolo corrisponde a un agente noto, diventa uno step della timeline
const Heading3 = ({ children }) => {
  const text = flattenText(children)
  const meta = matchAgent(text)
  if (meta) {
    const Icon = meta.icon
    return (
      <div className="agent-step">
        <div className="agent-step-icon" style={{ background: meta.color }}>
          <Icon size={16} color="#fff" />
        </div>
        <div className="agent-step-heading">
          <h4 className="agent-step-title">{children}</h4>
          <span className="agent-step-tag" style={{ color: meta.color, borderColor: meta.color }}>{meta.label}</span>
        </div>
      </div>
    )
  }
  return <h3>{children}</h3>
}

const CopyButton = ({ text }) => {
  const [copied, setCopied] = useState(false)
  return (
    <button className="export-btn" onClick={() => {
      navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    }}>
      {copied ? <Check size={18} /> : <Copy size={18} />} {copied ? "Copied!" : "Copy Report"}
    </button>
  )
}

const CustomCodeBlock = ({ node, inline, className, children, ...props }) => {
  const match = /language-(\w+)/.exec(className || '')
  if (!inline && match && match[1] === 'json') {
    try {
      const parsedData = JSON.parse(String(children).replace(/\n$/, ''))
      if (parsedData && (parsedData.chart_data || parsedData.five_v_evaluation)) {

        const chartType = parsedData.chart_type || 'bar';

        const renderChart = () => {
          if (!parsedData.chart_data) return null;

          if (chartType === 'pie') {
            return (
              <ResponsiveContainer>
                <PieChart>
                  <Tooltip contentStyle={tooltipStyle} itemStyle={{ color: '#bae6fd' }} />
                  <Legend />
                  <Pie data={parsedData.chart_data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={120} label>
                    {parsedData.chart_data.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            )
          } else if (chartType === 'line') {
            return (
              <ResponsiveContainer>
                <LineChart data={parsedData.chart_data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis dataKey="name" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip contentStyle={tooltipStyle} itemStyle={{ color: '#bae6fd' }} />
                  <Legend />
                  <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={3} dot={{ r: 5 }} activeDot={{ r: 8 }} />
                </LineChart>
              </ResponsiveContainer>
            )
          } else {
            return (
              <ResponsiveContainer>
                <BarChart data={parsedData.chart_data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis dataKey="name" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip contentStyle={tooltipStyle} itemStyle={{ color: '#bae6fd' }} />
                  <Legend />
                  <Bar dataKey="value" fill="#3b82f6" radius={[6, 6, 0, 0]} animationDuration={1500}>
                    {parsedData.chart_data.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )
          }
        }

        const downloadCSV = () => {
          if (!parsedData.chart_data) return;
          const csvRows = ['Name,Value'];
          parsedData.chart_data.forEach(item => {
            csvRows.push(`"${item.name}",${item.value}`);
          });
          const blob = new Blob([csvRows.join('\n')], { type: 'text/csv' });
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = 'ev_nexus_data.csv';
          a.click();
        }

        return (
          <div style={{ width: '100%', marginTop: '2rem', marginBottom: '2rem' }}>
            {parsedData.chart_data && (
              <div style={{ height: 350 }}>
                <h3 style={{ textAlign: 'center', marginBottom: '1rem', color: '#bae6fd' }}>Graphical Representation</h3>
                {renderChart()}
              </div>
            )}

            <FiveVRadar evaluation={parsedData.five_v_evaluation} />

            <div className="export-buttons">
              <button className="export-btn" onClick={downloadCSV}>
                <Download size={18} /> Download Data (CSV)
              </button>
              <button className="export-btn" onClick={() => window.print()}>
                <Printer size={18} /> Print Report (PDF)
              </button>
              <CopyButton text={parsedData.chart_data ? JSON.stringify(parsedData.chart_data) : ''} />
            </div>
          </div>
        )
      }
    } catch (e) {
      // Fallback a text se non è JSON valido
    }
  }

  return (
    <pre style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '8px', overflowX: 'auto', marginBottom: '1rem' }}>
      <code className={className} {...props}>
        {children}
      </code>
    </pre>
  )
}

function App() {
  // Navigazione state-driven a due pagine: 'chat' (Live Agent Query) e 'analytics' (Global Analytics)
  const [activeView, setActiveView] = useState('chat')

  const [query, setQuery] = useState("What is the ratio between registered Tesla cars and the availability of fast charging stations?")
  const [isLoading, setIsLoading] = useState(false)
  const [report, setReport] = useState("")
  const [progress, setProgress] = useState(0)
  const [agents, setAgents] = useState(makeInitialAgentState())
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [hasRunOnce, setHasRunOnce] = useState(false)

  const pollRef = useRef(null)

  const [history, setHistory] = useState(() => {
    const saved = localStorage.getItem('ev_nexus_history');
    return saved ? JSON.parse(saved) : [];
  })

  const [dashboardData, setDashboardData] = useState(null)
  const [dashboardLoading, setDashboardLoading] = useState(false)
  const [dashboardError, setDashboardError] = useState(null)
  const [activeTab, setActiveTab] = useState("overview")
  const [currentView, setCurrentView] = useState("home")
  const [showDashboard, setShowDashboard] = useState(false)

  const fetchDashboard = () => {
    setDashboardLoading(true)
    setDashboardError(null)
    fetch(`${API_BASE}/api/dashboard?include_charging=true&include_income=true`)
      .then(res => {
        if (!res.ok) throw new Error("the backend responded with an error")
        return res.json()
      })
      .then(json => {
        if (json.error) throw new Error(json.error)
        setDashboardData(json)
      })
      .catch(err => setDashboardError(err.message))
      .finally(() => setDashboardLoading(false))
  }


  useEffect(() => {
    if (report || isLoading || showDashboard) {
      const includeCharging = activeTab === "infrastructure";
      const includeIncome = activeTab === "marketing";
      fetchDashboard(includeCharging, includeIncome);
    }
  }, [activeTab, report, showDashboard, isLoading]);

  // Pulizia del polling se il componente viene smontato a metà richiesta
  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [])

  // Applica un aggiornamento di stato ricevuto dal polling ai 4 box agente.
  // Lo stato (idle/running/completed) è derivato da message+progress come prima,
  // ma il CONTENUTO del terminale ora arriva direttamente da `agent_logs`,
  // popolato lato backend dal Crew-level step_callback ad ogni singolo step
  // (pensiero/tool-call/osservazione), non solo al termine di ogni task.
  const applyStatusUpdate = (data) => {
    const { message, progress, status, agent_logs } = data
    const isDone = status === "completed"
    setAgents(prev => {
      const next = {}
      const activeIdx = isDone ? AGENT_CONFIG.length - 1 : resolveActiveAgentIndex(progress)
      AGENT_CONFIG.forEach((cfg, idx) => {
        const current = prev[cfg.key] || { status: 'idle', logs: [] }
        let st
        if (isDone) st = 'completed'
        else if (idx < activeIdx) st = 'completed'
        else if (idx === activeIdx) st = 'running'
        else st = 'idle'

        // agent_logs è la fonte di verità quando disponibile (backend aggiornato);
        // fallback ai log locali se il backend non la espone ancora.
        const logs = (agent_logs && agent_logs[cfg.key]) ? agent_logs[cfg.key] : current.logs
        next[cfg.key] = { status: st, logs }
      })
      return next
    })
  }

  const runQuery = async (q) => {
    if (!q.trim() || isLoading) return
    setIsLoading(true)
    setHasRunOnce(true)
    setReport("")
    setProgress(0)
    setAgents(makeInitialAgentState())
    setActiveView('chat')
    if (pollRef.current) clearInterval(pollRef.current)

    try {
      const startResponse = await fetch(`${API_BASE}/api/analyze/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q }),
      })

      if (!startResponse.ok) {
        throw new Error("Network error communicating with the Backend")
      }

      const { task_id } = await startResponse.json()

      pollRef.current = setInterval(async () => {
        try {
          const statusRes = await fetch(`${API_BASE}/api/analyze/status/${task_id}`)
          const data = await statusRes.json()

          if (data.status === "not_found") return

          applyStatusUpdate(data)
          if (typeof data.progress === "number") setProgress(data.progress)

          if (data.status === "completed") {
            clearInterval(pollRef.current)
            setProgress(100)
            setReport(data.report)
            setIsLoading(false)

            const newEntry = {
              query: q,
              report: data.report,
              date: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            };
            setHistory(prev => {
              const filtered = prev.filter(item => item.query !== q);
              const newHistory = [newEntry, ...filtered].slice(0, 10);
              localStorage.setItem('ev_nexus_history', JSON.stringify(newHistory));
              return newHistory;
            });
          } else if (data.status === "error") {
            clearInterval(pollRef.current)
            setReport(`**Error:** ${data.error}`)
            setIsLoading(false)
          }
        } catch (pollError) {
          clearInterval(pollRef.current)
          setReport(`**Error:** ${pollError.message}`)
          setIsLoading(false)
        }
      }, 900)

    } catch (error) {
      setReport(`**Error:** ${error.message}`)
      setIsLoading(false)
    }
  }

  const handleAnalyze = (e) => {
    e.preventDefault()
    runQuery(query)
  }

  const handleChipClick = (e, q) => {
    e.preventDefault()
    setQuery(q)
    runQuery(q)
  }

  const loadHistoryItem = (item) => {
    if (pollRef.current) clearInterval(pollRef.current)
    setIsLoading(false)
    setHasRunOnce(true)
    setShowDashboard(false)
    setQuery(item.query);
    setReport(item.report);
  }


  return (
    <div className="app-layout">

      <div className={`sidebar-container ${isSidebarOpen ? 'open' : 'closed'}`}>
        <aside className="sidebar">
          <button
            className={`nav-button ${showDashboard ? 'active' : ''}`}
            style={{ marginBottom: '1.5rem' }}
            onClick={() => setShowDashboard(!showDashboard)}
            title="Toggle Dashboard & Tests"
          >
            <LayoutDashboard size={18} />
            <span>Dashboard</span>
          </button>

          <div className="sidebar-title">
            <History size={18} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'sub' }} />
            Search History
          </div>
          {history.length === 0 && (
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', fontStyle: 'italic' }}>No saved searches.</div>
          )}
          {history.map((item, index) => (
            <div key={index} className="sidebar-item" onClick={() => loadHistoryItem(item)}>
              <div className="sidebar-item-query">{item.query}</div>
              <div className="sidebar-item-date">{item.date}</div>
            </div>
          ))}
        </aside>
        <button
          className="sidebar-toggle"
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          title={isSidebarOpen ? "Close Sidebar" : "Open Sidebar"}
        >
          {isSidebarOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
        </button>
      </div>

      <main className="main-content">
        <header className="header">
          <h1>EV Nexus</h1>
        </header>

        {!showDashboard && (
          <section className="glass-card">
            <form className="search-box" onSubmit={handleAnalyze}>
              <input
                type="text"
                className="search-input"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask your agents a question..."
                disabled={isLoading}
              />
              <button type="submit" className="search-button" disabled={isLoading || !query.trim()}>
                {isLoading ? "Processing..." : "Analyze"}
                {!isLoading && <Car size={20} />}
              </button>
            </form>

            <div className="suggested-queries-container">
              <p className="suggested-title">Analysis suggestions:</p>
              <div className="suggested-grid">
                {SUGGESTED_QUERIES.map((queryText, index) => (
                  <button key={index} type="button" className="query-chip" disabled={isLoading} onClick={(e) => handleChipClick(e, queryText)}>
                    <span className="chip-icon">💡</span>
                    <span className="chip-text">
                      {queryText.length > 55 ? queryText.slice(0, 55) + "…" : queryText}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {hasRunOnce && (
              <div className="agent-monitor-section">
                <div className="agent-monitor-heading">
                  <Terminal size={16} />
                  <span>Live Agent Monitor</span>
                  {isLoading && <span className="progress-pill">{progress}%</span>}
                </div>
                {isLoading && (
                  <div className="mini-progress-track" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
                    <div className="mini-progress-fill" style={{ width: `${progress}%` }} />
                  </div>
                )}
                <AgentMonitor agents={agents} />
              </div>
            )}

            {report && !isLoading && (
              <div className="glass-card report-content">
                <div className="report-toolbar">
                  <CopyButton text={report} />
                  <button className="export-btn" onClick={() => window.print()}>
                    <Printer size={18} /> Print (PDF)
                  </button>
                </div>
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    code: CustomCodeBlock,
                    h2: Heading2,
                    h3: Heading3
                  }}
                >
                  {report}
                </ReactMarkdown>
              </div>
            )}
          </section>
        )}

        {showDashboard && (
          <Dashboard
            data={dashboardData}
            loading={dashboardLoading}
            error={dashboardError}
            onRetry={() => fetchDashboard(activeTab === "infrastructure", activeTab === "marketing")}
            activeTab={activeTab}
            setActiveTab={setActiveTab}
            onBack={() => setShowDashboard(false)}
          />
        )}

        <footer style={{ textAlign: 'center', padding: '2rem', marginTop: '3rem', color: '#94a3b8', fontSize: '0.9rem', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
          <p style={{ margin: '0 0 0.5rem 0', fontWeight: '500', letterSpacing: '0.5px' }}>Big Data Architectural Project</p>
          <p style={{ margin: 0 }}>
            Designed and Developed by: <strong style={{ color: '#e2e8f0' }}>Leonardo Anatra</strong> ed <strong style={{ color: '#e2e8f0' }}>Edoardo Piazzolla</strong>
          </p>
          <div style={{ marginTop: '1.5rem' }}>
            <img
              src="/logo-romatre.png"
              alt="Roma Tre University"
              style={{
                maxHeight: '80px',
                borderRadius: '8px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
              }}
            />
          </div>
        </footer>
      </main>
    </div>
  )
}

export default App