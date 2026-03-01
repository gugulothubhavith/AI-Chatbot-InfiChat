import { useState, useEffect, useCallback, useRef } from "react";
import Editor from "@monaco-editor/react";
import { useAuth } from "../hooks/useAuth";
import { useTheme } from "../context/ThemeContext";
import axios from "axios";
import { Button } from "../components/ui/Button";
import { Logo } from "../components/Logo";
import { Play, Terminal, Loader2, Sparkles } from "lucide-react";

export default function CodeAgentWorkspace() {
  const { token } = useAuth();
  const { theme } = useTheme();
  const [code, setCode] = useState("");
  const [output, setOutput] = useState("");
  const [task, setTask] = useState("generate");
  const [loading, setLoading] = useState(false);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [useMultiAgent, setUseMultiAgent] = useState(false);
  const [leftWidth, setLeftWidth] = useState(30);
  const [isResizing, setIsResizing] = useState(false);
  const terminalRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [output]);

  const startResizing = useCallback(() => {
    setIsResizing(true);
  }, []);

  const stopResizing = useCallback(() => {
    setIsResizing(false);
  }, []);

  const resize = useCallback(
    (e: MouseEvent) => {
      if (!isResizing || !containerRef.current) return;

      const containerRect = containerRef.current.getBoundingClientRect();
      const newWidth = ((e.clientX - containerRect.left) / containerRect.width) * 100;

      // Constraints
      if (newWidth > 15 && newWidth < 85) {
        setLeftWidth(newWidth);
      }
    },
    [isResizing]
  );

  useEffect(() => {
    if (isResizing) {
      window.addEventListener("mousemove", resize);
      window.addEventListener("mouseup", stopResizing);
    } else {
      window.removeEventListener("mousemove", resize);
      window.removeEventListener("mouseup", stopResizing);
    }

    return () => {
      window.removeEventListener("mousemove", resize);
      window.removeEventListener("mouseup", stopResizing);
    };
  }, [isResizing, resize, stopResizing]);

  const handleExecute = async () => {
    // 2. Multi-Agent Squad Mode (WS Streaming)
    if (useMultiAgent && task === "generate") {
      if (ws) ws.close();
      setOutput("");
      setLoading(true);

      const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const wsHost = window.location.hostname;
      const socket = new WebSocket(`${wsProtocol}//${wsHost}:8000/ws/code/squad`);
      socket.onopen = () => {
        socket.send(JSON.stringify({ prompt: code }));
      };
      socket.onmessage = (event) => {
        // If message contains #### (file header), we clear the status and append
        if (event.data.includes("####")) {
          setOutput((prev) => prev + "\n" + event.data);
        } else {
          // Otherwise just append as a status line
          setOutput((prev) => prev + "\n" + event.data);
        }
      };
      socket.onclose = () => {
        setWs(null);
        setLoading(false);
      };
      socket.onerror = (err) => {
        setOutput((prev) => prev + "\n❌ Connection Error: " + err);
        setLoading(false);
      };
      setWs(socket);
      return;
    }

    // 3. Standard HTTP tasks (Refactor, Explain, Test)
    setLoading(true);
    try {
      const endpoint = task === "generate" ? "/api/code/generate" : `/api/code/${task}`;
      const payload =
        task === "generate"
          ? { prompt: code, use_agents: useMultiAgent }
          : task === "refactor"
            ? { code, goal: "improve" }
            : { code };

      const res = await axios.post(endpoint, payload, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setOutput(res.data.result);
    } catch (err: any) {
      setOutput(`Error: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };



  return (
    <div className="flex flex-col h-full bg-white dark:bg-[#0B1120] text-gray-900 dark:text-white overflow-hidden transition-colors duration-300">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 bg-white/80 dark:bg-[#0B1120]/50 backdrop-blur-md sticky top-0 z-10 border-b border-gray-200 dark:border-gray-800">
        <div className="flex items-center gap-4">
          <Logo hideIcon={true} nameSize={22} className="ml-[-8px]" />
          <div className="h-5 w-px bg-gray-300 dark:bg-gray-700"></div>
          <h1 className="font-semibold text-gray-900 dark:text-white text-lg tracking-tight">Code Agent</h1>
        </div>

        {/* Toolbar */}
        <div className="flex items-center gap-3">
          {task === "generate" && (
            <label className="flex items-center gap-2 cursor-pointer bg-gray-100 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 px-3 py-2 rounded-lg hover:border-indigo-500 transition-all select-none">
              <input
                type="checkbox"
                checked={useMultiAgent}
                onChange={(e) => setUseMultiAgent(e.target.checked)}
                className="accent-indigo-500 h-4 w-4"
              />
              <span className="text-sm text-gray-700 dark:text-gray-300">Multi-Agent Squad</span>
            </label>
          )}



          <select
            value={task}
            onChange={(e) => setTask(e.target.value)}
            className="bg-gray-100 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 text-gray-900 dark:text-white text-sm rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-500/50 hover:bg-gray-200 dark:hover:bg-gray-800 transition-colors cursor-pointer"
          >
            <option value="generate">Generate Code</option>
            <option value="refactor">Refactor / Optimize</option>
            <option value="explain">Explain Code</option>
            <option value="test">Generate Tests</option>
          </select>

          <Button
            onClick={handleExecute}
            disabled={loading}
            className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg shadow-indigo-500/20 ml-2 border dark:border-0 border-indigo-700"
          >
            {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4 fill-current" />}
            {loading ? "Running..." : "Run Agent"}
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div
        ref={containerRef}
        className={`flex-1 flex gap-0 overflow-hidden ${isResizing ? 'cursor-col-resize select-none' : ''}`}
      >
        {/* Editor Panel */}
        <div
          style={{ width: `${leftWidth}%` }}
          className="flex flex-col border-r border-gray-800"
        >
          <div className="bg-gray-100 dark:bg-gray-900/50 px-4 py-2 border-b border-gray-200 dark:border-gray-800 text-xs font-mono text-gray-500 dark:text-gray-400 flex justify-between items-center whitespace-nowrap overflow-hidden transition-colors duration-200">
            <span>INPUT</span>
            <span className="text-gray-600 hidden md:inline">Monaco Editor</span>
          </div>
          <div className="flex-1 relative">
            <Editor
              height="100%"
              theme={theme === 'dark' ? "vs-dark" : "light"}
              value={code}
              onChange={(v) => setCode(v || "")}
              options={{
                fontSize: 14,
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                padding: { top: 16, bottom: 16 },
                fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
                automaticLayout: true,
              }}
            />
          </div>
        </div>

        {/* Resizer Divider */}
        <div
          onMouseDown={startResizing}
          className={`w-1.5 flex-shrink-0 cursor-col-resize hover:bg-gray-500/30 transition-colors relative group ${isResizing ? 'bg-gray-500/50' : 'bg-gray-200 dark:bg-gray-800/20'}`}
        >
          <div className="absolute inset-y-0 left-1/2 -translate-x-1/2 w-px bg-gray-300 dark:bg-gray-700 group-hover:bg-gray-400 transition-colors" />
        </div>

        {/* Output Panel (Interactive Terminal) */}
        <div style={{ width: `${100 - leftWidth}%` }} className="flex flex-col bg-white dark:bg-[#0f1623] transition-colors duration-200">
          <div className={`px-4 py-2 border-b border-gray-200 dark:border-gray-800 text-xs font-mono flex items-center gap-2 transition-colors duration-200 ${ws ? 'bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400' : 'bg-gray-100 dark:bg-gray-900/50 text-gray-500 dark:text-gray-400'}`}>
            <Terminal className="h-3 w-3" />
            <span>OUTPUT / CONSOLE</span>
            {ws && <span className="ml-auto text-[10px] uppercase tracking-wider text-green-400 flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" /> LIVE</span>}
          </div>

          <div
            ref={terminalRef}
            className="flex-1 p-4 font-mono text-sm overflow-auto custom-scrollbar"
          >
            {output ? (
              <pre className="whitespace-pre-wrap text-emerald-600 dark:text-emerald-400 break-words">{output}</pre>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-gray-400 dark:text-gray-600">
                <Sparkles className="h-8 w-8 mb-3 opacity-20" />
                <p>Output will appear here...</p>
              </div>
            )}
          </div>


        </div>
      </div>
    </div>
  );
}
