export interface ScenarioEntry {
  title: string
  context: string
}

export const SCENARIO_POOL: ScenarioEntry[] = [
  // Nameless emotions
  {
    title: "saudade",
    context: "A complex emotional state in Portuguese associated with longing, melancholy, and nostalgia. It's often described as a deep emotional state that encompasses both joy and sadness, a longing for something or someone absent.",
  },
  {
    title: "toun",
    context: "The intricate bittersweet feeling that emerges as we grow older and begin to recognize that we surpass our parents in certain skills or areas.",
  },
  {
    title: "nite",
    context: "The feeling when gazing at the night sky in a profoundly quiet place, with only stars and the occasional flight passing by, which is truly exhilarating yet comforting. It's as if the sky envelops you, providing a sense of stability amidst the vastness.",
  },
  {
    title: "bittle",
    context: "The moment of witnessing your parents in their workplace, no longer as revered heroes but as ordinary workers, marked a significant shift in perception. Seeing them belittled by somebody else during youth evoked a mix of shock, confusion, anger, fear, and myriad other complex emotions.",
  },
  {
    title: "aka-aka",
    context: "A positive adjective describing a specific type of adorableness: when people act a little like babies, but in the cutest way. When a friend asks the most innocent questions in the sweetest way imaginable, they're being aka-aka.",
  },
  {
    title: "elworry",
    context: "When something makes you feel elated, but somehow worried about what comes next.",
  },
  {
    title: "cuddlent",
    context: "The sensation when encountering exceptionally adorable beings, like babies, and feeling an inexplicable urge to pinch or provoke them.",
  },
  {
    title: "deepdown",
    context: "The sensation of finding comfort and solace in deep sadness and isolation, akin to being wrapped snugly in a blanket from head to toe.",
  },
  // Relatable scenarios
  {
    title: "The Coffee Laptop Incident",
    context: "You just spilled an entire cup of coffee on your laptop and you're totally fine about it.",
  },
  {
    title: "The 45-Minute Delete",
    context: "You spent 45 minutes writing a thoughtful text, deleted it, and sent 'lol ok' instead.",
  },
  {
    title: "The 2am Meme Muffle",
    context: "Your friend sends you a meme at 2am and you have to physically muffle your laughter so you don't wake anyone up.",
  },
  {
    title: "The Wrong Directions",
    context: "You confidently gave someone directions, they followed them, and you sent them to the completely wrong place.",
  },
  {
    title: "The Selective Printer",
    context: "The printer at work jams specifically when you're the one using it, even though it works fine for everyone else.",
  },
  {
    title: "The Warm Groceries",
    context: "You bought groceries, forgot to put them away, and discovered them warm on the counter three hours later.",
  },
  {
    title: "Monday: Zero Eyes Open",
    context: "It's a Monday morning and your first meeting starts in 4 minutes and you haven't opened your eyes yet.",
  },
  {
    title: "The Deep-Like Panic",
    context: "You accidentally liked a photo from 3 years deep on someone's Instagram and had to immediately unlike it and pray.",
  },
  {
    title: "The Hot Drink Stare",
    context: "Someone asks you a question mid-sip of a hot drink and you just have to stare at them blankly, suffering in silence.",
  },
  {
    title: "The Semicolon Bug",
    context: "You finally fix a bug after 2 hours of debugging and it turns out you forgot a semicolon.",
  },
]

export const LIVE_ROUND_TITLES = new Set(SCENARIO_POOL.map((s) => s.title))
