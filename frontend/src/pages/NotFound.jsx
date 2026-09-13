import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Brain, Home, Search, Sparkles } from "lucide-react";

export default function NotFound() {
    const navigate = useNavigate();
    const [pulse, setPulse] = useState(0);

    useEffect(() => {
        const id = window.setInterval(() => setPulse(value => (value + 1) % 3), 900);
        return () => window.clearInterval(id);
    }, []);

    return (
        <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#05070d] px-6 text-white">
            <div className="pointer-events-none absolute inset-0 opacity-70" aria-hidden="true">
                <div className="absolute left-1/2 top-1/2 h-[520px] w-[520px] -translate-x-1/2 -translate-y-1/2 rounded-full border border-cyan-400/10 shadow-[0_0_120px_rgba(34,211,238,.08)]" />
                <div className="absolute left-1/2 top-1/2 h-[360px] w-[360px] -translate-x-1/2 -translate-y-1/2 rounded-full border border-violet-400/10" />
                <div className="absolute left-1/2 top-1/2 h-24 w-24 -translate-x-1/2 -translate-y-1/2 rounded-full bg-cyan-400/10 blur-2xl" />
            </div>
            <section className="relative z-10 w-full max-w-2xl rounded-[32px] border border-white/[.08] bg-white/[.025] p-8 text-center shadow-[0_30px_120px_rgba(0,0,0,.45)] backdrop-blur-xl sm:p-12">
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl border border-cyan-400/20 bg-cyan-400/[.06] text-cyan-300 shadow-[0_0_40px_rgba(34,211,238,.08)]">
                    <Brain size={30} />
                </div>
                <div className="mt-7 font-mono text-xs tracking-[.35em] text-cyan-400/70">NOVA NAVIGATION ANOMALY</div>
                <h1 className="mt-4 text-7xl font-black tracking-tighter sm:text-9xl">404</h1>
                <p className="mx-auto mt-5 max-w-lg text-base leading-7 text-slate-400">This coordinate does not exist in Nova. The rest of the system is still online.</p>
                <div className="mx-auto mt-7 flex max-w-xs items-center justify-center gap-2 rounded-2xl border border-white/[.06] bg-black/20 px-4 py-3 font-mono text-[10px] text-slate-500">
                    <Search size={13} className="text-cyan-400" />
                    <span>scanning{'.'.repeat(pulse + 1)}</span>
                    <Sparkles size={13} className="text-violet-400" />
                </div>
                <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
                    <button onClick={() => navigate(-1)} className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/[.08] bg-white/[.035] px-5 py-3 text-sm font-semibold text-slate-300 transition hover:-translate-y-1 hover:bg-white/[.07] hover:text-white">
                        <ArrowLeft size={16} /> Go back
                    </button>
                    <button onClick={() => navigate('/')} className="inline-flex items-center justify-center gap-2 rounded-xl bg-cyan-500 px-5 py-3 text-sm font-bold text-slate-950 transition hover:-translate-y-1 hover:bg-cyan-400">
                        <Home size={16} /> Return home
                    </button>
                </div>
            </section>
        </main>
    );
}
