import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, X, MessageSquare, Plus } from "lucide-react";
import { cn } from "../lib/utils";
import { isToday, isYesterday, isThisWeek, isThisMonth } from "date-fns";
import { useNavigate } from "react-router-dom";

interface ChatSession {
    id: string;
    title: string;
    is_pinned: boolean;
    is_archived: boolean;
    created_at: string;
    updated_at: string;
}

interface SearchModalProps {
    isOpen: boolean;
    onClose: () => void;
    sessions: ChatSession[];
}

export function SearchModal({ isOpen, onClose, sessions }: SearchModalProps) {
    const [query, setQuery] = useState("");
    const [selectedIndex, setSelectedIndex] = useState(0);
    const inputRef = useRef<HTMLInputElement>(null);
    const navigate = useNavigate();

    // Reset state on open
    useEffect(() => {
        if (isOpen) {
            setQuery("");
            setSelectedIndex(0);
            setTimeout(() => inputRef.current?.focus(), 100);
        }
    }, [isOpen]);

    // Filtering and Grouping
    const filteredSessions = sessions
        .filter(s => !s.is_archived)
        .filter(s => s.title.toLowerCase().includes(query.toLowerCase()));

    const groupSessions = (sessions: ChatSession[]) => {
        const groups: { [key: string]: ChatSession[] } = {
            Today: [],
            Yesterday: [],
            "Previous 7 Days": [],
            "This Month": [],
            Older: []
        };

        sessions.forEach(s => {
            const date = new Date(s.updated_at);
            if (isToday(date)) groups["Today"].push(s);
            else if (isYesterday(date)) groups["Yesterday"].push(s);
            else if (isThisWeek(date)) groups["Previous 7 Days"].push(s);
            else if (isThisMonth(date)) groups["This Month"].push(s);
            else groups["Older"].push(s);
        });

        return Object.entries(groups).filter(([_, items]) => items.length > 0);
    };

    const groupedResults = groupSessions(filteredSessions);
    const flatResults = groupedResults.flatMap(([_, items]) => items);

    // Keyboard navigation
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === "ArrowDown") {
                setSelectedIndex(prev => Math.min(prev + 1, flatResults.length));
            } else if (e.key === "ArrowUp") {
                setSelectedIndex(prev => Math.max(prev - 1, 0));
            } else if (e.key === "Enter") {
                if (selectedIndex === 0) {
                    navigate("/");
                    onClose();
                } else if (flatResults[selectedIndex - 1]) {
                    navigate(`/${flatResults[selectedIndex - 1].id}`);
                    onClose();
                }
            } else if (e.key === "Escape") {
                onClose();
            }
        };

        if (isOpen) {
            window.addEventListener("keydown", handleKeyDown);
            return () => window.removeEventListener("keydown", handleKeyDown);
        }
    }, [isOpen, flatResults, selectedIndex, navigate, onClose]);

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 bg-black/60 z-[100]"
                    />

                    {/* Modal Container */}
                    <div className="fixed inset-0 flex items-center justify-center p-4 z-[101] pointer-events-none">
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95, y: 20 }}
                            className="w-full max-w-2xl bg-white dark:bg-[#171717] border border-gray-200 dark:border-white/10 rounded-2xl shadow-2xl overflow-hidden pointer-events-auto flex flex-col max-h-[80vh] transition-colors duration-200"
                        >
                            {/* Search Header */}
                            <div className="flex items-center gap-3 px-4 py-4 border-b border-gray-200 dark:border-white/5 transition-colors duration-200">
                                <Search className="h-5 w-5 text-gray-400" />
                                <input
                                    ref={inputRef}
                                    type="text"
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    placeholder="Search chats..."
                                    className="flex-1 bg-transparent text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 outline-none text-base"
                                />
                                <button
                                    onClick={onClose}
                                    className="p-1 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg text-gray-500 transition-colors"
                                >
                                    <X className="h-5 w-5" />
                                </button>
                            </div>

                            {/* Suggestions / Results */}
                            <div className="flex-1 overflow-y-auto p-2 custom-scrollbar">
                                {/* Fixed "New Chat" Option */}
                                <div
                                    className={cn(
                                        "flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-colors group mb-2",
                                        selectedIndex === 0 ? "bg-gray-100 dark:bg-white/10 text-gray-900 dark:text-white" : "text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-white/5"
                                    )}
                                    onClick={() => { navigate("/"); onClose(); }}
                                    onMouseEnter={() => setSelectedIndex(0)}
                                >
                                    <div className="h-8 w-8 rounded-lg bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                                        <Plus className="h-4 w-4 text-gray-400" />
                                    </div>
                                    <span className="text-sm font-medium">New chat</span>
                                </div>

                                {groupedResults.length > 0 ? (
                                    groupedResults.map(([group, items], _groupIndex) => (
                                        <div key={group} className="mb-4 last:mb-0">
                                            <h4 className="px-3 py-2 text-[11px] font-bold text-gray-500 uppercase tracking-wider flex items-center gap-2">
                                                {group}
                                            </h4>
                                            <div className="space-y-1">
                                                {items.map((session, _itemIndex) => {
                                                    // Find index in flatResults
                                                    const flatIndex = flatResults.findIndex(f => f.id === session.id) + 1;
                                                    const isSelected = selectedIndex === flatIndex;

                                                    return (
                                                        <div
                                                            key={session.id}
                                                            className={cn(
                                                                "flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all",
                                                                isSelected ? "bg-gray-100 dark:bg-white/10 text-gray-900 dark:text-white" : "text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-white/5"
                                                            )}
                                                            onClick={() => { navigate(`/${session.id}`); onClose(); }}
                                                            onMouseEnter={() => setSelectedIndex(flatIndex)}
                                                        >
                                                            <MessageSquare className="h-4 w-4 opacity-50" />
                                                            <div className="flex-1 min-w-0">
                                                                <p className="text-sm font-medium truncate">{session.title}</p>
                                                            </div>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    ))
                                ) : (
                                    <div className="py-20 text-center">
                                        <p className="text-sm text-gray-500">No chats found for "{query}"</p>
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    </div>
                </>
            )}
        </AnimatePresence>
    );
}
