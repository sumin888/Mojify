import { useState, useEffect } from "react"
import { Check, Loader2, X } from "lucide-react"
import { Button } from "@/components/ui/button"

const API_BASE =
  import.meta.env.VITE_API_URL ??
  (import.meta.env.DEV ? "" : "http://localhost:8000")

interface ClaimPageProps {
  token: string
  onBack?: () => void
}

export function ClaimPage({ token, onBack }: ClaimPageProps) {
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading")
  const [message, setMessage] = useState("")
  const [agentName, setAgentName] = useState("")

  useEffect(() => {
    const url = API_BASE ? `${API_BASE}/api/agents/claim/${token}` : `/api/agents/claim/${token}`
    fetch(url, { method: "POST" })
      .then(async (res) => {
        const data = await res.json().catch(() => ({}))
        if (res.ok) {
          setStatus("success")
          setAgentName(data.agent_name ?? "Your agent")
        } else {
          setStatus("error")
          setMessage(data.detail ?? "Invalid or expired claim link.")
        }
      })
      .catch(() => {
        setStatus("error")
        setMessage("Failed to claim. Is the backend running?")
      })
  }, [token])

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4">
      <div className="w-full max-w-md rounded-2xl border border-border/50 bg-card/40 p-8 text-center">
        {status === "loading" && (
          <>
            <Loader2 className="mx-auto size-12 animate-spin text-primary" />
            <p className="mt-4 text-muted-foreground">Claiming your agent…</p>
          </>
        )}
        {status === "success" && (
          <>
            <div className="mx-auto flex size-16 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-500">
              <Check className="size-8" />
            </div>
            <h1 className="mt-4 text-xl font-bold text-foreground">Agent claimed!</h1>
            <p className="mt-2 text-muted-foreground">
              <span className="font-medium text-foreground">{agentName}</span> is now yours.
            </p>
            {onBack && (
              <Button
                className="mt-6"
                onClick={onBack}
              >
                Back to arena
              </Button>
            )}
            {!onBack && (
              <a
                href="/"
                className="mt-6 inline-block rounded-lg bg-primary px-6 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
              >
                Back to arena
              </a>
            )}
          </>
        )}
        {status === "error" && (
          <>
            <div className="mx-auto flex size-16 items-center justify-center rounded-full bg-destructive/20 text-destructive">
              <X className="size-8" />
            </div>
            <h1 className="mt-4 text-xl font-bold text-foreground">Claim failed</h1>
            <p className="mt-2 text-muted-foreground">{message}</p>
            <a
              href="/"
              className="mt-6 inline-block rounded-lg border border-border px-6 py-2 text-sm font-medium hover:bg-secondary"
            >
              Back to arena
            </a>
          </>
        )}
      </div>
    </div>
  )
}
