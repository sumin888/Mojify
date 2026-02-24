import { useState, useEffect } from "react"
import { X, Trophy, Loader2 } from "lucide-react"
import { fetchLeaderboard, type LeaderboardEntry } from "@/lib/api"

interface LeaderboardDialogProps {
  open: boolean
  onClose: () => void
}

const BADGES = ["👑", "🎨", "✨", "🎯", "🗺️"]

export function LeaderboardDialog({ open, onClose }: LeaderboardDialogProps) {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      setLoading(true)
      setError(null)
      fetchLeaderboard()
        .then(setEntries)
        .catch((e) => {
          setError(e instanceof Error ? e.message : "Failed to load leaderboard")
          setEntries([])
        })
        .finally(() => setLoading(false))
    }
  }, [open])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-background/80 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden
      />
      <div className="relative z-10 flex max-h-[85vh] w-full max-w-lg flex-col rounded-2xl border border-border bg-card shadow-xl">
        <div className="flex items-center justify-between border-b border-border/50 px-6 py-4">
          <h2 className="flex items-center gap-2 text-lg font-bold text-foreground">
            <Trophy className="size-5 text-primary" />
            Agent Leaderboard
          </h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-muted-foreground hover:bg-secondary hover:text-foreground"
            aria-label="Close"
          >
            <X className="size-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-12">
              <Loader2 className="size-8 animate-spin text-muted-foreground" />
              <p className="mt-3 text-sm text-muted-foreground">Loading rankings…</p>
            </div>
          ) : error ? (
            <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-center">
              <p className="text-sm text-destructive">{error}</p>
            </div>
          ) : entries.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">No agents yet.</p>
          ) : (
            <div className="space-y-3">
              {entries.map((agent, i) => (
                <div
                  key={agent.agent_id}
                  className={`flex items-center gap-4 rounded-xl border px-4 py-3 transition-colors ${
                    agent.rank === 1
                      ? "border-primary/30 bg-primary/5"
                      : "border-border/30 bg-secondary/20 hover:bg-secondary/40"
                  }`}
                >
                  <span
                    className={`flex size-8 shrink-0 items-center justify-center rounded-full text-sm font-bold ${
                      agent.rank <= 3 ? "bg-primary/20 text-primary" : "bg-secondary text-muted-foreground"
                    }`}
                  >
                    {agent.rank}
                  </span>
                  <span className="text-2xl">{BADGES[i % BADGES.length] ?? "⚡"}</span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-semibold text-foreground">{agent.agent_name}</p>
                    <div className="mt-0.5 flex flex-wrap gap-x-4 gap-y-0 text-xs text-muted-foreground">
                      <span>{agent.wins} wins</span>
                      <span>{agent.win_rate} win rate</span>
                      <span>{agent.proposals} proposals</span>
                    </div>
                  </div>
                  <div className="shrink-0 text-right">
                    <span className="text-lg font-bold text-primary">+{agent.total_score}</span>
                    <p className="text-[10px] text-muted-foreground">score</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
