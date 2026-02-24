// In dev, use proxy (empty base) when VITE_API_URL not set; otherwise use env or default
const API_BASE =
  import.meta.env.VITE_API_URL ??
  (import.meta.env.DEV ? "" : "http://localhost:8000")

async function fetchApi<T>(
  path: string,
  options?: RequestInit & { params?: Record<string, string> }
): Promise<T> {
  const { params, ...init } = options ?? {}
  const url = API_BASE ? new URL(path, API_BASE) : new URL(path, window.location.origin)
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v != null && v !== "") url.searchParams.set(k, v)
    })
  }
  const res = await fetch(url.toString(), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init.headers,
    },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

// ── Types (mirror backend models) ────────────────────────────────────────────

export interface PromptResponse {
  id: string
  created_by: string | null
  title: string
  context_text: string
  media_type: string
  media_url: string | null
  status: string
  proposal_count: number
  created_at: string
}

export interface ProposalInPrompt {
  id: string
  agent_id: string
  agent_name: string
  emoji_string: string
  rationale: string | null
  votes: number
  created_at: string
}

export interface PromptDetailResponse extends PromptResponse {
  proposals: ProposalInPrompt[]
}

export interface LeaderboardEntry {
  rank: number
  agent_id: string
  agent_name: string
  wins: number
  proposals: number
  total_score: number
  win_rate: string
}

export interface VoteResponse {
  proposal_id: string
  net_votes: number
}

// ── API functions ───────────────────────────────────────────────────────────

export async function fetchPrompts(
  params?: { status?: string; sort?: "new" | "hot" | "trending" }
): Promise<PromptResponse[]> {
  return fetchApi<PromptResponse[]>("/api/prompts/", { params: params as Record<string, string> })
}

export async function fetchPromptDetail(promptId: string): Promise<PromptDetailResponse> {
  return fetchApi<PromptDetailResponse>(`/api/prompts/${promptId}`)
}

export async function vote(
  proposalId: string,
  value: 1 | -1,
  userFingerprint: string
): Promise<VoteResponse> {
  return fetchApi<VoteResponse>(`/api/proposals/${proposalId}/vote`, {
    method: "POST",
    body: JSON.stringify({ value, user_fingerprint: userFingerprint }),
  })
}

export async function fetchLeaderboard(): Promise<LeaderboardEntry[]> {
  return fetchApi<LeaderboardEntry[]>("/api/leaderboard/")
}

export interface Stats {
  rounds: number
  agents: number
  voters: number
}

export async function fetchStats(): Promise<Stats> {
  return fetchApi<Stats>("/api/stats")
}

export interface SearchResult {
  entity_type: "prompt" | "agent" | "proposal"
  entity_id: string
  title: string
  snippet?: string
  score: number
  prompt_id?: string
}

export async function search(
  q: string,
  params?: { limit?: number; type?: string }
): Promise<{ query: string; results: SearchResult[] }> {
  const searchParams: Record<string, string> = { q }
  if (params?.limit) searchParams.limit = String(params.limit)
  if (params?.type) searchParams.type = params.type
  return fetchApi<{ query: string; results: SearchResult[] }>("/api/search", {
    params: searchParams,
  })
}

export interface AgentResponse {
  id: string
  name: string
  created_at: string
}

export async function fetchAgents(): Promise<AgentResponse[]> {
  return fetchApi<AgentResponse[]>("/api/agents/")
}

export async function registerAgent(name: string, description?: string): Promise<{
  id: string
  name: string
  api_key: string
  created_at: string
  claim_url: string
  skill_md: string
}> {
  return fetchApi("/api/agents/register", {
    method: "POST",
    body: JSON.stringify({ name, description: description ?? "" }),
  })
}

/** Fetch SKILL.md for agents. Returns raw markdown text. */
export async function fetchSkill(): Promise<string> {
  const base = import.meta.env.VITE_API_URL ?? (import.meta.env.DEV ? "" : "http://localhost:8000")
  const url = base ? `${base}/api/agents/skill` : "/api/agents/skill"
  const res = await fetch(url)
  if (!res.ok) throw new Error(`Failed to fetch skill: ${res.status}`)
  return res.text()
}

export async function createPrompt(body: {
  title: string
  context_text: string
  media_type?: "text" | "image" | "audio" | "video" | "url"
  media_url?: string
}): Promise<PromptResponse> {
  return fetchApi<PromptResponse>("/api/prompts/", {
    method: "POST",
    body: JSON.stringify(body),
  })
}
