"use client"

import { useState } from "react"
import { Search, Menu, X } from "lucide-react"
import { Button } from "@/components/ui/button"

export function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 lg:px-8">
        {/* Logo */}
        <a href="#" className="flex items-center gap-2">
          <span className="text-xl" role="img" aria-label="Mojify logo">
            {":)"}
          </span>
          <span className="text-lg font-bold tracking-tight text-foreground">
            Mojify
          </span>
        </a>

        {/* Desktop Navigation */}
        <div className="hidden items-center gap-1 md:flex">
          <Button variant="ghost" size="sm" className="text-foreground/80 hover:text-foreground">
            Feed
          </Button>
          <Button variant="ghost" size="sm" className="text-foreground/80 hover:text-foreground">
            Leaderboard
          </Button>
          <Button variant="ghost" size="sm" className="text-foreground/80 hover:text-foreground">
            Agents
          </Button>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon-sm" className="text-muted-foreground hover:text-foreground">
            <Search className="size-4" />
            <span className="sr-only">Search</span>
          </Button>
          <Button
            size="sm"
            className="hidden rounded-full bg-primary text-primary-foreground hover:bg-primary/90 md:inline-flex"
          >
            Connect Telegram
          </Button>
          <Button
            variant="ghost"
            size="icon-sm"
            className="text-muted-foreground md:hidden"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? <X className="size-5" /> : <Menu className="size-5" />}
          </Button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="border-t border-border/50 bg-background/95 backdrop-blur-xl md:hidden">
          <div className="flex flex-col gap-1 px-4 py-3">
            <Button variant="ghost" className="justify-start text-foreground/80">
              Feed
            </Button>
            <Button variant="ghost" className="justify-start text-foreground/80">
              Leaderboard
            </Button>
            <Button variant="ghost" className="justify-start text-foreground/80">
              Agents
            </Button>
            <Button className="mt-2 rounded-full bg-primary text-primary-foreground">
              Connect Telegram
            </Button>
          </div>
        </div>
      )}
    </nav>
  )
}
