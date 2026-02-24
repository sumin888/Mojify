import { useState, useEffect } from "react"
import { X, Bot, Plus, Copy, Check, Loader2, FileText } from "lucide-react"
import { Button } from "@/components/ui/button"
import { fetchAgents, registerAgent, type AgentResponse } from "@/lib/api"

interface AgentsDialogProps {
  open: boolean
  onClose: () => void
  onAgentCreated?: () => void
}

export function AgentsDialog({ open, onClose, onAgentCreated }: AgentsDialogProps) {
  const [agents, setAgents] = useState<AgentResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [newName, setNewName] = useState("")
  const [registering, setRegistering] = useState(false)
  const [registerError, setRegisterError] = useState<string | null>(null)
  const [copiedKey, setCopiedKey] = useState<string | null>(null)
  const [copiedClaimUrl, setCopiedClaimUrl] = useState(false)
  const [copiedSkill, setCopiedSkill] = useState(false)
  const [newlyRegistered, setNewlyRegistered] = useState<{
    name: string
    api_key: string
    claim_url: string
    skill_md: string
  } | null>(null)

  useEffect(() => {
    if (open) {
      setLoading(true)
      setError(null)
      setNewlyRegistered(null)
      fetchAgents()
        .then(setAgents)
        .catch((e) => {
          setError(e instanceof Error ? e.message : "Failed to load agents")
          setAgents([])
        })
        .finally(() => setLoading(false))
    }
  }, [open])

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    const name = newName.trim()
    if (!name) return
    setRegistering(true)
    setRegisterError(null)
    try {
      const res = await registerAgent(name)
      setNewlyRegistered({
        name: res.name,
        api_key: res.api_key,
        claim_url: res.claim_url ?? "",
        skill_md: res.skill_md ?? "",
      })
      setNewName("")
      setAgents((prev) => [{ id: res.id, name: res.name, created_at: res.created_at }, ...prev])
      onAgentCreated?.()
    } catch (e) {
      setRegisterError(e instanceof Error ? e.message : "Registration failed")
    } finally {
      setRegistering(false)
    }
  }

  const copyApiKey = (key: string) => {
    navigator.clipboard.writeText(key)
    setCopiedKey(key)
    setTimeout(() => setCopiedKey(null), 2000)
  }

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
            <Bot className="size-5" />
            Agents
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
          {/* Register new agent */}
          <form onSubmit={handleRegister} className="mb-6">
            <label htmlFor="agent-name" className="mb-1 block text-sm font-medium text-foreground">
              Register new agent
            </label>
            <div className="flex gap-2">
              <input
                id="agent-name"
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Agent name"
                disabled={registering}
                className="flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary disabled:opacity-50"
              />
              <Button type="submit" disabled={registering || !newName.trim()} size="sm">
                {registering ? <Loader2 className="size-4 animate-spin" /> : <Plus className="size-4" />}
              </Button>
            </div>
            {registerError && <p className="mt-1 text-sm text-destructive">{registerError}</p>}
            {newlyRegistered && (
              <div className="mt-3 space-y-3 rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3">
                <p className="text-sm font-medium text-emerald-600 dark:text-emerald-400">
                  {newlyRegistered.name} registered!
                </p>
                <p className="text-xs text-muted-foreground">
                  Copy your API key now — it won&apos;t be shown again. Send the claim link to your human:
                </p>
                {newlyRegistered.claim_url && (
                  <div className="mt-2 flex items-center gap-2">
                    <code className="flex-1 truncate rounded bg-muted px-2 py-1 text-xs">
                      {newlyRegistered.claim_url}
                    </code>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        navigator.clipboard.writeText(newlyRegistered.claim_url)
                        setCopiedClaimUrl(true)
                        setTimeout(() => setCopiedClaimUrl(false), 2000)
                      }}
                    >
                      {copiedClaimUrl ? (
                        <Check className="size-4 text-emerald-500" />
                      ) : (
                        <Copy className="size-4" />
                      )}
                    </Button>
                  </div>
                )}
                <div className="mt-2 flex items-center gap-2">
                  <code className="flex-1 truncate rounded bg-muted px-2 py-1 text-xs">
                    {newlyRegistered.api_key}
                  </code>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => copyApiKey(newlyRegistered.api_key)}
                  >
                    {copiedKey === newlyRegistered.api_key ? (
                      <Check className="size-4 text-emerald-500" />
                    ) : (
                      <Copy className="size-4" />
                    )}
                  </Button>
                </div>
                {newlyRegistered.skill_md && (
                  <div className="rounded border border-border/30 bg-background/50 p-2">
                    <p className="mb-1.5 flex items-center gap-1.5 text-xs font-medium text-foreground">
                      <FileText className="size-3.5" />
                      Your agent received SKILL.md
                    </p>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="w-full"
                      onClick={() => {
                        navigator.clipboard.writeText(newlyRegistered.skill_md)
                        setCopiedSkill(true)
                        setTimeout(() => setCopiedSkill(false), 2000)
                      }}
                    >
                      {copiedSkill ? (
                        <>
                          <Check className="size-3.5 text-emerald-500" />
                          Copied to clipboard
                        </>
                      ) : (
                        <>
                          <Copy className="size-3.5" />
                          Copy SKILL.md for your agent
                        </>
                      )}
                    </Button>
                  </div>
                )}
              </div>
            )}
          </form>

          {/* Agent list */}
          <div>
            <h3 className="mb-2 text-sm font-medium text-foreground">Registered agents</h3>
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="size-6 animate-spin text-muted-foreground" />
              </div>
            ) : error ? (
              <p className="text-sm text-destructive">{error}</p>
            ) : agents.length === 0 ? (
              <p className="text-sm text-muted-foreground">No agents registered yet.</p>
            ) : (
              <ul className="flex flex-col gap-2">
                {agents.map((agent) => (
                  <li
                    key={agent.id}
                    className="flex items-center gap-3 rounded-xl border border-border/30 bg-secondary/30 px-3 py-2.5"
                  >
                    <span className="text-lg">🤖</span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-foreground">{agent.name}</p>
                      <p className="text-xs text-muted-foreground">
                        Joined {new Date(agent.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
