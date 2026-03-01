import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import axios from "axios";
import { MessageSquare, Calendar, ChevronLeft } from "lucide-react";
import { cn } from "../lib/utils";
import { Logo } from "../components/Logo";

interface SharedMessage {
  role: string;
  content: string;
  created_at: string;
}

interface SharedData {
  title: string;
  messages: SharedMessage[];
  created_at: string;
}

export default function SharedChatView() {
  const { token } = useParams<{ token: string }>();
  const [data, setData] = useState<SharedData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchShared = async () => {
      try {
        const res = await axios.get(`/api/chat/shared/${token}`);
        setData(res.data);
      } catch (err) {
        console.error("Failed to load shared chat", err);
        setError("This shared chat could not be found or has expired.");
      } finally {
        setLoading(false);
      }
    };
    fetchShared();
  }, [token]);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50 dark:bg-gray-950">
        <div className="animate-pulse flex flex-col items-center gap-4">
          <Logo iconOnly className="h-12 w-12 opacity-50" />
          <p className="text-gray-500 animate-bounce">Loading shared conversation...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex h-screen flex-col items-center justify-center bg-gray-50 dark:bg-gray-950 px-4">
        <div className="bg-white dark:bg-gray-900 p-8 rounded-2xl shadow-xl max-w-md w-full text-center border border-gray-100 dark:border-gray-800">
          <div className="h-16 w-16 bg-red-100 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-full flex items-center justify-center mx-auto mb-6">
            <MessageSquare className="h-8 w-8" />
          </div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Unavailable</h1>
          <p className="text-gray-500 dark:text-gray-400 mb-8">{error}</p>
          <Link to="/" className="inline-flex items-center justify-center px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-xl transition-all w-full">
            Back to Home
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <header className="h-16 border-b border-gray-100 dark:border-gray-800 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md sticky top-0 z-10 px-4 md:px-8">
        <div className="max-w-4xl mx-auto h-full flex items-center justify-between">
          <div className="flex items-center gap-4 overflow-hidden">
            <Link to="/" className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-gray-500 flex-shrink-0">
                <ChevronLeft className="h-5 w-5" />
            </Link>
            <div className="overflow-hidden">
              <h1 className="text-base font-bold text-gray-900 dark:text-white truncate">{data.title}</h1>
              <div className="flex items-center gap-2 text-[10px] text-gray-500">
                <Calendar className="h-3 w-3" />
                <span>Shared on {new Date(data.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
          <div className="flex-shrink-0">
             <Logo iconOnly className="h-8 w-8" />
          </div>
        </div>
      </header>

      {/* Messages */}
      <main className="flex-1 overflow-y-auto pt-8 pb-12 px-4">
        <div className="max-w-4xl mx-auto space-y-8">
          {data.messages.map((msg, idx) => (
            <div 
              key={idx} 
              className={cn(
                "flex flex-col gap-2 max-w-[85%]",
                msg.role === "user" ? "ml-auto items-end" : "mr-auto items-start"
              )}
            >
              <div 
                className={cn(
                  "px-4 py-3 rounded-2xl whitespace-pre-wrap text-sm leading-relaxed",
                  msg.role === "user" 
                    ? "bg-indigo-600 text-white rounded-tr-none shadow-md" 
                    : "bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-200 border border-gray-100 dark:border-gray-800 shadow-sm rounded-tl-none"
                )}
              >
                {msg.content}
              </div>
              <span className="text-[10px] text-gray-400 font-medium px-1">
                {msg.role === "user" ? "You" : "InfiChat Assistant"}
              </span>
            </div>
          ))}
          
          {/* Join CTA */}
          <div className="pt-12 text-center">
             <div className="bg-indigo-50 dark:bg-indigo-900/20 rounded-2xl p-8 border border-indigo-100/50 dark:border-indigo-500/10">
                <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-2 font-outfit">Powered by InfiChat</h2>
                <p className="text-gray-600 dark:text-gray-400 text-sm mb-6">Create your own professional AI chatbot experience with RAG, Vision, and code execution.</p>
                <Link to="/login" className="inline-flex items-center justify-center px-8 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl shadow-lg shadow-indigo-500/20 transition-all">
                  Get Started for Free
                </Link>
             </div>
          </div>
        </div>
      </main>
    </div>
  );
}
