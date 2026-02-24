interface SectionLink {
  id: string
  label: string
}

interface PageSidebarProps {
  sections: SectionLink[]
  children: React.ReactNode
}

function scrollToSection(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth" })
}

export function PageSidebar({ sections, children }: PageSidebarProps) {
  return (
    <div className="mx-auto max-w-7xl px-4 pb-24 pt-28 lg:px-8">
      {/* Mobile: horizontal nav at top */}
      <nav
        className="md:hidden sticky top-16 z-30 -mx-4 mb-8 flex gap-2 overflow-x-auto border-b border-border/50 bg-background/95 px-4 py-3 backdrop-blur-xl"
        aria-label="Page sections"
      >
        {sections.map(({ id, label }) => (
          <button
            key={id}
            type="button"
            onClick={() => scrollToSection(id)}
            className="shrink-0 rounded-full border border-border/50 bg-muted/30 px-4 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-muted/50 hover:text-foreground"
          >
            {label}
          </button>
        ))}
      </nav>

      {/* Sidebar + content */}
      <div className="flex gap-12">
        <aside className="hidden shrink-0 md:block">
          <nav
            className="sticky top-24 w-44 space-y-1 border-r border-border/50 pr-6"
            aria-label="Page sections"
          >
            <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              On this page
            </p>
            {sections.map(({ id, label }) => (
              <button
                key={id}
                type="button"
                onClick={() => scrollToSection(id)}
                className="block w-full text-left text-sm text-muted-foreground transition-colors hover:text-foreground"
              >
                {label}
              </button>
            ))}
          </nav>
        </aside>

        <main className="min-w-0 flex-1 flex justify-center">
          <article className="w-full max-w-4xl">{children}</article>
        </main>
      </div>
    </div>
  )
}
