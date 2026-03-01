import { motion } from "framer-motion";
import { Shield, Zap, Cpu, Users, Globe, Database, Lock, Code, Bot } from "lucide-react";
import { Logo } from "../components/Logo";

const features = [
    {
        icon: <Bot className="h-6 w-6 text-indigo-500" />,
        title: "Multi-Agent Swarm",
        description: "A coordinated team of Planner, Coder, and Reviewer agents working together to solve complex tasks."
    },
    {
        icon: <Database className="h-6 w-6 text-cyan-500" />,
        title: "Advanced RAG",
        description: "Talk to your documents securely using vector embeddings and semantic retrieval via ChromaDB."
    },
    {
        icon: <Shield className="h-6 w-6 text-green-500" />,
        title: "Privacy First",
        description: "Built-in PII scrubbing and data sovereignty. Your data never leaves your infrastructure."
    },
    {
        icon: <Zap className="h-6 w-6 text-orange-500" />,
        title: "High Performance",
        description: "Ultra-fast inference powered by Groq and optimized local models for instant responses."
    }
];

const techStack = [
    { category: "Frontend", tech: "React 18, Vite, TypeScript, Tailwind CSS" },
    { category: "Backend", tech: "FastAPI, Python 3.11, Uvicorn" },
    { category: "Storage", tech: "PostgreSQL, Redis, ChromaDB" },
    { category: "AI Engines", tech: "Groq, Gemini, Ollama, Faster Whisper" },
    { category: "Infrastructure", tech: "Docker, Docker Compose" }
];

export default function About() {
    return (
        <div className="flex flex-col h-full bg-white dark:bg-[#0B1120] text-gray-900 dark:text-gray-100 overflow-hidden transition-colors duration-300">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 bg-white/80 dark:bg-[#0B1120]/50 backdrop-blur-md sticky top-0 z-10 border-b border-white/0 dark:border-white/0">
                <div className="flex items-center gap-3">
                    <div>
                        <Logo hideIcon={true} nameSize={22} className="ml-[-8px]" />
                    </div>
                </div>
            </div>

            <div className="flex-1 p-6 md:p-12 overflow-y-auto bg-gray-50 dark:bg-[#0B1120]">
                <div className="max-w-4xl mx-auto space-y-16">

                    {/* Header Section */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5 }}
                        className="text-center space-y-4"
                    >
                        <div className="flex justify-center mb-6">
                            {/* Replaced large logo with standardized top-left header logo */}
                        </div>
                        <h1 className="sr-only">InfiChat</h1>
                        <p className="text-xl text-gray-500 dark:text-gray-400 max-w-2xl mx-auto leading-relaxed">
                            A production-grade, self-hosted platform designed for total privacy,
                            unmatched performance, and autonomous problem solving.
                        </p>
                    </motion.div>

                    {/* Mission Section */}
                    <section className="grid md:grid-cols-2 gap-12 items-center">
                        <motion.div
                            initial={{ opacity: 0, x: -20 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            viewport={{ once: true }}
                            className="space-y-6"
                        >
                            <h2 className="text-3xl font-bold flex items-center gap-3">
                                <Lock className="h-7 w-7 text-indigo-500" /> Our Mission
                            </h2>
                            <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                                In an era of centralized AI surveillance, we believe intelligence should be
                                <strong> sovereign</strong>. Our mission is to provide individuals and
                                enterprises with the tools to run cutting-edge Generative AI entirely on
                                their own hardware, ensuring complete data ownership and security.
                            </p>
                            <div className="flex flex-wrap gap-4">
                                <div className="px-4 py-2 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 flex items-center gap-2">
                                    <Globe className="h-4 w-4 text-blue-500" /> 100% Offline Capable
                                </div>
                                <div className="px-4 py-2 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 flex items-center gap-2">
                                    <Shield className="h-4 w-4 text-green-500" /> Zero 3rd Party Tracking
                                </div>
                            </div>
                        </motion.div>

                        <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            whileInView={{ opacity: 1, scale: 1 }}
                            viewport={{ once: true }}
                            className="bg-gradient-to-br from-indigo-600 to-purple-700 rounded-3xl p-8 text-white shadow-2xl relative overflow-hidden group"
                        >
                            <div className="absolute top-0 right-0 -mt-4 -mr-4 h-32 w-32 bg-white/10 rounded-full blur-3xl group-hover:bg-white/20 transition-all"></div>
                            <h3 className="text-2xl font-bold mb-4">Enterprise Grade</h3>
                            <ul className="space-y-3 opacity-90">
                                <li className="flex items-center gap-2">
                                    <div className="h-1.5 w-1.5 rounded-full bg-white"></div>
                                    Multi-tenant Authentication
                                </li>
                                <li className="flex items-center gap-2">
                                    <div className="h-1.5 w-1.5 rounded-full bg-white"></div>
                                    Isolated Docker Sandbox for Code
                                </li>
                                <li className="flex items-center gap-2">
                                    <div className="h-1.5 w-1.5 rounded-full bg-white"></div>
                                    Real-time Web Research Integration
                                </li>
                                <li className="flex items-center gap-2">
                                    <div className="h-1.5 w-1.5 rounded-full bg-white"></div>
                                    Multimodal (Vision & Voice) support
                                </li>
                            </ul>
                        </motion.div>
                    </section>

                    {/* Features Grid */}
                    <section className="space-y-8">
                        <h2 className="text-3xl font-bold text-center">Core Capabilities</h2>
                        <div className="grid sm:grid-cols-2 gap-6">
                            {features.map((f, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, y: 20 }}
                                    whileInView={{ opacity: 1, y: 0 }}
                                    viewport={{ once: true }}
                                    transition={{ delay: i * 0.1 }}
                                    className="p-6 bg-white dark:bg-gray-800/50 rounded-2xl border border-gray-200 dark:border-gray-700 hover:border-indigo-500/50 transition-all group"
                                >
                                    <div className="mb-4">{f.icon}</div>
                                    <h4 className="text-xl font-bold mb-2 group-hover:text-indigo-500 transition-colors">{f.title}</h4>
                                    <p className="text-gray-500 dark:text-gray-400 text-sm leading-relaxed">{f.description}</p>
                                </motion.div>
                            ))}
                        </div>
                    </section>

                    {/* Tech Stack Section */}
                    <section className="bg-gray-100 dark:bg-gray-800/30 rounded-3xl p-8 md:p-12 space-y-8">
                        <div className="text-center space-y-2">
                            <h2 className="text-3xl font-bold">Cutting Edge Tech Stack</h2>
                            <p className="text-gray-500">Built with the latest and most robust open-source technologies.</p>
                        </div>
                        <div className="grid gap-4">
                            {techStack.map((item, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, x: -10 }}
                                    whileInView={{ opacity: 1, x: 0 }}
                                    viewport={{ once: true }}
                                    className="flex flex-col md:flex-row md:items-center gap-2 md:gap-6 p-4 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700"
                                >
                                    <div className="md:w-32 font-bold text-indigo-500 text-sm uppercase tracking-widest">{item.category}</div>
                                    <div className="flex-1 font-mono text-sm text-gray-600 dark:text-gray-400">{item.tech}</div>
                                </motion.div>
                            ))}
                        </div>
                    </section>

                    {/* Architecture Section */}
                    <section className="text-center space-y-8">
                        <h2 className="text-3xl font-bold">Resilient Architecture</h2>
                        <div className="p-8 bg-white dark:bg-gray-800 rounded-2xl border border-dashed border-gray-300 dark:border-gray-700 flex items-center justify-center">
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                                <div className="flex flex-col items-center gap-2">
                                    <Cpu className="h-8 w-8 text-gray-400" />
                                    <span className="text-xs font-medium">FastAPI Core</span>
                                </div>
                                <div className="flex flex-col items-center gap-2">
                                    <Users className="h-8 w-8 text-gray-400" />
                                    <span className="text-xs font-medium">React Logic</span>
                                </div>
                                <div className="flex flex-col items-center gap-2">
                                    <Database className="h-8 w-8 text-gray-400" />
                                    <span className="text-xs font-medium">Postgres DB</span>
                                </div>
                                <div className="flex flex-col items-center gap-2">
                                    <Code className="h-8 w-8 text-gray-400" />
                                    <span className="text-xs font-medium">Docker Sandbox</span>
                                </div>
                            </div>
                        </div>
                    </section>

                    {/* Footer Info */}
                    <footer className="pt-8 border-t border-gray-200 dark:border-gray-800 text-center text-gray-500 text-sm">
                        <p>&copy; 2025 InfiChat Project. Built for the privacy-conscious community.</p>
                    </footer>

                </div>
            </div>
        </div>
    );
}
