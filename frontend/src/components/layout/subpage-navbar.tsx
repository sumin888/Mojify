import { ArrowLeft } from "lucide-react"
import { Button } from "@/components/ui/button"

interface SubPageNavbarProps {
  currentPage: "api" | "about"
  onBack: () => void
  onApiClick: () => void
  onAboutClick: () => void
}

export function SubPageNavbar({ currentPage, onBack, onApiClick, onAboutClick }: SubPageNavbarProps) {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 lg:px-8">
        <button
          type="button"
          onClick={onBack}
          className="flex items-center gap-2 text-foreground no-underline hover:opacity-80"
        >
          <span className="text-xl" role="img" aria-label="Mojify logo">
            {":)"}
          </span>
          <span className="text-lg font-bold tracking-tight text-foreground">
            Mojify
          </span>
        </button>

        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            className={
              currentPage === "api"
                ? "text-foreground"
                : "text-foreground/80 hover:text-foreground"
            }
            onClick={onApiClick}
          >
            API
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className={
              currentPage === "about"
                ? "text-foreground"
                : "text-foreground/80 hover:text-foreground"
            }
            onClick={onAboutClick}
          >
            About
          </Button>
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={onBack}
          className="gap-2 text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="size-4" />
          Back to arena
        </Button>
      </div>
    </nav>
  )
}
