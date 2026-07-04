"use client";

import React, { useState, useCallback, useEffect } from "react";
import IngestPanel from "@/components/IngestPanel";
import RecallPanel from "@/components/RecallPanel";
import EvidencePanel from "@/components/EvidencePanel";
import dynamic from "next/dynamic";
import { GraphData, Edge } from "@/lib/types";
import { forget, getOverlap, getGraph } from "@/lib/api";

// Load ForceGraph2D dynamically to avoid SSR issues
const GraphView = dynamic(() => import("@/components/GraphView"), { ssr: false });

export default function Home() {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [highlightedPath, setHighlightedPath] = useState<string[]>([]);
  const [overlapNodes, setOverlapNodes] = useState<string[]>([]);
  const [ingestedCases, setIngestedCases] = useState<string[]>([]);
  const [lastQuery, setLastQuery] = useState<string>("");
  
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

  const handleIngestComplete = async (sourceName: string) => {
    console.log("Ingestion streaming complete for", sourceName);
    
    try {
      const fullGraph = await getGraph();
      setGraphData(fullGraph); // Ensures confidences are up to date
      
      const newCases = [...ingestedCases, sourceName];
      setIngestedCases(newCases);
      
      // Check overlaps with all previously ingested cases
      let newOverlaps: string[] = [];
      for (const prevCase of ingestedCases) {
        const res = await getOverlap(prevCase, sourceName);
        if (res.overlap && res.overlap.length > 0) {
          newOverlaps = [...newOverlaps, ...res.overlap.map(n => n.id)];
        }
      }
      
      if (newOverlaps.length > 0) {
        setOverlapNodes(prev => [...prev, ...newOverlaps]);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleForget = async (edge: Edge, newConfidence: number) => {
    try {
      const res = await forget({
        target: edge.label,
        reason: "User contradicted this claim",
        confidence: newConfidence,
        query: lastQuery || "What happened?"
      });
      console.log("Forget response:", res);
      if (res.updated_answer) {
        alert(`Answer updated!\n\nBefore: ${res.previous_answer}\n\nAfter: ${res.updated_answer}`);
      }
      
      // Refresh graph to see faded edges
      const updatedGraph = await getGraph();
      setGraphData(updatedGraph);
    } catch (e) {
      console.error("Failed to forget:", e);
    }
  };

  const handleHighlight = (path: string[], query?: string) => {
    setHighlightedPath(path);
    if (query) setLastQuery(query);
  };

  return (
    <main className="flex h-screen w-full bg-black">
      <IngestPanel 
        onStart={handleIngestStart}
        onEvent={handleIngestEvent}
        onComplete={handleIngestComplete}
      />
      <div className="flex-1 relative">
        <GraphView data={graphData} highlightedPath={highlightedPath} overlapNodes={overlapNodes} />
        <RecallPanel onHighlight={handleHighlight} />
      </div>
      <EvidencePanel edges={graphData.edges} onForget={handleForget} />
    </main>
  );
}
