import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Brain, Bot, CheckCircle2, ChevronRight, FileText, Layers3, LineChart, Orbit, Play, Sparkles, Target, Trophy, Zap } from "lucide-react";
import NovaLogo from "../components/NovaLogo";

const FEATURES = [
    [Brain, "Adaptive tutoring", "Explanations and difficulty evolve around your actual understanding."],
    [Layers3, "Learning memory", "Nova keeps useful learning context across sessions."],
    [LineChart, "Progress intelligence", "See mastery, weak areas, momentum and what to study next."],
    [FileText, "Learn from material", "Turn notes and documents into focused learning sessions."],
    [Target, "Goal-driven study", "Move from vague intentions to concrete study targets."],
    [Bot, "Built to teach", "Nova is designed around understanding, practice and retention."],
];

const STEPS = [
    ["01", "Ask", "Turn confusion into a question."],
    ["02", "Understand", "Get an explanation shaped for you."],
    ["03", "Practice", "Test whether the idea really stuck."],
    ["04", "Master", "Return to weak areas until they become strengths."],
];

function FeatureCard({ icon: Icon, title, text, index }) {
    return (
        <article data-nova-reveal className="nova-reveal group relative overflow-hidden rounded-3xl border border-white/[0.07] bg-white/[0.025] p-6 transition duration-500 hover:-translate-y-2 hover:border-cyan-300/20 hover:bg-white/[0.05]" style={{ transitionDelay: `${index * 70}ms` }}>
            <div className="absolute -right-16 -top-16 h-32 w-32 rounded-full bg-cyan-400/[0.06] blur-3xl transition duration-500 group-hover:bg-cyan-400/[0.14]" />
            <div className="relative flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.05] text-cyan-300 transition duration-500 group-hover:scale-110 group-hover:rotate-3"><Icon size={20} /></div>
            <h3 className="relative mt-6 text-lg font-semibold tracking-tight">{title}</h3>
            <p className="relative mt-2 text-sm leading-6 text-slate-400">{text}</p>
            <div className="mt-6 flex items-center gap-2 text-xs font-medium text-slate-500 transition group-hover:text-cyan-300">Explore capability <ChevronRight size={14} className="transition group-hover:translate-x-1" /></div>
        </article>
    );
}

export default function Home() {
    const [pointer, setPointer] = useState({ x: 0, y: 0 });
    const [step, setStep] = useState(0);

    useEffect(() => {
        const onMove = event => setPointer({ x: (event.clientX / window.innerWidth - .5) * 2, y: (event.clientY / window.innerHeight - .5) * 2 });
        window.addEventListener("pointermove", onMove, { passive: true });
        return () => window.removeEventListener("pointermove", onMove);
    }, []);

    useEffect(() => {
        const observer = new IntersectionObserver(entries => entries.forEach(entry => entry.isIntersecting && entry.target.classList.add("nova-revealed")), { threshold: .12 });
        document.querySelectorAll("[data-nova-reveal]").forEach(node => observer.observe(node));
        return () => observer.disconnect();
    }, []);

    useEffect(() => {
        const id = window.setInterval(() => setStep(value => (value + 1) % STEPS.length), 3200);
        return () => window.clearInterval(id);
    }, []);

    const orbStyle = useMemo(() => ({ transform: `translate3d(${pointer.x * 10}px, ${pointer.y * 10}px, 0)` }), [pointer]);

    return (
        <main className="min-h-screen overflow-hidden bg-[#020617] text-white selection:bg-cyan-300/20">
            <style>{`.nova-reveal{opacity:0;transform:translateY(28px);transition:opacity .8s ease,transform .8s cubic-bezier(.2,.8,.2,1)}.nova-revealed{opacity:1;transform:none}@keyframes nf{0%,100%{transform:translateY(0)}50%{transform:translateY(-14px)}}@keyframes ns{to{transform:rotate(360deg)}}@keyframes np{0%,100%{opacity:.3;transform:scale(.95)}50%{opacity:.8;transform:scale(1.05)}}.nova-float{animation:nf 7s ease-in-out infinite}.nova-spin{animation:ns 22s linear infinite}.nova-pulse{animation:np 4s ease-in-out infinite}@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation-duration:.001ms!important;animation-iteration-count:1!important;transition-duration:.001ms!important}}`}</style>
            <div className="pointer-events-none fixed inset-0 z-0"><div className="absolute left-1/2 top-[-22rem] h-[55rem] w-[55rem] -translate-x-1/2 rounded-full bg-cyan-500/[0.08] blur-[140px]"/><div className="absolute bottom-[-20rem] left-[-12rem] h-[38rem] w-[38rem] rounded-full bg-violet-500/[0.08] blur-[120px]"/><div className="absolute right-[-15rem] top-[35%] h-[40rem] w-[40rem] rounded-full bg-blue-500/[0.06] blur-[130px]"/><div className="absolute inset-0 opacity-[0.025] [background-image:linear-gradient(rgba(255,255,255,.5)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.5)_1px,transparent_1px)] [background-size:64px_64px]"/></div>

            <header className="relative z-20 mx-auto flex max-w-7xl items-center justify-between px-6 py-6 lg:px-8">
                <Link to="/" className="flex items-center gap-3"><NovaLogo className="h-10 w-10 rounded-xl object-contain"/><div><div className="text-sm font-bold tracking-[.18em]">NOVA</div><div className="text-[10px] tracking-[.2em] text-slate-500">AI LEARNING</div></div></Link>
                <nav className="hidden items-center gap-1 md:flex"><Link to="/chat" className="rounded-xl px-4 py-2 text-sm text-slate-400 transition hover:bg-white/[.05] hover:text-white">Learn</Link><Link to="/dashboard" className="rounded-xl px-4 py-2 text-sm text-slate-400 transition hover:bg-white/[.05] hover:text-white">Dashboard</Link><Link to="/settings" className="rounded-xl px-4 py-2 text-sm text-slate-400 transition hover:bg-white/[.05] hover:text-white">Settings</Link></nav>
                <Link to="/chat" className="group hidden items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:-translate-y-0.5 hover:bg-slate-100 sm:flex">Start learning <ArrowRight size={15} className="transition group-hover:translate-x-1"/></Link>
            </header>

            <section className="relative z-10 mx-auto grid min-h-[calc(100vh-88px)] max-w-7xl items-center gap-12 px-6 pb-28 pt-10 lg:grid-cols-[1.05fr_.95fr] lg:px-8">
                <div>
                    <div className="inline-flex items-center gap-2 rounded-full border border-cyan-300/10 bg-cyan-300/[.06] px-3.5 py-2 text-xs font-medium text-cyan-200 backdrop-blur-xl"><span className="relative flex h-2 w-2"><span className="absolute h-full w-full animate-ping rounded-full bg-cyan-300 opacity-60"/><span className="relative h-2 w-2 rounded-full bg-cyan-300"/></span>Adaptive intelligence for learning</div>
                    <h1 className="mt-7 max-w-4xl text-5xl font-semibold leading-[.94] tracking-[-.055em] sm:text-7xl lg:text-[5.9rem]">Your learning.<span className="block bg-gradient-to-r from-cyan-200 via-white to-violet-300 bg-clip-text text-transparent">Elevated.</span></h1>
                    <p className="mt-7 max-w-2xl text-base leading-7 text-slate-400 sm:text-lg">Nova is an adaptive AI tutor that explains, remembers, challenges and guides you toward real understanding.</p>
                    <div className="mt-9 flex flex-col gap-3 sm:flex-row"><Link to="/chat" className="group inline-flex items-center justify-center gap-2.5 rounded-2xl bg-white px-6 py-4 text-sm font-bold text-slate-950 shadow-[0_20px_70px_rgba(255,255,255,.08)] transition duration-300 hover:-translate-y-1"><Play size={16} fill="currentColor"/>Enter Nova<ArrowRight size={16} className="transition group-hover:translate-x-1"/></Link><Link to="/dashboard" className="inline-flex items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/[.035] px-6 py-4 text-sm font-medium backdrop-blur-xl transition duration-300 hover:-translate-y-1 hover:border-white/20">Explore your progress <LineChart size={16}/></Link></div>
                    <div className="mt-10 flex flex-wrap gap-x-6 gap-y-3 text-xs text-slate-500">{["Adaptive explanations","Learning memory","Progress intelligence"].map(item=><span key={item} className="flex items-center gap-2"><CheckCircle2 size={14} className="text-emerald-400"/>{item}</span>)}</div>
                </div>

                <div className="relative flex min-h-[560px] items-center justify-center" style={orbStyle}>
                    <div className="nova-pulse absolute h-80 w-80 rounded-full bg-cyan-400/[.09] blur-[90px]"/><div className="nova-spin absolute h-[480px] w-[480px] rounded-full border border-white/[.06]"/><div className="nova-spin absolute h-[350px] w-[350px] rounded-full border border-dashed border-cyan-300/[.12]" style={{animationDirection:"reverse",animationDuration:"17s"}}/>
                    <div className="nova-float relative flex h-64 w-64 items-center justify-center rounded-[4.5rem] border border-white/10 bg-gradient-to-br from-cyan-300/20 via-slate-950 to-violet-500/20 shadow-[0_0_120px_rgba(34,211,238,.12)] backdrop-blur-2xl"><div className="absolute inset-5 rounded-[3.5rem] border border-white/[.07] bg-black/30"/><div className="relative flex h-28 w-28 items-center justify-center rounded-[2.2rem] border border-cyan-200/20 bg-white/[.055] shadow-[0_0_60px_rgba(34,211,238,.13)]"><Sparkles size={42}/></div><div className="absolute -right-10 top-10 rounded-2xl border border-white/10 bg-slate-950/80 p-4 shadow-2xl backdrop-blur-xl"><div className="flex items-center gap-3"><Zap size={17} className="text-cyan-300"/><div><div className="text-xs font-semibold">Adaptive</div><div className="text-[10px] text-slate-500">Teaching mode</div></div></div></div><div className="absolute -left-12 bottom-12 rounded-2xl border border-white/10 bg-slate-950/80 p-4 shadow-2xl backdrop-blur-xl"><div className="flex items-center gap-3"><Trophy size={17} className="text-violet-300"/><div><div className="text-xs font-semibold">Progress</div><div className="text-[10px] text-slate-500">Always moving</div></div></div></div></div>
                    <div className="absolute bottom-5 left-1/2 w-72 -translate-x-1/2 rounded-2xl border border-white/10 bg-slate-950/70 p-3 text-center text-xs text-slate-400 backdrop-blur-xl"><span className="text-white">{STEPS[step][1]}</span> · {STEPS[step][2]}</div>
                </div>
            </section>

            <section className="relative z-10 border-y border-white/[.06] bg-white/[.015]"><div className="mx-auto grid max-w-7xl grid-cols-2 md:grid-cols-4">{STEPS.map(([number,title,text],index)=><button key={number} onClick={()=>setStep(index)} className={`border-r border-white/[.06] p-6 text-left transition hover:bg-white/[.03] md:p-8 ${step===index?'bg-white/[.025]':''}`}><div className="text-xs text-slate-600">{number}</div><div className="mt-4 text-lg font-semibold">{title}</div><div className="mt-1 text-xs leading-5 text-slate-500">{text}</div></button>)}</div></section>

            <section className="relative z-10 mx-auto max-w-7xl px-6 py-28 lg:px-8"><div data-nova-reveal className="nova-reveal max-w-2xl"><div className="text-xs font-bold tracking-[.2em] text-cyan-300">THE NOVA SYSTEM</div><h2 className="mt-4 text-4xl font-semibold tracking-[-.04em] sm:text-5xl">A learning engine, not another chat box.</h2><p className="mt-5 text-base leading-7 text-slate-400">Everything is designed around the loop that matters: understand, practice, measure, adapt, repeat.</p></div><div className="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-3">{FEATURES.map(([icon,title,text],index)=><FeatureCard key={title} icon={icon} title={title} text={text} index={index}/>)}</div></section>

            <section className="relative z-10 mx-auto max-w-7xl px-6 pb-28 lg:px-8"><div data-nova-reveal className="nova-reveal overflow-hidden rounded-[2rem] border border-white/10 bg-gradient-to-br from-cyan-400/[.08] via-white/[.025] to-violet-400/[.08] p-8 sm:p-12"><div className="grid items-center gap-10 lg:grid-cols-[1fr_auto]"><div><div className="flex items-center gap-2 text-xs font-semibold tracking-[.18em] text-cyan-300"><Orbit size={15}/>READY WHEN YOU ARE</div><h2 className="mt-4 max-w-3xl text-3xl font-semibold tracking-[-.04em] sm:text-5xl">Stop collecting explanations. Start building understanding.</h2><p className="mt-5 max-w-2xl text-sm leading-6 text-slate-400">Open a session, choose what you need to learn, and let Nova turn the next hour into something measurable.</p></div><Link to="/chat" className="group inline-flex items-center justify-center gap-3 rounded-2xl bg-white px-6 py-4 text-sm font-bold text-slate-950 transition hover:-translate-y-1">Start a session <ArrowRight size={17} className="transition group-hover:translate-x-1"/></Link></div></div></section>

            <footer className="relative z-10 border-t border-white/[.06] px-6 py-10 lg:px-8"><div className="mx-auto flex max-w-7xl flex-col gap-5 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between"><div className="flex items-center gap-3"><NovaLogo className="h-7 w-7 rounded-lg object-contain"/><span>Nova AI · Adaptive learning</span></div><div className="flex gap-5"><Link to="/settings" className="hover:text-white">Settings</Link><Link to="/dashboard" className="hover:text-white">Dashboard</Link><Link to="/chat" className="hover:text-white">Learn</Link></div></div></footer>
        </main>
    );
}
