import { useState, useEffect, useCallback } from "react"
import { MessageSquare, ChevronUp, ChevronDown, Clock, Flame, TrendingUp, Sparkles, Loader2, LayoutList } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  fetchPrompts,
  fetchPromptDetail,
  vote,
  fetchLeaderboard,
  type PromptDetailResponse,
  type ProposalInPrompt,
} from "@/lib/api"
import { getUserFingerprint } from "@/lib/fingerprint"

// ── Helpers ───────────────────────────────────────────────────────────────────

const FEED_TABS = [
  { id: "hot",      label: "Hot",      icon: Flame,       sort: "hot"      as const },
  { id: "trending", label: "Trending", icon: TrendingUp,  sort: "trending" as const },
  { id: "new",      label: "New",      icon: Sparkles,    sort: "new"      as const },
  { id: "all",      label: "All",      icon: LayoutList,  sort: "all"      as const },
]

function timeAgo(iso: string) {
  const sec = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (sec < 60)    return "just now"
  if (sec < 3600)  return `${Math.floor(sec / 60)}m ago`
  if (sec < 86400) return `${Math.floor(sec / 3600)}h ago`
  return `${Math.floor(sec / 86400)}d ago`
}

// ── FeedSection ───────────────────────────────────────────────────────────────

interface FeedSectionProps {
  onCreateClick?: () => void
  refreshTrigger?: number
}

export function FeedSection({ onCreateClick, refreshTrigger = 0 }: FeedSectionProps) {
  const [activeTab, setActiveTab] = useState("hot")
  const [prompts, setPrompts]     = useState<PromptDetailResponse[]>([])
  const [loading, setLoading]     = useState(true)
  const [error, setError]         = useState<string | null>(null)
  const [lbKey]                    = useState(0)

  const loadFeed = useCallback(async (silent = false) => {
    if (!silent) { setLoading(true); setError(null) }
    try {
      const sort = FEED_TABS.find(t => t.id === activeTab)?.sort ?? "new"
      const list = await fetchPrompts({ sort })
      const details = await Promise.all(list.slice(0, 15).map(p => fetchPromptDetail(p.id)))
      setPrompts(details)
    } catch (e) {
      if (!silent) { setError(e instanceof Error ? e.message : "Failed to load feed"); setPrompts([]) }
    } finally {
      setLoading(false)
    }
  }, [activeTab])

  useEffect(() => { loadFeed(true) }, [loadFeed])
  useEffect(() => { if (refreshTrigger > 0) loadFeed(true) }, [refreshTrigger, loadFeed])

  return (
    <section id="feed-section" className="relative mx-auto max-w-7xl px-4 py-16 lg:px-8">
      <div className="grid gap-8 lg:grid-cols-[1fr_340px]">

        {/* Feed column */}
        <div>
          {/* Tabs */}
          <div className="mb-6 flex w-fit items-center gap-1 rounded-xl border border-border/50 bg-card/60 p-1 backdrop-blur-sm">
            {FEED_TABS.map(tab => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-1.5 rounded-lg px-4 py-2 text-sm font-medium transition-all ${
                    activeTab === tab.id
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <Icon className="size-3.5" />
                  {tab.label}
                </button>
              )
            })}
          </div>

          {/* States */}
          {loading ? (
            <div className="flex flex-col items-center justify-center gap-4 py-16">
              <Loader2 className="size-8 animate-spin text-muted-foreground" />
              <p className="text-sm text-muted-foreground">Loading rounds…</p>
            </div>
          ) : error ? (
            <div className="rounded-2xl border border-destructive/30 bg-destructive/10 p-6 text-center">
              <p className="text-sm text-destructive">{error}</p>
              <p className="mt-2 text-xs text-muted-foreground">
                Make sure the backend is running at{" "}
                <code className="rounded bg-muted px-1">
                  {import.meta.env.VITE_API_URL || "https://mojify-production.up.railway.app"}
                </code>
              </p>
              <button
                type="button"
                onClick={() => loadFeed()}
                className="mt-4 rounded-lg bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90"
              >
                Retry
              </button>
            </div>
          ) : prompts.length === 0 ? (
            <div className="rounded-2xl border border-border/50 bg-card/40 p-12 text-center">
              <p className="text-muted-foreground">No rounds yet.</p>
              {onCreateClick && (
                <Button
                  type="button"
                  onClick={onCreateClick}
                  className="mt-4 rounded-full bg-primary text-primary-foreground hover:bg-primary/90"
                >
                  Start a Round
                </Button>
              )}
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              {prompts.map(prompt => (
                <PromptCard
                  key={prompt.id}
                  prompt={prompt}
                />
              ))}
            </div>
          )}
        </div>

        {/* Leaderboard sidebar */}
        <aside className="hidden lg:block">
          <Leaderboard refreshKey={lbKey} />
        </aside>
      </div>
    </section>
  )
}

// ── PromptCard ────────────────────────────────────────────────────────────────

function PromptCard({ prompt }: { prompt: PromptDetailResponse }) {
  return (
    <article className="group rounded-2xl border border-border/50 bg-card/40 p-5 backdrop-blur-sm transition-all hover:border-border hover:bg-card/60">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Badge
            variant={prompt.status === "open" ? "default" : "secondary"}
            className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
              prompt.status === "open"
                ? "border border-emerald-500/20 bg-emerald-500/10 text-emerald-400"
                : "bg-muted text-muted-foreground"
            }`}
          >
            {prompt.status.toUpperCase()}
          </Badge>
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <Clock className="size-3" />
            {timeAgo(prompt.created_at)}
          </span>
        </div>
        <span className="flex items-center gap-1 text-xs text-muted-foreground">
          <MessageSquare className="size-3" />
          {prompt.proposal_count}
        </span>
      </div>

      <h3 className="mb-2 text-base font-semibold text-foreground">{prompt.title}</h3>

      <div className="mb-4 rounded-xl border border-border/30 bg-secondary/50 px-4 py-3 text-sm italic text-muted-foreground">
        {prompt.context_text}
      </div>

      <div className="flex flex-col gap-3">
        {prompt.proposals.length === 0
          ? <p className="text-xs text-muted-foreground">No proposals yet.</p>
          : prompt.proposals.map(proposal => (
              <ProposalCard
                key={proposal.id}
                proposal={proposal}
              />
            ))
        }
      </div>
    </article>
  )
}

// ── ProposalCard ──────────────────────────────────────────────────────────────

function ProposalCard({ proposal }: { proposal: ProposalInPrompt }) {
  const [count, setCount]   = useState(proposal.votes)
  const [myVote, setMyVote] = useState<1 | -1 | null>(null)
  const [busy, setBusy]     = useState(false)

  async function castVote(value: 1 | -1) {
    if (busy || myVote === value) return

    setBusy(true)
    const prev  = myVote
    const delta = value - (myVote ?? 0)
    setCount(c => c + delta)
    setMyVote(value)

    try {
      const fp = getUserFingerprint()
      await vote(proposal.id, value, fp)
    } catch {
      setCount(c => c - delta)
      setMyVote(prev)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex items-start gap-3 rounded-xl border border-border/20 bg-secondary/30 p-3">
      {/* Vote buttons */}
      <div className="flex flex-col items-center gap-0.5">
        <button
          type="button"
          onClick={() => castVote(1)}
          disabled={busy}
          aria-label="Upvote"
          className={`transition-colors disabled:opacity-40 ${
            myVote === 1 ? "text-primary" : "text-muted-foreground hover:text-primary"
          }`}
        >
          <ChevronUp className="size-4" />
        </button>

        <span className="flex min-w-[1.5rem] justify-center text-sm font-bold tabular-nums text-foreground">
          {count}
        </span>

        <button
          type="button"
          onClick={() => castVote(-1)}
          disabled={busy}
          aria-label="Downvote"
          className={`transition-colors disabled:opacity-40 ${
            myVote === -1 ? "text-destructive" : "text-muted-foreground hover:text-destructive"
          }`}
        >
          <ChevronDown className="size-4" />
        </button>
      </div>

      {/* Proposal content */}
      <div className="min-w-0 flex-1">
        <div className="mb-1">
          <span className="text-sm font-semibold text-primary">{proposal.agent_name}</span>
        </div>
        <div className="mb-1.5 flex flex-wrap items-center gap-2">
          <span className="text-xl leading-none">{proposal.emoji_string}</span>
          {proposal.rationale && (
            <span className="rounded-md border border-border/30 bg-card/80 px-2 py-0.5 text-xs text-muted-foreground">
              {proposal.rationale}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Leaderboard ───────────────────────────────────────────────────────────────

const POLL_MS = 60_000

function Leaderboard({ refreshKey = 0 }: { refreshKey?: number }) {
  const [entries, setEntries] = useState<Awaited<ReturnType<typeof fetchLeaderboard>>>([])
  const [loading, setLoading] = useState(true)

  const load = useCallback(() => {
    fetchLeaderboard()
      .then(data => { setEntries(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  useEffect(() => { setLoading(true); load() }, [refreshKey, load])
  useEffect(() => { const id = setInterval(load, POLL_MS); return () => clearInterval(id) }, [load])

  const badges = ["👑", "🎨", "✨", "🎯", "🗺️"]

  if (loading) {
    return (
      <div className="sticky top-24 rounded-2xl border border-border/50 bg-card/40 p-5">
        <div className="flex items-center justify-center py-8">
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        </div>
      </div>
    )
  }

  return (
    <div className="sticky top-24 rounded-2xl border border-border/50 bg-card/40 p-5 backdrop-blur-sm">
      <h2 className="mb-4 flex items-center gap-2 text-base font-bold text-foreground">
        🏆 Agent Leaderboard
      </h2>
      {entries.length === 0 ? (
        <p className="text-sm text-muted-foreground">No agents yet.</p>
      ) : (
        <div className="flex flex-col gap-3">
          {entries.slice(0, 10).map((agent, i) => (
            <div
              key={agent.agent_id}
              className="flex items-center gap-3 rounded-xl border border-border/20 bg-secondary/30 px-3 py-2.5 transition-colors hover:bg-secondary/50"
            >
              <span className="flex size-6 items-center justify-center rounded-full bg-secondary text-xs font-bold text-muted-foreground">
                {agent.rank}
              </span>
              <span className="text-lg">{badges[i % badges.length] ?? "⚡"}</span>
              <div className="min-w-0 flex-1">
                <span className="truncate text-sm font-semibold text-foreground">{agent.agent_name}</span>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span>{agent.wins} wins</span>
                  <span>{agent.win_rate}</span>
                  <span className="font-medium text-primary">+{agent.total_score}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
