import React, { useState, useMemo } from 'react'
import {
  Truck,
  AlertTriangle,
  Search,
  Filter,
  ArrowUpDown,
  Tag,
  CheckCircle2,
  HelpCircle,
} from 'lucide-react'

export default function DispatchTable({ plan = [] }) {
  const dispatches = Array.isArray(plan) ? plan : []
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState('ALL') // ALL, DISCOUNTED, FULL_PRICE, SPOILED
  const [sortBy, setSortBy] = useState('DEFAULT') // DEFAULT, REVENUE_DESC, QTY_DESC, DISCOUNT_DESC

  const filteredAndSortedDispatches = useMemo(() => {
    let result = [...dispatches]

    // 1. Text Search Filter
    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase().trim()
      result = result.filter((item) => {
        const comm = String(item?.commodity || '').toLowerCase()
        const dest = String(item?.destination_name || item?.destination || '').toLowerCase()
        const reason = String(item?.reason || '').toLowerCase()
        const bId = String(item?.batch_id || '')
        return comm.includes(q) || dest.includes(q) || reason.includes(q) || bId.includes(q)
      })
    }

    // 2. Tab Filter
    if (filterType === 'DISCOUNTED') {
      result = result.filter((item) => {
        const disc = Number(item?.discount_pct ?? item?.discount ?? 0)
        return disc > 0 && !item?.is_spoiled
      })
    } else if (filterType === 'FULL_PRICE') {
      result = result.filter((item) => {
        const disc = Number(item?.discount_pct ?? item?.discount ?? 0)
        return disc === 0 && !item?.is_spoiled && item?.destination_name !== 'None'
      })
    } else if (filterType === 'SPOILED') {
      result = result.filter((item) => item?.is_spoiled || item?.destination_name === 'None')
    }

    // 3. Sorting
    if (sortBy === 'REVENUE_DESC') {
      result.sort((a, b) => Number(b?.revenue ?? 0) - Number(a?.revenue ?? 0))
    } else if (sortBy === 'QTY_DESC') {
      result.sort((a, b) => Number(b?.quantity_kg ?? 0) - Number(a?.quantity_kg ?? 0))
    } else if (sortBy === 'DISCOUNT_DESC') {
      result.sort((a, b) => Number(b?.discount_pct ?? 0) - Number(a?.discount_pct ?? 0))
    }

    return result
  }, [dispatches, searchTerm, filterType, sortBy])

  const counts = useMemo(() => {
    return {
      all: dispatches.length,
      discounted: dispatches.filter((d) => Number(d?.discount_pct ?? 0) > 0 && !d?.is_spoiled).length,
      fullPrice: dispatches.filter((d) => Number(d?.discount_pct ?? 0) === 0 && !d?.is_spoiled && d?.destination_name !== 'None').length,
      unallocated: dispatches.filter((d) => d?.is_spoiled || d?.destination_name === 'None').length,
    }
  }, [dispatches])

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
      {/* Title & Controls Bar */}
      <div className="p-5 border-b border-gray-100 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-fresh-100 text-fresh-700 flex items-center justify-center shrink-0">
            <Truck className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold text-gray-900">Optimized Dispatch Plan</h3>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-fresh-100 text-fresh-800 border border-fresh-200">
                {dispatches.length} allocations
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-0.5">
              Explainable routing decisions sorted by decay urgency and profit feasibility
            </p>
          </div>
        </div>

        {/* Filter and Search Bar */}
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="relative">
            <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Filter produce or city..."
              className="pl-9 pr-3 py-1.5 text-xs bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-fresh-500 w-44 sm:w-52"
            />
          </div>

          <div className="flex items-center gap-1 bg-gray-50 p-1 rounded-lg border border-gray-200">
            <ArrowUpDown className="w-3.5 h-3.5 text-gray-400 ml-1.5" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="text-xs bg-transparent border-none text-gray-700 font-medium focus:outline-none cursor-pointer pr-1"
            >
              <option value="DEFAULT">Order: Urgency</option>
              <option value="REVENUE_DESC">Sort: Revenue (High)</option>
              <option value="QTY_DESC">Sort: Quantity (High)</option>
              <option value="DISCOUNT_DESC">Sort: Discount %</option>
            </select>
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="px-5 py-2.5 bg-gray-50/60 border-b border-gray-100 flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => setFilterType('ALL')}
          className={`px-3 py-1 rounded-lg text-xs font-medium transition ${
            filterType === 'ALL'
              ? 'bg-white text-gray-900 shadow-xs border border-gray-200'
              : 'text-gray-500 hover:text-gray-900'
          }`}
        >
          All ({counts.all})
        </button>
        <button
          type="button"
          onClick={() => setFilterType('DISCOUNTED')}
          className={`px-3 py-1 rounded-lg text-xs font-medium transition ${
            filterType === 'DISCOUNTED'
              ? 'bg-amber-100 text-amber-900 shadow-xs border border-amber-200 font-semibold'
              : 'text-gray-500 hover:text-gray-900'
          }`}
        >
          ⚡ Markdown Deals ({counts.discounted})
        </button>
        <button
          type="button"
          onClick={() => setFilterType('FULL_PRICE')}
          className={`px-3 py-1 rounded-lg text-xs font-medium transition ${
            filterType === 'FULL_PRICE'
              ? 'bg-fresh-100 text-fresh-900 shadow-xs border border-fresh-200 font-semibold'
              : 'text-gray-500 hover:text-gray-900'
          }`}
        >
          ✓ Full Price ({counts.fullPrice})
        </button>
        {counts.unallocated > 0 && (
          <button
            type="button"
            onClick={() => setFilterType('SPOILED')}
            className={`px-3 py-1 rounded-lg text-xs font-medium transition ${
              filterType === 'SPOILED'
                ? 'bg-rose-100 text-rose-900 shadow-xs border border-rose-200 font-semibold'
                : 'text-gray-500 hover:text-gray-900'
            }`}
          >
            ⚠ Unallocated ({counts.unallocated})
          </button>
        )}
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 text-left">
          <thead className="bg-gray-50/80">
            <tr>
              <th scope="col" className="px-5 py-3 text-xs font-semibold uppercase tracking-wider text-gray-500">
                #
              </th>
              <th scope="col" className="px-5 py-3 text-xs font-semibold uppercase tracking-wider text-gray-500">
                Batch ID
              </th>
              <th scope="col" className="px-5 py-3 text-xs font-semibold uppercase tracking-wider text-gray-500">
                Commodity
              </th>
              <th scope="col" className="px-5 py-3 text-xs font-semibold uppercase tracking-wider text-gray-500">
                Destination
              </th>
              <th scope="col" className="px-5 py-3 text-xs font-semibold uppercase tracking-wider text-gray-500">
                Quantity
              </th>
              <th scope="col" className="px-5 py-3 text-xs font-semibold uppercase tracking-wider text-gray-500">
                Discount
              </th>
              <th scope="col" className="px-5 py-3 text-xs font-semibold uppercase tracking-wider text-gray-500">
                Realized Revenue
              </th>
              <th scope="col" className="px-5 py-3 text-xs font-semibold uppercase tracking-wider text-gray-500">
                Decision Reason
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 text-sm">
            {filteredAndSortedDispatches.length === 0 ? (
              <tr>
                <td colSpan="8" className="px-6 py-12 text-center text-gray-400">
                  No matching dispatch records found
                </td>
              </tr>
            ) : (
              filteredAndSortedDispatches.map((item, idx) => {
                const isSpoiled = Boolean(item?.is_spoiled || item?.destination_name === 'None')
                const rawDiscount = Number(item?.discount_pct ?? item?.discount)
                const discount = Number.isFinite(rawDiscount) ? rawDiscount : 0
                const rawRev = Number(item?.expected_revenue ?? item?.revenue)
                const revenue = Number.isFinite(rawRev) ? rawRev : null
                const rawQty = Number(item?.quantity_kg ?? item?.quantity)
                const qty = Number.isFinite(rawQty) ? rawQty : null
                const reason = item?.reason ?? item?.dispatch_reason ?? 'Optimal direct routing'
                const batchId = item?.batch_id ?? item?.batchId ?? `B-${idx + 1}`
                const commodity = item?.commodity ?? item?.commodity_name ?? '—'
                const destination = item?.destination_name ?? item?.destination ?? 'None'

                const rowBg = isSpoiled
                  ? 'bg-rose-50/70 hover:bg-rose-100/60 text-gray-900'
                  : discount > 0
                  ? 'bg-amber-50/30 hover:bg-amber-100/30 text-gray-900'
                  : idx % 2 === 1
                  ? 'bg-gray-50/50 hover:bg-gray-100/50 text-gray-800'
                  : 'bg-white hover:bg-gray-50 text-gray-800'

                return (
                  <tr key={batchId + '-' + idx} className={`${rowBg} transition-colors border-b border-gray-100`}>
                    {/* Index */}
                    <td className="px-5 py-3.5 whitespace-nowrap text-xs font-medium text-gray-400">
                      {idx + 1}
                    </td>

                    {/* Batch ID */}
                    <td className="px-5 py-3.5 whitespace-nowrap font-mono text-xs font-semibold text-gray-900">
                      <div className="flex items-center gap-1.5">
                        {isSpoiled ? (
                          <AlertTriangle className="w-3.5 h-3.5 text-rose-500 shrink-0" />
                        ) : (
                          <CheckCircle2 className="w-3.5 h-3.5 text-fresh-600 shrink-0" />
                        )}
                        <span>{batchId}</span>
                      </div>
                    </td>

                    {/* Commodity */}
                    <td className="px-5 py-3.5 whitespace-nowrap font-medium text-gray-900">
                      {commodity}
                    </td>

                    {/* Destination */}
                    <td className="px-5 py-3.5 whitespace-nowrap text-gray-700">
                      <span className={destination === 'None' ? 'text-gray-400 italic' : 'font-medium'}>
                        {destination}
                      </span>
                    </td>

                    {/* Quantity */}
                    <td className="px-5 py-3.5 whitespace-nowrap font-medium text-gray-800">
                      {qty !== null ? `${Math.round(qty).toLocaleString()} kg` : 'N/A'}
                    </td>

                    {/* Discount Badge */}
                    <td className="px-5 py-3.5 whitespace-nowrap">
                      {discount > 0 ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-200">
                          <Tag className="w-3 h-3 text-amber-600" />
                          {discount}% off
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-50 text-green-700 border border-green-200">
                          Full Price
                        </span>
                      )}
                    </td>

                    {/* Revenue */}
                    <td className="px-5 py-3.5 whitespace-nowrap font-semibold text-gray-900 font-mono text-xs">
                      {revenue !== null && revenue > 0
                        ? `₹${Math.round(revenue).toLocaleString()}`
                        : <span className="text-gray-400">₹0</span>}
                    </td>

                    {/* Reason */}
                    <td className="px-5 py-3.5 max-w-sm text-xs text-gray-600 truncate" title={reason}>
                      {reason}
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
