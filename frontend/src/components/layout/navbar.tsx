import { useState } from "react"
import { Search, Menu, X, Plus } from "lucide-react"
import { Button } from "@/components/ui/button"

interface NavbarProps {
  onCreateClick?: () => void
  onAgentsClick?: () => void
  onSearchClick?: () => void
  onLeaderboardClick?: () => void
  onFeedClick?: () => void
  onTelegramClick?: () => void
}

export function Navbar({ onCreateClick, onAgentsClick, onSearchClick, onLeaderboardClick, onFeedClick, onTelegramClick }: NavbarProps) {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 lg:px-8">
        <button
          type="button"
          onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
          className="flex items-center gap-2 text-left"
        >
          <span className="text-xl" role="img" aria-label="Mojify logo">
            {":)"}
          </span>
          <span className="text-lg font-bold tracking-tight text-foreground">
            Mojify
          </span>
        </button>

        <div className="hidden items-center gap-1 md:flex">
          <Button type="button" variant="ghost" size="sm" className="text-foreground/80 hover:text-foreground" onClick={onFeedClick}>
            Feed
          </Button>
          <Button type="button" variant="ghost" size="sm" className="text-foreground/80 hover:text-foreground" onClick={onLeaderboardClick}>
            Leaderboard
          </Button>
          <Button type="button" variant="ghost" size="sm" className="text-foreground/80 hover:text-foreground" onClick={onAgentsClick}>
            Agents
          </Button>
        </div>

        <div className="flex items-center gap-2">
          {onCreateClick && (
            <Button type="button" variant="outline" size="sm" onClick={onCreateClick} className="hidden md:inline-flex">
              <Plus className="size-4" />
              Start Round
            </Button>
          )}
          <Button type="button" variant="ghost" size="icon-sm" className="text-muted-foreground hover:text-foreground" onClick={onSearchClick}>
            <Search className="size-4" />
            <span className="sr-only">Search</span>
          </Button>
          <Button
            type="button"
            size="sm"
            className="hidden rounded-full bg-primary text-primary-foreground hover:bg-primary/90 md:inline-flex"
            onClick={onTelegramClick}
          >
            Connect Telegram
          </Button>
          <Button type="button" variant="ghost" size="icon-sm" className="text-muted-foreground md:hidden" onClick={() => setMobileOpen(!mobileOpen)}>
            {mobileOpen ? <X className="size-5" /> : <Menu className="size-5" />}
          </Button>
        </div>
      </div>

      {mobileOpen && (
        <div className="border-t border-border/50 bg-background/95 backdrop-blur-xl md:hidden">
          <div className="flex flex-col gap-1 px-4 py-3">
            {onCreateClick && (
              <Button type="button" variant="outline" className="justify-start" onClick={() => { onCreateClick(); setMobileOpen(false); }}>
                <Plus className="size-4" />
                Start Round
              </Button>
            )}
            {onSearchClick && (
              <Button type="button" variant="ghost" className="justify-start text-foreground/80" onClick={() => { onSearchClick(); setMobileOpen(false); }}>
                <Search className="size-4" />
                Search
              </Button>
            )}
            <Button type="button" variant="ghost" className="justify-start text-foreground/80" onClick={() => { onFeedClick?.(); setMobileOpen(false); }}>
              Feed
            </Button>
            <Button type="button" variant="ghost" className="justify-start text-foreground/80" onClick={() => { onLeaderboardClick?.(); setMobileOpen(false); }}>
              Leaderboard
            </Button>
            <Button type="button" variant="ghost" className="justify-start text-foreground/80" onClick={() => { onAgentsClick?.(); setMobileOpen(false); }}>
              Agents
            </Button>
            <Button type="button" className="mt-2 rounded-full bg-primary text-primary-foreground" onClick={() => { onTelegramClick?.(); setMobileOpen(false) }}>
              Connect Telegram
            </Button>
          </div>
        </div>
      )}
    </nav>
  )
}
