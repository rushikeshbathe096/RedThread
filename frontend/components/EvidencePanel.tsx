"use client";

import React, { useState } from "react";
import { XCircle, ShieldAlert } from "lucide-react";
import { Edge } from "@/lib/types";

interface EvidencePanelProps {
  edges: Edge[];
  onForget: (edge: Edge, newConfidence: number) => void;
}

export default function EvidencePanel({ edges, onForget }: EvidencePanelProps) {
  // We'll just show unique labels as claims for simplicity
  const uniqueClaims = Array.from(new Map(edges.map(e => [e.label, e])).values());

  return (
    <div className="flex flex-col h-full bg-[#111111] border-l border-gray-800 p-6 w-[350px] shrink-0 z-10 overflow-y-auto">
      <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
        <ShieldAlert className="text-yellow-500" />
        Evidence / Claims
      </h2>
      
      <div className="flex flex-col gap-4">
        {uniqueClaims.length === 0 ? (
          <div className="text-gray-500 text-sm text-center mt-10">No claims extracted yet.</div>
        ) : (
          uniqueClaims.map((edge, idx) => {
            const conf = edge.confidence ?? 1.0;
            const isContradicted = conf < 0.5;
            
            return (
              <div key={idx} className={`p-3 rounded-lg border ${isContradicted ? 'bg-red-950/20 border-red-900/30' : 'bg-[#1a1a1a] border-gray-800'}`}>
                <div className="text-sm font-medium text-gray-200 break-words mb-2">
                  {edge.source} <span className="text-blue-400">→</span> {edge.label} <span className="text-blue-400">→</span> {edge.target}
                </div>
                
                <div className="flex items-center justify-between mt-3">
                  <div className="text-xs text-gray-500 flex items-center gap-1">
                    Confidence: <span className={isContradicted ? 'text-red-400' : 'text-green-400'}>{conf.toFixed(1)}</span>
                  </div>
                  
                  {!isContradicted && (
                    <button 
                      onClick={() => onForget(edge, 0.3)}
                      className="text-xs flex items-center gap-1 text-red-400 hover:text-red-300 transition-colors bg-red-950/30 px-2 py-1 rounded"
                    >
                      <XCircle className="w-3 h-3" /> Contradict
                    </button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
