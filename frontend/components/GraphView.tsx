"use client";

import React, { useRef } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { GraphData } from "@/lib/types";

interface GraphViewProps {
  data: GraphData;
  highlightedPath: string[]; // List of node IDs to highlight
  overlapNodes?: string[];
}

// Color nodes by type field
const NODE_COLORS: Record<string, string> = {
  person: "#ef4444",      // red
  organization: "#3b82f6",// blue
  wallet: "#eab308",      // yellow
  location: "#22c55e",    // green
  evidence: "#a855f7",    // purple
  default: "#9ca3af",     // gray
};

export default function GraphView({ data, highlightedPath, overlapNodes = [] }: GraphViewProps) {
  const fgRef = useRef<any>();

  // To keep animation running even when graph settles
  useEffect(() => {
    let interval: any;
    if (overlapNodes.length > 0) {
      interval = setInterval(() => {
         // trigger redraw but keep simulation stopped if it was
      }, 50);
    }
    return () => clearInterval(interval);
  }, [overlapNodes]);

  const getNodeColor = (type: string) => {
    const t = (type || "").toLowerCase();
    for (const key in NODE_COLORS) {
      if (t.includes(key)) return NODE_COLORS[key];
    }
    return NODE_COLORS.default;
  };

  return (
    <div className="relative w-full h-full bg-[#0a0a0a]">
      {data.nodes.length === 0 ? (
        <div className="absolute inset-0 flex items-center justify-center text-gray-500 font-medium">
          Drop evidence to begin an investigation
        </div>
      ) : (
        <>
          <div className="absolute top-4 left-4 z-10 bg-black/50 p-3 rounded-lg border border-gray-800 backdrop-blur-sm">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-2">Entity Types</h3>
            {Object.entries(NODE_COLORS).filter(([k]) => k !== 'default').map(([key, color]) => (
              <div key={key} className="flex items-center gap-2 mb-1">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                <span className="text-sm capitalize">{key}</span>
              </div>
            ))}
          </div>
          
          <ForceGraph2D
            ref={fgRef}
            graphData={data}
            nodeLabel="label"
            nodeColor={(node: any) => {
              if (highlightedPath.length > 0 && highlightedPath.includes(node.id)) {
                return "#ffffff"; // highlight color
              }
              return getNodeColor(node.type || "");
            }}
            nodeRelSize={6}
            nodeCanvasObjectMode={() => "before"}
            nodeCanvasObject={(node: any, ctx, globalScale) => {
              if (overlapNodes.includes(node.id)) {
                const r = 8 + (Math.sin(Date.now() / 200) + 1) * 2;
                ctx.beginPath();
                ctx.arc(node.x, node.y, r, 0, 2 * Math.PI, false);
                ctx.fillStyle = 'rgba(59, 130, 246, 0.4)';
                ctx.fill();
                ctx.strokeStyle = 'rgba(59, 130, 246, 0.8)';
                ctx.lineWidth = 1;
                ctx.stroke();
              }
            }}
            linkColor={(link: any) => {
              const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
              const targetId = typeof link.target === 'object' ? link.target.id : link.target;
              if (
                highlightedPath.length > 0 && 
                highlightedPath.includes(sourceId) &&
                highlightedPath.includes(targetId)
              ) {
                return "#ffffff";
              }
              const conf = typeof link.confidence === 'number' ? link.confidence : 1.0;
              // Map confidence 0-1 to opacity 0.1-1.0
              const opacity = Math.max(0.1, conf);
              return `rgba(150, 150, 150, ${opacity})`;
            }}
            linkWidth={(link: any) => {
              const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
              const targetId = typeof link.target === 'object' ? link.target.id : link.target;
              if (
                highlightedPath.length > 0 && 
                highlightedPath.includes(sourceId) &&
                highlightedPath.includes(targetId)
              ) {
                return 3;
              }
              return 1;
            }}
            backgroundColor="#0a0a0a"
          />
        </>
      )}
    </div>
  );
}
