import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { UserPlus } from "lucide-react";

const API_URL = "http://127.0.0.1:8000";

export default function Register() {

const navigate = useNavigate();

const [email, setEmail] = useState("");
const [password, setPassword] = useState("");

const [loading, setLoading] = useState(false);
const [error, setError] = useState("");
const [success, setSuccess] = useState("");

async function handleRegister(e) {

    e.preventDefault();

    setError("");
    setSuccess("");

    const cleanEmail = email.trim().toLowerCase();

    if (!cleanEmail || !password) {

        setError(
            "Please enter an email and password."
        );

        return;
    }

    if (!cleanEmail.includes("@")) {

        setError(
            "Please enter a valid email address."
        );

        return;
    }

    if (password.length < 6) {

        setError(
            "Password must be at least 6 characters."
        );

        return;
    }

    setLoading(true);

    try {

        const response = await fetch(
            `${API_URL}/register`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    email: cleanEmail,
                    password
                })
            }
        );

        let data;

        try {

            data = await response.json();

        } catch {

            throw new Error(
                "The server returned an invalid response."
            );

        }

        if (!response.ok) {

            throw new Error(
                data.detail ||
                data.message ||
                "Registration failed."
            );

        }

        if (!data.success) {

            setError(
                data.message ||
                "An account with this email may already exist."
            );

            return;
        }

        /*
         * Keep the same localStorage format
         * used by Login.jsx and Chat.jsx.
         */
        localStorage.setItem(
            "nova_user",
            JSON.stringify({
                email: cleanEmail
            })
        );

        setSuccess(
            "Account created successfully!"
        );

        /*
         * Give the success message a moment
         * before entering Nova.
         */
        setTimeout(() => {

            navigate("/chat");

        }, 500);

    }
    catch (error) {

        console.error(
            "Registration error:",
            error
        );

        setError(
            error.message ||
            "Unable to connect to Nova."
        );

    }
    finally {

        setLoading(false);

    }

}


return (

    <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center p-6">

        <div className="w-full max-w-md">

            <div className="text-center mb-8">

                <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-blue-600 mb-4">

                    <UserPlus size={26} />

                </div>

                <h1 className="text-4xl font-bold">
                    Create your account
                </h1>

                <p className="text-gray-400 mt-2">
                    Start learning with Nova.
                </p>

            </div>


            <form
                onSubmit={handleRegister}
                className="
                    bg-gray-900
                    border
                    border-gray-800
                    rounded-2xl
                    p-7
                    space-y-5
                "
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
                        disabled={loading}
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
                            disabled:opacity-50
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
                        placeholder="Create a password"
                        autoComplete="new-password"
                        disabled={loading}
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
                            disabled:opacity-50
                        "
                    />

                </div>


                {error && (

                    <div
                        className="
                            bg-red-950
                            border
                            border-red-800
                            text-red-300
                            rounded-xl
                            p-3
                            text-sm
                        "
                    >
                        {error}
                    </div>

                )}


                {success && (

                    <div
                        className="
                            bg-green-950
                            border
                            border-green-800
                            text-green-300
                            rounded-xl
                            p-3
                            text-sm
                        "
                    >
                        {success}
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
                        ? "Creating account..."
                        : "Create account"
                    }

                </button>


                <p className="text-center text-gray-400 text-sm">

                    Already have an account?{" "}

                    <Link
                        to="/login"
                        className="
                            text-blue-400
                            hover:text-blue-300
                        "
                    >
                        Sign in
                    </Link>

                </p>

            </form>

        </div>

    </div>

);


}
