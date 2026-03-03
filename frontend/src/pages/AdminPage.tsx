import { useState, useEffect, useCallback } from "react"
import { Loader2, LogOut, Lock, CheckCircle2, XCircle, RefreshCw, Eye, EyeOff, Radio } from "lucide-react"
import { LIVE_ROUND_TITLES } from "@/lib/live-round-pool"

// ── API helpers ───────────────────────────────────────────────────────────────

function getApiBase(): string {
  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL
  if (import.meta.env.DEV) return ""
  if (
    typeof window !== "undefined" &&
    (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
  )
    return ""
  return "https://mojify-production.up.railway.app"
}

async function adminFetch<T>(
  path: string,
  token: string,
  options?: RequestInit,
): Promise<T> {
  const base = getApiBase()
  const url = base ? `${base}${path}` : path
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "x-admin-token": token,
      ...options?.headers,
    },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

async function adminLogin(username: string, password: string): Promise<string> {
  const base = getApiBase()
  const url = base ? `${base}/api/admin/login` : "/api/admin/login"
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Login failed" }))
    throw new Error(err.detail ?? "Login failed")
  }
  const data = await res.json()
  return data.token as string
}

// ── Types ─────────────────────────────────────────────────────────────────────

interface AdminPrompt {
  id: string
  title: string
  context_text: string
  status: string
  created_at: string
  proposal_count: number
}

// ── Storage key ───────────────────────────────────────────────────────────────

const TOKEN_KEY = "mojify_admin_token"

// ── AdminPage ─────────────────────────────────────────────────────────────────

export function AdminPage({ onBack }: { onBack?: () => void }) {
  const [token, setToken] = useState<string | null>(() => sessionStorage.getItem(TOKEN_KEY))
  const [view, setView] = useState<"login" | "dashboard">(
    sessionStorage.getItem(TOKEN_KEY) ? "dashboard" : "login",
  )

  function handleLogout() {
    if (token) {
      const base = getApiBase()
      fetch(`${base || ""}/api/admin/logout`, {
        method: "POST",
        headers: { "x-admin-token": token },
      }).catch(() => {})
    }
    sessionStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setView("login")
  }

  function handleLoginSuccess(t: string) {
    sessionStorage.setItem(TOKEN_KEY, t)
    setToken(t)
    setView("dashboard")
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Top bar */}
      <header className="flex items-center justify-between border-b border-border/50 bg-card/60 px-6 py-3 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          {onBack && (
            <button
              type="button"
              onClick={onBack}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              ← Back
            </button>
          )}
          <span className="font-mono text-sm font-bold text-primary">mojify</span>
          <span className="text-xs text-muted-foreground">/ admin</span>
        </div>
        {view === "dashboard" && (
          <button
            type="button"
            onClick={handleLogout}
            className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs text-muted-foreground hover:bg-secondary hover:text-foreground"
          >
            <LogOut className="size-3.5" />
            Logout
          </button>
        )}
      </header>

      <main className="mx-auto max-w-5xl px-4 py-10 lg:px-8">
        {view === "login" ? (
          <LoginForm onSuccess={handleLoginSuccess} />
        ) : token ? (
          <Dashboard token={token} onAuthError={handleLogout} />
        ) : null}
      </main>
    </div>
  )
}

// ── LoginForm ─────────────────────────────────────────────────────────────────

function LoginForm({ onSuccess }: { onSuccess: (token: string) => void }) {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const token = await adminLogin(username, password)
      onSuccess(token)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="w-full max-w-sm rounded-2xl border border-border/50 bg-card/40 p-8 backdrop-blur-sm">
        <div className="mb-6 flex flex-col items-center gap-2">
          <div className="flex size-12 items-center justify-center rounded-full bg-primary/10 text-primary">
            <Lock className="size-5" />
          </div>
          <h1 className="text-lg font-bold text-foreground">Admin Login</h1>
          <p className="text-xs text-muted-foreground">Mojify control panel</p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-muted-foreground" htmlFor="username">
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
              className="rounded-xl border border-border/50 bg-background px-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/30"
              placeholder="Username"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-muted-foreground" htmlFor="password">
              Password
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
                className="w-full rounded-xl border border-border/50 bg-background px-4 py-2.5 pr-10 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/30"
                placeholder="Password"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="absolute inset-y-0 right-3 flex items-center text-muted-foreground hover:text-foreground"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
              </button>
            </div>
          </div>

          {error && (
            <p className="rounded-lg border border-destructive/20 bg-destructive/10 px-3 py-2 text-xs text-destructive">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="mt-1 flex items-center justify-center gap-2 rounded-xl bg-primary py-2.5 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-60"
          >
            {loading && <Loader2 className="size-4 animate-spin" />}
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  )
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

function Dashboard({ token, onAuthError }: { token: string; onAuthError: () => void }) {
  const [prompts, setPrompts] = useState<AdminPrompt[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busyIds, setBusyIds] = useState<Set<string>>(new Set())
  const [filter, setFilter] = useState<"all" | "open" | "closed">("all")

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await adminFetch<AdminPrompt[]>("/api/admin/prompts", token)
      setPrompts(data)
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to load"
      if (msg.toLowerCase().includes("invalid") || msg.toLowerCase().includes("expired")) {
        onAuthError()
      } else {
        setError(msg)
      }
    } finally {
      setLoading(false)
    }
  }, [token, onAuthError])

  useEffect(() => { load() }, [load])

  async function setStatus(id: string, status: "open" | "closed") {
    setBusyIds((s) => new Set(s).add(id))
    const action = status === "closed" ? "close" : "open"
    try {
      await adminFetch<AdminPrompt>(
        `/api/admin/prompts/${id}/${action}`,
        token,
        { method: "PATCH" },
      )
      // Reload from server to ensure UI always reflects actual DB state
      await load()
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Action failed"
      if (msg.toLowerCase().includes("invalid") || msg.toLowerCase().includes("expired")) {
        onAuthError()
      } else {
        setError(msg)
      }
    } finally {
      setBusyIds((s) => { const n = new Set(s); n.delete(id); return n })
    }
  }

  const visible = prompts.filter((p) =>
    filter === "all" ? true : p.status === filter,
  )

  const openCount = prompts.filter((p) => p.status === "open").length
  const closedCount = prompts.filter((p) => p.status === "closed").length

  // The current live round is the most recently created open prompt whose title
  // is in the live round pool. Closing it would break the live feature.
  const liveRoundId = prompts.find(
    (p) => p.status === "open" && LIVE_ROUND_TITLES.has(p.title),
  )?.id

  return (
    <div>
      {/* Header */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Rounds</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            {openCount} open · {closedCount} closed · {prompts.length} total
          </p>
        </div>
        <button
          type="button"
          onClick={load}
          disabled={loading}
          className="flex items-center gap-1.5 rounded-xl border border-border/50 bg-secondary/50 px-4 py-2 text-sm text-muted-foreground hover:bg-secondary hover:text-foreground disabled:opacity-50"
        >
          <RefreshCw className={`size-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Filter tabs */}
      <div className="mb-4 flex w-fit items-center gap-1 rounded-xl border border-border/50 bg-card/60 p-1">
        {(["all", "open", "closed"] as const).map((f) => (
          <button
            key={f}
            type="button"
            onClick={() => setFilter(f)}
            className={`rounded-lg px-4 py-1.5 text-sm font-medium capitalize transition-all ${
              filter === f
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 rounded-xl border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Table */}
      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="size-8 animate-spin text-muted-foreground" />
        </div>
      ) : visible.length === 0 ? (
        <div className="rounded-2xl border border-border/50 bg-card/40 py-16 text-center text-sm text-muted-foreground">
          No rounds found.
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          {visible.map((prompt) => (
            <PromptRow
              key={prompt.id}
              prompt={prompt}
              busy={busyIds.has(prompt.id)}
              isLive={prompt.id === liveRoundId}
              onOpen={() => setStatus(prompt.id, "open")}
              onClose={() => setStatus(prompt.id, "closed")}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// ── PromptRow ─────────────────────────────────────────────────────────────────

function PromptRow({
  prompt,
  busy,
  isLive,
  onOpen,
  onClose,
}: {
  prompt: AdminPrompt
  busy: boolean
  isLive: boolean
  onOpen: () => void
  onClose: () => void
}) {
  const isOpen = prompt.status === "open"

  function timeAgo(iso: string) {
    const sec = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
    if (sec < 60) return "just now"
    if (sec < 3600) return `${Math.floor(sec / 60)}m ago`
    if (sec < 86400) return `${Math.floor(sec / 3600)}h ago`
    return `${Math.floor(sec / 86400)}d ago`
  }

  return (
    <div
      className={`flex items-center gap-4 rounded-2xl border bg-card/40 px-5 py-4 backdrop-blur-sm ${
        isLive ? "border-red-500/30" : "border-border/50"
      }`}
    >
      {/* Status icon */}
      <div className="shrink-0">
        {isLive ? (
          <span className="relative flex size-5 items-center justify-center">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-75" />
            <Radio className="relative size-4 text-red-400" />
          </span>
        ) : isOpen ? (
          <CheckCircle2 className="size-5 text-emerald-400" />
        ) : (
          <XCircle className="size-5 text-muted-foreground/50" />
        )}
      </div>

      {/* Info */}
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="truncate text-sm font-semibold text-foreground">{prompt.title}</span>
          {isLive && (
            <span className="shrink-0 rounded-full border border-red-500/20 bg-red-500/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-red-400">
              live
            </span>
          )}
          <span
            className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
              isOpen
                ? "border border-emerald-500/20 bg-emerald-500/10 text-emerald-400"
                : "bg-muted text-muted-foreground"
            }`}
          >
            {prompt.status}
          </span>
        </div>
        <p className="mt-0.5 line-clamp-1 text-xs text-muted-foreground">{prompt.context_text}</p>
        <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
          <span>{prompt.proposal_count} proposal{prompt.proposal_count !== 1 ? "s" : ""}</span>
          <span>·</span>
          <span>{timeAgo(prompt.created_at)}</span>
        </div>
      </div>

      {/* Action */}
      {isLive ? (
        <div
          className="shrink-0 flex items-center gap-1.5 rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-2 text-xs font-semibold text-red-400/60 cursor-not-allowed"
          title="Cannot close the current live round"
        >
          <Radio className="size-3.5" />
          Live
        </div>
      ) : (
        <button
          type="button"
          onClick={isOpen ? onClose : onOpen}
          disabled={busy}
          className={`shrink-0 flex items-center gap-1.5 rounded-xl px-4 py-2 text-xs font-semibold transition-all disabled:opacity-50 ${
            isOpen
              ? "border border-destructive/30 bg-destructive/10 text-destructive hover:bg-destructive/20"
              : "border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20"
          }`}
        >
          {busy ? (
            <Loader2 className="size-3.5 animate-spin" />
          ) : isOpen ? (
            <XCircle className="size-3.5" />
          ) : (
            <CheckCircle2 className="size-3.5" />
          )}
          {isOpen ? "Close" : "Open"}
        </button>
      )}
    </div>
  )
}
