import { Link, useParams } from "react-router-dom";
import { ArrowLeft, ArrowRight, Brain, Bot, FileText, Layers3, LineChart, Target } from "lucide-react";
import NovaLogo from "../components/NovaLogo";

const CAPABILITIES = {
  "adaptive-tutoring": {
    icon: Brain,
    title: "Adaptive tutoring",
    summary: "Nova changes the way it teaches based on what you demonstrate, not just what you ask.",
    sections: [
      ["What it does", "Nova can adjust explanation depth, vocabulary, examples, hints and difficulty. If you are struggling, it can slow down and rebuild the missing foundation. If you already understand something, it can avoid repeating the basics and move toward deeper applications."],
      ["How it adapts", "Nova combines your current request with your saved learning preferences, demonstrated understanding, relevant previous discussions and learning signals. Your current message always has priority, so saying that you are confused can change the approach immediately."],
      ["Why it matters", "A fixed lesson assumes every learner starts in the same place. Adaptive tutoring tries to meet you where you actually are, then move you forward without turning every answer into either a lecture or a one-line solution."]
    ]
  },
  "learning-memory": {
    icon: Layers3,
    title: "Learning memory",
    summary: "Nova can carry useful context across conversations so you do not have to rebuild your learning history every time.",
    sections: [
      ["What it remembers", "Nova stores conversation episodes and extracts useful long-term information such as facts, preferences, goals and learning-related information. It can also use recent conversations when they are relevant to a new request."],
      ["How it uses memory", "Relevant history is retrieved for the current request rather than blindly dumping an entire archive into every prompt. Recent continuity and related previous discussions can help Nova understand references such as continuing a topic you studied earlier."],
      ["What memory is not", "Memory is evidence, not absolute truth. A current message can correct an older memory. Nova should never force an unrelated old conversation into a new answer."]
    ]
  },
  "progress-intelligence": {
    icon: LineChart,
    title: "Progress intelligence",
    summary: "Nova turns learning activity into signals you can use to decide what to work on next.",
    sections: [
      ["What it looks at", "Progress can include mastery signals, weak areas, learning activity, previous attempts and the subjects or topics you have been working on."],
      ["How it helps", "Instead of treating every question as isolated, Nova can use your learning history to choose more appropriate explanations, practice and difficulty. The goal is to make progress visible and actionable rather than just collecting chat transcripts."],
      ["The goal", "Progress intelligence is designed to support better study decisions. It should help answer questions such as what you understand, what still needs work and what would be useful to practice next."]
    ]
  },
  "learn-from-material": {
    icon: FileText,
    title: "Learn from material",
    summary: "Use your own notes and learning material as the starting point for focused study.",
    sections: [
      ["What it is for", "Material-based learning is intended to turn documents and notes into questions, explanations, summaries and study sessions instead of making you manually copy every useful section into a chat."],
      ["A better workflow", "Start with the material, ask Nova what you want to understand, then use explanations and practice to check whether the information actually stuck."],
      ["Keep context useful", "Nova should use supplied material as context for the task while still distinguishing the source material from its own reasoning and from information that is uncertain."]
    ]
  },
  "goal-driven-study": {
    icon: Target,
    title: "Goal-driven study",
    summary: "Turn a vague intention such as 'I need to study biology' into a more concrete learning path.",
    sections: [
      ["Set direction", "Goals give Nova a target. A useful goal can describe a subject, exam, topic, skill or outcome you want to reach."],
      ["Connect the pieces", "Goals can work alongside memory, progress and adaptive tutoring so Nova can keep the larger objective in view while responding to the question in front of it."],
      ["Stay practical", "The purpose is not to create a complicated productivity system. It is to make study sessions more connected to what you are actually trying to accomplish."]
    ]
  },
  "built-to-teach": {
    icon: Bot,
    title: "Built to teach",
    summary: "Nova is designed as an educational tutor first, rather than a generic chatbot with a school-themed coat of paint.",
    sections: [
      ["Teaching first", "Nova's instructions prioritize understanding, explanation, practice, correction and retention. It can explain concepts, solve academic problems, give hints, quiz you and change strategy when an explanation is not working."],
      ["Personalization", "Your name, language, academic level, teaching style, difficulty, response length, tone and other saved preferences are intended to shape how Nova responds."],
      ["Its identity", "Nova is Nova: an adaptive educational AI tutor. The underlying language model is a component used by Nova, not Nova's identity. Nova should not invent a different product identity when you ask what it is."]
    ]
  }
};

export default function Capabilities() {
  const { capability } = useParams();
  const item = CAPABILITIES[capability] || CAPABILITIES["adaptive-tutoring"];
  const Icon = item.icon;
  const entries = Object.entries(CAPABILITIES);

  return (
    <main className="min-h-screen bg-[#020617] text-white">
      <header className="border-b border-white/[.06] bg-[#020617]/90 px-6 py-5 backdrop-blur-xl">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-3"><NovaLogo className="h-9 w-9 rounded-xl object-contain"/><span className="text-sm font-bold tracking-[.18em]">NOVA</span></Link>
          <Link to="/" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white"><ArrowLeft size={16}/> Back home</Link>
        </div>
      </header>

      <div className="mx-auto grid max-w-5xl gap-8 px-6 py-12 lg:grid-cols-[220px_1fr]">
        <aside className="lg:sticky lg:top-8 lg:self-start">
          <p className="mb-3 text-[10px] font-bold tracking-[.2em] text-cyan-300">EXPLORE NOVA</p>
          <nav className="space-y-1">
            {entries.map(([key, value]) => {
              const ActiveIcon = value.icon;
              return <Link key={key} to={`/capabilities/${key}`} className={`flex items-center gap-2 rounded-xl px-3 py-2.5 text-sm transition ${key === capability ? "bg-white/[.07] text-white" : "text-slate-500 hover:bg-white/[.04] hover:text-white"}`}><ActiveIcon size={15}/>{value.title}</Link>;
            })}
          </nav>
        </aside>

        <article>
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-cyan-300/10 bg-cyan-300/[.06] text-cyan-300"><Icon size={25}/></div>
          <p className="mt-7 text-xs font-bold tracking-[.2em] text-cyan-300">NOVA CAPABILITY</p>
          <h1 className="mt-3 text-4xl font-semibold tracking-[-.04em] sm:text-6xl">{item.title}</h1>
          <p className="mt-5 max-w-3xl text-lg leading-8 text-slate-400">{item.summary}</p>

          <div className="mt-12 space-y-8">
            {item.sections.map(([heading, text]) => <section key={heading} className="rounded-3xl border border-white/[.07] bg-white/[.025] p-6 sm:p-8"><h2 className="text-xl font-semibold">{heading}</h2><p className="mt-3 leading-7 text-slate-400">{text}</p></section>)}
          </div>

          <div className="mt-10 flex flex-col gap-3 sm:flex-row"><Link to="/chat" className="inline-flex items-center justify-center gap-2 rounded-2xl bg-white px-5 py-3 font-semibold text-cyan-700">Try Nova <ArrowRight size={16}/></Link><Link to="/about" className="inline-flex items-center justify-center gap-2 rounded-2xl border border-white/10 px-5 py-3 text-slate-300">About Nova</Link></div>
        </article>
      </div>
    </main>
  );
}
