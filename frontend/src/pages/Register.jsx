import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

const API_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");
const REGISTER_ENDPOINT = `${API_URL}/register`;
const MIN_PASSWORD_LENGTH = 6;

function ageFromDate(value) {
    if (!value) return null;
    const born = new Date(`${value}T00:00:00`);
    if (Number.isNaN(born.getTime())) return null;
    const today = new Date();
    let age = today.getFullYear() - born.getFullYear();
    const beforeBirthday = today.getMonth() < born.getMonth() ||
        (today.getMonth() === born.getMonth() && today.getDate() < born.getDate());
    if (beforeBirthday) age -= 1;
    return age;
}

export default function Register() {
    const navigate = useNavigate();
    const [email, setEmail] = useState("");
    const [dateOfBirth, setDateOfBirth] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const clientAge = ageFromDate(dateOfBirth);

    async function handleSubmit(event) {
        event.preventDefault();
        setError("");

        const normalizedEmail = email.trim().toLowerCase();
        if (!/^\S+@\S+\.\S+$/.test(normalizedEmail)) {
            setError("Please enter a valid email address.");
            return;
        }
        if (!dateOfBirth) {
            setError("Your date of birth is required to verify that you are at least 16.");
            return;
        }
        if (clientAge === null || clientAge < 16) {
            setError("Nova V1 is available to users aged 16 or older.");
            return;
        }
        if (password.length < MIN_PASSWORD_LENGTH) {
            setError(`Password must be at least ${MIN_PASSWORD_LENGTH} characters.`);
            return;
        }
        if (password !== confirmPassword) {
            setError("Passwords do not match.");
            return;
        }

        setLoading(true);
        try {
            const response = await fetch(REGISTER_ENDPOINT, {
                method: "POST",
                headers: { "Content-Type": "application/json", Accept: "application/json" },
                credentials: "include",
                body: JSON.stringify({ email: normalizedEmail, password, date_of_birth: dateOfBirth })
            });

            let data = {};
            try { data = await response.json(); } catch { /* handled below */ }
            if (!response.ok || data?.success === false) {
                const message = data?.error?.message || data?.detail || data?.message || "Unable to create your account.";
                throw new Error(typeof message === "string" ? message : "Unable to create your account.");
            }

            const session = data?.session;
            const user = data?.user || { email: normalizedEmail };
            localStorage.setItem("nova_user", JSON.stringify({ ...user, email: normalizedEmail }));
            if (session?.token) {
                localStorage.setItem("nova_session", JSON.stringify(session));
            }
            window.dispatchEvent(new CustomEvent("nova:auth", { detail: { type: "login", user } }));
            navigate("/chat", { replace: true });
        } catch (requestError) {
            setError(requestError?.message || "Unable to create your account.");
        } finally {
            setLoading(false);
        }
    }

    return (
        <main className="min-h-screen bg-slate-950 text-white flex items-center justify-center px-6 py-12">
            <section className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900/80 p-7 shadow-2xl">
                <div className="mb-7">
                    <p className="text-sm font-semibold text-cyan-400">NOVA AI</p>
                    <h1 className="mt-2 text-3xl font-bold">Create your account</h1>
                    <p className="mt-2 text-sm text-slate-400">Your date of birth is used only to verify the V1 minimum age. Nova does not store it.</p>
                </div>

                {error && (
                    <div role="alert" className="mb-5 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                    <label className="block">
                        <span className="mb-2 block text-sm text-slate-300">Email</span>
                        <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" autoComplete="email" required className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-cyan-400" />
                    </label>

                    <label className="block">
                        <span className="mb-2 block text-sm text-slate-300">Date of birth</span>
                        <input value={dateOfBirth} onChange={(e) => setDateOfBirth(e.target.value)} type="date" autoComplete="bday" required className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-cyan-400" />
                        <span className="mt-1 block text-xs text-slate-500">You must be at least 16 to use Nova V1.</span>
                    </label>

                    <label className="block">
                        <span className="mb-2 block text-sm text-slate-300">Password</span>
                        <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" autoComplete="new-password" minLength={MIN_PASSWORD_LENGTH} required className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-cyan-400" />
                    </label>

                    <label className="block">
                        <span className="mb-2 block text-sm text-slate-300">Confirm password</span>
                        <input value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} type="password" autoComplete="new-password" minLength={MIN_PASSWORD_LENGTH} required className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-cyan-400" />
                    </label>

                    <label className="flex items-start gap-3 rounded-xl border border-slate-800 bg-slate-950/60 p-3 text-xs text-slate-400">
                        <input type="checkbox" required className="mt-0.5" />
                        <span>I confirm that I am at least 16 years old and agree to Nova's <a className="text-cyan-400 hover:underline" href="/terms.html">Terms</a> and <a className="text-cyan-400 hover:underline" href="/privacy.html">Privacy Notice</a>.</span>
                    </label>

                    <button disabled={loading} type="submit" className="w-full rounded-xl bg-cyan-500 px-4 py-3 font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-50">
                        {loading ? "Creating account…" : "Create account"}
                    </button>
                </form>

                <p className="mt-6 text-center text-sm text-slate-400">
                    Already have an account? <Link to="/login" className="text-cyan-400 hover:underline">Sign in</Link>
                </p>
            </section>
        </main>
    );
}
