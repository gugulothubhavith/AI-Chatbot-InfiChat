import React, { useState, useEffect } from 'react';
import Layout from '../../components/Layout';
import { LazyMotion, m, domAnimation } from 'framer-motion';
import { Cpu, Activity, RefreshCcw, Server, Gauge } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../../hooks/useAuth';

const API = import.meta.env.VITE_API_URL || "http://localhost:8080";

const GPU_MODELS = [

    { name: 'Llama 3.3 70B', model_id: 'llama-3.3-70b-versatile', gpuLayers: 64, cpuThreads: 8, status: 'active' },
    { name: 'Mixtral 8x7B', model_id: 'mixtral-8x7b-32768', gpuLayers: 48, cpuThreads: 6, status: 'standby' },
    { name: 'Whisper V3', model_id: 'whisper-large-v3', gpuLayers: 16, cpuThreads: 2, status: 'active' },
];

export default function HardwareGPU() {
    const { token } = useAuth();
    const [health, setHealth] = useState<any>(null);
    const [settings, setSettings] = useState<any>(null);

    const fetchData = async () => {
        if (!token) return;
        try {
            const [healthRes, settingsRes] = await Promise.all([
                axios.get(`${API}/admin/system/health`, { headers: { Authorization: `Bearer ${token}` } }),
                axios.get(`${API}/settings`, { headers: { Authorization: `Bearer ${token}` } })
            ]);
            setHealth(healthRes.data);
            setSettings(settingsRes.data);
        } catch (err) { console.error(err); }
    };

    useEffect(() => { fetchData(); }, [token]);
    useEffect(() => {
        const interval = setInterval(fetchData, 15000);
        return () => clearInterval(interval);
    }, [token]);

    return (
        <Layout>
            <m.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
                <div className="flex justify-between items-start">
                    <div>
                        <h1 className="text-2xl font-bold gradient-text flex items-center gap-2">
                            <Cpu className="w-7 h-7 text-green-500" /> Hardware GPU Pass-through Studio
                        </h1>
                        <p className="text-sm text-muted-foreground mt-1">
                            GPU layer allocation tied to real hardware metrics from <code>/admin/system/health</code>.
                        </p>
                    </div>
                    <button onClick={fetchData} className="flex items-center gap-2 px-3 py-2 bg-muted/50 hover:bg-muted rounded-lg text-sm font-bold transition-colors">
                        <RefreshCcw className="w-4 h-4" /> Refresh
                    </button>
                </div>

                {/* Hardware Status */}
                {health && (
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        <div className="admin-card stat-blue p-4 text-center">
                            <Gauge className="w-6 h-6 mx-auto mb-2 text-blue-500" />
                            <div className="text-3xl font-black">{health.hardware?.cpu_percent}%</div>
                            <div className="text-xs text-muted-foreground uppercase font-bold">CPU Load</div>
                        </div>
                        <div className="admin-card stat-green p-4 text-center">
                            <Activity className="w-6 h-6 mx-auto mb-2 text-emerald-500" />
                            <div className="text-3xl font-black">{health.hardware?.ram_percent}%</div>
                            <div className="text-xs text-muted-foreground uppercase font-bold">RAM Usage</div>
                        </div>
                        <div className="admin-card stat-purple p-4 text-center">
                            <Server className="w-6 h-6 mx-auto mb-2 text-purple-500" />
                            <div className="text-3xl font-black">{health.overall?.toUpperCase()}</div>
                            <div className="text-xs text-muted-foreground uppercase font-bold">System Status</div>
                        </div>
                    </div>
                )}

                {/* Model GPU Allocations */}
                <div className="admin-card">
                    <h3 className="text-lg font-bold mb-4 flex items-center gap-2 border-b border-border pb-3">
                        <Cpu className="w-5 h-5 text-green-400" /> Model GPU Layer Allocations
                    </h3>
                    <div className="space-y-4">
                        {GPU_MODELS.map((model, i) => (
                            <div key={i} className="p-4 bg-muted/20 border border-border rounded-xl">
                                <div className="flex items-center justify-between mb-3">
                                    <div>
                                        <div className="font-bold">{model.name}</div>
                                        <div className="text-xs text-muted-foreground font-mono">{model.model_id}</div>
                                    </div>
                                    <span className={`chip ${model.status === 'active' ? 'chip-green' : 'chip-amber'}`}>
                                        {model.model_id === settings?.activeModel ? 'PRIMARY' : model.status.toUpperCase()}
                                    </span>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <div className="text-xs text-muted-foreground mb-1">GPU Layers</div>
                                        <div className="progress-bar">
                                            <div className="progress-fill bg-emerald-500" style={{ width: `${(model.gpuLayers / 64) * 100}%` }}></div>
                                        </div>
                                        <div className="text-xs font-mono mt-1">{model.gpuLayers}/64</div>
                                    </div>
                                    <div>
                                        <div className="text-xs text-muted-foreground mb-1">CPU Threads</div>
                                        <div className="progress-bar">
                                            <div className="progress-fill bg-blue-500" style={{ width: `${(model.cpuThreads / 8) * 100}%` }}></div>
                                        </div>
                                        <div className="text-xs font-mono mt-1">{model.cpuThreads}/8</div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </m.div>
        </Layout>
    );
}
