import { useState, FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { GoogleLogin, GoogleOAuthProvider } from "@react-oauth/google";
import { Logo } from "../components/Logo";

export default function Register() {
    const { register, loginWithGoogle } = useAuth();
    const navigate = useNavigate();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setError("");

        if (password !== confirmPassword) {
            setError("Passwords do not match");
            return;
        }

        setLoading(true);

        try {
            await register(email, password);
            setSuccess(true);
        } catch (err: any) {
            setError(err.response?.data?.detail || "Registration failed");
        } finally {
            setLoading(false);
        }
    };

    const handleGoogleSuccess = async (credentialResponse: any) => {
        try {
            await loginWithGoogle(credentialResponse.credential);
            navigate("/");
        } catch (err: any) {
            setError("Google sign up failed");
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4 transition-colors duration-300">
            <div className="w-full max-w-md">
                <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl dark:shadow-2xl p-8 border border-gray-200 dark:border-gray-700">
                    <div className="flex justify-center mb-8">
                        <Logo direction="col" iconSize={64} nameSize={28} gap={12} />
                    </div>

                    <p className="text-gray-500 dark:text-gray-400 text-center mb-8">Create your account</p>

                    {error && (
                        <div className="bg-red-500/10 border border-red-500 text-red-400 px-4 py-3 rounded mb-4 text-sm text-center">
                            {error}
                        </div>
                    )}

                    {success ? (
                        <div className="text-center py-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
                            <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 p-5 rounded-xl mb-8 shadow-sm">
                                <h3 className="font-semibold text-xl mb-2 flex items-center justify-center gap-2">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6">
                                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                                        <polyline points="22 4 12 14.01 9 11.01"></polyline>
                                    </svg>
                                    Registration Successful!
                                </h3>
                                <p className="text-sm">Your account has been created. You can now sign in with your credentials.</p>
                            </div>
                            <button
                                onClick={() => navigate("/login")}
                                className="w-full bg-cyan-600 hover:bg-cyan-700 text-white py-3 rounded-xl font-semibold shadow-lg shadow-cyan-500/20 transition-all flex items-center justify-center"
                            >
                                Go to Sign In
                            </button>
                        </div>
                    ) : (
                        <>
                            <form onSubmit={handleSubmit} className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                                        Email
                                    </label>
                                    <input
                                        type="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        placeholder="Email address"
                                        className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-xl text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all text-sm"
                                        required
                                    />
                                </div>
        
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                                        Password
                                    </label>
                                    <input
                                        type="password"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        placeholder="Password"
                                        className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-xl text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all text-sm"
                                        required
                                    />
                                </div>
        
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                                        Confirm Password
                                    </label>
                                    <input
                                        type="password"
                                        value={confirmPassword}
                                        onChange={(e) => setConfirmPassword(e.target.value)}
                                        placeholder="Password"
                                        className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-xl text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all text-sm"
                                        required
                                    />
                                </div>
        
                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full bg-cyan-600 hover:bg-cyan-700 text-white py-2.5 rounded-xl font-semibold shadow-lg shadow-cyan-500/20 transition-all disabled:opacity-50 flex items-center justify-center mt-2"
                                >
                                    {loading ? (
                                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                    ) : (
                                        "Sign Up"
                                    )}
                                </button>
                            </form>
        
                            <div className="relative my-8">
                                <div className="absolute inset-0 flex items-center">
                                    <div className="w-full border-t border-gray-300 dark:border-gray-600"></div>
                                </div>
                                <div className="relative flex justify-center text-sm">
                                    <span className="px-2 bg-white dark:bg-gray-800 text-gray-500 dark:text-gray-400">Or continue with</span>
                                </div>
                            </div>
        
                            <div className="flex justify-center">
                                <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID}>
                                    <GoogleLogin
                                        onSuccess={handleGoogleSuccess}
                                        onError={() => setError("Google sign up failed")}
                                        theme="filled_black"
                                        size="large"
                                        width="100%"
                                    />
                                </GoogleOAuthProvider>
                            </div>
        
                            <p className="text-center text-gray-500 dark:text-gray-400 mt-8 text-sm">
                                Already have an account?{" "}
                                <button 
                                    onClick={() => navigate("/login")}
                                    className="text-cyan-600 dark:text-cyan-400 font-semibold hover:underline"
                                >
                                    Sign in
                                </button>
                            </p>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}
