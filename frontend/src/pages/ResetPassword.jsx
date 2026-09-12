import { useState } from "react";

export default function ResetPassword() {
    const token = new URLSearchParams(window.location.search).get("token") || "";
    const [password, setPassword] = useState("");
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");
    async function submit(event) {
        event.preventDefault(); setMessage(""); setError("");
        try {
            const response = await fetch("https://nova-api-i07q.onrender.com/auth/reset-password", { method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" }, body: JSON.stringify({ token, password }) });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) throw new Error(data?.error?.message || "The reset link is invalid or expired.");
            setMessage("Your password has been changed. You can now sign in with the new password.");
        } catch (err) { setError(err.message); }
    }
    return <main className="min-h-screen bg-[#070a13] px-6 py-12 text-white"><div className="mx-auto max-w-md rounded-2xl border border-white/10 bg-white/[.04] p-6"><h1 className="text-2xl font-bold">Choose a new password</h1><form className="mt-6 space-y-4" onSubmit={submit}><input className="w-full rounded-xl border border-white/10 bg-black/20 p-3" type="password" minLength={6} required placeholder="New password" value={password} onChange={e => setPassword(e.target.value)}/><button className="w-full rounded-xl bg-white px-4 py-3 font-semibold text-slate-950">Update password</button></form>{message && <p className="mt-4 text-sm text-emerald-300">{message}</p>}{error && <p className="mt-4 text-sm text-red-300">{error}</p>}</div></main>;
}
