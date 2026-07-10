import { Card } from '@/components/ui/card'
import type { TreatmentSource } from '@/types'

interface RagEvidencePanelProps {
  sources?: TreatmentSource[]
}

function stripMarkdown(text: string): string {
  return text
    .replace(/#{1,6}\s+/g, '') // Remove headers anywhere in text
    .replace(/\*\*([^*]+)\*\*/g, '$1') // Remove bold
    .replace(/\*([^*]+)\*/g, '$1') // Remove italic
    .replace(/`([^`]+)`/g, '$1') // Remove inline code
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // Remove links
    .replace(/^[-*+]\s+/gm, '') // Remove list bullets at start of line
    .replace(/^\d+\.\s+/gm, '') // Remove numbered lists at start of line
    .replace(/^>\s+/gm, '') // Remove blockquotes at start of line
    .replace(/\n{3,}/g, '\n\n') // Normalize multiple newlines
    .trim()
}

export function RagEvidencePanel({ sources = [] }: RagEvidencePanelProps) {
  return (
    <Card className="p-6 space-y-4">
      <div>
        <h3 className="text-lg font-semibold">RAG Evidence</h3>
        <p className="text-sm text-gray-600 mt-1">Retrieved local knowledge base passages used to ground treatment guidance</p>
      </div>

      {sources.length === 0 ? (
        <p className="text-sm text-gray-600">No RAG evidence returned for this diagnosis.</p>
      ) : (
        <div className="space-y-3">
          {sources.map((source, idx) => {
            const text = source.text || ''
            const cleanText = stripMarkdown(text)
            const excerpt = cleanText.length > 280 ? `${cleanText.slice(0, 280).trim()}...` : cleanText

            return (
              <div key={`${source.embedding_id ?? idx}-${source.title ?? source.document_title ?? 'source'}`} className="rounded-lg border border-gray-200 p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-gray-900">
                      {source.title || source.document_title || 'Retrieved document'}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {source.document_source ? source.document_source.split('/').pop() : 'Knowledge base'}
                    </p>
                  </div>
                  <div className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
                    Score {typeof source.score === 'number' ? source.score.toFixed(3) : 'N/A'}
                  </div>
                </div>

                <div className="mt-3 flex flex-wrap gap-2 text-xs text-gray-700">
                  <span className="rounded-full bg-gray-100 px-2 py-1">Semantic {typeof source.semantic_score === 'number' ? source.semantic_score.toFixed(3) : 'N/A'}</span>
                  <span className="rounded-full bg-gray-100 px-2 py-1">Lexical {typeof source.lexical_score === 'number' ? source.lexical_score.toFixed(3) : 'N/A'}</span>
                  <span className="rounded-full bg-gray-100 px-2 py-1">Distance {typeof source.distance === 'number' ? source.distance.toFixed(4) : 'N/A'}</span>
                </div>

                {excerpt ? <p className="mt-3 text-sm text-gray-600 whitespace-pre-line">{excerpt}</p> : null}
              </div>
            )
          })}
        </div>
      )}
    </Card>
  )
}
