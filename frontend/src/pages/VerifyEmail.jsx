import { useEffect, useState } from "react";

export default function VerifyEmail() {
    const token = new URLSearchParams(window.location.search).get("token") || "";
    const [state, setState] = useState("verifying");
    useEffect(() => {
        if (!token) { setState("invalid"); return; }
        fetch("https://nova-api-i07q.onrender.com/auth/verify-email", { method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" }, body: JSON.stringify({ token }) })
            .then(async response => { const data = await response.json().catch(() => ({})); if (!response.ok) throw new Error(data?.error?.message || "The verification link is invalid or expired."); setState("verified"); })
            .catch(() => setState("invalid"));
    }, [token]);
    return <main className="min-h-screen bg-[#070a13] px-6 py-12 text-white"><div className="mx-auto max-w-md rounded-2xl border border-white/10 bg-white/[.04] p-6 text-center"><h1 className="text-2xl font-bold">{state === "verifying" ? "Verifying your email..." : state === "verified" ? "Email verified" : "Verification failed"}</h1><p className="mt-3 text-sm text-slate-400">{state === "verified" ? "Your Nova email address is now verified." : state === "invalid" ? "This link is invalid or has expired. Request a new verification email from account security." : "Nova is checking the verification link."}</p></div></main>;
}
