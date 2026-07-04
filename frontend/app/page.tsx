"use client";

import React, { useState, useCallback } from "react";
import IngestPanel from "@/components/IngestPanel";
import RecallPanel from "@/components/RecallPanel";
import dynamic from "next/dynamic";
import { GraphData } from "@/lib/types";

// Load ForceGraph2D dynamically to avoid SSR issues
const GraphView = dynamic(() => import("@/components/GraphView"), { ssr: false });

export default function Home() {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [highlightedPath, setHighlightedPath] = useState<string[]>([]);
  
  // Using refs or relying on state update callback logic to avoid stale closures
  const handleIngestStart = () => {
    setHighlightedPath([]);
  };

  const handleIngestEvent = useCallback((type: string, data: any) => {
    if (type === "node") {
      setGraphData((prev) => {
        // Prevent duplicate nodes by checking ID
        if (prev.nodes.some(n => n.id === data.id)) return prev;
        return { ...prev, nodes: [...prev.nodes, data] };
      });
    } else if (type === "edge") {
      setGraphData((prev) => {
        // Prevent duplicate edges
        const edgeExists = prev.edges.some(
          e => e.source === data.source && e.target === data.target && e.label === data.label
        );
        if (edgeExists) return prev;
        return { ...prev, edges: [...prev.edges, data] };
      });
    }
  }, []);

  const handleIngestComplete = () => {
    console.log("Ingestion streaming complete.");
  };

  const handleHighlight = (path: string[]) => {
    setHighlightedPath(path);
  };

  return (
    <main className="flex h-screen w-full bg-black">
      <IngestPanel 
        onStart={handleIngestStart}
        onEvent={handleIngestEvent}
        onComplete={handleIngestComplete}
      />
      <div className="flex-1 relative">
        <GraphView data={graphData} highlightedPath={highlightedPath} />
        <RecallPanel onHighlight={handleHighlight} />
      </div>
    </main>
  );
}
