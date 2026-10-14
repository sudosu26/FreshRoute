import React, { useState, useEffect } from 'react'
import {
  Leaf,
  Loader2,
  AlertCircle,
  Copy,
  Check,
  Sparkles,
  Layers,
  Fingerprint,
} from 'lucide-react'
import SummaryCards from './components/SummaryCards'
import ComparisonChart from './components/ComparisonChart'
import DispatchTable from './components/DispatchTable'

const ARCHETYPE_OPTIONS = [
  { label: '🎲 Random Archetype', value: '' },
  { label: 'Normal Week', value: 'NORMAL' },
  { label: 'Peak Harvest Glut', value: 'HARVEST_GLUT' },
  { label: 'Festival Demand Surge', value: 'FESTIVAL_SURGE' },
  { label: 'Fuel Price Spike', value: 'FUEL_SPIKE' },
  { label: 'Monsoon Road Delays', value: 'MONSOON_DELAYS' },
  { label: 'Cold Chain Failure', value: 'COLD_CHAIN_FAIL' },
]

export default function App() {
  const [scenario, setScenario] = useState(null)
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [seedInput, setSeedInput] = useState('')
  const [copiedSeed, setCopiedSeed] = useState(false)
  const [copiedHash, setCopiedHash] = useState(false)
  const [selectedArchetype, setSelectedArchetype] = useState('')

  // Fetch scenario and compute optimization in a single fast round-trip
  const loadScenario = async (targetSeed = null, targetArchetype = '') => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()
      if (targetSeed !== null && targetSeed !== undefined && targetSeed !== '') {
        params.append('seed', targetSeed)
      }
      if (targetArchetype) {
        params.append('archetype', targetArchetype)
      }
      params.append('include_optimization', 'true')

      const url = `/api/scenario?${params.toString()}`
      const scenarioRes = await fetch(url)
      if (!scenarioRes.ok) {
        throw new Error(`Failed to load scenario: ${scenarioRes.status} ${scenarioRes.statusText}`)
      }

      const scenarioData = await scenarioRes.json()
      setScenario(scenarioData)
      setSeedInput(String(scenarioData.seed))

      if (scenarioData.optimization) {
        setResults(scenarioData.optimization)
      } else {
        // Fallback to separate optimize call if needed
        const optRes = await fetch('/api/optimize', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ scenario: scenarioData }),
        })
        if (!optRes.ok) throw new Error('Optimization failed')
        const optData = await optRes.json()
        setResults(optData)
      }
    } catch (err) {
      console.error('Scenario / Optimization error:', err)
      setError(err.message || 'An error occurred while generating scenario.')
    } finally {
      setLoading(false)
    }
  }

  // Initial load on mount
  useEffect(() => {
    loadScenario(null, '')
  }, [])

  const handleNewScenario = () => {
    loadScenario(null, selectedArchetype)
  }

  const handleArchetypeChange = (e) => {
    const val = e.target.value
    setSelectedArchetype(val)
    loadScenario(null, val)
  }

  const handleReplay = (e) => {
    if (e) e.preventDefault()
    if (!seedInput || isNaN(Number(seedInput))) {
      setError('Please enter a valid numeric seed to replay.')
      return
    }
    loadScenario(parseInt(seedInput, 10), selectedArchetype)
  }

  const handleCopySeed = () => {
    if (!scenario?.seed) return
    navigator.clipboard.writeText(String(scenario.seed))
    setCopiedSeed(true)
    setTimeout(() => setCopiedSeed(false), 2000)
  }

  const handleCopyHash = () => {
    const hash = results?.plan_hash
    if (!hash) return
    navigator.clipboard.writeText(String(hash))
    setCopiedHash(true)
    setTimeout(() => setCopiedHash(false), 2000)
  }

  const summaryData = results?.summary || {}
  const planData = results?.optimized_plan || []

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 pb-16">
      {/* Top Navigation Bar */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-30 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div>
              <div className="flex items-center gap-2.5">
                <span className="text-3xl leading-none" role="img" aria-label="FreshRoute Logo">
                  🥬
                </span>
                <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight">
                  FreshRoute
                </h1>
                <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-fresh-50 text-fresh-700 border border-fresh-200">
                  Decision Support Engine
                </span>
              </div>
              <p className="mt-0.5 text-xs sm:text-sm font-medium text-gray-500">
                Deterministic Heuristic Optimizer for Perishable Produce Distribution
              </p>
            </div>

            {/* Action Controls */}
            <div className="flex flex-wrap items-center gap-2.5">
              {/* Archetype Quick Selector */}
              <div className="relative">
                <select
                  value={selectedArchetype}
                  onChange={handleArchetypeChange}
                  disabled={loading}
                  className="text-xs font-medium bg-gray-50 border border-gray-200 rounded-lg px-2.5 py-2 text-gray-700 focus:outline-none focus:ring-1 focus:ring-fresh-500 cursor-pointer disabled:opacity-50"
                >
                  {ARCHETYPE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Replay Seed Form */}
              <form
                onSubmit={handleReplay}
                className="flex items-center gap-1.5 bg-gray-50 p-1 rounded-lg border border-gray-200"
              >
                <label htmlFor="seedInput" className="text-xs font-medium text-gray-500 pl-2">
                  Replay seed:
                </label>
                <input
                  id="seedInput"
                  type="number"
                  value={seedInput}
                  onChange={(e) => setSeedInput(e.target.value)}
                  placeholder="e.g. 12345"
                  className="w-20 sm:w-24 px-2 py-1 text-xs font-mono bg-white border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-fresh-500"
                />
                <button
                  type="submit"
                  disabled={loading || !seedInput.trim()}
                  className="px-2.5 py-1 text-xs font-semibold text-gray-700 bg-white border border-gray-200 hover:bg-gray-100 rounded disabled:opacity-50 transition cursor-pointer"
                >
                  Replay
                </button>
              </form>

              {/* New Scenario Button */}
              <button
                type="button"
                onClick={handleNewScenario}
                disabled={loading}
                className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-fresh-600 text-sm font-semibold text-white shadow-sm hover:bg-fresh-700 active:bg-fresh-800 disabled:opacity-50 transition cursor-pointer"
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin text-white" />
                ) : (
                  <span className="text-base leading-none">🎲</span>
                )}
                <span>New Scenario</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error Notification */}
        {error && (
          <div className="mb-6 rounded-xl border border-red-200 bg-red-50 p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-red-800">Notice</h4>
              <p className="text-sm text-red-700 mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {/* Loading Spinner State */}
        {loading && (
          <div className="my-16 flex flex-col items-center justify-center text-center p-12 bg-white rounded-2xl border border-gray-100 shadow-sm animate-pulse">
            <div className="w-16 h-16 rounded-full bg-fresh-50 flex items-center justify-center mb-4">
              <Loader2 className="w-8 h-8 text-fresh-600 animate-spin" />
            </div>
            <h3 className="text-xl font-bold text-gray-900">Simulating Corridors & Optimizing Allocations</h3>
            <p className="mt-2 text-sm text-gray-500 max-w-md">
              Evaluating decay kinetics, route feasibility, dynamic markdown thresholds, and baseline FIFO comparisons...
            </p>
          </div>
        )}

        {/* Dashboard Content */}
        {!loading && (
          <div className="space-y-8 animate-fadeIn">
            {/* Scenario Banner */}
            {scenario && (
              <section aria-label="Scenario Context">
                <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5 sm:p-6 transition-all hover:border-fresh-200">
                  <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                    <div className="space-y-1.5 flex-1">
                      <div className="flex flex-wrap items-center gap-2.5">
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-fresh-100 text-fresh-800 border border-fresh-200">
                          <Sparkles className="w-3.5 h-3.5 text-fresh-600" />
                          {scenario.scenario_name}
                        </span>
                        <span className="text-xs font-medium text-gray-400">
                          ID: <span className="font-mono text-gray-600">{scenario.scenario_id}</span>
                        </span>
                        {scenario.modifier_text && (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium bg-amber-50 text-amber-800 border border-amber-200">
                            ⚡ {scenario.modifier_text}
                          </span>
                        )}
                      </div>

                      <h2 className="text-lg font-bold text-gray-900 pt-1">
                        {scenario.scenario_name}
                      </h2>
                      <p className="text-sm font-medium text-gray-600 leading-relaxed">
                        {scenario.scenario_description}
                      </p>

                      <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500 pt-2 border-t border-gray-100 mt-3">
                        <span>📦 <strong>{scenario.batches?.length || 0}</strong> batches ({Math.round(scenario.stats?.total_batch_quantity_kg || 0).toLocaleString()} kg)</span>
                        <span>📍 <strong>{scenario.destinations?.length || 0}</strong> destination markets</span>
                        <span>🚛 <strong>{scenario.trucks?.length || 0}</strong> reefer trucks (fleet cap: {Math.round(scenario.stats?.total_truck_capacity_kg || 0).toLocaleString()} kg)</span>
                      </div>
                    </div>

                    {/* Metadata Badges: Seed & Audit Hash */}
                    <div className="flex flex-col sm:flex-row md:flex-col gap-2 self-start shrink-0">
                      {/* Seed Badge */}
                      <div className="flex items-center justify-between gap-2 bg-gray-50 border border-gray-200 px-3 py-1.5 rounded-lg">
                        <span className="text-xs text-gray-500 font-medium">Scenario Seed:</span>
                        <code className="text-xs font-mono font-bold text-gray-800 select-all">
                          {scenario.seed}
                        </code>
                        <button
                          type="button"
                          onClick={handleCopySeed}
                          className="text-gray-400 hover:text-gray-700 transition p-0.5 cursor-pointer"
                          title="Copy seed"
                        >
                          {copiedSeed ? (
                            <Check className="w-3.5 h-3.5 text-fresh-600" />
                          ) : (
                            <Copy className="w-3.5 h-3.5" />
                          )}
                        </button>
                      </div>

                      {/* Audit Plan Hash */}
                      {results?.plan_hash && (
                        <div className="flex items-center justify-between gap-2 bg-gray-50 border border-gray-200 px-3 py-1.5 rounded-lg">
                          <span className="text-xs text-gray-500 font-medium flex items-center gap-1">
                            <Fingerprint className="w-3.5 h-3.5 text-gray-400" />
                            Audit Hash:
                          </span>
                          <code className="text-xs font-mono text-gray-700 select-all">
                            {results.plan_hash}
                          </code>
                          <button
                            type="button"
                            onClick={handleCopyHash}
                            className="text-gray-400 hover:text-gray-700 transition p-0.5 cursor-pointer"
                            title="Copy plan hash"
                          >
                            {copiedHash ? (
                              <Check className="w-3.5 h-3.5 text-fresh-600" />
                            ) : (
                              <Copy className="w-3.5 h-3.5" />
                            )}
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </section>
            )}

            {/* 1. Summary Cards */}
            <section aria-label="Performance Summary">
              <SummaryCards summary={summaryData} optimizedPlan={planData} />
            </section>

            {/* 2. Comparison Charts */}
            <section aria-label="Comparative Visualizations">
              <ComparisonChart summary={summaryData} />
            </section>

            {/* 3. Dispatch Plan Table */}
            <section aria-label="Optimized Dispatch Plan">
              <DispatchTable plan={planData} />
            </section>
          </div>
        )}
      </main>
    </div>
  )
}
