import React from 'react'

export default function ScorecardPanel({ summary = {}, planHash = '', seed = null, warnings = [] }) {
  const rows = [
    {
      metric: 'Spoilage (% of batch qty)',
      baseline: summary.baseline_spoilage_pct,
      optimized: summary.optimized_spoilage_pct,
      format: (value) => `${Number(value || 0).toFixed(1)}%`,
      delta: Number(summary.optimized_spoilage_pct || 0) - Number(summary.baseline_spoilage_pct || 0),
      deltaFormat: (value) => `${value > 0 ? '+' : ''}${value.toFixed(1)} pp`,
    },
    {
      metric: 'Net Revenue',
      baseline: summary.baseline_net_revenue,
      optimized: summary.optimized_net_revenue,
      format: (value) => `₹${Math.round(Number(value || 0)).toLocaleString()}`,
      delta: Number(summary.optimized_net_revenue || 0) - Number(summary.baseline_net_revenue || 0),
      deltaFormat: (value) => `${value >= 0 ? '+' : '−'}₹${Math.abs(Math.round(value)).toLocaleString()}`,
    },
    {
      metric: 'Demand Fulfilled (%)',
      baseline: summary.baseline_demand_fulfilled_pct,
      optimized: summary.optimized_demand_fulfilled_pct,
      format: (value) => `${Number(value || 0).toFixed(1)}%`,
      delta: Number(summary.optimized_demand_fulfilled_pct || 0) - Number(summary.baseline_demand_fulfilled_pct || 0),
      deltaFormat: (value) => `${value > 0 ? '+' : ''}${value.toFixed(1)} pp`,
    },
    {
      metric: 'Feasibility Violations',
      baseline: summary.baseline_feasibility_violations,
      optimized: summary.optimized_feasibility_violations,
      format: (value) => Number(value || 0).toLocaleString(),
      delta: Number(summary.optimized_feasibility_violations || 0) - Number(summary.baseline_feasibility_violations || 0),
      deltaFormat: (value) => `${value > 0 ? '+' : ''}${value}`,
    },
    {
      metric: 'Truck Capacity Used (%)',
      baseline: summary.baseline_truck_capacity_used_pct,
      optimized: summary.optimized_truck_capacity_used_pct,
      format: (value) => `${Number(value || 0).toFixed(1)}%`,
      delta: Number(summary.optimized_truck_capacity_used_pct || 0) - Number(summary.baseline_truck_capacity_used_pct || 0),
      deltaFormat: (value) => `${value > 0 ? '+' : ''}${value.toFixed(1)} pp`,
    },
  ]
  const destinationFulfillment = summary.optimized_destination_fulfillment || []

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900">Optimization Scorecard</h3>
        <p className="mt-1 text-sm text-gray-500">Comparable baseline and optimized outcomes for this scenario</p>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 text-left">
          <thead className="bg-gray-50">
            <tr>
              {['Metric', 'Baseline', 'Optimized', 'Delta'].map((heading) => (
                <th key={heading} className="px-5 py-3 text-xs font-semibold uppercase tracking-wider text-gray-500">
                  {heading}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 text-sm">
            {rows.map((row) => (
              <tr key={row.metric}>
                <th className="px-5 py-3.5 font-medium text-gray-700">
                  {row.metric}
                  {row.metric === 'Demand Fulfilled (%)' && destinationFulfillment.length > 0 && (
                    <div className="mt-1 max-w-sm text-xs font-normal text-gray-400">
                      {destinationFulfillment.map((destination) => (
                        <span key={destination.destination_id} className="mr-2 inline-block">
                          {destination.destination_name}: {Number(destination.fulfillment_pct || 0).toFixed(0)}%
                        </span>
                      ))}
                    </div>
                  )}
                </th>
                <td className="px-5 py-3.5 whitespace-nowrap text-gray-600">{row.format(row.baseline)}</td>
                <td className="px-5 py-3.5 whitespace-nowrap font-semibold text-gray-900">{row.format(row.optimized)}</td>
                <td className="px-5 py-3.5 whitespace-nowrap text-gray-600">{row.deltaFormat(row.delta)}</td>
              </tr>
            ))}
            <tr>
              <th className="px-5 py-3.5 font-medium text-gray-700">Plan Hash (seed)</th>
              <td className="px-5 py-3.5 text-gray-400">—</td>
              <td className="px-5 py-3.5 font-mono text-xs text-gray-800" title={planHash}>
                {planHash ? `${planHash.slice(0, 12)}… (${seed ?? 'n/a'})` : 'N/A'}
              </td>
              <td className="px-5 py-3.5 text-gray-400">—</td>
            </tr>
          </tbody>
        </table>
      </div>
      {warnings.length > 0 && (
        <div className="border-t border-amber-100 bg-amber-50 px-5 py-3 text-sm text-amber-800">
          {warnings.map((warning) => <p key={warning}>{warning}</p>)}
        </div>
      )}
    </div>
  )
}
