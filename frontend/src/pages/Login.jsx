import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { LogIn } from "lucide-react";

const API_URL = "http://127.0.0.1:8000";

export default function Login() {

    const navigate = useNavigate();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    async function handleLogin(e) {

        e.preventDefault();

        setError("");

        if (!email.trim() || !password) {
            setError("Please enter your email and password.");
            return;
        }

        setLoading(true);

        try {

            const response = await fetch(
                `${API_URL}/login`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        email: email.trim(),
                        password
                    })
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail || "Login failed."
                );
            }

            if (!data.success) {
                setError(
                    data.message || "Incorrect email or password."
                );

                return;
            }

            localStorage.setItem(
                "nova_user",
                JSON.stringify({
                    email: email.trim()
                })
            );

            navigate("/dashboard");

        } catch (error) {

            setError(
                error.message ||
                "Unable to connect to Nova."
            );

        } finally {

            setLoading(false);

        }
    }

    return (

        <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center p-6">

            <div className="w-full max-w-md">

                <div className="text-center mb-8">

                    <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-blue-600 mb-4">
                        <LogIn size={26} />
                    </div>

                    <h1 className="text-4xl font-bold">
                        Welcome back
                    </h1>

                    <p className="text-gray-400 mt-2">
                        Sign in to continue learning with Nova.
                    </p>

                </div>

                <form
                    onSubmit={handleLogin}
                    className="bg-gray-900 border border-gray-800 rounded-2xl p-7 space-y-5"
                >

                    <div>

                        <label className="block text-sm text-gray-400 mb-2">
                            Email
                        </label>

                        <input
                            type="email"
                            value={email}
                            onChange={e =>
                                setEmail(e.target.value)
                            }
                            placeholder="you@example.com"
                            autoComplete="email"
                            className="
                                w-full
                                bg-gray-950
                                border
                                border-gray-700
                                rounded-xl
                                px-4
                                py-3
                                outline-none
                                focus:border-blue-500
                            "
                        />

                    </div>

                    <div>

                        <label className="block text-sm text-gray-400 mb-2">
                            Password
                        </label>

                        <input
                            type="password"
                            value={password}
                            onChange={e =>
                                setPassword(e.target.value)
                            }
                            placeholder="Your password"
                            autoComplete="current-password"
                            className="
                                w-full
                                bg-gray-950
                                border
                                border-gray-700
                                rounded-xl
                                px-4
                                py-3
                                outline-none
                                focus:border-blue-500
                            "
                        />

                    </div>

                    {error && (

                        <div className="bg-red-950 border border-red-800 text-red-300 rounded-xl p-3 text-sm">
                            {error}
                        </div>

                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="
                            w-full
                            bg-blue-600
                            hover:bg-blue-700
                            disabled:bg-gray-700
                            rounded-xl
                            py-3
                            font-semibold
                            transition
                        "
                    >
                        {loading
                            ? "Signing in..."
                            : "Sign in"
                        }
                    </button>

                    <p className="text-center text-gray-400 text-sm">

                        Don't have an account?{" "}

                        <Link
                            to="/register"
                            className="text-blue-400 hover:text-blue-300"
                        >
                            Create one
                        </Link>

                    </p>

                </form>

            </div>

        </div>

    );
}