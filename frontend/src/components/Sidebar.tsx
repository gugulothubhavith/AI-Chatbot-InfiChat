import { useState, useEffect, useMemo } from "react";
import { Link, useNavigate, useLocation, useParams } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import axios from "axios";
import { Logo } from "./Logo";
import { SettingsModal } from "./SettingsModal";
import {
  SquarePen,
  ImagePlus as ImageIcon,
  Settings,
  LogOut,
  User as UserIcon,
  PanelLeft,
  MessageSquare,
  Code,
  Trash2,
  MoreHorizontal,
  Share2,
  Edit3,
  Pin,
  Archive,
  ArchiveRestore,
  Info,
  X,
  Search as SearchIcon,
  MessageSquare as ChatIcon,
} from "lucide-react";

import { cn } from "../lib/utils";


interface ChatSession {
  id: string;
  title: string;
  is_pinned: boolean;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export default function Sidebar() {
  const { logout, user, token } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { sessionId: currentSessionId } = useParams<{ sessionId?: string }>();

  // Layout State
  const [isExpanded, setIsExpanded] = useState(false);

  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [menuSessionId, setMenuSessionId] = useState<string | null>(null);
  const [renameSessionId, setRenameSessionId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [isSharing, setIsSharing] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  // Derived & Sorted Sessions
  const sortedSessions = useMemo(() => {
    return [...sessions].sort((a, b) => {
      if (a.is_pinned && !b.is_pinned) return -1;
      if (!a.is_pinned && b.is_pinned) return 1;
      return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
    });
  }, [sessions]);

  // Grouped & Filtered Sessions for Search
  const groupedFilteredSessions = useMemo(() => {
    const filtered = sortedSessions.filter(s => 
      s.title.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const now = new Date();
    const groups: Record<string, ChatSession[]> = {
      "Today": [],
      "Yesterday": [],
      "Previous 7 Days": [],
      "Previous 30 Days": [],
      "Older": []
    };

    filtered.forEach(session => {
      const updated = new Date(session.updated_at);
      const diffTime = now.getTime() - updated.getTime();
      const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

      if (diffDays === 0 && now.getDate() === updated.getDate()) {
        groups["Today"].push(session);
      } else if (diffDays === 1 || (diffDays === 0 && now.getDate() !== updated.getDate())) {
        groups["Yesterday"].push(session);
      } else if (diffDays < 7) {
        groups["Previous 7 Days"].push(session);
      } else if (diffDays < 30) {
        groups["Previous 30 Days"].push(session);
      } else {
        groups["Older"].push(session);
      }
    });

    return groups;
  }, [sortedSessions, searchQuery]);

  // --- Effects & Data Loading ---

  useEffect(() => {
    const handleClickOutside = () => {
      setShowProfileMenu(false);
      setMenuSessionId(null);
    };
    document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  }, []);

  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === "Escape") setIsSearchOpen(false);
    };
    window.addEventListener("keydown", handleEsc);
    return () => window.removeEventListener("keydown", handleEsc);
  }, []);

  const loadSessions = async () => {
    if (!token) return;
    try {
      const res = await axios.get("/api/chat/sessions", {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSessions(res.data);
    } catch (err) {
      console.error("Failed to load sessions", err);
    }
  };

  const handleArchiveSession = async (e: React.MouseEvent, session: ChatSession) => {
    e.stopPropagation();
    if (!token) return;
    try {
      await axios.patch(`/api/chat/sessions/${session.id}`,
        { is_archived: !session.is_archived },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      loadSessions();
      setMenuSessionId(null);
    } catch (err) {
      console.error("Failed to archive session", err);
    }
  };

  const handlePinSession = async (e: React.MouseEvent, session: ChatSession) => {
    e.stopPropagation();
    if (!token) return;
    try {
      await axios.patch(`/api/chat/sessions/${session.id}`,
        { is_pinned: !session.is_pinned },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      loadSessions();
      setMenuSessionId(null);
    } catch (err) {
      console.error("Failed to pin session", err);
    }
  };

  const handleRenameSession = (e: React.MouseEvent, session: ChatSession) => {
    e.stopPropagation();
    setRenameSessionId(session.id);
    setRenameValue(session.title);
    setMenuSessionId(null);
  };

  const handleSaveRename = async (sessionId: string) => {
    if (!renameValue.trim()) {
      setRenameSessionId(null);
      return;
    }
    if (!token) return;
    try {
      await axios.patch(`/api/chat/sessions/${sessionId}`,
        { title: renameValue },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      loadSessions();
      setRenameSessionId(null);
    } catch (err) {
      console.error("Failed to rename session", err);
    }
  };

  const handleShareSession = async (e: React.MouseEvent, session: ChatSession) => {
    e.stopPropagation();
    setIsSharing(true);
    try {
      if (!token) return;
      const res = await axios.post(`/api/chat/sessions/${session.id}/share`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const { share_token } = res.data;
      const url = `${window.location.origin}/share/${share_token}`;
      
      if (navigator.share) {
        await navigator.share({
          title: session.title,
          url: url
        });
      } else {
        await navigator.clipboard.writeText(url);
        alert("Share link copied to clipboard!");
      }
      setMenuSessionId(null);
    } catch (err) {
      console.error("Failed to share session", err);
    } finally {
      setIsSharing(false);
    }
  };





  const handleDeleteSession = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    if (!token) return;
    if (!window.confirm("Are you sure you want to delete this chat? This cannot be undone.")) return;

    try {
      await axios.delete(`/api/chat/sessions/${sessionId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      loadSessions();
      if (currentSessionId === sessionId) {
        navigate("/");
      }
    } catch (err) {
      console.error("Failed to delete session", err);
    }
  };

  useEffect(() => {
    loadSessions();
  }, [token, location.pathname]);

  // --- Actions ---

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  // --- Navigation Items ---
  const minimalNavItems = [
    { name: "New Chat", path: "/", icon: SquarePen },
    { name: "Chat", path: "/", icon: ChatIcon },
    { name: "Search Chats", onClick: () => setIsSearchOpen(true), icon: SearchIcon },
    { name: "Image Gen", path: "/image", icon: ImageIcon, isBeta: true },
    { name: "Code Agent", path: "/code", icon: Code },
    { name: "About", path: "/about", icon: Info },
  ];

  const fullNavItems = [
    { name: "New chat", path: "/", icon: SquarePen },
    { name: "Chat", path: "/", icon: ChatIcon },
    { name: "Search Chats", onClick: () => setIsSearchOpen(true), icon: SearchIcon },
    { name: "Image Gen", path: "/image", icon: ImageIcon, isBeta: true },
    { name: "Code Agent", path: "/code", icon: Code },
    { name: "About", path: "/about", icon: Info },
  ];

  const activeModule = fullNavItems.find(item => item.path && item.path !== "/" && location.pathname.startsWith(item.path))?.path || "/";


  return (
    <div
      className={cn(
        "flex flex-col h-screen transition-all duration-300 z-50 border-r border-gray-100 dark:border-gray-800 bg-white dark:bg-[#0B0B0B]",
        isExpanded ? "w-72" : "w-[72px] items-center py-6"
      )}
    >

      {/* --- MINIMAL MODE HEADER --- */}
      {!isExpanded && (
        <div className="mb-8 flex flex-col items-center gap-6">
          {/* Merged Brand / Toggle Button */}
          <button
            onClick={() => setIsExpanded(true)}
            className="group h-10 w-10 text-gray-400 dark:text-white flex items-center justify-center rounded-xl hover:bg-gray-100 dark:hover:bg-white/10 transition-colors relative"
            title="Expand Menu"
          >
            <div className="absolute inset-0 flex items-center justify-center transition-opacity duration-200 opacity-100 group-hover:opacity-0">
              <Logo iconOnly iconSize={28} />
            </div>
            <div className="absolute inset-0 flex items-center justify-center transition-opacity duration-200 opacity-0 group-hover:opacity-100">
              <PanelLeft className="h-6 w-6 text-gray-500 dark:text-gray-400" strokeWidth={1.5} />
            </div>
          </button>
        </div>
      )}


      {/* --- EXPANDED MODE HEADER --- */}
      {isExpanded && (
        <div className="px-4 pt-4 pb-2 flex-shrink-0 mb-10">
          <div className="flex items-center justify-between">
            <Logo iconOnly iconSize={28} />
            <button
              onClick={() => setIsExpanded(false)}
              className="p-1.5 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
            >
              <PanelLeft className="h-5 w-5" />
            </button>
          </div>
        </div>
      )}


      {/* --- CONTENT AREA --- */}

      {/* 1. Minimal Nav (Only visible when collapsed) */}
      {!isExpanded && (
        <nav className="flex-1 flex flex-col gap-4 w-full px-3">
          {minimalNavItems.map((item) => {
            const isActive = location.pathname === item.path;
            const Icon = item.icon;

            const content = (
              <>
                <Icon className="h-5 w-5" strokeWidth={1.5} />
                <div className="absolute left-14 bg-gray-900 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-50">
                  {item.name}
                </div>
              </>
            );

            const className = cn(
              "h-10 w-10 mx-auto flex items-center justify-center rounded-full transition-all duration-200 group relative",
              isActive
                ? "text-gray-900 dark:text-white bg-gray-100 dark:bg-white/10"
                : "text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/5"
            );

            if ('onClick' in item) {
              return (
                <button
                  key={item.name}
                  onClick={item.onClick}
                  className={className}
                  title={item.name}
                >
                  {content}
                </button>
              );
            }

            return (
              <Link
                key={item.name}
                to={item.path!}
                className={className}
                title={item.name}
              >
                {content}
              </Link>
            );
          })}
        </nav>
      )}


      {/* 2. Expanded Nav & History (Only visible when expanded) */}
      {isExpanded && (
        <div className="flex-1 overflow-hidden flex flex-col">
          <div className="px-4 pb-2">
            <nav className="space-y-0.5 mb-4">
              {fullNavItems.map((item) => {
                const isActive = activeModule === (item.path || "");
                const Icon = item.icon;
                const className = cn(
                  "relative flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 w-full text-left",
                  isActive
                    ? "text-gray-900 dark:text-white"
                    : "hover:bg-gray-100 dark:hover:bg-gray-800/50 hover:text-gray-900 dark:hover:text-white text-gray-600 dark:text-gray-400"
                );

                const inner = (
                  <>
                    <Icon className={cn("h-4 w-4 flex-shrink-0", isActive && "text-gray-900 dark:text-white")} />
                    <span className="truncate">{item.name}</span>
                    {'isBeta' in item && item.isBeta && (
                      <span className="ml-auto text-[9px] bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 px-1.5 py-0.5 rounded font-semibold uppercase tracking-wider">Beta</span>
                    )}
                  </>
                );

                if ('onClick' in item) {
                  return (
                    <button
                      key={item.name}
                      onClick={item.onClick}
                      className={className}
                    >
                      {inner}
                    </button>
                  );
                }

                return (
                  <Link
                    key={item.name}
                    to={item.path!}
                    className={className}
                  >
                    {inner}
                  </Link>
                );
              })}
            </nav>

            <div className="flex items-center justify-between h-6 mb-2">
              <h3 className="text-xs font-semibold text-gray-500">Your Chats</h3>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto space-y-0.5 px-4 pb-2 scrollbar-thin scrollbar-thumb-gray-200 dark:scrollbar-thumb-gray-800">
            {sortedSessions
              .filter(s => !s.is_archived)
              .map(session => (
                <div
                  key={session.id}
                  className={cn(
                    "group relative flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-all border border-transparent pr-16",
                    currentSessionId === session.id
                      ? "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white"
                      : "text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800/30 hover:text-gray-900 dark:hover:text-white"
                  )}
                  onClick={() => renameSessionId !== session.id && navigate(`/${session.id}`)}
                >
                  <MessageSquare className="h-3.5 w-3.5 opacity-70 flex-shrink-0" />
                  <div className="flex-1 truncate text-xs font-medium">
                    {renameSessionId === session.id ? (
                      <div className="flex items-center w-full" onClick={(e) => e.stopPropagation()}>
                        <input
                          autoFocus
                          value={renameValue}
                          onChange={(e) => setRenameValue(e.target.value)}
                          onBlur={() => handleSaveRename(session.id)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") handleSaveRename(session.id);
                            if (e.key === "Escape") setRenameSessionId(null);
                          }}
                          className="flex-1 bg-white dark:bg-gray-700 border border-gray-400 rounded px-1.5 py-0.5 outline-none text-xs"
                        />
                      </div>
                    ) : (
                      <div className="flex items-center gap-1.5">
                        <span className="truncate">{session.title}</span>
                        {session.is_pinned && <Pin className="h-2.5 w-2.5 fill-current text-gray-500 opacity-70" />}
                      </div>
                    )}
                  </div>
                  
                  {/* Action Menu Trigger */}
                  <div className="absolute right-2 flex items-center gap-1 pl-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setMenuSessionId(menuSessionId === session.id ? null : session.id);
                      }}
                      className={cn(
                        "p-1 text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-all",
                        menuSessionId === session.id ? "opacity-100 bg-gray-100 dark:bg-gray-800" : "opacity-0 group-hover:opacity-100"
                      )}
                      title="More actions"
                    >
                      <MoreHorizontal className="h-4 w-4" />
                    </button>

                    {/* Action Dropdown Menu */}
                    {menuSessionId === session.id && (
                      <div 
                        className="absolute right-0 top-full mt-1 w-44 bg-white dark:bg-[#1a1f2e] border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl z-[100] py-1 animate-in fade-in slide-in-from-top-2"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <button
                          onClick={(e) => handleShareSession(e, session)}
                          disabled={isSharing}
                          className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-50"
                        >
                          {isSharing ? (
                            <div className="h-4 w-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                          ) : (
                            <Share2 className="h-4 w-4" />
                          )} 
                          {isSharing ? "Sharing..." : "Share"}
                        </button>
                        <button
                          onClick={(e) => handleRenameSession(e, session)}
                          className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
                        >
                          <Edit3 className="h-4 w-4" /> Rename
                        </button>
                        <button
                          onClick={(e) => handlePinSession(e, session)}
                          className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
                        >
                          <Pin className={cn("h-4 w-4", session.is_pinned && "fill-current text-gray-500")} /> 
                          {session.is_pinned ? "Unpin chat" : "Pin chat"}
                        </button>
                        <button
                          onClick={(e) => handleArchiveSession(e, session)}
                          className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
                        >
                          {session.is_archived ? <ArchiveRestore className="h-4 w-4" /> : <Archive className="h-4 w-4" />}
                          {session.is_archived ? "Unarchive" : "Archive"}
                        </button>
                        <hr className="my-1 border-gray-100 dark:border-gray-800" />
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteSession(e, session.id);
                            setMenuSessionId(null);
                          }}
                          className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/10"
                        >
                          <Trash2 className="h-4 w-4" /> Delete
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* --- FOOTER / PROFILE --- */}
      <div className="mt-auto flex flex-col items-center w-full pb-4 relative bg-inherit">

        {/* Expanded Profile */}
        {isExpanded ? (
          <div
            className="w-full p-4 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800/50 transition-colors relative"
            onClick={(e) => {
              e.stopPropagation();
              setShowProfileMenu(!showProfileMenu);
            }}
          >
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 rounded-full bg-gray-600 flex-shrink-0 flex items-center justify-center text-white text-xs overflow-hidden">
                {user?.picture ? (
                  <img src={user.picture} alt="Profile" className="h-full w-full object-cover" />
                ) : (
                  user?.email?.charAt(0).toUpperCase() || 'U'
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{user?.email}</p>
              </div>
              <MoreHorizontal className="h-4 w-4 text-gray-400" />
            </div>

            {/* Popup Menu */}
            {showProfileMenu && (
              <div className="absolute bottom-full left-2 right-2 mb-2 bg-white dark:bg-[#1a1f2e] border border-gray-200 dark:border-gray-700 rounded-lg shadow-2xl p-1 z-[100] animate-in fade-in slide-in-from-bottom-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setIsSettingsOpen(true);
                    setShowProfileMenu(false);
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
                >
                  <Settings className="h-4 w-4" /> Settings
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleLogout();
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/10 rounded"
                >
                  <LogOut className="h-4 w-4" /> Sign Out
                </button>
              </div>
            )}
          </div>
        ) : (
          /* Minimal Profile */
          <div className="relative pt-4 w-full flex justify-center">
            {showProfileMenu && (
              <div className="absolute bottom-12 left-14 w-48 bg-white dark:bg-[#1a1f2e] border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl overflow-hidden z-[100] animate-in fade-in slide-in-from-bottom-2 min-w-[12rem]">
                <div className="p-3 border-b border-gray-100 dark:border-gray-700">
                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate px-1">{user?.email}</p>
                </div>
                <div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setIsSettingsOpen(true);
                      setShowProfileMenu(false);
                    }}
                    className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white transition-colors text-left"
                  >
                    <Settings className="h-4 w-4" /> Settings
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleLogout();
                    }}
                    className="w-full flex items-center gap-3 px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 hover:text-red-700 dark:hover:text-red-300 transition-colors text-left"
                  >
                    <LogOut className="h-4 w-4" /> Sign Out
                  </button>
                </div>
              </div>
            )}

            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowProfileMenu(!showProfileMenu);
              }}
              className="h-10 w-10 rounded-full bg-orange-500 flex items-center justify-center text-white font-semibold text-xs border-2 border-white dark:border-[#0B1120] hover:ring-2 hover:ring-orange-500/50 transition-all overflow-hidden flex-shrink-0"
            >
              {user?.picture ? (
                <img src={user.picture} alt="Profile" className="h-full w-full object-cover" />
              ) : (
                user?.email?.substring(0, 2).toUpperCase() || <UserIcon className="h-5 w-5" />
              )}
            </button>
          </div>
        )}

      </div>

      {/* Search Modal Overlay */}
      {isSearchOpen && (
        <div 
          className="fixed inset-0 bg-black/60 z-[200] flex items-center justify-center px-4 animate-in fade-in duration-300" 
          onClick={() => { setIsSearchOpen(false); setSearchQuery(""); }}
        >
          <div 
            className="bg-white dark:bg-[#1a1f2e] w-full max-w-2xl rounded-[28px] shadow-2xl overflow-hidden animate-in zoom-in-95 slide-in-from-top-8 duration-300 border border-gray-100 dark:border-gray-800"
            onClick={e => e.stopPropagation()}
          >
            {/* Search Input Section */}
            <div className="p-5 border-b border-gray-100 dark:border-gray-800 flex items-center gap-4 bg-gray-50/50 dark:bg-gray-800/30">
              <div className="p-2.5 bg-white dark:bg-gray-800 rounded-2xl shadow-sm">
                <SearchIcon className="h-5 w-5 text-gray-400" />
              </div>
              <input
                autoFocus
                placeholder="Search Chats"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="flex-1 bg-transparent border-none outline-none text-gray-900 dark:text-white placeholder-gray-400 text-lg font-medium"
              />
              <div className="flex items-center gap-1">
                {searchQuery && (
                  <button 
                    onClick={() => setSearchQuery("")} 
                    className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-xl text-gray-400 transition-colors"
                    title="Clear search"
                  >
                    <X className="h-4 w-4 opacity-70" />
                  </button>
                )}
                <button 
                  onClick={() => { setIsSearchOpen(false); setSearchQuery(""); }} 
                  className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-all"
                  title="Close search"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>

            {/* Results Section */}
            <div className="max-h-[60vh] overflow-y-auto p-3 scrollbar-hide">
              {/* New Chat Button (matches ChatGPT style) */}
              {!searchQuery && (
                 <button 
                  onClick={() => { navigate("/"); setIsSearchOpen(false); }}
                  className="w-full flex items-center gap-4 px-4 py-3 rounded-2xl hover:bg-gray-50 dark:hover:bg-gray-800/50 text-gray-900 dark:text-white transition-all group"
                >
                  <div className="h-9 w-9 rounded-full bg-gray-100 dark:bg-gray-800/50 flex items-center justify-center text-gray-500 dark:text-gray-400 group-hover:scale-110 transition-transform shadow-sm">
                    <SquarePen className="h-4 w-4" />
                  </div>
                  <div className="flex-1 truncate text-left">
                    <p className="font-semibold text-sm truncate">New chat</p>
                  </div>
                </button>
              )}

              {/* Grouped Results */}
              {Object.entries(groupedFilteredSessions).map(([group, groupSessions]) => (
                groupSessions.length > 0 && (
                  <div key={group} className="mt-5 first:mt-2">
                    <div className="px-4 mb-2 flex items-center gap-2">
                       <span className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">{group}</span>
                    </div>
                    <div className="space-y-1">
                      {groupSessions.map(session => (
                        <button
                          key={session.id}
                          onClick={() => { navigate(`/${session.id}`); setIsSearchOpen(false); setSearchQuery(""); }}
                          className="w-full flex items-center gap-4 px-4 py-3 rounded-2xl hover:bg-gray-100 dark:hover:bg-gray-800/80 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-all text-left group"
                        >
                          <div className="h-9 w-9 rounded-full bg-gray-50 dark:bg-gray-800/50 flex items-center justify-center group-hover:bg-white dark:group-hover:bg-gray-800 transition-colors shadow-sm">
                            <ChatIcon className="h-4 w-4 opacity-40 group-hover:opacity-100 transition-opacity" />
                          </div>
                          <div className="flex-1 truncate">
                            <p className="font-semibold text-sm truncate">{session.title}</p>
                          </div>
                          {session.is_pinned && (
                            <div className="h-6 w-6 rounded-lg bg-gray-100 dark:bg-gray-800/50 flex items-center justify-center">
                              <Pin className="h-3 w-3 fill-current text-gray-400" />
                            </div>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                )
              ))}

              {/* No Results Fallback */}
              {searchQuery && Object.values(groupedFilteredSessions).every(g => g.length === 0) && (
                <div className="py-20 text-center animate-in fade-in slide-in-from-bottom-4 duration-500">
                  <div className="h-16 w-16 bg-gray-50 dark:bg-gray-800/50 rounded-full flex items-center justify-center mx-auto mb-6 shadow-inner">
                    <SearchIcon className="h-8 w-8 text-gray-200 dark:text-gray-700" />
                  </div>
                  <h3 className="text-gray-900 dark:text-white font-bold mb-1">No matches found</h3>
                  <p className="text-sm text-gray-400">Try searching for keywords in your titles</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      {/* Settings Modal Overlay */}
      <SettingsModal 
        isOpen={isSettingsOpen} 
        onClose={() => setIsSettingsOpen(false)} 
      />
    </div>
  );
}
