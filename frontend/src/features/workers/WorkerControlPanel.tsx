import React, { useState } from 'react';
import {
  Activity,
  Bot,
  Pause,
  StopCircle,
  MonitorPlay,
  Loader2,
  Clock,
  Cpu,
} from 'lucide-react';

interface WorkerControlPanelProps {
  token: string;
}

interface WorkerCard {
  id: string;
  company: string;
  jobTitle: string;
  currentStep: string;
  status: 'Running' | 'Paused' | 'Stopped' | 'Completed' | 'Failed';
  mode: string;
  startedAt: string;
}

const MOCK_WORKERS: WorkerCard[] = [
  {
    id: 'worker-1',
    company: 'Microsoft',
    jobTitle: 'Senior Software Engineer',
    currentStep: 'Uploading Resume',
    status: 'Running',
    mode: 'Autonomous',
    startedAt: new Date(Date.now() - 120000).toISOString(),
  },
  {
    id: 'worker-2',
    company: 'Stripe',
    jobTitle: 'Backend Engineer',
    currentStep: 'Filling Contact Details',
    status: 'Running',
    mode: 'Assisted',
    startedAt: new Date(Date.now() - 45000).toISOString(),
  },
];

function getStatusBadgeClass(status: WorkerCard['status']): string {
  switch (status) {
    case 'Running':
      return 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/20';
    case 'Paused':
      return 'bg-amber-500/15 text-amber-400 border border-amber-500/20';
    case 'Stopped':
      return 'bg-rose-500/15 text-rose-400 border border-rose-500/20';
    case 'Completed':
      return 'bg-sky-500/15 text-sky-400 border border-sky-500/20';
    case 'Failed':
      return 'bg-rose-500/15 text-rose-400 border border-rose-500/20';
    default:
      return 'bg-slate-500/15 text-slate-400 border border-slate-500/20';
  }
}

function getElapsedTime(startedAt: string): string {
  const elapsed = Math.floor((Date.now() - new Date(startedAt).getTime()) / 1000);
  if (elapsed < 60) return `${elapsed}s ago`;
  const minutes = Math.floor(elapsed / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ago`;
}

function getWorkerNumber(id: string): string {
  const match = id.match(/\d+$/);
  return match ? `#${match[0]}` : id;
}

interface WorkerCardProps {
  worker: WorkerCard;
  actionLoading: string | null;
  onPause: (id: string) => void;
  onStop: (id: string) => void;
  onTakeControl: (id: string) => void;
}

const WorkerCardComponent: React.FC<WorkerCardProps> = ({
  worker,
  actionLoading,
  onPause,
  onStop,
  onTakeControl,
}) => {
  const isLoading = actionLoading === worker.id;
  const isTerminal = worker.status === 'Stopped' || worker.status === 'Completed';

  return (
    <div className="bg-slate-950/20 border border-slate-800/60 rounded-2xl p-5 flex flex-col gap-4">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Cpu className="h-4 w-4 text-slate-500" />
          <span className="text-xs font-semibold text-slate-400 bg-slate-800/60 border border-slate-700/40 px-2 py-0.5 rounded-full">
            Worker {getWorkerNumber(worker.id)}
          </span>
        </div>
        <span
          className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${getStatusBadgeClass(worker.status)}`}
        >
          {worker.status}
        </span>
      </div>

      {/* Company + job title */}
      <div>
        <p className="text-base font-bold text-white leading-tight">{worker.company}</p>
        <p className="text-sm text-slate-400 mt-0.5">{worker.jobTitle}</p>
      </div>

      {/* Current step */}
      <div className="flex items-center gap-2">
        {worker.status === 'Running' && (
          <span className="relative flex h-2 w-2 shrink-0">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
        )}
        <p className="text-xs text-slate-300 truncate">{worker.currentStep}</p>
      </div>

      {/* Mode + elapsed time */}
      <div className="flex items-center justify-between text-xs text-slate-500">
        <div className="flex items-center gap-1.5">
          <Bot className="h-3.5 w-3.5" />
          <span className="bg-slate-800/60 border border-slate-700/40 px-2 py-0.5 rounded-full text-slate-400">
            {worker.mode}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <Clock className="h-3.5 w-3.5" />
          <span>{getElapsedTime(worker.startedAt)}</span>
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-2 pt-1 border-t border-slate-800/60">
        {/* Pause */}
        <button
          onClick={() => onPause(worker.id)}
          disabled={worker.status !== 'Running' || isLoading}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all focus:outline-none disabled:opacity-50 bg-amber-500/10 text-amber-400 border border-amber-500/20 hover:bg-amber-500/20 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Pause className="h-3.5 w-3.5" />
          )}
          Pause
        </button>

        {/* Take Control */}
        <button
          onClick={() => onTakeControl(worker.id)}
          disabled={isTerminal || isLoading}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all focus:outline-none disabled:opacity-50 bg-sky-500/10 text-sky-400 border border-sky-500/20 hover:bg-sky-500/20 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <MonitorPlay className="h-3.5 w-3.5" />
          )}
          Take Control
        </button>

        {/* Stop */}
        <button
          onClick={() => onStop(worker.id)}
          disabled={isTerminal || isLoading}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all focus:outline-none disabled:opacity-50 bg-rose-500/10 text-rose-400 border border-rose-500/20 hover:bg-rose-500/20 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <StopCircle className="h-3.5 w-3.5" />
          )}
          Stop
        </button>
      </div>
    </div>
  );
};

export const WorkerControlPanel: React.FC<WorkerControlPanelProps> = ({ token: _token }) => {
  const [workers, setWorkers] = useState<WorkerCard[]>(MOCK_WORKERS);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const handlePause = (workerId: string): void => {
    setActionLoading(workerId);
    setTimeout(() => {
      setWorkers(prev =>
        prev.map(w => (w.id === workerId ? { ...w, status: 'Paused' } : w))
      );
      setActionLoading(null);
    }, 800);
  };

  const handleStop = (workerId: string): void => {
    setActionLoading(workerId);
    setTimeout(() => {
      setWorkers(prev =>
        prev.map(w => (w.id === workerId ? { ...w, status: 'Stopped' } : w))
      );
      setActionLoading(null);
    }, 800);
  };

  const handleTakeControl = (workerId: string): void => {
    setActionLoading(workerId);
    setTimeout(() => {
      setWorkers(prev =>
        prev.map(w =>
          w.id === workerId
            ? { ...w, currentStep: 'Awaiting Manual Input', status: 'Paused' }
            : w
        )
      );
      setActionLoading(null);
    }, 800);
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Section header */}
      <div className="flex items-center gap-3 border-b border-slate-800 pb-5">
        <Activity className="h-6 w-6 text-sky-400" />
        <div>
          <h2 className="text-xl font-bold text-white">Live Worker Telemetry</h2>
          <p className="text-xs text-slate-500">
            Monitor active automation workers and control execution in real time
          </p>
        </div>
      </div>

      {/* Empty state */}
      {workers.length === 0 && (
        <div className="flex flex-col items-center justify-center p-16 bg-slate-950/10 border border-slate-800/40 rounded-2xl space-y-3">
          <Bot className="h-10 w-10 text-slate-600" />
          <p className="text-slate-400 text-sm">No active workers running</p>
          <p className="text-slate-600 text-xs">
            Workers will appear here when automation tasks are dispatched
          </p>
        </div>
      )}

      {/* Worker cards grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {workers.map(worker => (
          <WorkerCardComponent
            key={worker.id}
            worker={worker}
            actionLoading={actionLoading}
            onPause={handlePause}
            onStop={handleStop}
            onTakeControl={handleTakeControl}
          />
        ))}
      </div>
    </div>
  );
};
