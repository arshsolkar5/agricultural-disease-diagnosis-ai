import { Card } from '@/components/ui/card'
import type { MarketData } from '@/types'
import { formatCurrency, formatPercent } from './reportUtils'

interface MarketAnalysisPanelProps {
  marketData?: MarketData
}

export function MarketAnalysisPanel({ marketData }: MarketAnalysisPanelProps) {
  const price = marketData?.current_price_per_quintal

  return (
    <Card className="p-6 space-y-4">
      <div>
        <h3 className="text-lg font-semibold">Market Analysis</h3>
        <p className="text-sm text-gray-600 mt-1">Location-aware guidance for crop timing and pricing</p>
      </div>

      {!marketData ? (
        <p className="text-sm text-gray-600">No market analysis available.</p>
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-lg bg-gray-50 p-4">
              <p className="text-xs text-gray-500">Price</p>
              <p className="mt-1 text-lg font-semibold">{price ? formatCurrency(price) : 'Not available'}</p>
            </div>
            <div className="rounded-lg bg-gray-50 p-4">
              <p className="text-xs text-gray-500">Trend</p>
              <p className="mt-1 text-lg font-semibold capitalize">{marketData.market_trend || 'Unknown'}</p>
            </div>
            <div className="rounded-lg bg-gray-50 p-4">
              <p className="text-xs text-gray-500">Volatility</p>
              <p className="mt-1 text-lg font-semibold capitalize">{marketData.price_volatility || 'Unknown'}</p>
            </div>
            <div className="rounded-lg bg-gray-50 p-4">
              <p className="text-xs text-gray-500">Confidence</p>
              <p className="mt-1 text-lg font-semibold">{formatPercent(marketData.confidence ?? null)}</p>
            </div>
          </div>

          <div className="space-y-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Recommendation</p>
              <p className="mt-1 text-sm text-gray-700">{marketData.recommendation || 'No recommendation available.'}</p>
            </div>

            {marketData.uncertainties?.length ? (
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Uncertainties</p>
                <ul className="mt-2 space-y-1 text-sm text-gray-700">
                  {marketData.uncertainties.map((item) => (
                    <li key={item} className="flex gap-2">
                      <span className="mt-1 h-1.5 w-1.5 rounded-full bg-emerald-600" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            <p className="text-xs text-gray-500">
              {marketData.location ? `Location: ${marketData.location}` : 'Location not specified'}
              {marketData.crop_type ? ` · Crop: ${marketData.crop_type}` : ''}
            </p>
          </div>
        </>
      )}
    </Card>
  )
}
