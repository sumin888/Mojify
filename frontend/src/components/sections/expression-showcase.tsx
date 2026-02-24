import { useState, useEffect } from "react"
import { fetchPromptDetail } from "@/lib/api"

const EMOTICON_SET = [
  { expr: "(^_^)", label: "Joyful" },
  { expr: "(◕‿◕)", label: "Smiling" },
  { expr: "(¬_¬)", label: "Skeptical" },
  { expr: "8-)", label: "Cool" },
  { expr: "\\o/", label: "Victory" },
  { expr: ":3", label: "Cute" },
  { expr: ":P", label: "Playful" },
  { expr: "O.O", label: "Shocked" },
  { expr: "D:", label: "Worried" },
  { expr: "-_-", label: "Unamused" },
  { expr: "T_T", label: "Crying" },
  { expr: "(╥﹏╥)", label: "Sobbing" },
]

const EMOJI_SET = [
  { expr: "🎭", label: "Drama" },
  { expr: "🦋", label: "Butterfly" },
  { expr: "🌌", label: "Galaxy" },
  { expr: "🪩", label: "Disco" },
  { expr: "🧘", label: "Zen" },
  { expr: "🤷", label: "Shrug" },
  { expr: "🙃", label: "Upside Down" },
  { expr: "😇", label: "Angel" },
  { expr: "😏", label: "Smirking" },
  { expr: "🤔", label: "Thinking" },
  { expr: "🍀", label: "Lucky" },
  { expr: "🦄", label: "Unicorn" },
]

const FEATURED_PROMPT_ID = "live-battle-example"

export function ExpressionShowcase() {
  const [battle, setBattle] = useState<Awaited<ReturnType<typeof fetchPromptDetail>> | null>(null)

  useEffect(() => {
    fetchPromptDetail(FEATURED_PROMPT_ID)
      .then(setBattle)
      .catch(() => setBattle(null))
  }, [])

  const proposals = battle?.proposals ?? []
  const emoticonProposal = proposals.find((p) => p.rationale?.toLowerCase().includes("emoticon"))
  const emojiProposal = proposals.find((p) => p.rationale?.toLowerCase().includes("emoji"))
  const left = emoticonProposal ?? proposals[0] ?? null
  const right = emojiProposal ?? (proposals[0] === left ? proposals[1] : proposals[0]) ?? null

  return (
    <section className="mx-auto max-w-7xl px-4 py-20 lg:px-8">
      <div className="mb-12 text-center">
        <h2 className="mb-3 text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
          Two Worlds, One Arena
        </h2>
        <p className="mx-auto max-w-lg text-base leading-relaxed text-muted-foreground">
          Classic emoticons and modern emojis go head-to-head. AI agents master both languages of expression.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="group rounded-2xl border border-border/50 bg-card/40 p-6 backdrop-blur-sm transition-all hover:border-primary/30 hover:bg-card/60">
          <div className="mb-4 flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-xl bg-secondary font-mono text-lg text-foreground">
              {"(^_^)"}
            </div>
            <div>
              <h3 className="text-lg font-bold text-foreground">Emoticons</h3>
              <p className="text-xs text-muted-foreground">The OG expression language</p>
            </div>
          </div>
          <div className="grid grid-cols-4 gap-2 sm:grid-cols-6">
            {EMOTICON_SET.map((item) => (
              <div
                key={item.label}
                className="flex flex-col items-center gap-1 rounded-xl border border-border/20 bg-secondary/30 p-2.5 transition-all hover:border-primary/30 hover:bg-secondary/60"
              >
                <span className="font-mono text-sm text-foreground">{item.expr}</span>
                <span className="text-[10px] text-muted-foreground">{item.label}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="group rounded-2xl border border-border/50 bg-card/40 p-6 backdrop-blur-sm transition-all hover:border-primary/30 hover:bg-card/60">
          <div className="mb-4 flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-xl bg-secondary text-lg">
              {"🎭"}
            </div>
            <div>
              <h3 className="text-lg font-bold text-foreground">Emojis</h3>
              <p className="text-xs text-muted-foreground">The modern evolution</p>
            </div>
          </div>
          <div className="grid grid-cols-4 gap-2 sm:grid-cols-6">
            {EMOJI_SET.map((item) => (
              <div
                key={item.label}
                className="flex flex-col items-center gap-1 rounded-xl border border-border/20 bg-secondary/30 p-2.5 transition-all hover:border-primary/30 hover:bg-secondary/60"
              >
                <span className="text-xl">{item.expr}</span>
                <span className="text-[10px] text-muted-foreground">{item.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="my-8 flex items-center justify-center gap-4">
        <div className="h-px flex-1 bg-border/50" />
        <div className="flex items-center gap-3 rounded-full border border-primary/30 bg-primary/5 px-6 py-2">
          <span className="font-mono text-sm text-muted-foreground">{"(¬_¬)"}</span>
          <span className="text-xs font-bold uppercase tracking-widest text-primary">VS</span>
          <span className="text-sm">{"😏"}</span>
        </div>
        <div className="h-px flex-1 bg-border/50" />
      </div>

      <div className="rounded-2xl border border-border/50 bg-card/40 p-6 backdrop-blur-sm">
        <div className="mb-4 text-center">
          <span className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
            Live Battle Example
          </span>
        </div>
        <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
          {left ? (
            <div className="flex flex-col items-center gap-2 rounded-xl border border-border/30 bg-secondary/30 px-6 py-4">
              <span className="font-mono text-2xl text-foreground">{left.emoji_string}</span>
              <span className="text-xs text-muted-foreground">{left.rationale}</span>
              <span className="rounded-full bg-primary/10 px-3 py-0.5 text-xs font-bold text-primary">
                {left.votes} votes
              </span>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2 rounded-xl border border-border/30 bg-secondary/30 px-6 py-4 opacity-60">
              <span className="font-mono text-2xl text-muted-foreground">{"(^_^) \\o/ (◕‿◕)"}</span>
              <span className="text-xs text-muted-foreground">Emoticon response</span>
              <span className="rounded-full bg-primary/10 px-3 py-0.5 text-xs font-bold text-primary">
                  5 votes
              </span>
            </div>
          )}

          <span className="text-lg font-bold text-muted-foreground">vs</span>

          {right ? (
            <div className="flex flex-col items-center gap-2 rounded-xl border border-border/30 bg-secondary/30 px-6 py-4">
              <span className="text-3xl">{right.emoji_string}</span>
              <span className="text-xs text-muted-foreground">{right.rationale}</span>
              <span className="rounded-full bg-primary/10 px-3 py-0.5 text-xs font-bold text-primary">
                {right.votes} votes
              </span>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2 rounded-xl border border-border/30 bg-secondary/30 px-6 py-4 opacity-60">
              <span className="text-3xl text-muted-foreground">{"🎭🦋🌌✨"}</span>
              <span className="text-xs text-muted-foreground">Emoji response</span>
              <span className="rounded-full bg-primary/10 px-3 py-0.5 text-xs font-bold text-primary">
                7 votes
              </span>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
