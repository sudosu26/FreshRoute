import React, { useState, useEffect } from 'react'
import {
  Play,
  RotateCcw,
  Leaf,
  Loader2,
  AlertCircle,
  Copy,
  Check,
  Sparkles,
} from 'lucide-react'
import SummaryCards from './components/SummaryCards'
import ComparisonChart from './components/ComparisonChart'
import DispatchTable from './components/DispatchTable'

export default function App() {
  const [scenario, setScenario] = useState(null)
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [seedInput, setSeedInput] = useState('')
  const [copied, setCopied] = useState(false)

  // Fetch a scenario and immediately run optimization
  const loadScenario = async (targetSeed = null) => {
    setLoading(true)
    setError(null)
    try {
      const url =
        targetSeed !== null && targetSeed !== undefined && targetSeed !== ''
          ? `/api/scenario?seed=${encodeURIComponent(targetSeed)}`
          : '/api/scenario'

      const scenarioRes = await fetch(url)
      if (!scenarioRes.ok) {
        throw new Error(`Failed to load scenario: ${scenarioRes.status} ${scenarioRes.statusText}`)
      }

      const scenarioData = await scenarioRes.json()
      setScenario(scenarioData)
      setSeedInput(String(scenarioData.seed))

      // Run optimization on the freshly generated scenario payload
      const optRes = await fetch('/api/optimize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ scenario: scenarioData }),
      })

      if (!optRes.ok) {
        throw new Error(`Optimization failed: ${optRes.status} ${optRes.statusText}`)
      }

      const optData = await optRes.json()
      setResults(optData)
    } catch (err) {
      console.error('Scenario / Optimization error:', err)
      setError(err.message || 'An error occurred while generating scenario and running optimization.')
    } finally {
      setLoading(false)
    }
  }

  // Initial load on app start
  useEffect(() => {
    loadScenario(null)
  }, [])

  const handleNewScenario = () => {
    loadScenario(null)
  }

  const handleReplay = (e) => {
    if (e) e.preventDefault()
    if (!seedInput || isNaN(Number(seedInput))) {
      setError('Please enter a valid numeric seed to replay.')
      return
    }
    loadScenario(parseInt(seedInput, 10))
  }

  const handleCopySeed = () => {
    if (!scenario?.seed) return
    navigator.clipboard.writeText(String(scenario.seed))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const summaryData = results?.summary || {}
  const planData = results?.optimized_plan || []

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 pb-16">
      {/* Top Navigation / App Bar */}
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
              </div>
              <p className="mt-0.5 text-xs sm:text-sm font-medium text-gray-500">
                Decision Support for Perishable Produce Distribution
              </p>
            </div>

            {/* Action Controls */}
            <div className="flex flex-wrap items-center gap-3">
              {/* Replay seed input */}
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
                  className="w-24 px-2 py-1 text-xs font-mono bg-white border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-fresh-500"
                />
                <button
                  type="submit"
                  disabled={loading || !seedInput.trim()}
                  className="px-2.5 py-1 text-xs font-semibold text-gray-700 bg-white border border-gray-200 hover:bg-gray-100 rounded disabled:opacity-50 transition"
                >
                  Replay
                </button>
              </form>

              {/* New Scenario button */}
              <button
                type="button"
                onClick={handleNewScenario}
                disabled={loading}
                className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg bg-fresh-600 text-sm font-semibold text-white shadow-sm hover:bg-fresh-700 active:bg-fresh-800 disabled:opacity-50 transition"
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
            <h3 className="text-xl font-bold text-gray-900">Generating Scenario & Computing Optimization</h3>
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
                        <span>🚛 <strong>{scenario.trucks?.length || 0}</strong> reefer trucks (fleet capacity: {Math.round(scenario.stats?.total_truck_capacity_kg || 0).toLocaleString()} kg)</span>
                      </div>
                    </div>

                    {/* Copyable Seed Badge */}
                    <div className="flex items-center gap-2 self-start bg-gray-50 border border-gray-200 px-3 py-2 rounded-lg">
                      <span className="text-xs text-gray-500 font-medium">Scenario Seed:</span>
                      <code className="text-xs font-mono font-bold text-gray-800 select-all">
                        {scenario.seed}
                      </code>
                      <button
                        type="button"
                        onClick={handleCopySeed}
                        className="text-gray-400 hover:text-gray-700 transition p-0.5"
                        title="Copy seed"
                      >
                        {copied ? (
                          <Check className="w-3.5 h-3.5 text-fresh-600" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                      </button>
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
