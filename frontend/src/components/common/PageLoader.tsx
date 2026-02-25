import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"

const EMOJIS = ["😎", "🔥", "✨", "🎭", "💫", "🫶", "🥺", "😂", "🤖", "⚡"]

const PageLoader = ({ onComplete }: { onComplete: () => void }) => {
  const [progress, setProgress] = useState(0)
  const [phase, setPhase] = useState<"emojis" | "text" | "done">("emojis")

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval)
          return 100
        }
        return prev + 2
      })
    }, 40)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (progress >= 60) setPhase("text")
    if (progress >= 100) {
      const timeout = setTimeout(() => {
        setPhase("done")
        setTimeout(onComplete, 500)
      }, 400)
      return () => clearTimeout(timeout)
    }
  }, [progress, onComplete])

  return (
    <AnimatePresence>
      {phase !== "done" && (
        <motion.div
          className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-background"
          exit={{ opacity: 0, scale: 1.05 }}
          transition={{ duration: 0.5, ease: "easeInOut" }}
        >
          {/* Background grid pattern */}
          <div
            className="absolute inset-0 opacity-[0.03]"
            style={{
              backgroundImage: "radial-gradient(circle, rgba(255,255,255,0.5) 1px, transparent 1px)",
              backgroundSize: "40px 40px",
            }}
          />

          {/* Floating emojis */}
          <div className="relative mb-12 h-32 w-80">
            {EMOJIS.slice(0, 5).map((emoji, i) => (
              <motion.span
                key={i}
                className="absolute text-4xl"
                style={{ left: `${i * 20}%` }}
                initial={{ y: 40, opacity: 0, scale: 0.5 }}
                animate={{
                  y: [0, -20, 0],
                  opacity: 1,
                  scale: [1, 1.2, 1],
                  rotate: [0, i % 2 === 0 ? 15 : -15, 0],
                }}
                transition={{
                  delay: i * 0.15,
                  duration: 1.5,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
              >
                {emoji}
              </motion.span>
            ))}
          </div>

          {/* Logo text */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.6 }}
            className="mb-8 text-center"
          >
            <h1 className="text-5xl font-bold tracking-tight">
              <span className="text-gradient">Mojify</span>
            </h1>
            <motion.p
              className="mt-2 text-sm text-muted-foreground"
              initial={{ opacity: 0 }}
              animate={{ opacity: phase === "text" ? 1 : 0 }}
              transition={{ duration: 0.3 }}
            >
              where emojis compete for glory
            </motion.p>
          </motion.div>

          {/* Progress bar */}
          <div className="relative h-1 w-64 overflow-hidden rounded-full bg-secondary">
            <motion.div
              className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-primary to-amber-300"
              style={{ width: `${progress}%` }}
              transition={{ duration: 0.1 }}
            />
          </div>

          {/* Percentage */}
          <motion.span
            className="mt-3 text-xs font-medium tabular-nums text-muted-foreground"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            {progress}%
          </motion.span>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default PageLoader
