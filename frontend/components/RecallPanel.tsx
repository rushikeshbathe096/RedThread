"use client";

import React, { useState } from "react";
import { Search } from "lucide-react";
import { recall } from "@/lib/api";

interface RecallPanelProps {
  onHighlight: (path: string[]) => void;
}

export default function RecallPanel({ onHighlight }: RecallPanelProps) {
  const [query, setQuery] = useState("");
  const [isRecalling, setIsRecalling] = useState(false);
  const [answer, setAnswer] = useState("");

  const handleRecall = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setIsRecalling(true);
    setAnswer("");
    onHighlight([]);
    try {
      const res = await recall({ query });
      setAnswer(res.answer);
      if (res.path && res.path.length > 0) {
        onHighlight(res.path);
      }
    } catch (e) {
      console.error(e);
      setAnswer("Failed to recall information.");
    }
    setIsRecalling(false);
  };

  return (
    <div className="absolute top-6 right-6 w-96 bg-[#111111] border border-gray-800 rounded-xl shadow-2xl overflow-hidden flex flex-col z-10">
      <div className="p-4 bg-[#1a1a1a] border-b border-gray-800">
        <form onSubmit={handleRecall} className="flex gap-2 relative">
          <input
            type="text"
            className="flex-1 bg-black border border-gray-700 rounded-lg pl-10 pr-3 py-2 text-sm focus:outline-none focus:border-blue-500"
            placeholder="Ask a question..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={isRecalling}
          />
          <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <button 
            type="submit" 
            disabled={isRecalling || !query.trim()}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg disabled:opacity-50"
          >
            {isRecalling ? "..." : "Ask"}
          </button>
        </form>
      </div>
      
      {answer && (
        <div className="p-5 max-h-96 overflow-y-auto custom-scrollbar">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">Analysis</h3>
          <p className="text-gray-200 text-sm leading-relaxed whitespace-pre-wrap">
            {answer}
          </p>
        </div>
      )}
    </div>
  );
}
