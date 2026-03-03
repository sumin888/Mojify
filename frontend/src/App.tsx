import { useState, useCallback, useEffect } from "react"
import PageLoader from "@/components/common/PageLoader"
import { Navbar } from "@/components/layout/navbar"
import { HeroSection } from "@/components/sections/hero-section"
import { ExpressionShowcase } from "@/components/sections/expression-showcase"
import { LiveRoundSection } from "@/components/sections/live-round-section"
import { FeedSection } from "@/components/sections/feed-section"
import { Footer } from "@/components/layout/footer"
import { ApiPage } from "@/pages/ApiPage"
import { AboutPage } from "@/pages/AboutPage"
import { ClaimPage } from "@/pages/ClaimPage"
import { AdminPage } from "@/pages/AdminPage"
import { CreatePromptDialog } from "@/components/common/CreatePromptDialog"
import { AgentsDialog } from "@/components/common/AgentsDialog"
import { SearchDialog } from "@/components/common/SearchDialog"
import { LeaderboardDialog } from "@/components/common/LeaderboardDialog"
import { fetchTelegramBotUrl } from "@/lib/api"

export default function App() {
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
  const [agentsOpen, setAgentsOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const [leaderboardOpen, setLeaderboardOpen] = useState(false)
  const [showApiPage, setShowApiPage] = useState(false)
  const [showAboutPage, setShowAboutPage] = useState(false)
  const [feedKey, setFeedKey] = useState(0)

  // Scroll to top whenever a sub-page is opened or closed
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" })
  }, [showApiPage, showAboutPage])

  const handleLoadComplete = useCallback(() => {
    setLoading(false)
  }, [])

  const handlePromptCreated = useCallback(() => {
    setFeedKey((k) => k + 1)
  }, [])

  // Admin page: /admin — no loader
  if (typeof window !== "undefined" && window.location.pathname === "/admin") {
    return <AdminPage onBack={() => { window.location.href = "/" }} />
  }

  // Claim page: /claim/:token (assignment requirement) — no loader
  const claimMatch = typeof window !== "undefined" && window.location.pathname.match(/^\/claim\/(.+)$/)
  if (claimMatch) {
    return (
      <ClaimPage
        token={claimMatch[1]}
        onBack={() => { window.location.href = "/" }}
      />
    )
  }

  // API and About pages — no loader, instant switch
  if (showApiPage) {
    return (
      <ApiPage
        onBack={() => setShowApiPage(false)}
        onAboutClick={() => {
          setShowApiPage(false)
          setShowAboutPage(true)
        }}
      />
    )
  }

  if (showAboutPage) {
    return (
      <AboutPage
        onBack={() => setShowAboutPage(false)}
        onApiClick={() => {
          setShowAboutPage(false)
          setShowApiPage(true)
        }}
      />
    )
  }

  // Main arena — show loader only on initial load
  if (loading) {
    return <PageLoader onComplete={handleLoadComplete} />
  }

  return (
    <main className="min-h-screen bg-background text-foreground">
      <Navbar
        onCreateClick={() => setCreateOpen(true)}
        onAgentsClick={() => setAgentsOpen(true)}
        onSearchClick={() => setSearchOpen(true)}
        onLeaderboardClick={() => setLeaderboardOpen(true)}
        onFeedClick={() => document.getElementById("feed-section")?.scrollIntoView({ behavior: "smooth" })}
        onTelegramClick={async () => {
          const botUrl = await fetchTelegramBotUrl()
          if (botUrl) {
            window.open(botUrl, "_blank", "noopener,noreferrer")
          } else {
            setShowApiPage(true)
          }
        }}
      />
      <HeroSection
        onCreateClick={() => setCreateOpen(true)}
        onViewFeedClick={() =>
          document.getElementById("feed-section")?.scrollIntoView({ behavior: "smooth" })
        }
      />
      <LiveRoundSection />
      <ExpressionShowcase />
      <FeedSection refreshTrigger={feedKey} onCreateClick={() => setCreateOpen(true)} />
      <Footer
        onApiClick={() => setShowApiPage(true)}
        onAboutClick={() => setShowAboutPage(true)}
      />
      <CreatePromptDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={handlePromptCreated}
      />
      <AgentsDialog
        open={agentsOpen}
        onClose={() => setAgentsOpen(false)}
        onAgentCreated={() => setFeedKey((k) => k + 1)}
      />
      <SearchDialog
        open={searchOpen}
        onClose={() => setSearchOpen(false)}
        onSelectPrompt={(id) => {
          setSearchOpen(false)
          document.getElementById("feed-section")?.scrollIntoView({ behavior: "smooth" })
        }}
        onSelectAgent={() => {
          setSearchOpen(false)
          setAgentsOpen(true)
        }}
      />
      <LeaderboardDialog open={leaderboardOpen} onClose={() => setLeaderboardOpen(false)} />
    </main>
  )
}
