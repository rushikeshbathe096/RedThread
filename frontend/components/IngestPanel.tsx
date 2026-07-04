"use client";

import React, { useState } from "react";
import { UploadCloud } from "lucide-react";
import { STREAM_URL } from "@/lib/api";

interface IngestPanelProps {
  onEvent: (type: string, data: any) => void;
  onStart: () => void;
  onComplete: (source_name: string) => void;
}

export default function IngestPanel({ onEvent, onStart, onComplete }: IngestPanelProps) {
  const [text, setText] = useState("");
  const [isIngesting, setIsIngesting] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const startStream = async (formData: FormData) => {
    setIsIngesting(true);
    onStart();
    try {
      const res = await fetch(STREAM_URL, {
        method: "POST",
        body: formData,
      });
      if (!res.body) throw new Error("No readable stream");
      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");

      let buffer = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";
        
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const parsed = JSON.parse(line.slice(6));
              if (parsed.type === "done") {
                onComplete(formData.get("source_name") as string);
                setIsIngesting(false);
                return;
              } else if (parsed.type === "error") {
                console.error("Ingestion error:", parsed.data);
              } else {
                onEvent(parsed.type, parsed.data);
              }
            } catch (e) {
              console.error("Error parsing SSE:", e);
            }
          }
        }
      }
    } catch (e) {
      console.error(e);
      setIsIngesting(false);
    }
  };

  const handlePaste = (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;
    const formData = new FormData();
    formData.append("text", text);
    formData.append("source_name", "pasted_text");
    startStream(formData);
    setText("");
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      const formData = new FormData();
      formData.append("file", file);
      formData.append("source_name", file.name);
      startStream(formData);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#111111] border-r border-gray-800 p-6 w-[350px] shrink-0 z-10">
      <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
        <UploadCloud className="text-blue-500" />
        Ingest Evidence
      </h2>
      
      <div 
        className={`flex-1 border-2 border-dashed rounded-xl flex flex-col items-center justify-center p-6 text-center transition-colors mb-6 ${dragActive ? 'border-blue-500 bg-blue-500/10' : 'border-gray-700 hover:border-gray-500'}`}
        onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
        onDragLeave={(e) => { e.preventDefault(); setDragActive(false); }}
        onDrop={handleDrop}
      >
        <UploadCloud className="w-12 h-12 text-gray-500 mb-4" />
        <p className="text-sm text-gray-400 mb-2">Drag & drop a file here</p>
        <p className="text-xs text-gray-600">.txt or .pdf</p>
      </div>

      <div className="flex flex-col gap-3">
        <div className="text-sm font-medium text-gray-400">Or paste raw text</div>
        <textarea 
          className="w-full bg-[#0a0a0a] border border-gray-800 rounded-lg p-3 text-sm focus:outline-none focus:border-blue-500 resize-none h-32"
          placeholder="Paste investigation notes here..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={isIngesting}
        />
        <button 
          onClick={handlePaste}
          disabled={isIngesting || !text.trim()}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white py-2 rounded-lg font-medium transition-colors"
        >
          {isIngesting ? "Ingesting..." : "Process Text"}
        </button>
      </div>
    </div>
  );
}
