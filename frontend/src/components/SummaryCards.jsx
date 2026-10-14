import React from 'react'
import { TrendingDown, TrendingUp, Package, Tag } from 'lucide-react'

export default function SummaryCards({ summary = {}, optimizedPlan = [] }) {
  const safeNum = (val) => {
    const n = Number(val)
    return Number.isFinite(n) ? n : null
  }

  // Calculate average discount on batches where discount > 0
  const discountedBatches = (optimizedPlan || []).filter((item) => {
    const discount = safeNum(item?.discount_pct ?? item?.discount)
    return discount !== null && discount > 0
  })

  const rawAvgDiscount =
    discountedBatches.length > 0
      ? discountedBatches.reduce(
          (acc, item) => acc + (safeNum(item?.discount_pct ?? item?.discount) || 0),
          0
        ) / discountedBatches.length
      : 0

  const spoilageReduction = safeNum(summary?.spoilage_reduction_pct)
  const revenueIncrease = safeNum(summary?.revenue_increase_pct)
  const baselineSpoilage = safeNum(summary?.baseline_spoilage_kg)
  const optimizedSpoilage = safeNum(summary?.optimized_spoilage_kg)
  const baselineRevenue = safeNum(summary?.baseline_revenue)
  const optimizedRevenue = safeNum(summary?.optimized_revenue)
  const totalBatches = summary?.total_batches ?? (optimizedPlan ? optimizedPlan.length : 0)
  const totalQuantity = safeNum(summary?.total_quantity_kg)
  const avgDiscount = safeNum(rawAvgDiscount)

  const formatPct = (val, prefix = '') => {
    if (val === null) return 'N/A'
    return `${prefix}${val.toFixed(1)}%`
  }

  const formatCurrency = (val) => {
    if (val === null) return 'N/A'
    return `₹${Math.round(val).toLocaleString()}`
  }

  const formatKg = (val) => {
    if (val === null) return 'N/A'
    return `${Math.round(val).toLocaleString()}kg`
  }

  const cards = [
    {
      id: 'spoilage',
      title: 'Spoilage Reduced',
      value: formatPct(spoilageReduction),
      subtitle: `${formatKg(baselineSpoilage)} → ${formatKg(optimizedSpoilage)}`,
      icon: TrendingDown,
      iconBg: 'bg-fresh-100 text-fresh-700',
      valueColor: 'text-fresh-700',
    },
    {
      id: 'revenue',
      title: 'Revenue Impact',
      value: revenueIncrease !== null ? (revenueIncrease >= 0 ? `+${revenueIncrease.toFixed(1)}%` : `${revenueIncrease.toFixed(1)}%`) : 'N/A',
      subtitle: `${formatCurrency(baselineRevenue)} → ${formatCurrency(optimizedRevenue)}`,
      icon: TrendingUp,
      iconBg: 'bg-fresh-100 text-fresh-700',
      valueColor: revenueIncrease !== null && revenueIncrease < 0 ? 'text-amber-600' : 'text-fresh-700',
    },
    {
      id: 'batches',
      title: 'Batches Processed',
      value: totalBatches !== null && totalBatches !== undefined ? totalBatches.toLocaleString() : 'N/A',
      subtitle: totalQuantity !== null ? `${Math.round(totalQuantity).toLocaleString()}kg total` : 'N/A',
      icon: Package,
      iconBg: 'bg-blue-50 text-blue-600',
      valueColor: 'text-gray-900',
    },
    {
      id: 'discount',
      title: 'Avg Clearance Markdown',
      value: formatPct(avgDiscount),
      subtitle: `Applied to ${discountedBatches.length} batch${discountedBatches.length === 1 ? '' : 'es'}`,
      icon: Tag,
      iconBg: 'bg-amber-50 text-amber-600',
      valueColor: 'text-gray-900',
    },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {cards.map((card) => {
        const IconComponent = card.icon
        return (
          <div
            key={card.id}
            className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex flex-col justify-between transition-all hover:shadow-md"
          >
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm font-medium text-gray-500">{card.title}</span>
              <div className={`w-10 h-10 rounded-full flex items-center justify-center ${card.iconBg}`}>
                <IconComponent className="w-5 h-5" />
              </div>
            </div>
            <div>
              <div className={`text-3xl font-bold tracking-tight ${card.valueColor}`}>
                {card.value}
              </div>
              <p className="mt-1 text-sm text-gray-500">{card.subtitle}</p>
            </div>
          </div>
        )
      })}
    </div>
  )
}
