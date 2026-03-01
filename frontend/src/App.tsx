import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { AuthProvider, useAuth } from "./hooks/useAuth";
import { ThemeProvider } from "./context/ThemeContext";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Chat from "./pages/Chat";
import CodeAgent from "./pages/CodeAgent";
import RAG from "./pages/RAG";
import ImageGen from "./pages/ImageGen";
import Snippets from "./pages/Snippets";
import About from "./pages/About";
import SharedChatView from "./pages/SharedChatView";
import Sidebar from "./components/Sidebar";

// Protected route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
    const { token } = useAuth();
    return token ? <>{children}</> : <Navigate to="/login" />;
}

// Layout with sidebar
function DashboardLayout({ children }: { children: React.ReactNode }) {
    return (
        <div className="flex h-screen bg-gray-50 dark:bg-gray-950">
            <Sidebar />
            <main className="flex-1 overflow-y-auto">{children}</main>
        </div>
    );
}

function App() {
    const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";

    return (
        <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
            <ThemeProvider>
                <AuthProvider>
                    <BrowserRouter>
                        <Routes>
                            <Route path="/login" element={<Login />} />
                            <Route path="/register" element={<Register />} />
                            <Route path="/share/:token" element={<SharedChatView />} />

                            <Route
                                path="/:sessionId?"
                                element={
                                    <ProtectedRoute>
                                        <DashboardLayout>
                                            <Chat />
                                        </DashboardLayout>
                                    </ProtectedRoute>
                                }
                            />

                            <Route
                                path="/code"
                                element={
                                    <ProtectedRoute>
                                        <DashboardLayout>
                                            <CodeAgent />
                                        </DashboardLayout>
                                    </ProtectedRoute>
                                }
                            />

                            <Route
                                path="/rag"
                                element={
                                    <ProtectedRoute>
                                        <DashboardLayout>
                                            <RAG />
                                        </DashboardLayout>
                                    </ProtectedRoute>
                                }
                            />

                            <Route
                                path="/image"
                                element={
                                    <ProtectedRoute>
                                        <DashboardLayout>
                                            <ImageGen />
                                        </DashboardLayout>
                                    </ProtectedRoute>
                                }
                            />



                            <Route
                                path="/snippets"
                                element={
                                    <ProtectedRoute>
                                        <DashboardLayout>
                                            <Snippets />
                                        </DashboardLayout>
                                    </ProtectedRoute>
                                }
                            />
                            <Route
                                path="/about"
                                element={
                                    <ProtectedRoute>
                                        <DashboardLayout>
                                            <About />
                                        </DashboardLayout>
                                    </ProtectedRoute>
                                }
                            />
                        </Routes>
                    </BrowserRouter>
                </AuthProvider>
            </ThemeProvider>
        </GoogleOAuthProvider>
    );
}

export default App;
