'use client'

import { Card } from '@/components/ui/card'
import { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import type { EconomicsLineItem } from '@/types'
import { formatCurrency, formatNumber, formatPercent } from './reportUtils'

interface EconomicsChartProps {
  data?: EconomicsLineItem[]
}

export function EconomicsChart({ data = [] }: EconomicsChartProps) {
  // Validate data quality - check if all values are identical
  const hasValidData = data.length > 0
  const hasVariedData = data.length > 1 && !data.every(
    (item, _, arr) => 
      Math.abs(item.net_profit_rupees - arr[0].net_profit_rupees) < 1 &&
      Math.abs(item.roi_percent - arr[0].roi_percent) < 0.1
  )

  return (
    <Card className="p-6 space-y-4">
      <div>
        <h3 className="text-lg font-semibold">Economics Analysis</h3>
        <p className="text-sm text-gray-600 mt-1">Estimated profitability and break-even outlook for each treatment</p>
      </div>
      {!hasValidData ? (
        <p className="text-gray-600 text-sm h-64 flex items-center">No economics data available.</p>
      ) : !hasVariedData ? (
        <div className="text-center py-8">
          <p className="text-orange-600 text-sm font-medium">⚠️ Economics data quality issue detected</p>
          <p className="text-gray-600 text-sm mt-2">All treatments show identical values. This may indicate a calculation error.</p>
          <p className="text-gray-500 text-xs mt-1">Showing available data below for reference:</p>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4 mt-4">
            {data.map((item) => (
              <div key={item.treatment} className="rounded-lg bg-orange-50 border border-orange-200 p-4">
                <p className="text-xs text-gray-500">{item.treatment}</p>
                <p className="mt-2 text-sm font-semibold text-gray-900">{formatCurrency(item.net_profit_rupees)}</p>
                <p className="text-xs text-gray-600">ROI {formatPercent(item.roi_percent / 100)}</p>
                <p className="text-xs text-gray-600">Break-even {formatNumber(item.break_even_days)} days</p>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <>
          <ResponsiveContainer width="100%" height={320}>
            <ComposedChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="treatment" tick={{ fontSize: 12 }} />
              <YAxis yAxisId="left" tickFormatter={(value) => `INR ${Number(value).toLocaleString()}`} />
              <YAxis yAxisId="right" orientation="right" tickFormatter={(value) => `${Number(value).toFixed(0)}%`} />
              <Tooltip
                formatter={(value: number | string, name) => {
                  if (name === 'roi_percent') return [`${Number(value).toFixed(1)}%`, 'ROI']
                  if (name === 'net_profit_rupees') return [formatCurrency(Number(value)), 'Net profit']
                  if (name === 'break_even_days') return [`${Number(value).toFixed(0)} days`, 'Break-even']
                  return [value, name]
                }}
                labelFormatter={(label) => `Treatment: ${label}`}
              />
              <Bar yAxisId="left" dataKey="net_profit_rupees" fill="#10b981" radius={[6, 6, 0, 0]} />
              <Line yAxisId="right" type="monotone" dataKey="roi_percent" stroke="#065f46" strokeWidth={2} dot={{ r: 3 }} />
            </ComposedChart>
          </ResponsiveContainer>

          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {data.map((item) => (
              <div key={item.treatment} className="rounded-lg bg-gray-50 p-4">
                <p className="text-xs text-gray-500">{item.treatment}</p>
                <p className="mt-2 text-sm font-semibold text-gray-900">{formatCurrency(item.net_profit_rupees)}</p>
                <p className="text-xs text-gray-600">ROI {formatPercent(item.roi_percent / 100)}</p>
                <p className="text-xs text-gray-600">Break-even {formatNumber(item.break_even_days)} days</p>
              </div>
            ))}
          </div>
        </>
      )}
    </Card>
  )
}
