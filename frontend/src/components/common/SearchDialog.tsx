import { useState, useEffect, useCallback, useRef } from "react"
import { X, Search, Loader2, Zap, Bot, MessageSquare } from "lucide-react"
import { search, type SearchResult } from "@/lib/api"

interface SearchDialogProps {
  open: boolean
  onClose: () => void
  onSelectPrompt?: (promptId: string) => void
  onSelectAgent?: (agentId: string) => void
}

const DEBOUNCE_MS = 300

export function SearchDialog({
  open,
  onClose,
  onSelectPrompt,
  onSelectAgent,
}: SearchDialogProps) {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const doSearch = useCallback(async (q: string) => {
    if (!q.trim()) {
      setResults([])
      return
    }
    setLoading(true)
    setError(null)
    try {
      const res = await search(q, { limit: 15 })
      setResults(res.results)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed")
      setResults([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!open) return
    inputRef.current?.focus()
    setQuery("")
    setResults([])
    setError(null)
  }, [open])

  useEffect(() => {
    if (!open || !query.trim()) {
      setResults([])
      return
    }
    const t = setTimeout(() => doSearch(query), DEBOUNCE_MS)
    return () => clearTimeout(t)
  }, [query, open, doSearch])

  const handleSelect = (r: SearchResult) => {
    if (r.entity_type === "prompt" && onSelectPrompt) {
      onSelectPrompt(r.entity_id)
      onClose()
    } else if (r.entity_type === "agent" && onSelectAgent) {
      onSelectAgent(r.entity_id)
      onClose()
    } else if (r.entity_type === "proposal" && r.prompt_id && onSelectPrompt) {
      onSelectPrompt(r.prompt_id)
      onClose()
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] px-4">
      <div
        className="absolute inset-0 bg-background/80 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden
      />
      <div className="relative z-10 w-full max-w-xl rounded-2xl border border-border bg-card shadow-xl">
        <div className="flex items-center gap-2 border-b border-border/50 px-4 py-3">
          <Search className="size-5 text-muted-foreground" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search rounds, agents, proposals..."
            className="flex-1 bg-transparent text-foreground placeholder:text-muted-foreground focus:outline-none"
            autoComplete="off"
          />
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1 text-muted-foreground hover:bg-secondary hover:text-foreground"
            aria-label="Close"
          >
            <X className="size-5" />
          </button>
        </div>

        <div className="max-h-[60vh] overflow-y-auto p-2">
          {loading && (
            <div className="flex items-center justify-center gap-2 py-8 text-muted-foreground">
              <Loader2 className="size-5 animate-spin" />
              <span className="text-sm">Searching…</span>
            </div>
          )}
          {error && (
            <p className="py-4 text-center text-sm text-destructive">{error}</p>
          )}
          {!loading && !error && query.trim() && results.length === 0 && (
            <p className="py-8 text-center text-sm text-muted-foreground">
              No results for &quot;{query}&quot;
            </p>
          )}
          {!loading && results.length > 0 && (
            <SearchResultsBySection results={results} onSelect={handleSelect} />
          )}
        </div>
      </div>
    </div>
  )
}

const SECTIONS: { type: SearchResult["entity_type"]; label: string; Icon: typeof Zap }[] = [
  { type: "prompt", label: "Rounds", Icon: Zap },
  { type: "agent", label: "Agents", Icon: Bot },
  { type: "proposal", label: "Proposals", Icon: MessageSquare },
]

function SearchResultsBySection({
  results,
  onSelect,
}: {
  results: SearchResult[]
  onSelect: (r: SearchResult) => void
}) {
  const byType = results.reduce(
    (acc, r) => {
      if (!acc[r.entity_type]) acc[r.entity_type] = []
      acc[r.entity_type].push(r)
      return acc
    },
    {} as Record<SearchResult["entity_type"], SearchResult[]>
  )

  return (
    <div className="flex flex-col gap-6">
      {SECTIONS.map(({ type, label, Icon }) => {
        const items = byType[type] ?? []
        if (items.length === 0) return null
        return (
          <section key={type}>
            <div className="mb-2 flex items-center gap-2 px-2">
              <Icon className="size-4 text-muted-foreground" />
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                {label}
              </h3>
            </div>
            <ul className="flex flex-col gap-0.5">
              {items.map((r) => (
                <SearchResultItem
                  key={`${r.entity_type}-${r.entity_id}`}
                  result={r}
                  onSelect={() => onSelect(r)}
                />
              ))}
            </ul>
          </section>
        )
      })}
    </div>
  )
}

function SearchResultItem({
  result,
  onSelect,
}: {
  result: SearchResult
  onSelect: () => void
}) {
  const Icon =
    result.entity_type === "prompt"
      ? Zap
      : result.entity_type === "agent"
        ? Bot
        : MessageSquare

  return (
    <li>
      <button
        type="button"
        onClick={onSelect}
        className="flex w-full items-start gap-3 rounded-xl px-3 py-2.5 text-left transition-colors hover:bg-secondary/80"
      >
        <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-secondary text-muted-foreground">
          <Icon className="size-4" />
        </span>
        <div className="min-w-0 flex-1">
          <span className="text-sm font-medium text-foreground">
            {result.title || "(untitled)"}
          </span>
          {result.snippet && (
            <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">
              {result.snippet}
            </p>
          )}
        </div>
      </button>
    </li>
  )
}
