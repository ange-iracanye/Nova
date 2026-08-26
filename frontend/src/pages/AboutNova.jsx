import { Link } from "react-router-dom";
import { ArrowLeft, ArrowRight, Brain, CalendarDays, GraduationCap, Sparkles } from "lucide-react";
import NovaLogo from "../components/NovaLogo";

const FACTS = [
  [GraduationCap, "What Nova is", "Nova is an adaptive educational AI tutor. It is built to help students understand concepts, practice skills, correct mistakes and make progress."],
  [Brain, "What Nova can do", "Nova can explain concepts, solve problems, quiz you, give hints, adapt difficulty, use relevant learning context, remember useful information and personalize responses from your settings."],
  [Sparkles, "Why Nova exists", "Nova is designed around a simple idea: learning works better when explanations, practice, memory and adaptation work together instead of living in separate tools."],
  [CalendarDays, "When Nova was created", "Nova's exact creation history is a product fact maintained by its application documentation. If a specific date is not available in the current product context, Nova should say that rather than inventing one."],
];

export default function AboutNova() {
  return (
    <main className="min-h-screen bg-[#020617] text-white">
      <header className="border-b border-white/[.06] px-6 py-5"><div className="mx-auto flex max-w-5xl items-center justify-between"><Link to="/" className="flex items-center gap-3"><NovaLogo className="h-9 w-9 rounded-xl object-contain"/><span className="text-sm font-bold tracking-[.18em]">NOVA</span></Link><Link to="/" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white"><ArrowLeft size={16}/> Back home</Link></div></header>
      <section className="mx-auto max-w-5xl px-6 py-16"><p className="text-xs font-bold tracking-[.2em] text-cyan-300">ABOUT NOVA</p><h1 className="mt-4 max-w-4xl text-5xl font-semibold tracking-[-.05em] sm:text-7xl">Meet Nova, the tutor behind the learning loop.</h1><p className="mt-7 max-w-3xl text-lg leading-8 text-slate-400">Nova is not the name of the underlying model. Nova is the educational product and tutor experience built around it.</p>
        <div className="mt-12 grid gap-4 sm:grid-cols-2">{FACTS.map(([Icon, title, text]) => <article key={title} className="rounded-3xl border border-white/[.07] bg-white/[.025] p-7"><Icon className="text-cyan-300" size={22}/><h2 className="mt-5 text-xl font-semibold">{title}</h2><p className="mt-3 leading-7 text-slate-400">{text}</p></article>)}</div>
        <div className="mt-10 rounded-3xl border border-cyan-300/10 bg-cyan-300/[.04] p-7"><h2 className="text-xl font-semibold">Nova's identity rule</h2><p className="mt-3 leading-7 text-slate-400">When you ask Nova who it is, it should identify itself as Nova, explain that it is an adaptive educational AI tutor, and describe its capabilities accurately. It should never claim to be Nvidia or invent an unrelated identity.</p></div>
        <div className="mt-8 flex flex-col gap-3 sm:flex-row"><Link to="/chat" className="inline-flex items-center justify-center gap-2 rounded-2xl bg-white px-5 py-3 font-semibold text-cyan-700">Talk to Nova <ArrowRight size={16}/></Link><Link to="/capabilities/adaptive-tutoring" className="inline-flex items-center justify-center gap-2 rounded-2xl border border-white/10 px-5 py-3 text-slate-300">Explore capabilities</Link></div>
      </section>
    </main>
  );
}
