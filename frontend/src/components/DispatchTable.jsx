import React from 'react'
import { Truck, AlertTriangle } from 'lucide-react'

export default function DispatchTable({ plan = [] }) {
  const dispatches = Array.isArray(plan) ? plan : []

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      {/* Title bar */}
      <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-white">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-fresh-100 text-fresh-700 flex items-center justify-center">
            <Truck className="w-4 h-4" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">Optimized Dispatch Plan</h3>
        </div>
        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-fresh-100 text-fresh-800 border border-fresh-200">
          {dispatches.length} {dispatches.length === 1 ? 'Dispatch' : 'Dispatches'}
        </span>
      </div>

      {/* Table content */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 text-left">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-5 py-3.5 text-xs font-semibold uppercase tracking-wider text-gray-500">
                #
              </th>
              <th scope="col" className="px-5 py-3.5 text-xs font-semibold uppercase tracking-wider text-gray-500">
                Batch ID
              </th>
              <th scope="col" className="px-5 py-3.5 text-xs font-semibold uppercase tracking-wider text-gray-500">
                Commodity
              </th>
              <th scope="col" className="px-5 py-3.5 text-xs font-semibold uppercase tracking-wider text-gray-500">
                Destination
              </th>
              <th scope="col" className="px-5 py-3.5 text-xs font-semibold uppercase tracking-wider text-gray-500">
                Qty (kg)
              </th>
              <th scope="col" className="px-5 py-3.5 text-xs font-semibold uppercase tracking-wider text-gray-500">
                Discount
              </th>
              <th scope="col" className="px-5 py-3.5 text-xs font-semibold uppercase tracking-wider text-gray-500">
                Revenue (₹)
              </th>
              <th scope="col" className="px-5 py-3.5 text-xs font-semibold uppercase tracking-wider text-gray-500">
                Reason
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 text-sm">
            {dispatches.length === 0 ? (
              <tr>
                <td colSpan="8" className="px-6 py-12 text-center text-gray-400">
                  No dispatch records available
                </td>
              </tr>
            ) : (
              dispatches.map((item, idx) => {
                const isSpoiled = Boolean(item?.is_spoiled ?? item?.spoiled ?? false)
                const rawDiscount = Number(item?.discount_pct ?? item?.discount)
                const discount = Number.isFinite(rawDiscount) ? rawDiscount : 0
                const rawRev = Number(item?.expected_revenue ?? item?.revenue)
                const revenue = Number.isFinite(rawRev) ? rawRev : null
                const rawQty = Number(item?.quantity_kg ?? item?.quantity)
                const qty = Number.isFinite(rawQty) ? rawQty : null
                const reason = item?.reason ?? item?.dispatch_reason ?? 'Standard routing'
                const batchId = item?.batch_id ?? item?.batchId ?? `B-${idx + 1}`
                const commodity = item?.commodity ?? item?.commodity_name ?? '—'
                const destination = item?.destination_name ?? item?.destination ?? item?.destination_market ?? '—'

                const rowBg = isSpoiled
                  ? 'bg-red-50/80 hover:bg-red-100/70 text-red-950'
                  : idx % 2 === 1
                  ? 'bg-gray-50/60 hover:bg-gray-100/60 text-gray-800'
                  : 'bg-white hover:bg-gray-50 text-gray-800'

                return (
                  <tr key={batchId + idx} className={`${rowBg} transition-colors border-b border-gray-100`}>
                    {/* Index */}
                    <td className="px-5 py-4 whitespace-nowrap text-xs font-medium text-gray-400">
                      {idx + 1}
                    </td>

                    {/* Batch ID */}
                    <td className="px-5 py-4 whitespace-nowrap font-mono text-xs font-semibold text-gray-900">
                      <div className="flex items-center gap-1.5">
                        {isSpoiled && (
                          <span title="Batch is spoiled or at critical risk">
                            <AlertTriangle className="w-4 h-4 text-red-500 shrink-0" />
                          </span>
                        )}
                        <span>{batchId}</span>
                      </div>
                    </td>

                    {/* Commodity */}
                    <td className="px-5 py-4 whitespace-nowrap font-medium text-gray-900">
                      {commodity}
                    </td>

                    {/* Destination */}
                    <td className="px-5 py-4 whitespace-nowrap text-gray-700">
                      {destination}
                    </td>

                    {/* Quantity */}
                    <td className="px-5 py-4 whitespace-nowrap font-medium text-gray-800">
                      {qty !== null ? `${Math.round(qty).toLocaleString()} kg` : 'N/A'}
                    </td>

                    {/* Discount */}
                    <td className="px-5 py-4 whitespace-nowrap">
                      {discount > 0 ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-200">
                          {discount}% off
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-50 text-green-700 border border-green-200">
                          None
                        </span>
                      )}
                    </td>

                    {/* Revenue */}
                    <td className="px-5 py-4 whitespace-nowrap font-semibold text-gray-900">
                      {revenue !== null ? `₹${revenue.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}` : 'N/A'}
                    </td>

                    {/* Reason */}
                    <td className="px-5 py-4 max-w-xs text-xs text-gray-600 truncate" title={reason}>
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
