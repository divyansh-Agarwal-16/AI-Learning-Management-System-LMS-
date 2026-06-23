"use client";

import React, { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import ReactFlow, { Background, Controls, Node, Edge } from "reactflow";
import "reactflow/dist/style.css";
import { aiApi } from "@/lib/api";

interface ConceptMapProps {
  topic: string;
  onExplainConcept: (conceptLabel: string) => void;
}

export function ConceptMap({ topic, onExplainConcept }: ConceptMapProps) {
  const { data: res, isLoading, error } = useQuery({
    queryKey: ["conceptMap", topic],
    queryFn: () => aiApi.getConceptMap(topic),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const { nodes, edges } = useMemo(() => {
    if (!res?.success || !res.data) {
      return { nodes: [], edges: [] };
    }

    const { nodes: rawNodes, edges: rawEdges } = res.data;

    // Arrange nodes in a star layout around the primary concept (first node)
    const rfNodes: Node[] = rawNodes.map((node, index) => {
      let x = 250;
      let y = 180;

      if (index > 0 && rawNodes.length > 1) {
        const angle = ((index - 1) / (rawNodes.length - 1)) * 2 * Math.PI;
        const radius = 160;
        x = 250 + radius * Math.cos(angle);
        y = 180 + radius * Math.sin(angle);
      }

      const isCenter = index === 0;

      return {
        id: node.id,
        position: { x, y },
        data: { label: node.label },
        style: {
          background: isCenter ? "rgba(99, 102, 241, 0.9)" : "rgba(15, 23, 42, 0.8)", // indigo-500 vs slate-900
          color: isCenter ? "#ffffff" : "#cbd5e1", // white vs slate-300
          border: isCenter ? "2px solid #818cf8" : "1px solid #334155", // indigo-400 vs slate-700
          borderRadius: "12px",
          padding: "10px 8px",
          fontSize: "11px",
          fontWeight: "600",
          width: 120,
          textAlign: "center",
          boxShadow: isCenter 
            ? "0 0 15px rgba(99, 102, 241, 0.4)" 
            : "0 4px 6px -1px rgba(0, 0, 0, 0.3)",
          cursor: "pointer",
        },
      };
    });

    const rfEdges: Edge[] = rawEdges.map((edge, idx) => ({
      id: `edge-${edge.source}-${edge.target}-${idx}`,
      source: edge.source,
      target: edge.target,
      label: edge.label,
      animated: true,
      style: { stroke: "rgba(99, 102, 241, 0.4)", strokeWidth: 1.5 },
      labelStyle: { fill: "#94a3b8", fontSize: 9, fontWeight: 500, fillOpacity: 0.8 },
      labelBgStyle: { fill: "#0b0f19", fillOpacity: 0.9 },
      labelBgPadding: [4, 2],
      labelBgBorderRadius: 4,
    }));

    return { nodes: rfNodes, edges: rfEdges };
  }, [res]);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-[400px] bg-slate-950/40 border border-slate-900 rounded-xl space-y-4">
        <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-xs text-slate-400 font-medium">Generating visual concept map...</span>
      </div>
    );
  }

  if (error || !res?.success) {
    return (
      <div className="flex flex-col items-center justify-center h-[400px] bg-slate-950/40 border border-slate-900 rounded-xl text-center px-6 space-y-3">
        <span className="text-2xl">🗺️</span>
        <h4 className="text-sm font-bold text-slate-200">Failed to load Concept Map</h4>
        <p className="text-xs text-slate-400 max-w-xs">
          The AI system encountered an issue generating the concept network for &quot;{topic}&quot;.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="font-bold text-slate-200 text-base">Knowledge Concept Map</h4>
          <p className="text-xs text-slate-400 mt-0.5">
            Click any concept node to request an in-depth explanation from the AI Tutor.
          </p>
        </div>
      </div>

      <div className="h-[400px] w-full bg-[#0b0f19] border border-slate-900 rounded-xl overflow-hidden relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodeClick={(_, node) => {
            if (node.data?.label) {
              onExplainConcept(node.data.label);
            }
          }}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          maxZoom={1.5}
          minZoom={0.5}
        >
          <Background color="#334155" gap={16} size={1} />
          <Controls className="react-flow-controls-custom" style={{ display: 'flex', flexDirection: 'row', bottom: 10, left: 10, top: 'auto', right: 'auto' }} />
        </ReactFlow>
      </div>
    </div>
  );
}
