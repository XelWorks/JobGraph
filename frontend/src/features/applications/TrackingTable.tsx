import React from 'react';
import {
  Briefcase,
  Clock,
  CheckCircle2,
  XCircle,
  FileText,
  MessageSquare,
  ChevronRight,
  ExternalLink,
  Loader,
  Play
} from 'lucide-react';

export interface JobCompact {
  id: string;
  title: string;
  company: string;
  location: string | null;
  url: string;
}

export interface ApplicationRecord {
  id: string;
  user_id: string;
  job_posting_id: string;
  status: 'Backlog' | 'Scheduled' | 'Auto-Filled' | 'Submitted' | 'Failed';
  mode: 'Manual' | 'Assisted' | 'Autonomous';
  tailored_resume_key: string | null;
  cover_letter_key: string | null;
  tailored_resume_url: string | null;
  cover_letter_url: string | null;
  date_applied: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  job_posting: JobCompact;
}

interface TrackingTableProps {
  applications: ApplicationRecord[];
  onUpdateStatus: (appId: string, status: string, notes?: string) => Promise<void>;
  onTriggerSubmission: (appId: string, mode: string) => Promise<void>;
  updatingAppId: string | null;
}

export const TrackingTable: React.FC<TrackingTableProps> = ({
  applications,
  onUpdateStatus,
  onTriggerSubmission,
  updatingAppId
}) => {
  const [selectedNotesApp, setSelectedNotesApp] = React.useState<{ id: string; notes: string; status: string } | null>(null);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Submitted':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-bold rounded-lg border bg-emerald-500/10 border-emerald-500/20 text-emerald-400">
            <CheckCircle2 className="h-3.5 w-3.5" /> Submitted
          </span>
        );
      case 'Failed':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-bold rounded-lg border bg-rose-500/10 border-rose-500/20 text-rose-400">
            <XCircle className="h-3.5 w-3.5" /> Failed
          </span>
        );
      case 'Scheduled':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-bold rounded-lg border bg-sky-500/10 border-sky-500/20 text-sky-400">
            <Clock className="h-3.5 w-3.5 animate-pulse" /> Scheduled
          </span>
        );
      case 'Auto-Filled':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-bold rounded-lg border bg-indigo-500/10 border-indigo-500/20 text-indigo-400">
            <Briefcase className="h-3.5 w-3.5" /> Auto-Filled
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-bold rounded-lg border bg-slate-800/40 border-slate-700/60 text-slate-400">
            <Clock className="h-3.5 w-3.5" /> Backlog
          </span>
        );
    }
  };

  const getModeBadge = (mode: string) => {
    switch (mode) {
      case 'Autonomous':
        return (
          <span className="text-[10px] font-extrabold px-2 py-0.5 uppercase tracking-wider rounded bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            🤖 Autonomous
          </span>
        );
      case 'Assisted':
        return (
          <span className="text-[10px] font-extrabold px-2 py-0.5 uppercase tracking-wider rounded bg-sky-500/10 border border-sky-500/20 text-sky-400">
            🤝 Assisted
          </span>
        );
      default:
        return (
          <span className="text-[10px] font-extrabold px-2 py-0.5 uppercase tracking-wider rounded bg-slate-900 border border-slate-800 text-slate-400">
            ✍️ Manual
          </span>
        );
    }
  };

  const handleOpenNotes = (app: ApplicationRecord) => {
    setSelectedNotesApp({ id: app.id, notes: app.notes || '', status: app.status });
  };

  const handleSaveNotes = async () => {
    if (!selectedNotesApp) return;
    await onUpdateStatus(selectedNotesApp.id, selectedNotesApp.status, selectedNotesApp.notes);
    setSelectedNotesApp(null);
  };

  return (
    <div className="bg-slate-950/20 border border-slate-800/60 rounded-2xl overflow-hidden animate-fadeIn">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-800/80 bg-slate-950/40 text-xs font-bold uppercase tracking-wider text-slate-400">
              <th className="px-6 py-4.5">Job / Position</th>
              <th className="px-6 py-4.5">Submission Mode</th>
              <th className="px-6 py-4.5">Pipeline Status</th>
              <th className="px-6 py-4.5">Tailored Documents</th>
              <th className="px-6 py-4.5">Applied Date</th>
              <th className="px-6 py-4.5 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/40 text-sm text-slate-300">
            {applications.map((app) => (
              <tr key={app.id} className="hover:bg-slate-950/30 transition-all">
                {/* Job Info */}
                <td className="px-6 py-4 max-w-xs">
                  <div className="space-y-1">
                    <h4 className="font-bold text-white tracking-tight truncate hover:text-sky-300 transition-colors">
                      <a href={app.job_posting.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1">
                        {app.job_posting.title} <ExternalLink className="h-3.5 w-3.5 text-slate-500" />
                      </a>
                    </h4>
                    <p className="text-xs text-slate-400 font-medium">
                      {app.job_posting.company} &bull; {app.job_posting.location || 'Remote'}
                    </p>
                  </div>
                </td>

                {/* Submission Mode */}
                <td className="px-6 py-4">
                  {getModeBadge(app.mode)}
                </td>

                {/* Pipeline Status */}
                <td className="px-6 py-4">
                  {getStatusBadge(app.status)}
                </td>

                {/* Tailored Files */}
                <td className="px-6 py-4">
                  <div className="flex gap-2.5">
                    {app.tailored_resume_url ? (
                      <a
                        href={app.tailored_resume_url}
                        target="_blank"
                        rel="noreferrer"
                        title="View Tailored Resume PDF"
                        className="p-1.5 rounded-lg border border-slate-800 bg-slate-900/60 hover:border-sky-500/30 text-sky-400 hover:text-sky-300 transition-all"
                      >
                        <FileText className="h-4.5 w-4.5" />
                      </a>
                    ) : (
                      <span className="text-xs text-slate-600 italic">None</span>
                    )}

                    {app.cover_letter_url && (
                      <a
                        href={app.cover_letter_url}
                        target="_blank"
                        rel="noreferrer"
                        title="View Tailored Cover Letter PDF"
                        className="p-1.5 rounded-lg border border-slate-800 bg-slate-900/60 hover:border-sky-500/30 text-sky-400 hover:text-sky-300 transition-all"
                      >
                        <FileText className="h-4.5 w-4.5 text-indigo-400 hover:text-indigo-300" />
                      </a>
                    )}
                  </div>
                </td>

                {/* Date Applied */}
                <td className="px-6 py-4 text-xs font-medium text-slate-400">
                  {app.date_applied ? (
                    new Date(app.date_applied).toLocaleDateString()
                  ) : (
                    <span className="text-slate-600 italic">Pending</span>
                  )}
                </td>

                {/* Action Buttons */}
                <td className="px-6 py-4 text-right">
                  <div className="inline-flex gap-2">
                    {/* Log result / edit notes */}
                    <button
                      onClick={() => handleOpenNotes(app)}
                      className="p-1.5 rounded-lg border border-slate-800 hover:border-slate-700 bg-slate-900/40 text-slate-400 hover:text-white transition-all outline-none"
                      title="Update notes & status"
                    >
                      <MessageSquare className="h-4 w-4" />
                    </button>

                    {/* Run play Trigger button if not yet submitted */}
                    {app.status !== 'Submitted' && (
                      <button
                        onClick={() => onTriggerSubmission(app.id, app.mode)}
                        disabled={updatingAppId !== null}
                        className="inline-flex items-center gap-1 px-3 py-1.5 bg-gradient-to-r from-sky-500 to-indigo-500 hover:from-sky-400 hover:to-indigo-400 text-white rounded-lg text-xs font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Run Submission"
                      >
                        {updatingAppId === app.id ? (
                          <Loader className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                          <Play className="h-3.5 w-3.5 fill-current" />
                        )}
                        Run
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {applications.length === 0 && (
              <tr>
                <td colSpan={6} className="p-16 text-center">
                  <div className="h-12 w-12 rounded-full bg-slate-900 flex items-center justify-center text-slate-500 mx-auto mb-4 border border-slate-800">
                    <Briefcase className="h-6 w-6" />
                  </div>
                  <h3 className="text-base font-semibold text-slate-200">No Applications Logged</h3>
                  <p className="text-xs text-slate-500 max-w-md mx-auto mt-2 leading-relaxed">
                    Trigger application customization or discovery to start tracking listings here.
                  </p>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Edit Notes / Logging Modal Overlay */}
      {selectedNotesApp && (
        <div className="fixed inset-0 z-50 flex items-center justify-center animate-fadeIn p-4">
          <div className="absolute inset-0 bg-slate-950/70 backdrop-blur-sm" onClick={() => setSelectedNotesApp(null)} />
          <div className="relative w-full max-w-lg bg-slate-950 border border-slate-800 shadow-2xl rounded-2xl p-6 space-y-4 z-10 animate-slideUp">
            
            <div className="flex justify-between items-center border-b border-slate-800 pb-3.5">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">Log Application Status & Notes</h3>
              <button onClick={() => setSelectedNotesApp(null)} className="text-slate-500 hover:text-white transition-all text-xs">✕</button>
            </div>

            <div className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-400">Application Status</label>
                <select
                  value={selectedNotesApp.status}
                  onChange={(e) => setSelectedNotesApp({ ...selectedNotesApp, status: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-800 focus:border-sky-500/80 rounded-xl px-3 py-2 text-sm text-slate-200 outline-none cursor-pointer"
                >
                  <option value="Backlog">Backlog</option>
                  <option value="Scheduled">Scheduled</option>
                  <option value="Auto-Filled">Auto-Filled (Customized PDFs)</option>
                  <option value="Submitted">Submitted (Success)</option>
                  <option value="Failed">Failed</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-400">Recruiter Notes & Logs</label>
                <textarea
                  value={selectedNotesApp.notes}
                  onChange={(e) => setSelectedNotesApp({ ...selectedNotesApp, notes: e.target.value })}
                  placeholder="Record interview invites, application issues, or next steps..."
                  className="w-full h-32 bg-slate-900 border border-slate-800 focus:border-sky-500/80 rounded-xl px-3 py-2 text-sm text-slate-200 outline-none placeholder:text-slate-600 resize-none"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setSelectedNotesApp(null)}
                className="px-4 py-2 border border-slate-800 text-slate-400 hover:text-white rounded-lg text-xs font-semibold transition-all hover:bg-slate-900"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveNotes}
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-sky-500 to-indigo-500 hover:from-sky-400 hover:to-indigo-400 text-white rounded-lg text-xs font-bold transition-all"
              >
                Save Details <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>

          </div>
        </div>
      )}
    </div>
  );
};
