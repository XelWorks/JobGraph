import React, { useCallback, useEffect, useState } from 'react';
import {
  Background,
  Controls,
  Edge,
  MarkerType,
  Node,
  Panel,
  Position,
  ReactFlow,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { AlertCircle, FileText, GitBranch, Users, X } from 'lucide-react';

const API_BASE = import.meta.env?.VITE_API_URL || 'http://localhost:8000';

interface GraphNodeData {
  id: string;
  label: string;
  epic: number;
  wave: number;
  developer: string;
  files_touched: string[];
  requires: string[];
  enables: string[];
}

interface GraphEdgeData {
  id: string;
  source: string;
  target: string;
  type: string;
}

interface GraphResponse {
  nodes: GraphNodeData[];
  edges: GraphEdgeData[];
  waves: Array<Record<string, unknown>>;
  epics: Array<Record<string, unknown>>;
}

const EPIC_COLORS: Record<number, { bg: string; border: string; text: string; hex: string }> = {
  1: { bg: 'bg-sky-500/20', border: 'border-sky-500/40', text: 'text-sky-400', hex: '#0ea5e9' },
  2: { bg: 'bg-indigo-500/20', border: 'border-indigo-500/40', text: 'text-indigo-400', hex: '#6366f1' },
  3: { bg: 'bg-purple-500/20', border: 'border-purple-500/40', text: 'text-purple-400', hex: '#a855f7' },
  4: { bg: 'bg-amber-500/20', border: 'border-amber-500/40', text: 'text-amber-400', hex: '#f59e0b' },
  5: { bg: 'bg-emerald-500/20', border: 'border-emerald-500/40', text: 'text-emerald-400', hex: '#10b981' },
  6: { bg: 'bg-rose-500/20', border: 'border-rose-500/40', text: 'text-rose-400', hex: '#f43f5e' },
  7: { bg: 'bg-teal-500/20', border: 'border-teal-500/40', text: 'text-teal-400', hex: '#14b8a6' },
  8: { bg: 'bg-cyan-500/20', border: 'border-cyan-500/40', text: 'text-cyan-400', hex: '#06b6d4' },
  9: { bg: 'bg-orange-500/20', border: 'border-orange-500/40', text: 'text-orange-400', hex: '#f97316' },
  10: { bg: 'bg-pink-500/20', border: 'border-pink-500/40', text: 'text-pink-400', hex: '#ec4899' },
};

function getEpicColor(epic: number) {
  return EPIC_COLORS[epic] || { bg: 'bg-slate-500/20', border: 'border-slate-500/40', text: 'text-slate-400', hex: '#64748b' };
}

export const DependencyGraph: React.FC<{ token: string }> = ({ token }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [selectedNode, setSelectedNode] = useState<GraphNodeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchGraph = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(`${API_BASE}/api/v1/graph`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data: GraphResponse = await resp.json();

      const waveGroups: Record<number, GraphNodeData[]> = {};
      data.nodes.forEach((n) => {
        if (!waveGroups[n.wave]) waveGroups[n.wave] = [];
        waveGroups[n.wave].push(n);
      });

      const xGap = 280;
      const yGap = 120;
      const flowNodes: Node[] = data.nodes.map((n) => {
        const waveIndex = Object.keys(waveGroups)
          .map(Number)
          .sort((a, b) => a - b)
          .indexOf(n.wave);
        const epicIndex = n.epic;
        const col = waveGroups[n.wave].indexOf(n);

        return {
          id: n.id,
          type: 'default',
          position: { x: waveIndex * xGap + col * 220, y: epicIndex * yGap },
          data: {
            label: n.label,
            epic: n.epic,
            developer: n.developer,
          },
          style: {
            background: `${getEpicColor(n.epic).hex}22`,
            border: `1px solid ${getEpicColor(n.epic).hex}66`,
            color: '#e2e8f0',
            borderRadius: '12px',
            padding: '10px 14px',
            fontSize: '12px',
            fontWeight: 500,
            minWidth: '180px',
            maxWidth: '240px',
            textAlign: 'center',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.3)',
          },
          sourcePosition: Position.Right,
          targetPosition: Position.Left,
        };
      });

      const flowEdges: Edge[] = data.edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        type: 'smoothstep',
        animated: true,
        style: { stroke: '#475569', strokeWidth: 1.5 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#475569' },
      }));

      setNodes(flowNodes);
      setEdges(flowEdges);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dependency graph');
    } finally {
      setLoading(false);
    }
  }, [token, setNodes, setEdges]);

  useEffect(() => {
    fetchGraph();
  }, [fetchGraph]);

  const onNodeClick = useCallback((_event: React.MouseEvent, node: Node) => {
    const data = node.data as GraphNodeData & { label: string };
    const story = data;
    setSelectedNode({
      id: story.id || node.id,
      label: story.label || node.data.label as string,
      epic: story.epic || 1,
      wave: story.wave || 1,
      developer: story.developer || 'Unknown',
      files_touched: story.files_touched || [],
      requires: story.requires || [],
      enables: story.enables || [],
    });
  }, []);

  const epicColor = selectedNode ? getEpicColor(selectedNode.epic) : null;

  return (
    <div className="space-y-4 animate-fadeIn">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dependency Graph</h1>
          <p className="text-sm text-slate-400 mt-1">
            Interactive story dependency map across waves and epics
          </p>
        </div>
        <button
          onClick={fetchGraph}
          disabled={loading}
          className="inline-flex items-center gap-2 px-4 py-2 bg-slate-800 text-slate-300 border border-slate-700 rounded-xl font-medium text-sm hover:bg-slate-700 transition-colors disabled:opacity-50"
        >
          Refresh
        </button>
      </div>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-4 flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-rose-400 shrink-0" />
          <span className="text-sm text-rose-300">{error}</span>
        </div>
      )}

      <div className="bg-slate-950/20 border border-slate-800/60 rounded-xl overflow-hidden" style={{ height: '70vh' }}>
        {loading ? (
          <div className="flex items-center justify-center h-full text-slate-400 text-sm">Loading graph...</div>
        ) : (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            fitView
            attributionPosition="bottom-left"
          >
            <Background color="#1e293b" gap={20} />
            <Controls className="bg-slate-900 border border-slate-700 text-slate-200" />
            <Panel position="top-right" className="m-4">
              <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3 space-y-2 text-xs text-slate-400">
                <div className="font-semibold text-slate-200 mb-1">Legend</div>
                {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((e) => {
                  const c = getEpicColor(e);
                  return (
                    <div key={e} className="flex items-center gap-2">
                      <span className={`inline-block h-3 w-3 rounded ${c.bg} ${c.border} border`} />
                      <span>Epic {e}</span>
                    </div>
                  );
                })}
              </div>
            </Panel>
          </ReactFlow>
        )}
      </div>

      {selectedNode && (
        <div className="bg-slate-950/20 border border-slate-800/60 rounded-xl p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${epicColor?.bg} ${epicColor?.text} border ${epicColor?.border} mb-2`}>
                <GitBranch className="h-3.5 w-3.5" /> Epic {selectedNode.epic}
              </span>
              <h3 className="text-lg font-bold text-white">{selectedNode.label}</h3>
            </div>
            <button onClick={() => setSelectedNode(null)} className="text-slate-400 hover:text-slate-200">
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="flex items-center gap-2 text-sm text-slate-300">
              <GitBranch className="h-4 w-4 text-sky-400" />
              <span>Wave {selectedNode.wave}</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-300">
              <Users className="h-4 w-4 text-indigo-400" />
              <span>{selectedNode.developer}</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-300">
              <span className="text-slate-500">ID:</span>
              <span className="font-mono text-xs">{selectedNode.id}</span>
            </div>
          </div>

          <div className="space-y-3">
            <div>
              <h4 className="text-xs font-semibold text-slate-400 mb-1">Requires</h4>
              {selectedNode.requires.length === 0 ? (
                <span className="text-xs text-slate-500">None</span>
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {selectedNode.requires.map((r) => (
                    <span key={r} className="text-xs px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 font-mono">
                      {r}
                    </span>
                  ))}
                </div>
              )}
            </div>
            <div>
              <h4 className="text-xs font-semibold text-slate-400 mb-1">Enables</h4>
              {selectedNode.enables.length === 0 ? (
                <span className="text-xs text-slate-500">None</span>
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {selectedNode.enables.map((e) => (
                    <span key={e} className="text-xs px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 font-mono">
                      {e}
                    </span>
                  ))}
                </div>
              )}
            </div>
            <div>
              <h4 className="text-xs font-semibold text-slate-400 mb-1 flex items-center gap-1">
                <FileText className="h-3.5 w-3.5" /> Files Touched
              </h4>
              {selectedNode.files_touched.length === 0 ? (
                <span className="text-xs text-slate-500">None</span>
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {selectedNode.files_touched.map((f) => (
                    <span key={f} className="text-xs px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-400 font-mono">
                      {f}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
