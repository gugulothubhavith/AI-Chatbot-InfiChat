import React, { useState, useEffect } from 'react';
import Layout from '../../components/Layout';
import { LazyMotion, m, domAnimation } from 'framer-motion';
import { Bot, Save, Cpu, Zap, Sliders, Key, Shield } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../../hooks/useAuth';

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8080";

const availableModels = [

    { id: "llama-3.3-70b-versatile", name: "Llama 3.3 70B (Smart)", provider: "Groq", type: "LLM" },
    { id: "mixtral-8x7b-32768", name: "Mixtral 8x7B", provider: "Groq", type: "LLM" },
    { id: "gemma2-9b-it", name: "Gemma 2 9B", provider: "Groq", type: "LLM" },
    { id: "whisper-large-v3", name: "Whisper V3", provider: "Groq (Audio)", type: "STT" }
];

export default function ModelHub() {
    const { token } = useAuth();
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    
    // Model Settings State
    const [activeModel, setActiveModel] = useState("llama-3.3-70b-versatile");
    const [temperature, setTemperature] = useState(0.7);
    const [maxTokens, setMaxTokens] = useState(2048);
    const [customInstructions, setCustomInstructions] = useState("");
    

    useEffect(() => {
        if (!token) return;
        axios.get(`${API_URL}/settings`, { headers: { Authorization: `Bearer ${token}` } })
            .then(res => {
                const s = res.data;
                if (s.activeModel) setActiveModel(s.activeModel);
                if (s.temperature) setTemperature(s.temperature);
                if (s.maxTokens) setMaxTokens(s.maxTokens);
                if (s.customInstructions !== undefined) setCustomInstructions(s.customInstructions);
                setLoading(false);
            })
            .catch(err => {
                console.error("Failed to fetch settings", err);
                setLoading(false);
            });
    }, [token]);

    const handleSave = async () => {
        setSaving(true);
        try {
            await axios.post(`${API_URL}/settings`, {
                activeModel,
                temperature,
                maxTokens,
                customInstructions
            }, { headers: { Authorization: `Bearer ${token}` } });
            alert("Model Configuration Saved Successfully!");
        } catch (err) {
            console.error(err);
            alert("Failed to save configuration.");
        }
        setSaving(false);
    };

    return (
<LazyMotion features={domAnimation}>
        <Layout>
            <m.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6 pb-20">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div>
                        <h1 className="text-2xl font-bold gradient-text flex items-center gap-2">
                            <Bot className="w-7 h-7 text-blue-500" /> AI Model Configuration Hub
                        </h1>
                        <p className="text-sm text-muted-foreground mt-1">
                            Dynamically switch active LLMs, tune hyperparameters, and configure System Prompts globally.
                        </p>
                    </div>
                    
                    <button 
                        onClick={handleSave} 
                        disabled={saving}
                        className="btn-primary py-2 px-6 flex items-center gap-2 shadow-blue-500/20 shadow-lg"
                    >
                        {saving ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Save className="w-4 h-4" />}
                        {saving ? "Deploying..." : "Deploy Configuration"}
                    </button>
                </div>

                {loading ? (
                    <div className="h-64 flex items-center justify-center">
                        <div className="w-8 h-8 rounded-full border-2 border-blue-500 border-t-transparent animate-spin"></div>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
                        
                        {/* Column 1: Active Model Selection */}
                        <div className="xl:col-span-2 space-y-6">
                            <div className="admin-card">
                                <h3 className="text-lg font-bold mb-4 flex items-center gap-2 border-b border-border pb-3">
                                    <Cpu className="w-5 h-5 text-indigo-400" /> Inference Engine Selection
                                </h3>
                                
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {availableModels.map(model => (
                                        <div 
                                            key={model.id}
                                            onClick={() => setActiveModel(model.id)}
                                            className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${activeModel === model.id ? 'border-indigo-500 bg-indigo-500/10 shadow-lg shadow-indigo-500/10' : 'border-border bg-muted/20 hover:border-indigo-500/50 hover:bg-muted/50'}`}
                                        >
                                            <div className="flex justify-between items-start mb-2">
                                                <div className="font-bold text-foreground">{model.name}</div>
                                                <div className={`text-[10px] font-bold px-2 py-0.5 rounded ${model.type === 'LLM' ? 'bg-blue-500/20 text-blue-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
                                                    {model.type}
                                                </div>
                                            </div>
                                            <div className="text-xs text-muted-foreground mb-3">{model.id}</div>
                                            <div className="flex items-center gap-1.5 text-[11px] font-medium text-slate-400">
                                                <Zap className="w-3 h-3 text-amber-500" /> Powered by {model.provider}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="admin-card">
                                <h3 className="text-lg font-bold mb-4 flex items-center gap-2 border-b border-border pb-3">
                                    <Shield className="w-5 h-5 text-emerald-400" /> Global System Prompt
                                </h3>
                                <p className="text-xs text-muted-foreground mb-3">
                                    This prompt will be prepended to all autonomous agents and user conversations system-wide.
                                </p>
                                <textarea 
                                    value={customInstructions}
                                    onChange={(e) => setCustomInstructions(e.target.value)}
                                    placeholder="e.g. You are InfiChat, a radically secure, hyper-intelligent AI..."
                                    className="w-full h-32 bg-background border border-border rounded-xl p-3 text-sm focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 resize-none font-mono"
                                />
                            </div>
                        </div>

                        {/* Column 2: Parameters */}
                        <div className="space-y-6">
                            <div className="admin-card">
                                <h3 className="text-lg font-bold mb-4 flex items-center gap-2 border-b border-border pb-3">
                                    <Sliders className="w-5 h-5 text-pink-400" /> Hyperparameters
                                </h3>
                                
                                <div className="space-y-5">
                                    <div>
                                        <div className="flex justify-between text-sm mb-2">
                                            <span className="font-medium">Temperature</span>
                                            <span className="text-pink-400 font-mono">{temperature.toFixed(2)}</span>
                                        </div>
                                        <input 
                                            type="range" min="0" max="2" step="0.05" 
                                            value={temperature} onChange={(e) => setTemperature(parseFloat(e.target.value))}
                                            className="w-full accent-pink-500"
                                        />
                                        <div className="flex justify-between text-[10px] text-muted-foreground mt-1">
                                            <span>Deterministic</span>
                                            <span>Creative</span>
                                        </div>
                                    </div>

                                    <div>
                                        <div className="flex justify-between text-sm mb-2">
                                            <span className="font-medium">Max Output Tokens</span>
                                            <span className="text-pink-400 font-mono">{maxTokens}</span>
                                        </div>
                                        <input 
                                            type="range" min="256" max="8192" step="256" 
                                            value={maxTokens} onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                                            className="w-full accent-pink-500"
                                        />
                                        <div className="flex justify-between text-[10px] text-muted-foreground mt-1">
                                            <span>Short</span>
                                            <span>Long</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="admin-card border-amber-500/20 relative overflow-hidden">
                                <div className="absolute top-0 right-0 w-32 h-32 bg-amber-500/10 blur-3xl rounded-full"></div>
                                <h3 className="text-lg font-bold mb-4 flex items-center gap-2 border-b border-border pb-3 relative z-10">
                                    <Key className="w-5 h-5 text-amber-500" /> Provider API Keys
                                </h3>
                                <p className="text-xs text-muted-foreground mb-4 relative z-10">
                                    API keys are securely vaulted in the backend environment mapping. To rotate keys, request a secure terminal session.
                                </p>
                                
                                <div className="space-y-3 relative z-10">
                                    <div className="bg-background border border-border rounded-lg p-2.5 flex justify-between items-center">
                                        <div className="flex items-center gap-2">
                                            <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]"></div>
                                            <span className="text-sm font-semibold">Groq API</span>
                                        </div>
                                        <span className="text-xs font-mono text-muted-foreground pr-2">Vaulted</span>
                                    </div>
                                    <div className="bg-background border border-border rounded-lg p-2.5 flex justify-between items-center opacity-50">
                                        <div className="flex items-center gap-2">
                                            <div className="w-2 h-2 rounded-full bg-red-500"></div>
                                            <span className="text-sm font-semibold">OpenAI API</span>
                                        </div>
                                        <span className="text-[10px] px-2 py-0.5 rounded bg-muted">Not Configured</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                    </div>
                )}
            </m.div>
        </Layout>
    </LazyMotion>
);
}
