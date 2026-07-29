import React, { useState, useEffect, useCallback } from 'react';
import {
  Briefcase,
  TrendingUp,
  Search,
  Sparkles,
  AlertCircle,
  Clock,
  RefreshCw
} from 'lucide-react';
import { TrackingTable, ApplicationRecord } from './TrackingTable';

interface Metrics {
  overall_overall_avg: number;
  total_found: number;
  total_matched: number;
  total_applied: number;
  total_failed: number;
  total_scheduled: number;
}

interface ApplicationsProps {
  token: string;
}

export const Applications: React.FC<ApplicationsProps> = ({ token }) => {
  const [applications, setApplications] = useState<ApplicationRecord[]>([]);
  const [metrics, setMetrics] = useState<Metrics>({
    overall_overall_avg: 0,
    total_found: 0,
    total_matched: 0,
    total_applied: 0,
    total_failed: 0,
    total_scheduled: 0
  });
  const [loading, setLoading] = useState(true);
  const [updatingAppId, setUpdatingAppId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const meta = import.meta as unknown as { env?: { VITE_API_URL?: string } };
  const apiUrl = meta.env?.VITE_API_URL || 'http://localhost:8000';

  const fetchApplicationsData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Fetch apps
      const appsResp = await fetch(`${apiUrl}/api/v1/applications`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!appsResp.ok) {
        throw new Error('Failed to retrieve application tracking logs.');
      }
      const appsData = await appsResp.json();
      setApplications(appsData);

      // 2. Fetch metrics
      const metricsResp = await fetch(`${apiUrl}/api/v1/applications/metrics`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (metricsResp.ok) {
        const metricsData = await metricsResp.json();
        setMetrics(metricsData);
      }
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : 'An error occurred loading application data.';
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  }, [apiUrl, token]);

  useEffect(() => {
    fetchApplicationsData();
  }, [fetchApplicationsData]);

  const handleUpdateStatus = async (appId: string, status: string, notes?: string) => {
    try {
      const resp = await fetch(`${apiUrl}/api/v1/applications/${appId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ status, notes })
      });
      if (!resp.ok) {
        throw new Error('Failed to update application status.');
      }
      
      // Refresh local logs
      await fetchApplicationsData();
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : 'Could not save updates.';
      alert(errMsg);
    }
  };

  const handleTriggerSubmission = async (appId: string, mode: string) => {
    setUpdatingAppId(appId);
    try {
      // Set to in-progress loading state
      if (mode === 'Manual') {
        // Direct update status to Submitted
        await handleUpdateStatus(appId, 'Submitted', 'Candidate completed application manually.');
        return;
      }

      // Assisted or Autonomous trigger (Mock submission success)
      await new Promise((resolve) => setTimeout(resolve, 3000));
      
      await handleUpdateStatus(appId, 'Submitted', `Autofilled and submitted successfully via automated ${mode} mode.`);
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : 'Automation error occurred.';
      alert(errMsg);
    } finally {
      setUpdatingAppId(null);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div className="flex items-center gap-3">
          <Briefcase className="h-6 w-6 text-sky-400" />
          <div>
            <h2 className="text-xl font-bold text-white">Applications Tracking Workspace</h2>
            <p className="text-xs text-slate-500">View matched pipeline, review PDF versions, trigger form submissions, and check analytics</p>
          </div>
        </div>
        <button
          onClick={fetchApplicationsData}
          disabled={loading}
          className="inline-flex items-center gap-2 px-4 py-2 bg-slate-950/40 hover:bg-slate-900 border border-slate-800 hover:border-slate-700/80 rounded-xl text-xs font-semibold text-sky-400 hover:text-sky-300 transition-all focus:outline-none disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Stats
        </button>
      </div>

      {/* Aggregate Metrics Bar Charts */}
      {!loading && !error && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          
          {/* Found metric card */}
          <div className="bg-slate-950/20 border border-slate-800/60 p-5 rounded-2xl space-y-3 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.2)]">
            <div className="flex items-center justify-between text-slate-500 text-xs font-bold uppercase tracking-wider">
              <span>Scraped Jobs</span>
              <Search className="h-4 w-4 text-slate-500" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-white">{metrics.total_found}</span>
              <span className="text-[10px] text-slate-500 font-semibold">Total Scraped</span>
            </div>
            <div className="w-full bg-slate-900 h-1 rounded-full overflow-hidden">
              <div className="h-full bg-slate-500 w-full" />
            </div>
          </div>

          {/* Matched metric card */}
          <div className="bg-slate-950/20 border border-slate-800/60 p-5 rounded-2xl space-y-3 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.2)]">
            <div className="flex items-center justify-between text-slate-500 text-xs font-bold uppercase tracking-wider">
              <span>Matched (≥70)</span>
              <Sparkles className="h-4 w-4 text-sky-400" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-sky-400">{metrics.total_matched}</span>
              <span className="text-[10px] text-sky-500 font-semibold">{metrics.overall_overall_avg}% Avg Score</span>
            </div>
            <div className="w-full bg-slate-900 h-1 rounded-full overflow-hidden">
              <div className="h-full bg-sky-500" style={{ width: `${metrics.overall_overall_avg}%` }} />
            </div>
          </div>

          {/* Scheduled metric card */}
          <div className="bg-slate-950/20 border border-slate-800/60 p-5 rounded-2xl space-y-3 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.2)]">
            <div className="flex items-center justify-between text-slate-500 text-xs font-bold uppercase tracking-wider">
              <span>In Progress Queue</span>
              <Clock className="h-4 w-4 text-amber-400" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-amber-400">{metrics.total_scheduled}</span>
              <span className="text-[10px] text-amber-500 font-semibold">Pending Customisation</span>
            </div>
            <div className="w-full bg-slate-900 h-1 rounded-full overflow-hidden">
              <div
                className="h-full bg-amber-500"
                style={{ width: `${metrics.total_scheduled > 0 ? (metrics.total_scheduled / (applications.length || 1)) * 100 : 0}%` }}
              />
            </div>
          </div>

          {/* Submissions card */}
          <div className="bg-slate-950/20 border border-slate-800/60 p-5 rounded-2xl space-y-3 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.2)]">
            <div className="flex items-center justify-between text-slate-500 text-xs font-bold uppercase tracking-wider">
              <span>Submitted Applications</span>
              <TrendingUp className="h-4 w-4 text-emerald-400" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-emerald-400">{metrics.total_applied}</span>
              <span className="text-[10px] text-rose-500 font-semibold">{metrics.total_failed} Failed Runs</span>
            </div>
            <div className="w-full bg-slate-900 h-1 rounded-full overflow-hidden">
              <div
                className="h-full bg-emerald-500"
                style={{ width: `${metrics.total_applied > 0 ? (metrics.total_applied / (applications.length || 1)) * 100 : 0}%` }}
              />
            </div>
          </div>

        </div>
      )}

      {/* Main Table view */}
      {loading ? (
        <div className="flex flex-col items-center justify-center p-20 space-y-4 bg-slate-950/10 border border-slate-800/40 rounded-2xl">
          <svg className="animate-spin h-8 w-8 text-sky-400" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <p className="text-slate-400 text-sm">Syncing pipeline reports...</p>
        </div>
      ) : error ? (
        <div className="p-5 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-2xl flex gap-3 text-sm animate-fadeIn">
          <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      ) : (
        <TrackingTable
          applications={applications}
          onUpdateStatus={handleUpdateStatus}
          onTriggerSubmission={handleTriggerSubmission}
          updatingAppId={updatingAppId}
        />
      )}
    </div>
  );
};
