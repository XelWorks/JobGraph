import React, { useState, useEffect, useCallback } from 'react';
import {
  Bot,
  Play,
  Pause,
  ShieldCheck,
  AlertTriangle,
  Clock,
  Activity,
  Settings2,
} from 'lucide-react';

interface AutonomyStatus {
  is_enabled: boolean;
  is_running: boolean;
  last_run_at: string | null;
  next_run_at: string | null;
  applications_today: number;
  daily_limit: number;
  errors_last_hour: number;
}

interface AutonomyControlPanelProps {
  token: string;
}

const API_BASE = import.meta.env?.VITE_API_URL || 'http://localhost:8000';

export const AutonomyControlPanel: React.FC<AutonomyControlPanelProps> = ({ token }) => {
  const [status, setStatus] = useState<AutonomyStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<'enable' | 'disable' | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const resp = await fetch(`${API_BASE}/api/v1/autonomy/status`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!resp.ok) {
        if (resp.status === 404) {
          // Endpoint doesn't exist yet, show default disabled state
          setStatus({
            is_enabled: false,
            is_running: false,
            last_run_at: null,
            next_run_at: null,
            applications_today: 0,
            daily_limit: 50,
            errors_last_hour: 0,
          });
          return;
        }
        throw new Error(`HTTP ${resp.status}`);
      }
      const data = await resp.json();
      setStatus(data);
    } catch (err) {
      setError(`Failed to load autonomy status: ${err}`);
    }
  }, [token]);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000); // Poll every 30 seconds
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const handleToggle = async (enable: boolean) => {
    setActionLoading(enable ? 'enable' : 'disable');
    setError(null);
    try {
      const resp = await fetch(`${API_BASE}/api/v1/autonomy/${enable ? 'enable' : 'disable'}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({}),
      });

      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`);
      }

      await fetchStatus();
    } catch (err) {
      setError(`Failed to ${enable ? 'enable' : 'disable'} autonomy: ${err}`);
    } finally {
      setActionLoading(null);
    }
  };

  if (!status) {
    return (
      <div className="bg-slate-950/20 border border-slate-800/60 rounded-xl p-6 flex items-center justify-center">
        <div className="flex items-center gap-2 text-slate-400">
          <Activity className="h-5 w-5 animate-pulse" />
          <span className="text-sm">Loading autonomy status...</span>
        </div>
      </div>
    );
  }

  const formatDateTime = (isoString: string | null) => {
    if (!isoString) return 'Not scheduled';
    return new Date(isoString).toLocaleString();
  };

  const usagePercentage = (status.applications_today / status.daily_limit) * 100;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`p-2.5 rounded-xl ${
            status.is_enabled 
              ? 'bg-emerald-500/15 border border-emerald-500/30' 
              : 'bg-slate-800/60 border border-slate-700/50'
          }`}>
            <Bot className={`h-6 w-6 ${
              status.is_enabled ? 'text-emerald-400' : 'text-slate-400'
            }`} />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">Autonomous Application System</h2>
            <p className="text-xs text-slate-400">
              {status.is_enabled 
                ? 'System is actively discovering and applying to jobs on your behalf' 
                : 'System is paused - no automatic applications will be made'}
            </p>
          </div>
        </div>

        <button
          onClick={() => handleToggle(!status.is_enabled)}
          disabled={actionLoading !== null}
          className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm transition-all focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed ${
            status.is_enabled
              ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30 hover:bg-rose-500/25'
              : 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/25'
          }`}
        >
          {actionLoading ? (
            <>
              <Clock className="h-4 w-4 animate-spin" />
              Processing...
            </>
          ) : status.is_enabled ? (
            <>
              <Pause className="h-4 w-4" />
              Disable Autonomy
            </>
          ) : (
            <>
              <Play className="h-4 w-4" />
              Enable Autonomy
            </>
          )}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-4 flex items-center gap-3">
          <AlertTriangle className="h-5 w-5 text-rose-400 shrink-0" />
          <span className="text-sm text-rose-300">{error}</span>
        </div>
      )}

      {/* Status Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Status Badge */}
        <div className="bg-slate-950/20 border border-slate-800/60 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-3">
            <ShieldCheck className="h-4 w-4 text-sky-400" />
            <span className="text-xs font-semibold text-slate-400">System Status</span>
          </div>
          <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-bold ${
            status.is_enabled
              ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/20'
              : 'bg-slate-800/60 text-slate-400 border border-slate-700/50'
          }`}>
            <span className={`h-2 w-2 rounded-full ${
              status.is_enabled ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'
            }`} />
            {status.is_enabled ? 'Active & Running' : 'Disabled'}
          </div>
        </div>

        {/* Applications Today */}
        <div className="bg-slate-950/20 border border-slate-800/60 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-3">
            <Activity className="h-4 w-4 text-indigo-400" />
            <span className="text-xs font-semibold text-slate-400">Applications Today</span>
          </div>
          <div className="flex items-end justify-between">
            <span className="text-2xl font-bold text-white">
              {status.applications_today}
              <span className="text-sm font-normal text-slate-500 ml-1">/ {status.daily_limit}</span>
            </span>
            <span className={`text-xs font-semibold ${
              usagePercentage > 80 ? 'text-amber-400' : 'text-slate-500'
            }`}>
              {Math.round(usagePercentage)}% used
            </span>
          </div>
          <div className="mt-2 h-1.5 bg-slate-800 rounded-full overflow-hidden">
            <div 
              className={`h-full rounded-full transition-all ${
                usagePercentage > 80 
                  ? 'bg-amber-500' 
                  : usagePercentage > 50 
                  ? 'bg-indigo-500' 
                  : 'bg-emerald-500'
              }`}
              style={{ width: `${Math.min(usagePercentage, 100)}%` }}
            />
          </div>
        </div>

        {/* Last Run */}
        <div className="bg-slate-950/20 border border-slate-800/60 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-3">
            <Clock className="h-4 w-4 text-purple-400" />
            <span className="text-xs font-semibold text-slate-400">Last Discovery Run</span>
          </div>
          <span className="text-sm font-medium text-slate-300">
            {formatDateTime(status.last_run_at)}
          </span>
        </div>

        {/* Next Scheduled Run */}
        <div className="bg-slate-950/20 border border-slate-800/60 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-3">
            <Settings2 className="h-4 w-4 text-amber-400" />
            <span className="text-xs font-semibold text-slate-400">Next Scheduled Run</span>
          </div>
          <span className="text-sm font-medium text-slate-300">
            {formatDateTime(status.next_run_at)}
          </span>
        </div>
      </div>

      {/* Important Notice */}
      <div className="bg-sky-500/10 border border-sky-500/30 rounded-xl p-5">
        <div className="flex items-start gap-3">
          <ShieldCheck className="h-5 w-5 text-sky-400 shrink-0 mt-0.5" />
          <div className="space-y-2">
            <h3 className="text-sm font-bold text-sky-300">Before Enabling Autonomous Mode</h3>
            <ul className="text-xs text-sky-200/80 space-y-1 list-disc list-inside">
              <li>Ensure you have connected at least one job portal account in the Vault section</li>
              <li>Complete your profile with skills, experience, and resume in the Profile section</li>
              <li>Review your daily application limit (default: 50 applications/day)</li>
              <li>The system will automatically discover jobs, tailor resumes, and submit applications</li>
              <li>You can disable autonomy at any time from this panel</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Quick Stats Row */}
      {status.is_enabled && (
        <div className="bg-slate-950/20 border border-slate-800/60 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="h-4 w-4 text-emerald-400" />
            <span className="text-xs font-semibold text-slate-400">Live Activity Metrics</span>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-3 bg-slate-900/30 rounded-lg">
              <div className="text-xs text-slate-500 mb-1">Errors (Last Hour)</div>
              <div className={`text-lg font-bold ${
                status.errors_last_hour > 0 ? 'text-amber-400' : 'text-emerald-400'
              }`}>
                {status.errors_last_hour}
              </div>
            </div>
            <div className="text-center p-3 bg-slate-900/30 rounded-lg">
              <div className="text-xs text-slate-500 mb-1">System State</div>
              <div className="text-lg font-bold text-sky-400">
                {status.is_running ? 'Running' : 'Idle'}
              </div>
            </div>
            <div className="text-center p-3 bg-slate-900/30 rounded-lg">
              <div className="text-xs text-slate-500 mb-1">Daily Limit</div>
              <div className="text-lg font-bold text-indigo-400">
                {status.daily_limit}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
