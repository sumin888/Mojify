interface FooterProps {
  onApiClick?: () => void
  onAboutClick?: () => void
}

export function Footer({ onApiClick, onAboutClick }: FooterProps) {
  return (
    <footer className="border-t border-border/50 bg-card/20">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 py-8 sm:flex-row lg:px-8">
        <div className="flex items-center gap-2">
          <span className="font-mono text-sm text-muted-foreground">{":)"}</span>
          <span className="text-sm font-semibold text-foreground">Mojify</span>
        </div>
        <p className="text-xs text-muted-foreground">
          Built with <span className="font-mono">{"<3"}</span> and <span>{"❤️"}</span>
        </p>
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          {onAboutClick ? (
            <button type="button" onClick={onAboutClick} className="transition-colors hover:text-foreground">
              About
            </button>
          ) : (
            <a href="#" className="transition-colors hover:text-foreground">About</a>
          )}
          {onApiClick ? (
            <button type="button" onClick={onApiClick} className="transition-colors hover:text-foreground">
              API
            </button>
          ) : (
            <a href="#" className="transition-colors hover:text-foreground">API</a>
          )}
          <a href="#" className="transition-colors hover:text-foreground">Discord</a>
        </div>
      </div>
    </footer>
  )
}
