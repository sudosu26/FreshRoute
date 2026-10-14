import React from 'react'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from 'recharts'

export default function ComparisonChart({ summary = {} }) {
  const safeNum = (val) => {
    const n = Number(val)
    return Number.isFinite(n) ? n : 0
  }

  const baselineSpoilage = safeNum(summary?.baseline_spoilage_kg)
  const optimizedSpoilage = safeNum(summary?.optimized_spoilage_kg)
  const baselineRevenue = safeNum(summary?.baseline_revenue)
  const optimizedRevenue = safeNum(summary?.optimized_revenue)

  const spoilageData = [
    { name: 'Baseline', value: baselineSpoilage, color: '#f87171' }, // red/rose-400
    { name: 'Optimized', value: optimizedSpoilage, color: '#22c55e' }, // fresh-500
  ]

  const revenueData = [
    { name: 'Baseline', value: baselineRevenue, color: '#fbbf24' }, // amber-400
    { name: 'Optimized', value: optimizedRevenue, color: '#22c55e' }, // fresh-500
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Spoilage Comparison Chart */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Spoilage (kg)</h3>
            <p className="text-xs text-gray-500">Lower is better • Post-harvest losses</p>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1.5 text-gray-600">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-400"></span> Baseline
            </span>
            <span className="flex items-center gap-1.5 text-fresh-700 font-medium">
              <span className="w-2.5 h-2.5 rounded-full bg-fresh-500"></span> Optimized
            </span>
          </div>
        </div>

        <div className="w-full h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={spoilageData}
              margin={{ top: 20, right: 20, left: 10, bottom: 10 }}
            >
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
              <XAxis
                dataKey="name"
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#6b7280', fontSize: 13 }}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#6b7280', fontSize: 12 }}
                tickFormatter={(val) => Number.isFinite(val) ? `${Math.round(val).toLocaleString()} kg` : 'N/A'}
              />
              <Tooltip
                cursor={{ fill: 'rgba(243, 244, 246, 0.4)' }}
                formatter={(val) => [Number.isFinite(Number(val)) ? `${Math.round(Number(val)).toLocaleString()} kg` : 'N/A', 'Spoilage']}
                contentStyle={{
                  backgroundColor: '#ffffff',
                  borderRadius: '0.5rem',
                  border: '1px solid #e5e7eb',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                }}
              />
              <Bar dataKey="value" radius={[6, 6, 0, 0]} maxBarSize={64}>
                {spoilageData.map((entry, index) => (
                  <Cell key={`spoilage-cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Revenue Comparison Chart */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Net Revenue (₹)</h3>
            <p className="text-xs text-gray-500">Marketplace revenue after transport costs</p>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1.5 text-gray-600">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-400"></span> Baseline
            </span>
            <span className="flex items-center gap-1.5 text-fresh-700 font-medium">
              <span className="w-2.5 h-2.5 rounded-full bg-fresh-500"></span> Optimized
            </span>
          </div>
        </div>

        <div className="w-full h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={revenueData}
              margin={{ top: 20, right: 20, left: 15, bottom: 10 }}
            >
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
              <XAxis
                dataKey="name"
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#6b7280', fontSize: 13 }}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#6b7280', fontSize: 12 }}
                tickFormatter={(val) => Number.isFinite(val) ? `₹${Math.round(val).toLocaleString()}` : 'N/A'}
              />
              <Tooltip
                cursor={{ fill: 'rgba(243, 244, 246, 0.4)' }}
                formatter={(val) => [Number.isFinite(Number(val)) ? `₹${Math.round(Number(val)).toLocaleString()}` : 'N/A', 'Revenue']}
                contentStyle={{
                  backgroundColor: '#ffffff',
                  borderRadius: '0.5rem',
                  border: '1px solid #e5e7eb',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                }}
              />
              <Bar dataKey="value" radius={[6, 6, 0, 0]} maxBarSize={64}>
                {revenueData.map((entry, index) => (
                  <Cell key={`revenue-cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
