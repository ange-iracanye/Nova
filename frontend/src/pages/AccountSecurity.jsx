import { useEffect, useState } from "react";

const API = "https://nova-api-i07q.onrender.com";

async function call(path, body) {
    const raw = localStorage.getItem("nova_session");
    let token = "";
    try { token = JSON.parse(raw || "{}").token || ""; } catch {}
    const headers = { "Content-Type": "application/json", Accept: "application/json" };
    if (token) headers.Authorization = `Bearer ${token}`;
    const response = await fetch(`${API}${path}`, { method: "POST", headers, credentials: "include", body: JSON.stringify(body || {}) });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data?.error?.message || data?.message || "Nova could not complete that request.");
    return data;
}

export default function AccountSecurity() {
    const [status, setStatus] = useState(null);
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");
    const [currentPassword, setCurrentPassword] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [newEmail, setNewEmail] = useState("");

    useEffect(() => {
        fetch(`${API}/auth/status`, { credentials: "include" })
            .then(r => r.json())
            .then(data => setStatus(data))
            .catch(() => {});
    }, []);

    async function run(action) {
        setMessage(""); setError("");
        try { const data = await action(); setMessage(data.message || "Done."); return data; }
        catch (err) { setError(err.message || "Something went wrong."); }
    }

    return <main className="min-h-screen bg-[#070a13] px-6 py-12 text-white">
        <div className="mx-auto max-w-2xl space-y-6">
            <div><p className="text-sm text-cyan-300">Nova account</p><h1 className="mt-1 text-3xl font-bold">Security & account</h1><p className="mt-2 text-slate-400">Manage verification, your password, and your email address.</p></div>
            {status && <div className="rounded-2xl border border-white/10 bg-white/[.04] p-5"><div className="text-sm text-slate-400">Signed in as</div><div className="mt-1 font-semibold">{status.email}</div><div className="mt-3 text-sm">Email verification: <span className={status.email_verified ? "text-emerald-300" : "text-amber-300"}>{status.email_verified ? "Verified" : "Not verified"}</span></div>{!status.email_verified && <button className="mt-3 rounded-xl bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950" onClick={() => run(() => call("/auth/request-verification"))}>Send verification email</button>}</div>}
            <section className="rounded-2xl border border-white/10 bg-white/[.04] p-5"><h2 className="text-lg font-semibold">Change password</h2><div className="mt-4 grid gap-3"><input className="rounded-xl border border-white/10 bg-black/20 p-3" type="password" placeholder="Current password" value={currentPassword} onChange={e => setCurrentPassword(e.target.value)}/><input className="rounded-xl border border-white/10 bg-black/20 p-3" type="password" placeholder="New password" value={newPassword} onChange={e => setNewPassword(e.target.value)}/><button className="rounded-xl bg-white px-4 py-2 font-semibold text-slate-950" onClick={() => run(() => call("/auth/change-password", { current_password: currentPassword, new_password: newPassword }))}>Change password</button></div></section>
            <section className="rounded-2xl border border-white/10 bg-white/[.04] p-5"><h2 className="text-lg font-semibold">Change email</h2><p className="mt-1 text-sm text-slate-400">A confirmation link will be sent to the new address. Your existing account data is migrated after confirmation.</p><div className="mt-4 flex gap-3"><input className="min-w-0 flex-1 rounded-xl border border-white/10 bg-black/20 p-3" type="email" placeholder="new@email.com" value={newEmail} onChange={e => setNewEmail(e.target.value)}/><button className="rounded-xl bg-white px-4 py-2 font-semibold text-slate-950" onClick={() => run(() => call("/auth/request-email-change", { new_email: newEmail }))}>Confirm by email</button></div></section>
            {message && <div className="rounded-xl border border-emerald-400/20 bg-emerald-400/10 p-4 text-sm text-emerald-200">{message}</div>}
            {error && <div className="rounded-xl border border-red-400/20 bg-red-400/10 p-4 text-sm text-red-200">{error}</div>}
        </div>
    </main>;
}
