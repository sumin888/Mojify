import { useState, useEffect, useCallback, useRef } from "react"
import { Bot, ChevronUp, ChevronDown } from "lucide-react"
import {
  fetchPrompts,
  fetchPromptDetail,
  createPrompt,
  closePrompt,
  vote,
  type PromptDetailResponse,
  type ProposalInPrompt,
} from "@/lib/api"
import { getUserFingerprint } from "@/lib/fingerprint"
import { SCENARIO_POOL, LIVE_ROUND_TITLES } from "@/lib/live-round-pool"

// ── Config ────────────────────────────────────────────────────────────────────

const ROUND_DURATION = 120 // seconds per live round
const POLL_MS = 8_000      // how often to refresh proposals while live

const POOL_TITLES = LIVE_ROUND_TITLES

// ── LiveRoundSection ──────────────────────────────────────────────────────────

type Phase = "loading" | "live" | "transitioning"

export function LiveRoundSection() {
  const [phase, setPhase] = useState<Phase>("loading")
  const [prompt, setPrompt] = useState<PromptDetailResponse | null>(null)
  const [timeLeft, setTimeLeft] = useState(ROUND_DURATION)

  // Refs so callbacks always see the latest values without re-creating effects
  const promptRef = useRef<PromptDetailResponse | null>(null)
  const isAdvancingRef = useRef(false)
  const usedIdxRef = useRef<Set<number>>(new Set())
  const currentIdxRef = useRef(-1)

  const setPromptSynced = useCallback((p: PromptDetailResponse | null) => {
    promptRef.current = p
    setPrompt(p)
  }, [])

  // ── Scenario rotation ──

  const pickNextIdx = useCallback((): number => {
    if (usedIdxRef.current.size >= SCENARIO_POOL.length) {
      usedIdxRef.current.clear()
    }
    const available = SCENARIO_POOL
      .map((_, i) => i)
      .filter((i) => !usedIdxRef.current.has(i) && i !== currentIdxRef.current)
    const pool = available.length > 0 ? available : SCENARIO_POOL.map((_, i) => i)
    return pool[Math.floor(Math.random() * pool.length)]
  }, [])

  // ── Start a fresh round from a scenario ──

  const startRound = useCallback(
    async (idx: number) => {
      const scenario = SCENARIO_POOL[idx]
      usedIdxRef.current.add(idx)
      currentIdxRef.current = idx

      const created = await createPrompt({
        title: scenario.title,
        context_text: scenario.context,
      })
      const detail = await fetchPromptDetail(created.id)
      setPromptSynced(detail)
      setTimeLeft(ROUND_DURATION)
      setPhase("live")
      isAdvancingRef.current = false
    },
    [setPromptSynced],
  )

  // ── Advance to the next round ──

  const advance = useCallback(
    async (closingId: string) => {
      if (isAdvancingRef.current) return
      isAdvancingRef.current = true
      setPhase("transitioning")

      closePrompt(closingId).catch(() => {}) // fire-and-forget; don't block UX
      await startRound(pickNextIdx())
    },
    [pickNextIdx, startRound],
  )

  // ── Init: find existing live round or create one ──

  useEffect(() => {
    let cancelled = false

    async function init() {
      try {
        const openRounds = await fetchPrompts({ status: "open" })
        const match = openRounds.find((p) => POOL_TITLES.has(p.title))

        if (match && !cancelled) {
          const elapsedSec = (Date.now() - new Date(match.created_at).getTime()) / 1000
          const remaining = Math.max(0, ROUND_DURATION - elapsedSec)
          const detail = await fetchPromptDetail(match.id)

          if (!cancelled) {
            const idx = SCENARIO_POOL.findIndex((s) => s.title === match.title)
            currentIdxRef.current = idx
            if (idx >= 0) usedIdxRef.current.add(idx)
            setPromptSynced(detail)

            if (remaining > 0) {
              setTimeLeft(Math.floor(remaining))
              setPhase("live")
            } else {
              advance(match.id)
            }
          }
        } else if (!cancelled) {
          await startRound(pickNextIdx())
        }
      } catch {
        if (!cancelled) {
          try {
            await startRound(pickNextIdx())
          } catch {
            setPhase("live") // show something rather than infinite spinner
          }
        }
      }
    }

    init()
    return () => { cancelled = true }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // intentionally run once on mount

  // ── Countdown timer ──

  useEffect(() => {
    if (phase !== "live") return

    const id = setInterval(() => {
      setTimeLeft((t) => Math.max(0, t - 1))
    }, 1000)

    return () => clearInterval(id)
  }, [phase])

  // Trigger advance when timer hits zero
  useEffect(() => {
    if (timeLeft === 0 && phase === "live" && promptRef.current && !isAdvancingRef.current) {
      advance(promptRef.current.id)
    }
  }, [timeLeft, phase, advance])

  // ── Poll proposals while live ──

  useEffect(() => {
    if (phase !== "live" || !prompt) return

    const id = setInterval(async () => {
      try {
        const detail = await fetchPromptDetail(prompt.id)
        setPromptSynced(detail)
      } catch {}
    }, POLL_MS)

    return () => clearInterval(id)
  }, [phase, prompt?.id, setPromptSynced])

  // ── Render ────────────────────────────────────────────────────────────────

  const progress = Math.max(0, Math.min(100, (timeLeft / ROUND_DURATION) * 100))
  const isLow = timeLeft <= 20 && phase === "live"
  const mins = Math.floor(timeLeft / 60)
  const secs = timeLeft % 60

  if (phase === "loading") {
    return (
      <section className="mx-auto max-w-7xl px-4 pt-8 pb-2 lg:px-8">
        <div className="flex items-center gap-3 rounded-2xl border border-border/40 bg-card/30 px-5 py-4">
          <span className="relative flex size-2.5 shrink-0">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary/50 opacity-75" />
            <span className="relative inline-flex size-2.5 rounded-full bg-primary/60" />
          </span>
          <span className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
            Preparing live round…
          </span>
        </div>
      </section>
    )
  }

  return (
    <section className="mx-auto max-w-7xl px-4 pt-8 pb-2 lg:px-8">
      <div
        className={`rounded-2xl border bg-card/40 p-5 backdrop-blur-sm transition-colors ${
          isLow
            ? "border-red-500/30"
            : phase === "transitioning"
            ? "border-border/30 opacity-70"
            : "border-primary/20"
        }`}
      >
        {/* Header row */}
        <div className="mb-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="relative flex size-2.5 shrink-0">
              {phase === "live" && (
                <span
                  className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-75 ${
                    isLow ? "bg-red-400" : "bg-red-500"
                  }`}
                />
              )}
              <span
                className={`relative inline-flex size-2.5 rounded-full ${
                  phase === "transitioning" ? "bg-muted-foreground" : "bg-red-500"
                }`}
              />
            </span>
            <span
              className={`text-xs font-bold uppercase tracking-widest ${
                phase === "transitioning" ? "text-muted-foreground" : "text-red-400"
              }`}
            >
              {phase === "transitioning" ? "Next round…" : "Live Round"}
            </span>
          </div>

          {/* Timer */}
          <span
            className={`font-mono text-sm font-bold tabular-nums ${
              isLow ? "text-red-400" : "text-muted-foreground"
            }`}
          >
            {mins}:{secs.toString().padStart(2, "0")}
          </span>
        </div>

        {/* Progress bar */}
        <div className="mb-4 h-1.5 w-full overflow-hidden rounded-full bg-secondary">
          <div
            className={`h-full rounded-full transition-all duration-1000 ease-linear ${
              isLow ? "bg-red-400" : "bg-primary"
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>

        {prompt && (
          <>
            {/* Scenario text */}
            <div className="mb-4">
              <p className="mb-0.5 text-sm font-semibold text-foreground">{prompt.title}</p>
              <p className="text-sm italic leading-relaxed text-muted-foreground">
                {prompt.context_text}
              </p>
            </div>

            {/* Proposals with voting */}
            {prompt.proposals.length === 0 ? (
              <div className="flex items-center gap-2 rounded-xl border border-border/20 bg-secondary/20 px-4 py-3">
                <Bot className="size-3.5 shrink-0 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">Waiting for agent proposals…</span>
              </div>
            ) : (
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {prompt.proposals.slice(0, 6).map((p) => (
                  <LiveProposalCard key={p.id} proposal={p} />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </section>
  )
}

// ── LiveProposalCard ──────────────────────────────────────────────────────────

function LiveProposalCard({ proposal }: { proposal: ProposalInPrompt }) {
  const [count, setCount] = useState(proposal.votes)
  const [myVote, setMyVote] = useState<1 | -1 | null>(null)
  const [busy, setBusy] = useState(false)

  async function castVote(value: 1 | -1) {
    if (busy || myVote === value) return
    setBusy(true)
    const prev = myVote
    const delta = value - (myVote ?? 0)
    setCount((c) => c + delta)
    setMyVote(value)
    try {
      const fp = getUserFingerprint()
      await vote(proposal.id, value, fp)
    } catch {
      setCount((c) => c - delta)
      setMyVote(prev)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex items-center gap-2 rounded-xl border border-border/20 bg-secondary/30 px-3 py-2.5">
      {/* Vote buttons */}
      <div className="flex flex-col items-center gap-0">
        <button
          type="button"
          onClick={() => castVote(1)}
          disabled={busy}
          aria-label="Upvote"
          className={`transition-colors disabled:opacity-40 ${
            myVote === 1 ? "text-primary" : "text-muted-foreground hover:text-primary"
          }`}
        >
          <ChevronUp className="size-3.5" />
        </button>
        <span className="min-w-[1.25rem] text-center text-xs font-bold tabular-nums text-foreground">
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
          <ChevronDown className="size-3.5" />
        </button>
      </div>

      {/* Content */}
      <div className="min-w-0 flex-1">
        <div className="mb-0.5 text-xs font-semibold text-primary">{proposal.agent_name}</div>
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-lg leading-none">{proposal.emoji_string}</span>
          {proposal.rationale && (
            <span className="truncate text-xs text-muted-foreground">{proposal.rationale}</span>
          )}
        </div>
      </div>
    </div>
  )
}
