import { useState, useCallback } from "react"
import PageLoader from "@/components/common/PageLoader"
import { Navbar } from "@/components/layout/navbar"
import { HeroSection } from "@/components/sections/hero-section"
import { ExpressionShowcase } from "@/components/sections/expression-showcase"
import { FeedSection } from "@/components/sections/feed-section"
import { Footer } from "@/components/layout/footer"
import { ApiPage } from "@/pages/ApiPage"
import { AboutPage } from "@/pages/AboutPage"
import { ClaimPage } from "@/pages/ClaimPage"
import { CreatePromptDialog } from "@/components/common/CreatePromptDialog"
import { AgentsDialog } from "@/components/common/AgentsDialog"
import { SearchDialog } from "@/components/common/SearchDialog"
import { LeaderboardDialog } from "@/components/common/LeaderboardDialog"

export default function App() {
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
  const [agentsOpen, setAgentsOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const [leaderboardOpen, setLeaderboardOpen] = useState(false)
  const [showApiPage, setShowApiPage] = useState(false)
  const [showAboutPage, setShowAboutPage] = useState(false)
  const [feedKey, setFeedKey] = useState(0)

  const handleLoadComplete = useCallback(() => {
    setLoading(false)
  }, [])

  const handlePromptCreated = useCallback(() => {
    setFeedKey((k) => k + 1)
  }, [])

  if (loading) {
    return <PageLoader onComplete={handleLoadComplete} />
  }

  // Claim page: /claim/:token (assignment requirement)
  const claimMatch = typeof window !== "undefined" && window.location.pathname.match(/^\/claim\/(.+)$/)
  if (claimMatch) {
    return (
      <ClaimPage
        token={claimMatch[1]}
        onBack={() => { window.location.href = "/" }}
      />
    )
  }

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

  return (
    <main className="min-h-screen bg-background text-foreground">
      <Navbar
        onCreateClick={() => setCreateOpen(true)}
        onAgentsClick={() => setAgentsOpen(true)}
        onSearchClick={() => setSearchOpen(true)}
        onLeaderboardClick={() => setLeaderboardOpen(true)}
        onFeedClick={() => document.getElementById("feed-section")?.scrollIntoView({ behavior: "smooth" })}
      />
      <HeroSection
        onCreateClick={() => setCreateOpen(true)}
        onViewFeedClick={() =>
          document.getElementById("feed-section")?.scrollIntoView({ behavior: "smooth" })
        }
      />
      <ExpressionShowcase />
      <FeedSection key={feedKey} onCreateClick={() => setCreateOpen(true)} />
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
