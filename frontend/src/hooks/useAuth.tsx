import { createContext, useContext, useState, ReactNode, useEffect } from "react";
import axios from "axios";

interface User {
    email: string;
    user_id: string;
    picture?: string;
}

interface AuthContextType {
    token: string | null;
    user: User | null;
    requestOTP: (email: string) => Promise<void>;
    verifyOTP: (email: string, otp: string) => Promise<void>;
    loginWithPassword: (email: string, password: string) => Promise<{ otp_required: boolean }>;
    loginWithGoogle: (credential: string) => Promise<void>;
    register: (email: string, password: string) => Promise<void>;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [token, setToken] = useState(() => localStorage.getItem("token"));
    const [user, setUser] = useState<User | null>(() => {
        const savedUser = localStorage.getItem("user");
        return savedUser ? JSON.parse(savedUser) : null;
    });

    // Sync token with axios headers
    const updateAuthHeader = (newToken: string | null) => {
        if (newToken) {
            axios.defaults.headers.common["Authorization"] = `Bearer ${newToken}`;
        } else {
            delete axios.defaults.headers.common["Authorization"];
        }
    };

    // Initialize header
    updateAuthHeader(token);

    // Response interceptor to handle 401s
    useEffect(() => {
        const interceptor = axios.interceptors.response.use(
            (response) => response,
            (error) => {
                if (error.response?.status === 401) {
                    logout();
                    // Optional: force reload to login
                    window.location.href = "/login";
                }
                return Promise.reject(error);
            }
        );
        return () => axios.interceptors.response.eject(interceptor);
    }, []);

    // Fetch user details to ensure we have the ID (fixes N/A issue)
    useEffect(() => {
        if (!token) return;

        const fetchMe = async () => {
            try {
                const res = await axios.get("/api/auth/me");
                console.log("DEBUG: /api/auth/me response:", res.data);
                // res.data contains user_id, email, avatar_url
                setUser((prev) => {
                    const updated = {
                        ...prev,
                        email: res.data.email,
                        user_id: res.data.user_id,
                        picture: res.data.avatar_url || prev?.picture // Use avatar_url from backend
                    } as User;
                    console.log("DEBUG: Updated user state from /me:", updated);
                    localStorage.setItem("user", JSON.stringify(updated));
                    return updated;
                });
            } catch (err) {
                console.error("Failed to refresh user data", err);
            }
        };

        fetchMe();
    }, [token]);

    const requestOTP = async (email: string) => {
        await axios.post("/api/auth/request-otp", { email });
    };

    const loginWithPassword = async (email: string, password: string) => {
        const res = await axios.post("/api/auth/login", { email, password });
        return res.data; // { otp_required: true, message: "..." }
    };

    const verifyOTP = async (email: string, otp: string) => {
        const res = await axios.post("/api/auth/verify-otp", { email, otp });
        const newToken = res.data.access_token;
        const userData = {
            email: res.data.email,
            user_id: res.data.user_id,
            picture: res.data.avatar_url
        };

        setToken(newToken);
        setUser(userData);
        localStorage.setItem("token", newToken);
        localStorage.setItem("user", JSON.stringify(userData));
        updateAuthHeader(newToken);
    };

    const loginWithGoogle = async (credential: string) => {
        const res = await axios.post("/api/auth/google", { credential });
        console.log("DEBUG: Google Login response:", res.data);
        const newToken = res.data.access_token;
        const userData = {
            email: res.data.user.email,
            user_id: res.data.user.id || '',
            picture: res.data.avatar_url || res.data.user.picture
        };
        console.log("DEBUG: Setting userData from Google:", userData);

        setToken(newToken);
        setUser(userData);
        localStorage.setItem("token", newToken);
        localStorage.setItem("user", JSON.stringify(userData));
        updateAuthHeader(newToken);
    };

    const register = async (email: string, password: string) => {
        await axios.post("/api/auth/register", { email, password });
        // NOTE: Registration no longer automatically logs the user in.
    };

    const logout = () => {
        setToken(null);
        setUser(null);
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        updateAuthHeader(null);
    };

    return (
        <AuthContext.Provider value={{ token, user, requestOTP, verifyOTP, loginWithPassword, loginWithGoogle, register, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error("useAuth must be inside AuthProvider");
    return ctx;
}
