import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Brain, ChevronRight, GraduationCap, Menu, MessageCircle, Play, Sparkles, X, Zap } from "lucide-react";
import NovaLogo from "../components/NovaLogo";

const DEMO_CHAT = "/chat?demo=true";

const FLOATERS = [
    ["Explain photosynthesis", "Start with the big picture, then build the details."],
    ["Quiz me on algebra", "One question at a time. Difficulty adapts as you learn."],
    ["Help me understand", "Nova turns confusion into a guided learning path."],
];

export default function DemoHome() {
    const [menu, setMenu] = useState(false);
    const [active, setActive] = useState(0);
    const [pointer, setPointer] = useState({ x: 0, y: 0 });

    useEffect(() => {
        const move = e => setPointer({ x: (e.clientX / innerWidth - .5) * 2, y: (e.clientY / innerHeight - .5) * 2 });
        addEventListener("pointermove", move, { passive: true });
        const timer = setInterval(() => setActive(v => (v + 1) % FLOATERS.length), 3600);
        return () => { removeEventListener("pointermove", move); clearInterval(timer); };
    }, []);

    const orb = useMemo(() => ({ transform: `translate3d(${pointer.x * 12}px,${pointer.y * 12}px,0)` }), [pointer]);

    return <main className="min-h-screen overflow-hidden bg-[#050816] text-white selection:bg-cyan-300/20">
        <style>{`@keyframes novaFloat{0%,100%{transform:translateY(0)}50%{transform:translateY(-18px)}}@keyframes novaSpin{to{transform:rotate(360deg)}}@keyframes novaGlow{0%,100%{opacity:.35;transform:scale(.92)}50%{opacity:.8;transform:scale(1.08)}}@keyframes novaRise{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:none}}.nova-rise{animation:novaRise .9s cubic-bezier(.2,.8,.2,1) both}.nova-float{animation:novaFloat 7s ease-in-out infinite}.nova-spin{animation:novaSpin 26s linear infinite}.nova-glow{animation:novaGlow 5s ease-in-out infinite}@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important}}`}</style>
        <div className="fixed inset-0 pointer-events-none">
            <div className="absolute left-1/2 top-[-18rem] h-[48rem] w-[48rem] -translate-x-1/2 rounded-full bg-cyan-500/10 blur-[130px] nova-glow" />
            <div className="absolute right-[-12rem] top-[28%] h-[36rem] w-[36rem] rounded-full bg-violet-500/10 blur-[130px]" />
            <div className="absolute inset-0 opacity-[.025] [background-image:linear-gradient(rgba(255,255,255,.6)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.6)_1px,transparent_1px)] [background-size:72px_72px]" />
        </div>

        <header className="relative z-30 mx-auto flex max-w-7xl items-center justify-between px-5 py-5 sm:px-8 lg:px-10">
            <Link to="/" className="flex items-center gap-3"><NovaLogo className="h-10 w-10 rounded-xl"/><div><div className="text-sm font-bold tracking-[.2em]">NOVA</div><div className="text-[9px] tracking-[.25em] text-slate-500">AI LEARNING</div></div></Link>
            <nav className="hidden items-center gap-2 md:flex"><Link to={DEMO_CHAT} className="rounded-xl px-4 py-2.5 text-sm text-slate-300 hover:bg-white/5 hover:text-white">Try Nova</Link><Link to="/login" className="rounded-xl px-4 py-2.5 text-sm text-slate-300 hover:bg-white/5 hover:text-white">Sign in</Link><Link to="/register" className="rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:-translate-y-0.5">Create account</Link></nav>
            <button onClick={() => setMenu(v => !v)} className="rounded-xl border border-white/10 p-2.5 md:hidden" aria-label="Menu">{menu ? <X size={20}/> : <Menu size={20}/>}</button>
        </header>
        {menu && <div className="relative z-30 mx-4 rounded-2xl border border-white/10 bg-slate-950/90 p-3 backdrop-blur-xl md:hidden"><Link onClick={()=>setMenu(false)} to={DEMO_CHAT} className="block rounded-xl px-4 py-3 text-sm hover:bg-white/5">Try Nova</Link><Link onClick={()=>setMenu(false)} to="/login" className="block rounded-xl px-4 py-3 text-sm hover:bg-white/5">Sign in</Link><Link onClick={()=>setMenu(false)} to="/register" className="block rounded-xl bg-white px-4 py-3 text-sm font-semibold text-slate-950">Create account</Link></div>}

        <section className="relative z-10 mx-auto grid min-h-[calc(100vh-80px)] max-w-7xl items-center gap-12 px-5 pb-20 pt-8 sm:px-8 lg:grid-cols-[1fr_.9fr] lg:px-10 lg:pt-0">
            <div className="nova-rise max-w-3xl">
                <div className="inline-flex items-center gap-2 rounded-full border border-cyan-300/15 bg-cyan-300/[.06] px-3.5 py-2 text-xs font-medium text-cyan-200 backdrop-blur-xl"><span className="h-2 w-2 animate-pulse rounded-full bg-cyan-300"/>Meet your adaptive AI tutor</div>
                <h1 className="mt-7 text-5xl font-semibold leading-[.92] tracking-[-.06em] sm:text-7xl lg:text-[6.2rem]">Learn smarter.<span className="block bg-gradient-to-r from-cyan-200 via-white to-violet-300 bg-clip-text text-transparent">With Nova.</span></h1>
                <p className="mt-7 max-w-2xl text-base leading-7 text-slate-400 sm:text-lg">Ask anything. Get unstuck. Practice until it clicks. Nova adapts the way it teaches to the way you learn.</p>
                <div className="mt-9 flex flex-col gap-3 sm:flex-row"><Link to={DEMO_CHAT} className="group inline-flex items-center justify-center gap-2 rounded-2xl bg-white px-6 py-4 text-sm font-bold text-slate-950 shadow-2xl transition hover:-translate-y-1"><Play size={16} fill="currentColor"/>Try the demo <ArrowRight size={16} className="transition group-hover:translate-x-1"/></Link><Link to="/register" className="inline-flex items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/[.04] px-6 py-4 text-sm font-medium backdrop-blur-xl transition hover:-translate-y-1 hover:bg-white/[.07]">Unlock your learning memory <Sparkles size={16}/></Link></div>
                <div className="mt-10 grid grid-cols-3 gap-3 max-w-xl"><div className="rounded-2xl border border-white/[.07] bg-white/[.025] p-4"><Brain className="text-cyan-300" size={18}/><div className="mt-3 text-xs font-semibold">Adaptive</div><div className="mt-1 text-[10px] text-slate-500">Teaching</div></div><div className="rounded-2xl border border-white/[.07] bg-white/[.025] p-4"><Zap className="text-violet-300" size={18}/><div className="mt-3 text-xs font-semibold">Interactive</div><div className="mt-1 text-[10px] text-slate-500">Practice</div></div><div className="rounded-2xl border border-white/[.07] bg-white/[.025] p-4"><GraduationCap className="text-emerald-300" size={18}/><div className="mt-3 text-xs font-semibold">Student-first</div><div className="mt-1 text-[10px] text-slate-500">Learning</div></div></div>
            </div>

            <div className="relative flex min-h-[430px] items-center justify-center lg:min-h-[600px]" style={orb}>
                <div className="absolute h-72 w-72 rounded-full bg-cyan-400/10 blur-[90px] nova-glow"/>
                <div className="nova-spin absolute h-[430px] w-[430px] rounded-full border border-white/[.07]"/>
                <div className="nova-spin absolute h-[320px] w-[320px] rounded-full border border-dashed border-cyan-300/[.14]" style={{animationDirection:"reverse",animationDuration:"18s"}}/>
                <div className="nova-float relative w-[min(78vw,330px)] rounded-[2.8rem] border border-white/10 bg-gradient-to-br from-cyan-300/15 via-slate-950 to-violet-500/15 p-5 shadow-[0_0_100px_rgba(34,211,238,.12)] backdrop-blur-2xl">
                    <div className="rounded-[2.2rem] border border-white/[.07] bg-black/25 p-5">
                        <div className="flex items-center gap-3"><div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-cyan-300/10 text-cyan-200"><MessageCircle size={20}/></div><div><div className="text-sm font-semibold">Nova</div><div className="text-[10px] text-emerald-300">Ready to teach</div></div></div>
                        <div className="mt-6 rounded-2xl border border-white/[.07] bg-white/[.035] p-4"><div className="text-[10px] font-bold uppercase tracking-[.18em] text-cyan-300">You</div><div className="mt-2 text-sm text-slate-200">{FLOATERS[active][0]}</div></div>
                        <div className="mt-3 rounded-2xl border border-white/[.07] bg-white/[.035] p-4"><div className="text-[10px] font-bold uppercase tracking-[.18em] text-violet-300">Nova</div><div className="mt-2 text-sm leading-6 text-slate-300">{FLOATERS[active][1]}</div></div>
                        <Link to={DEMO_CHAT} className="mt-4 flex items-center justify-center gap-2 rounded-xl bg-white py-3 text-xs font-bold text-slate-950">Open demo <ArrowRight size={14}/></Link>
                    </div>
                </div>
            </div>
        </section>

        <section className="relative z-10 border-y border-white/[.06] bg-white/[.015] px-5 py-16 sm:px-8 lg:px-10"><div className="mx-auto grid max-w-7xl gap-6 md:grid-cols-3"><div><div className="text-xs font-bold tracking-[.2em] text-cyan-300">01 · ASK</div><h2 className="mt-3 text-2xl font-semibold">Start with confusion.</h2><p className="mt-2 text-sm leading-6 text-slate-500">No perfect prompt required. Just tell Nova what you are trying to understand.</p></div><div><div className="text-xs font-bold tracking-[.2em] text-violet-300">02 · ADAPT</div><h2 className="mt-3 text-2xl font-semibold">Nova meets you there.</h2><p className="mt-2 text-sm leading-6 text-slate-500">Explanations, examples and practice can change as your understanding changes.</p></div><div><div className="text-xs font-bold tracking-[.2em] text-emerald-300">03 · MASTER</div><h2 className="mt-3 text-2xl font-semibold">Make it stick.</h2><p className="mt-2 text-sm leading-6 text-slate-500">Create an account when you want memory, progress tracking and a personal learning space.</p></div></div></section>
        <footer className="relative z-10 px-5 py-10 text-center text-xs text-slate-600">Nova AI · Adaptive learning · <Link className="hover:text-slate-300" to="/register">Create your free learning space</Link></footer>
    </main>;
}
