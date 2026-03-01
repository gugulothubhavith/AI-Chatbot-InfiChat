import { useState, FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { GoogleLogin, GoogleOAuthProvider } from "@react-oauth/google";
import { Logo } from "../components/Logo";

export default function Login() {
    console.log("DEBUG: VITE_GOOGLE_CLIENT_ID used:", import.meta.env.VITE_GOOGLE_CLIENT_ID);
    const { loginWithPassword, verifyOTP, loginWithGoogle, requestOTP } = useAuth();
    const navigate = useNavigate();

    // UI State
    const [step, setStep] = useState<"email_password" | "otp">("email_password");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [otp, setOtp] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    // Step 1: Login with Password
    const handleLoginWithPassword = async (e: FormEvent) => {
        if (e) e.preventDefault();
        setError("");
        setLoading(true);
        try {
            const res = await loginWithPassword(email, password);
            if (res.otp_required) {
                setStep("otp");
            } else {
                // Should not happen with new logic, but for robustness:
                navigate("/");
            }
        } catch (err: any) {
            const detail = err.response?.data?.detail;
            setError(detail || "Invalid email or password");
            // If the error indicates no password is set, we don't clear it yet so UI can show fallback
        } finally {
            setLoading(false);
        }
    };

    const handleLoginWithOTP = async (e?: FormEvent) => {
        if (e) e.preventDefault();
        if (!email) {
            setError("Please enter your email address first");
            return;
        }
        setError("");
        setLoading(true);
        try {
            await requestOTP(email);
            setStep("otp");
        } catch (err: any) {
            setError(err.response?.data?.detail || "Failed to send OTP. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    // Step 2: Verify OTP
    const handleVerifyOTP = async (e: FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);
        try {
            await verifyOTP(email, otp);
            navigate("/");
        } catch (err: any) {
            setError(err.response?.data?.detail || "Invalid OTP");
        } finally {
            setLoading(false);
        }
    };

    const handleGoogleSuccess = async (credentialResponse: any) => {
        try {
            await loginWithGoogle(credentialResponse.credential);
            navigate("/");
        } catch (err: any) {
            setError("Google login failed");
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4 transition-colors duration-300">
            <div className="w-full max-w-md">
                <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl dark:shadow-2xl p-8 border border-gray-200 dark:border-gray-700">
                    <div className="flex justify-center mb-8">
                        <Logo direction="col" iconSize={64} nameSize={28} gap={12} />
                    </div>

                    <p className="text-gray-500 dark:text-gray-400 text-center mb-8">
                        {step === "email_password" ? "Sign in to your account" : "Enter Verification Code"}
                    </p>

                    {error && (
                        <div className="bg-red-500/10 border border-red-500 text-red-500 px-4 py-3 rounded mb-4 text-sm">
                            {error}
                            {error.includes("no password set") && (
                                <button
                                    onClick={() => handleLoginWithOTP()}
                                    className="block mt-2 font-bold underline hover:text-red-600 transition-colors"
                                >
                                    Login with OTP instead →
                                </button>
                            )}
                        </div>
                    )}

                    {step === "email_password" ? (
                        <form onSubmit={handleLoginWithPassword} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Email</label>
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
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Password</label>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
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
                                    "Continue"
                                )}
                            </button>

                            <div className="text-center mt-4">
                                <button
                                    type="button"
                                    onClick={() => handleLoginWithOTP()}
                                    className="text-gray-500 hover:text-cyan-600 dark:text-gray-400 dark:hover:text-cyan-400 text-sm font-medium transition-colors"
                                >
                                    Login with OTP
                                </button>
                            </div>
                        </form>
                    ) : (
                        <form onSubmit={handleVerifyOTP} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                    One-Time Password
                                </label>
                                <input
                                    type="text"
                                    value={otp}
                                    onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                                    placeholder="123456"
                                    className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white text-center text-2xl tracking-widest focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all"
                                    required
                                    autoFocus
                                />
                                <p className="text-xs text-gray-500 mt-2 text-center">
                                    Check your email ({email}) for the code.
                                </p>
                            </div>
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full bg-gradient-to-r from-cyan-500 to-blue-600 text-white py-3 rounded-lg font-semibold hover:from-cyan-600 hover:to-blue-700 transition-all disabled:opacity-50 flex items-center justify-center"
                            >
                                {loading ? "Verifying..." : "Verify & Login"}
                            </button>
                            <button
                                type="button"
                                onClick={() => setStep("email_password")}
                                className="w-full text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white text-sm mt-4 font-medium"
                            >
                                ← Back to Login
                            </button>
                        </form>
                    )}

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
                                onError={() => setError("Google login failed")}
                                theme="filled_black"
                                size="large"
                                width="100%"
                            />
                        </GoogleOAuthProvider>
                    </div>

                    <p className="text-center text-gray-500 dark:text-gray-400 mt-8 text-sm">
                        Don't have an account?{" "}
                        <button 
                            onClick={() => navigate("/register")}
                            className="text-cyan-600 dark:text-cyan-400 font-semibold hover:underline"
                        >
                            Sign up
                        </button>
                    </p>
                </div>
            </div>
        </div>
    );
}

