import { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import axios from 'axios';
import { m, LazyMotion, domAnimation, AnimatePresence } from "framer-motion";
import {
    Plus, Edit3, Trash2, Check, X, DollarSign, ToggleLeft as ToggleIcon,
    ToggleRight, Globe, Lock, Star, Crown, ArrowUp, ArrowDown,
    Save, Loader2, AlertTriangle, Zap, Sparkles, Infinity
} from 'lucide-react';
import Layout from '../../components/Layout';

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8080";

interface SubscriptionPlan {
    id: string;
    name: string;
    description: string | null;
    price_monthly: number;
    features: Record<string, boolean>;
    limits: Record<string, number>;
    is_active: boolean;
    is_admin_plan: boolean;
    is_public: boolean;
    sort_order: number;
    created_at?: string;
}

interface PlanFormData {
    name: string;
    description: string;
    price_monthly: number;
    features: Record<string, boolean>;
    limits: Record<string, number>;
    is_admin_plan: boolean;
    is_public: boolean;
    sort_order: number;
}

const DEFAULT_LIMITS: Record<string, number> = {
    chat_messages_per_day: 20,
    chat_tokens_per_day: 10000,
    deep_research_per_month: 0,
    deep_thinking_per_month: 0,
    image_gen_per_month: 0,
    code_executions_per_month: 0,
    rag_documents: 3,
    max_tokens_per_response: 1024,
    max_context_length: 4096,
};

// Keys must match the backend's canonical feature names (see
// subscription_service.FEATURE_PATH_MAP / GATED_FEATURES). The entitlement gate
// denies any name it does not recognise, so a plan saved with a key like
// "image_generation" or "code_agent" returns HTTP 402 for that feature even
// though the toggle reads as enabled here.
const DEFAULT_FEATURES: Record<string, boolean> = {
    chat_messages: true,
    deep_research: false,
    deep_thinking: false,
    image_gen: false,
    code_executions: false,
    rag: true,
    voice: true,
    web_search: false,
};

function getPlanIcon(name: string) {
    switch (name) {
        case 'Free': return Zap;
        case 'Starter': return Star;
        case 'Pro': return Sparkles;
        case 'Max': return Crown;
        case 'Enterprise': return Infinity;
        default: return DollarSign;
    }
}

function getPlanColor(name: string) {
    switch (name) {
        case 'Free': return '#6b7280';
        case 'Starter': return '#3b82f6';
        case 'Pro': return '#8b5cf6';
        case 'Max': return '#f59e0b';
        case 'Enterprise': return '#ef4444';
        default: return '#6b7280';
    }
}

function PlanModal({ plan, onClose, onSave }: { plan?: SubscriptionPlan | null; onClose: () => void; onSave: (data: PlanFormData, planId?: string) => void }) {
    const [form, setForm] = useState<PlanFormData>({
        name: plan?.name || '',
        description: plan?.description || '',
        price_monthly: plan?.price_monthly || 0,
        features: plan?.features || { ...DEFAULT_FEATURES },
        limits: plan?.limits || { ...DEFAULT_LIMITS },
        is_admin_plan: plan?.is_admin_plan || false,
        is_public: plan?.is_public ?? true,
        sort_order: plan?.sort_order || 0,
    });
    const [saving, setSaving] = useState(false);

    const handleSave = async () => {
        setSaving(true);
        await onSave(form, plan?.id);
        setSaving(false);
        onClose();
    };

    const toggleFeature = (key: string) => {
        setForm(prev => ({
            ...prev,
            features: { ...prev.features, [key]: !prev.features[key] },
        }));
    };

    const updateLimit = (key: string, value: number) => {
        setForm(prev => ({
            ...prev,
            limits: { ...prev.limits, [key]: value },
        }));
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" onClick={onClose}>
            <m.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                className="bg-card rounded-3xl w-full max-w-2xl max-h-[85vh] overflow-y-auto shadow-2xl"
                onClick={e => e.stopPropagation()}
            >
                <div className="sticky top-0 bg-card z-10 flex items-center justify-between p-6 border-b">
                    <h2 className="text-xl font-bold">{plan ? `Edit ${plan.name}` : 'Create Plan'}</h2>
                    <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-xl"><X className="w-5 h-5" /></button>
                </div>

                <div className="p-6 space-y-6">
                    {/* Basic Info */}
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-foreground mb-1">Plan Name</label>
                            <input value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))}
                                className="w-full px-3 py-2 rounded-xl border border-border focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none" />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-foreground mb-1">Price (₹/month)</label>
                            <input type="number" value={form.price_monthly} onChange={e => setForm(p => ({ ...p, price_monthly: parseInt(e.target.value) || 0 }))}
                                className="w-full px-3 py-2 rounded-xl border border-border focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none" />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-foreground mb-1">Description</label>
                        <textarea value={form.description} onChange={e => setForm(p => ({ ...p, description: e.target.value }))}
                            className="w-full px-3 py-2 rounded-xl border border-border focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none" rows={2} />
                    </div>

                    {/* Features */}
                    <div>
                        <h3 className="font-semibold text-gray-800 mb-3">Feature Access</h3>
                        <div className="grid grid-cols-2 gap-3">
                            {Object.entries(DEFAULT_FEATURES).map(([key]) => (
                                <button key={key} onClick={() => toggleFeature(key)}
                                    className={`flex items-center gap-3 p-3 rounded-xl border transition-all ${form.features[key] ? 'border-green-300 bg-green-50' : 'border-border'}`}>
                                    {form.features[key] ? <Check className="w-4 h-4 text-green-600" /> : <X className="w-4 h-4 text-muted-foreground" />}
                                    <span className="text-sm font-medium capitalize">{key.replace(/_/g, ' ')}</span>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Limits */}
                    <div>
                        <h3 className="font-semibold text-gray-800 mb-3">Usage Limits</h3>
                        <div className="grid grid-cols-2 gap-4">
                            {Object.entries(DEFAULT_LIMITS).map(([key]) => (
                                <div key={key}>
                                    <label className="block text-xs font-medium text-muted-foreground mb-1 capitalize">{key.replace(/_/g, ' ')}</label>
                                    <input type="number" value={form.limits[key] || 0}
                                        onChange={e => updateLimit(key, parseInt(e.target.value) || 0)}
                                        className="w-full px-3 py-2 rounded-xl border border-border focus:border-indigo-500 outline-none text-sm" />
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Flags */}
                    <div className="flex items-center gap-6">
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input type="checkbox" checked={form.is_admin_plan}
                                onChange={e => setForm(p => ({ ...p, is_admin_plan: e.target.checked }))}
                                className="rounded accent-red-500" />
                            <span className="text-sm font-medium">Admin Plan (Unlimited)</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input type="checkbox" checked={form.is_public}
                                onChange={e => setForm(p => ({ ...p, is_public: e.target.checked }))}
                                className="rounded accent-indigo-500" />
                            <span className="text-sm font-medium">Public (user-subscribable)</span>
                        </label>
                    </div>
                </div>

                <div className="sticky bottom-0 bg-card p-4 border-t flex justify-end gap-3">
                    <button onClick={onClose} className="px-4 py-2 rounded-xl border border-border text-sm font-medium hover:bg-muted">Cancel</button>
                    <button onClick={handleSave} disabled={saving}
                        className="px-6 py-2 rounded-xl bg-indigo-600 text-white text-sm font-bold hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2">
                        {saving && <Loader2 className="w-4 h-4 animate-spin" />}
                        <Save className="w-4 h-4" /> {plan ? 'Update Plan' : 'Create Plan'}
                    </button>
                </div>
            </m.div>
        </div>
    );
}

export default function SubscriptionPlans() {
    const { token } = useAuth();
    const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
    const [loading, setLoading] = useState(true);
    const [modalOpen, setModalOpen] = useState(false);
    const [editingPlan, setEditingPlan] = useState<SubscriptionPlan | null>(null);
    const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' } | null>(null);
    const [deletingId, setDeletingId] = useState<string | null>(null);

    const fetchPlans = async () => {
        try {
            const res = await axios.get(`${API_URL}/subscription/admin/plans`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            setPlans(res.data);
        } catch (err) {
            console.error('Failed to fetch plans', err);
            showToast('Failed to load plans', 'error');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { if (token) fetchPlans(); }, [token]);

    const showToast = (msg: string, type: 'success' | 'error') => {
        setToast({ msg, type });
        setTimeout(() => setToast(null), 3000);
    };

    const handleCreate = () => {
        setEditingPlan(null);
        setModalOpen(true);
    };

    const handleEdit = (plan: SubscriptionPlan) => {
        setEditingPlan(plan);
        setModalOpen(true);
    };

    const handleSave = async (data: PlanFormData, planId?: string) => {
        try {
            if (planId) {
                await axios.put(`${API_URL}/subscription/admin/plans/${planId}`, data, {
                    headers: { Authorization: `Bearer ${token}` },
                });
                showToast('Plan updated', 'success');
            } else {
                await axios.post(`${API_URL}/subscription/admin/plans`, data, {
                    headers: { Authorization: `Bearer ${token}` },
                });
                showToast('Plan created', 'success');
            }
            fetchPlans();
        } catch (err: any) {
            showToast(err.response?.data?.detail || 'Operation failed', 'error');
        }
    };

    const handleToggleActive = async (plan: SubscriptionPlan) => {
        try {
            await axios.put(`${API_URL}/subscription/admin/plans/${plan.id}`, { is_active: !plan.is_active }, {
                headers: { Authorization: `Bearer ${token}` },
            });
            showToast(`${plan.name} ${plan.is_active ? 'deactivated' : 'activated'}`, 'success');
            fetchPlans();
        } catch (err) {
            showToast('Failed to toggle', 'error');
        }
    };

    const handleDelete = async (planId: string) => {
        try {
            await axios.delete(`${API_URL}/subscription/admin/plans/${planId}`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            showToast('Plan deleted', 'success');
            setDeletingId(null);
            fetchPlans();
        } catch (err) {
            showToast('Failed to delete', 'error');
        }
    };

    return (
<LazyMotion features={domAnimation}>
        <Layout>
            <div className="p-6 space-y-6">
                {/* Toast */}
                <AnimatePresence>
                    {toast && (
                        <m.div
                            initial={{ opacity: 0, y: -20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            className={`fixed top-5 right-5 z-50 px-4 py-3 rounded-xl shadow-xl text-sm font-medium ${
                                toast.type === 'success' ? 'bg-green-50 border border-green-200 text-green-800' : 'bg-red-50 border border-red-200 text-red-800'
                            }`}
                        >
                            {toast.msg}
                        </m.div>
                    )}
                </AnimatePresence>

                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-foreground">Subscription Plans</h1>
                        <p className="text-sm text-muted-foreground mt-1">Manage pricing tiers, features, and usage limits</p>
                    </div>
                    <button onClick={handleCreate}
                        className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-bold hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-200">
                        <Plus className="w-4 h-4" /> Create Plan
                    </button>
                </div>

                {/* Plan Cards */}
                {loading ? (
                    <div className="flex justify-center py-20">
                        <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {plans.sort((a, b) => a.sort_order - b.sort_order).map((plan, idx) => {
                            const PlanIcon = getPlanIcon(plan.name);
                            const planColor = getPlanColor(plan.name);
                            return (
                                <m.div
                                    key={plan.id}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: idx * 0.05 }}
                                    className={`rounded-2xl p-5 border transition-all hover:shadow-lg ${
                                        plan.is_active ? 'bg-card' : 'bg-muted opacity-75'
                                    }`}
                                >
                                    {/* Card Header */}
                                    <div className="flex items-start justify-between mb-4">
                                        <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: `${planColor}15` }}>
                                                <PlanIcon className="w-5 h-5" style={{ color: planColor }} />
                                            </div>
                                            <div>
                                                <h3 className="font-bold text-foreground">{plan.name}</h3>
                                                <p className="text-xs text-muted-foreground">{plan.is_admin_plan ? 'Admin Only' : plan.is_public ? 'Public' : 'Hidden'}</p>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <div className="text-lg font-black text-foreground">₹{plan.price_monthly}</div>
                                            {plan.price_monthly > 0 && <div className="text-[10px] text-muted-foreground">/month</div>}
                                        </div>
                                    </div>

                                    {plan.is_admin_plan && (
                                        <div className="mb-3 px-2.5 py-1 rounded-lg bg-red-50 border border-red-200 text-xs font-semibold text-red-600 flex items-center gap-1.5">
                                            <Infinity className="w-3.5 h-3.5" /> Unlimited Everything
                                        </div>
                                    )}

                                    {/* Features Summary */}
                                    <div className="space-y-1.5 mb-4">
                                        {Object.entries(plan.features || {}).slice(0, 5).map(([key, enabled]) => (
                                            <div key={key} className="flex items-center gap-2 text-xs">
                                                {enabled ?
                                                    <Check className="w-3 h-3 text-green-500" /> :
                                                    <X className="w-3 h-3 text-gray-300" />
                                                }
                                                <span className={enabled ? 'text-foreground' : 'text-muted-foreground'}>
                                                    {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                                </span>
                                            </div>
                                        ))}
                                        {Object.keys(plan.features || {}).length > 5 && (
                                            <span className="text-xs text-muted-foreground">+{Object.keys(plan.features).length - 5} more</span>
                                        )}
                                    </div>

                                    {/* Limits Bar */}
                                    <div className="space-y-1 mb-4">
                                        {Object.entries(plan.limits || {}).slice(0, 3).map(([key, value]) => (
                                            <div key={key} className="flex justify-between text-[11px]">
                                                <span className="text-muted-foreground capitalize">{key.replace(/_/g, ' ')}</span>
                                                <span className="font-medium text-foreground">{value >= 999999 ? '∞' : value.toLocaleString()}</span>
                                            </div>
                                        ))}
                                    </div>

                                    {/* Actions */}
                                    <div className="flex items-center gap-2 pt-3 border-t border-border">
                                        <button onClick={() => handleToggleActive(plan)}
                                            className={`p-2 rounded-lg transition-all ${plan.is_active ? 'text-green-600 hover:bg-green-50' : 'text-muted-foreground hover:bg-gray-100'}`}
                                            title={plan.is_active ? 'Deactivate' : 'Activate'}>
                                            {plan.is_active ? <ToggleRight className="w-4 h-4" /> : <ToggleIcon className="w-4 h-4" />}
                                        </button>
                                        <button onClick={() => handleEdit(plan)}
                                            className="p-2 rounded-lg text-muted-foreground hover:bg-gray-100 transition-all" title="Edit">
                                            <Edit3 className="w-4 h-4" />
                                        </button>
                                        <button onClick={() => setDeletingId(plan.id)}
                                            className="p-2 rounded-lg text-red-500 hover:bg-red-50 transition-all ml-auto" title="Delete">
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </m.div>
                            );
                        })}
                    </div>
                )}

                {/* Modal */}
                {modalOpen && <PlanModal plan={editingPlan} onClose={() => setModalOpen(false)} onSave={handleSave} />}

                {/* Delete Confirmation */}
                <AnimatePresence>
                    {deletingId && (
                        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm" onClick={() => setDeletingId(null)}>
                            <m.div
                                initial={{ scale: 0.9 }}
                                animate={{ scale: 1 }}
                                className="bg-card rounded-2xl p-6 max-w-sm w-full shadow-2xl"
                                onClick={e => e.stopPropagation()}
                            >
                                <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
                                <h3 className="text-lg font-bold text-center mb-2">Delete Plan?</h3>
                                <p className="text-sm text-muted-foreground text-center mb-6">This action cannot be undone. Users on this plan will lose their subscription.</p>
                                <div className="flex gap-3">
                                    <button onClick={() => setDeletingId(null)} className="flex-1 py-2.5 rounded-xl border border-border text-sm font-medium">Cancel</button>
                                    <button onClick={() => handleDelete(deletingId)} className="flex-1 py-2.5 rounded-xl bg-red-600 text-white text-sm font-bold">Delete</button>
                                </div>
                            </m.div>
                        </div>
                    )}
                </AnimatePresence>
            </div>
        </Layout>
    </LazyMotion>
);
}
