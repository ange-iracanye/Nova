import { useState } from "react";

export default function ForgotPassword() {
    const [email, setEmail] = useState("");
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");
    async function submit(event) {
        event.preventDefault(); setMessage(""); setError("");
        try {
            const response = await fetch("https://nova-api-i07q.onrender.com/auth/forgot-password", { method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" }, body: JSON.stringify({ email }) });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) throw new Error(data?.error?.message || data?.message || "Nova could not send the reset email.");
            setMessage(data.message || "If an account exists for that email, a reset link has been sent.");
        } catch (err) { setError(err.message); }
    }
    return <main className="min-h-screen bg-[#070a13] px-6 py-12 text-white"><div className="mx-auto max-w-md rounded-2xl border border-white/10 bg-white/[.04] p-6"><h1 className="text-2xl font-bold">Reset your password</h1><p className="mt-2 text-sm text-slate-400">Enter your Nova email and we will send a one-time reset link.</p><form className="mt-6 space-y-4" onSubmit={submit}><input className="w-full rounded-xl border border-white/10 bg-black/20 p-3" type="email" required placeholder="you@example.com" value={email} onChange={e => setEmail(e.target.value)}/><button className="w-full rounded-xl bg-white px-4 py-3 font-semibold text-slate-950">Send reset link</button></form>{message && <p className="mt-4 text-sm text-emerald-300">{message}</p>}{error && <p className="mt-4 text-sm text-red-300">{error}</p>}</div></main>;
}
