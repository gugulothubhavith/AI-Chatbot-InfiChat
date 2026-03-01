import { useState, useEffect } from "react";
import axios from "axios";
import { useAuth } from "../hooks/useAuth";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { atomDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Copy, Trash2, Plus, X, Search, Code } from "lucide-react";
import { Button } from "../components/ui/Button";


interface Snippet {
    id: string;
    title: string;
    content: string;
    language: string;
    tags: string[];
    created_at: string;
}

export default function Snippets() {
    const { token } = useAuth();
    const [snippets, setSnippets] = useState<Snippet[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [showModal, setShowModal] = useState(false);

    // New Snippet Form
    const [newTitle, setNewTitle] = useState("");
    const [newContent, setNewContent] = useState("");
    const [newLanguage, setNewLanguage] = useState("javascript");
    const [newTags, setNewTags] = useState("");

    useEffect(() => {
        fetchSnippets();
    }, [token]);

    const fetchSnippets = async () => {
        if (!token) return;
        try {
            const res = await axios.get("/api/snippets", {
                headers: { Authorization: `Bearer ${token}` }
            });
            setSnippets(res.data);
        } catch (err) {
            console.error("Failed to fetch snippets", err);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateSnippet = async () => {
        if (!token || !newTitle || !newContent) return;
        try {
            const tagsArray = newTags.split(",").map(t => t.trim()).filter(Boolean);
            await axios.post("/api/snippets", {
                title: newTitle,
                content: newContent,
                language: newLanguage,
                tags: tagsArray
            }, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setShowModal(false);
            setNewTitle("");
            setNewContent("");
            setNewTags("");
            fetchSnippets();
        } catch (err) {
            console.error("Failed to create snippet", err);
        }
    };

    const handleDeleteSnippet = async (id: string) => {
        if (!token) return;
        if (!confirm("Delete this snippet?")) return;
        try {
            await axios.delete(`/api/snippets/${id}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setSnippets(prev => prev.filter(s => s.id !== id));
        } catch (err) {
            console.error("Failed to delete snippet", err);
        }
    };

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
        // Could add toast here
    };

    const filteredSnippets = snippets.filter(s =>
        s.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.tags.some(t => t.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    return (
        <div className="flex flex-col h-full bg-white dark:bg-[#0B1120] text-gray-900 dark:text-gray-100 p-6 overflow-y-auto">
            <div className="max-w-6xl mx-auto w-full">
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-2xl font-bold flex items-center gap-2">
                            <Code className="h-6 w-6 text-indigo-500" />
                            Code Snippets
                        </h1>
                        <p className="text-gray-500 mt-1">Save and organize your reusable code blocks</p>
                    </div>
                    <Button onClick={() => setShowModal(true)} className="gap-2">
                        <Plus className="h-4 w-4" /> New Snippet
                    </Button>
                </div>

                {/* Search */}
                <div className="relative mb-6">
                    <Search className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Search snippets by title or tag..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                    />
                </div>

                {loading ? (
                    <div className="text-center py-12 text-gray-500">Loading snippets...</div>
                ) : filteredSnippets.length === 0 ? (
                    <div className="text-center py-12 text-gray-500 border-2 border-dashed border-gray-200 dark:border-gray-800 rounded-xl">
                        <Code className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                        <p>No snippets found. Create one to get started!</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {filteredSnippets.map(snippet => (
                            <div key={snippet.id} className="bg-white dark:bg-[#151b2b] border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden hover:shadow-lg transition-shadow flex flex-col">
                                <div className="p-4 border-b border-gray-100 dark:border-gray-800 flex items-start justify-between bg-gray-50/50 dark:bg-gray-800/30">
                                    <div>
                                        <h3 className="font-semibold text-lg">{snippet.title}</h3>
                                        <div className="flex flex-wrap gap-1 mt-2">
                                            <span className="text-xs px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 font-mono">
                                                {snippet.language}
                                            </span>
                                            {snippet.tags.map(tag => (
                                                <span key={tag} className="text-xs px-2 py-0.5 rounded bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                                                    #{tag}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                    <div className="flex gap-1">
                                        <button
                                            onClick={() => copyToClipboard(snippet.content)}
                                            className="p-1.5 text-gray-400 hover:text-green-500 hover:bg-green-50 dark:hover:bg-green-500/10 rounded-lg transition-colors"
                                            title="Copy Code"
                                        >
                                            <Copy className="h-4 w-4" />
                                        </button>
                                        <button
                                            onClick={() => handleDeleteSnippet(snippet.id)}
                                            className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-lg transition-colors"
                                            title="Delete"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </button>
                                    </div>
                                </div>
                                <div className="flex-1 bg-[#1e1e1e] relative group">
                                    <SyntaxHighlighter
                                        language={snippet.language}
                                        style={atomDark}
                                        customStyle={{ margin: 0, padding: '1rem', height: '100%', fontSize: '0.85rem' }}
                                        wrapLongLines={true}
                                    >
                                        {snippet.content}
                                    </SyntaxHighlighter>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Create Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="bg-white dark:bg-[#1a1f2e] w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
                        <div className="p-6 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
                            <h2 className="text-xl font-bold">New Snippet</h2>
                            <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-white">
                                <X className="h-5 w-5" />
                            </button>
                        </div>
                        <div className="p-6 space-y-4">
                            <div>
                                <label className="block text-sm font-medium mb-1">Title</label>
                                <input
                                    value={newTitle}
                                    onChange={e => setNewTitle(e.target.value)}
                                    className="w-full px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 outline-none focus:ring-2 focus:ring-indigo-500"
                                    placeholder="e.g. Auth Middleware"
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium mb-1">Language</label>
                                    <select
                                        value={newLanguage}
                                        onChange={e => setNewLanguage(e.target.value)}
                                        className="w-full px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 outline-none focus:ring-2 focus:ring-indigo-500"
                                    >
                                        <option value="javascript">JavaScript</option>
                                        <option value="typescript">TypeScript</option>
                                        <option value="python">Python</option>
                                        <option value="html">HTML</option>
                                        <option value="css">CSS</option>
                                        <option value="sql">SQL</option>
                                        <option value="json">JSON</option>
                                        <option value="sh">Shell</option>
                                        <option value="markdown">Markdown</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium mb-1">Tags (comma separated)</label>
                                    <input
                                        value={newTags}
                                        onChange={e => setNewTags(e.target.value)}
                                        className="w-full px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 outline-none focus:ring-2 focus:ring-indigo-500"
                                        placeholder="react, hooks, util"
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-1">Content</label>
                                <textarea
                                    value={newContent}
                                    onChange={e => setNewContent(e.target.value)}
                                    className="w-full h-64 px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-sm"
                                    placeholder="// Paste your code here..."
                                />
                            </div>
                        </div>
                        <div className="p-4 bg-gray-50 dark:bg-gray-800/50 flex justify-end gap-3">
                            <Button variant="ghost" onClick={() => setShowModal(false)}>Cancel</Button>
                            <Button onClick={handleCreateSnippet}>Save Snippet</Button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
