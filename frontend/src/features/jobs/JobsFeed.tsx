import React, { useState, useEffect, useCallback } from 'react';
import {
  Search,
  SlidersHorizontal,
  RefreshCw,
  Sliders,
  AlertCircle,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Sparkles,
  MapPin,
  Building2,
  Calendar,
  CheckCircle,
  ArrowRight,
  Archive,
  Eye,
  EyeOff
} from 'lucide-react';
import { TailorPanel } from '../tailoring/TailorPanel';

interface MatchScore {
  id: string;
  overall_score: number;
  skill_score: number;
  experience_score: number;
  location_score: number;
  salary_score: number;
  is_archived: boolean;
  evaluated_at: string;
}

interface JobPosting {
  id: string;
  platform: string;
  external_job_id: string;
  board_token: string;
  title: string;
  company: string;
  location: string | null;
  url: string;
  description_text: string | null;
  discovered_at: string;
  match_score: MatchScore | null;
}

interface ExperienceItemOriginal {
  company: string;
  role: string;
  dates: string;
  description: string | null;
}

interface OriginalData {
  skills: string[];
  experiences: ExperienceItemOriginal[];
}

interface ExperienceItemTailored {
  company: string;
  role: string;
  dates: string;
  bullets: string[];
}

interface TailoredData {
  summary: string;
  skills: string[];
  experience: ExperienceItemTailored[];
}

interface CoverLetterData {
  subject: string;
  body: string;
}

interface TailorDetailResponse {
  application_id: string;
  status: string;
  mode: string;
  tailored_resume_key: string | null;
  cover_letter_key: string | null;
  tailored_resume_url: string | null;
  cover_letter_url: string | null;
  original_data: OriginalData;
  tailored_data: TailoredData | null;
  cover_letter: CoverLetterData | null;
}

interface JobsFeedProps {
  token: string;
}

export const JobsFeed: React.FC<JobsFeedProps> = ({ token }) => {
  const [jobs, setJobs] = useState<JobPosting[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filtering & Sorting states
  const [includeArchived, setIncludeArchived] = useState(false);
  const [minScore, setMinScore] = useState(0);
  const [sortBy, setSortBy] = useState<'score' | 'date'>('score');
  const [searchQuery, setSearchBy] = useState('');
  
  // Expanded Job IDs for showing description details
  const [expandedJobId, setExpandedJobId] = useState<string | null>(null);
  
  // Mock trigger tracking
  const [tailoringJobs, setTailoringJobs] = useState<Record<string, 'idle' | 'running' | 'done'>>({});

  // Active Tailor Panel Workspace states
  const [activeTailorJob, setActiveTailorJob] = useState<{ id: string; title: string; company: string; url: string } | null>(null);
  const [tailorData, setTailorData] = useState<TailorDetailResponse | null>(null);

  const meta = import.meta as unknown as { env?: { VITE_API_URL?: string } };
  const apiUrl = meta.env?.VITE_API_URL || 'http://localhost:8000';

  const fetchJobs = useCallback(async (runDiscovery = false) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${apiUrl}/api/v1/jobs?include_archived=true`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok && response.status !== 404) {
        throw new Error('Failed to retrieve discovered job postings.');
      }

      let data = response.ok ? await response.json() : [];
      if (runDiscovery) {
        const discoverResponse = await fetch(`${apiUrl}/api/v1/jobs/discover`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (discoverResponse.ok) {
          data = await discoverResponse.json();
        } else if (!Array.isArray(data) || data.length === 0) {
          throw new Error('Discovery pipeline did not return any jobs.');
        }
      }

      setJobs(data);
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : 'An error occurred while loading jobs.';
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  }, [apiUrl, token]);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  // Sort and filter logic on client viewport
  const filteredJobs = jobs
    .filter((job) => {
      // Archived filter
      const isArchived = job.match_score?.is_archived ?? false;
      if (!includeArchived && isArchived) return false;

      // Score filter
      const score = job.match_score?.overall_score ?? 0;
      if (score < minScore) return false;

      // Search query (title / company / location)
      const q = searchQuery.toLowerCase();
      if (q) {
        const titleMatch = job.title.toLowerCase().includes(q);
        const companyMatch = job.company.toLowerCase().includes(q);
        const locationMatch = (job.location ?? '').toLowerCase().includes(q);
        if (!titleMatch && !companyMatch && !locationMatch) return false;
      }

      return true;
    })
    .sort((a, b) => {
      if (sortBy === 'score') {
        const scoreA = a.match_score?.overall_score ?? 0;
        const scoreB = b.match_score?.overall_score ?? 0;
        return scoreB - scoreA; // descending
      } else {
        return new Date(b.discovered_at).getTime() - new Date(a.discovered_at).getTime(); // descending
      }
    });

  const handleStartTailoring = async (jobId: string, jobTitle: string, companyName: string) => {
    setTailoringJobs((prev) => ({ ...prev, [jobId]: 'running' }));
    try {
      // 1. Try to fetch existing tailoring details first
      const getResponse = await fetch(`${apiUrl}/api/v1/tailor/${jobId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (getResponse.ok) {
        const existingData = await getResponse.json();
        setTailorData(existingData);
        setActiveTailorJob({ id: jobId, title: jobTitle, company: companyName, url: jobs.find((job) => job.id === jobId)?.url || '' });
        setTailoringJobs((prev) => ({ ...prev, [jobId]: 'done' }));
        return;
      }

      // 2. If 404, trigger fresh tailoring pipeline
      const triggerResponse = await fetch(`${apiUrl}/api/v1/tailor/trigger`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ job_posting_id: jobId })
      });

      if (!triggerResponse.ok) {
        const errorDetail = await triggerResponse.json().catch(() => ({}));
        throw new Error(errorDetail.detail || 'Failed to trigger Gemini tailoring pipeline.');
      }

      const freshData = await triggerResponse.json();
      setTailorData(freshData);
      setActiveTailorJob({ id: jobId, title: jobTitle, company: companyName, url: jobs.find((job) => job.id === jobId)?.url || '' });
      setTailoringJobs((prev) => ({ ...prev, [jobId]: 'done' }));
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : 'An error occurred during tailoring.';
      alert(errMsg);
      setTailoringJobs((prev) => ({ ...prev, [jobId]: 'idle' }));
    }
  };

  const getScoreColorClass = (score: number) => {
    if (score >= 85) return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
    if (score >= 70) return 'text-sky-400 bg-sky-500/10 border-sky-500/20';
    if (score >= 50) return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
    return 'text-rose-400 bg-rose-500/10 border-rose-500/20';
  };

  const getScoreProgressBarClass = (score: number) => {
    if (score >= 85) return 'bg-emerald-500';
    if (score >= 70) return 'bg-sky-500';
    if (score >= 50) return 'bg-amber-500';
    return 'bg-rose-500';
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div className="flex items-center gap-3">
          <Search className="h-6 w-6 text-sky-400" />
          <div>
            <h2 className="text-xl font-bold text-white">Discovered Jobs Feed</h2>
            <p className="text-xs text-slate-500">Live feed of automatically discovered job postings and their match alignment scores</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
        <button
          onClick={() => fetchJobs(true)}
          disabled={loading}
          className="inline-flex items-center gap-2 px-4 py-2 bg-sky-500/15 hover:bg-sky-500/25 border border-sky-500/30 rounded-xl text-xs font-semibold text-sky-400 hover:text-sky-300 transition-all focus:outline-none disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          Discover Jobs
        </button>
        <button
          onClick={() => fetchJobs(false)}
          disabled={loading}
          className="inline-flex items-center gap-2 px-4 py-2 bg-slate-950/40 hover:bg-slate-900 border border-slate-800 hover:border-slate-700/80 rounded-xl text-xs font-semibold text-slate-300 hover:text-slate-200 transition-all focus:outline-none disabled:opacity-50"
        >
          Refresh Feed
        </button>
        </div>
      </div>

      {/* Filter / Controls Bar */}
      <div className="bg-slate-950/20 border border-slate-800/60 rounded-2xl p-5 space-y-4">
        <div className="flex flex-col lg:flex-row gap-4 items-center justify-between">
          
          {/* Left: Search box */}
          <div className="w-full lg:max-w-xs relative">
            <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search roles or companies..."
              value={searchQuery}
              onChange={(e) => setSearchBy(e.target.value)}
              className="w-full bg-slate-900/60 border border-slate-800 focus:border-sky-500/80 rounded-xl pl-10 pr-4 py-2 text-sm text-slate-200 outline-none transition-all placeholder:text-slate-600"
            />
          </div>

          {/* Middle/Right: Interactive Sliders/Toggles */}
          <div className="w-full flex flex-wrap gap-4 items-center lg:justify-end">
            
            {/* Minimum Score Filter */}
            <div className="flex items-center gap-2.5 bg-slate-900/40 border border-slate-800 px-3.5 py-1.5 rounded-xl">
              <Sliders className="h-4 w-4 text-slate-500" />
              <span className="text-xs font-semibold text-slate-400 whitespace-nowrap">Min Score: {minScore}+</span>
              <input
                type="range"
                min="0"
                max="100"
                step="5"
                value={minScore}
                onChange={(e) => setMinScore(Number(e.target.value))}
                className="w-24 sm:w-32 accent-sky-500 h-1 bg-slate-800 rounded-lg cursor-pointer"
              />
            </div>

            {/* Include Archived Toggle */}
            <button
              onClick={() => setIncludeArchived(!includeArchived)}
              className={`inline-flex items-center gap-2 px-3.5 py-1.5 border rounded-xl text-xs font-semibold transition-all focus:outline-none ${
                includeArchived
                  ? 'bg-sky-500/10 border-sky-500/30 text-sky-400'
                  : 'bg-slate-900/40 border-slate-800 text-slate-400 hover:text-slate-300 hover:bg-slate-850'
              }`}
            >
              {includeArchived ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
              {includeArchived ? 'Showing Archived' : 'Hiding Archived (<70)'}
            </button>

            {/* Sort Select */}
            <div className="flex items-center gap-2 bg-slate-900/40 border border-slate-800 px-3.5 py-1.5 rounded-xl">
              <SlidersHorizontal className="h-4 w-4 text-slate-500" />
              <select
                value={sortBy}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSortBy(e.target.value as 'score' | 'date')}
                className="bg-transparent text-xs font-semibold text-slate-300 outline-none cursor-pointer border-none p-0 focus:ring-0"
              >
                <option value="score" className="bg-slate-950 text-slate-300">Sort by: Score</option>
                <option value="date" className="bg-slate-950 text-slate-300">Sort by: Date</option>
              </select>
            </div>

          </div>
        </div>
      </div>

      {/* Main Jobs Feed List */}
      {loading ? (
        <div className="flex flex-col items-center justify-center p-20 space-y-4">
          <svg className="animate-spin h-8 w-8 text-sky-400" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <p className="text-slate-400 text-sm">Fetching and syncing matching listings...</p>
        </div>
      ) : error ? (
        <div className="p-5 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-2xl flex gap-3 text-sm animate-fadeIn">
          <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      ) : filteredJobs.length === 0 ? (
        <div className="p-16 border-2 border-dashed border-slate-800 rounded-2xl text-center">
          <div className="h-12 w-12 rounded-full bg-slate-900 flex items-center justify-center text-slate-500 mx-auto mb-4 border border-slate-800">
            <Search className="h-6 w-6" />
          </div>
          <h3 className="text-base font-semibold text-slate-200">No Job Listings Found</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto mt-2 leading-relaxed">
            No listings currently match your filter selections or queries. Adjust minimum scoring levels or keywords above.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredJobs.map((job) => {
            const score = job.match_score?.overall_score ?? 0;
            const isArchived = job.match_score?.is_archived ?? false;
            const isExpanded = expandedJobId === job.id;
            const tailorState = tailoringJobs[job.id] || 'idle';
            
            return (
              <div
                key={job.id}
                className={`bg-slate-950/20 hover:bg-slate-950/40 border border-slate-800/60 rounded-2xl p-6 transition-all duration-300 space-y-4 ${
                  isArchived ? 'opacity-60 border-slate-900' : ''
                }`}
              >
                {/* Job Information Header */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                  <div className="space-y-1.5 min-w-0 flex-1">
                    <div className="flex flex-wrap gap-2 items-center">
                      <span className="text-[10px] font-bold px-2 py-0.5 uppercase tracking-wider bg-slate-900 border border-slate-800 text-slate-400 rounded">
                        {job.platform}
                      </span>
                      {isArchived && (
                        <span className="text-[10px] font-bold px-2 py-0.5 uppercase tracking-wider bg-amber-500/10 border border-amber-500/20 text-amber-400 rounded flex items-center gap-1">
                          <Archive className="h-3 w-3" /> Archived
                        </span>
                      )}
                    </div>
                    
                    <h3 className="text-lg font-bold text-white tracking-tight truncate hover:text-sky-300 transition-colors">
                      <a href={job.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5">
                        {job.title} <ExternalLink className="h-4 w-4 text-slate-500" />
                      </a>
                    </h3>

                    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-slate-400 font-medium">
                      <span className="flex items-center gap-1.5">
                        <Building2 className="h-3.5 w-3.5 text-slate-500" /> {job.company}
                      </span>
                      <span className="flex items-center gap-1.5">
                        <MapPin className="h-3.5 w-3.5 text-slate-500" /> {job.location || 'Remote'}
                      </span>
                      <span className="flex items-center gap-1.5">
                        <Calendar className="h-3.5 w-3.5 text-slate-500" /> Discovered {new Date(job.discovered_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>

                  {/* Right side: Overall Score badge */}
                  <div className="flex items-center gap-3.5 self-start sm:self-center shrink-0">
                    <div className={`px-4 py-2 border rounded-xl text-center min-w-24 ${getScoreColorClass(score)}`}>
                      <div className="text-[10px] font-bold uppercase tracking-wider opacity-60">Match Score</div>
                      <div className="text-xl font-extrabold">{score}%</div>
                    </div>
                  </div>
                </div>

                {/* Sub-component: Score breakdown progress bars */}
                {job.match_score && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-slate-900/10 border border-slate-800/40 rounded-xl text-xs">
                    {[
                      { label: 'Skills Alignment (40%)', val: job.match_score.skill_score },
                      { label: 'Experience Match (30%)', val: job.match_score.experience_score },
                      { label: 'Preferred Location (15%)', val: job.match_score.location_score },
                      { label: 'Salary Target (15%)', val: job.match_score.salary_score }
                    ].map((item, index) => (
                      <div key={index} className="space-y-1.5">
                        <div className="flex justify-between font-semibold text-slate-400">
                          <span>{item.label}</span>
                          <span className="text-slate-200">{item.val}%</span>
                        </div>
                        <div className="w-full bg-slate-850 h-1.5 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${getScoreProgressBarClass(item.val)}`}
                            style={{ width: `${item.val}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Expanded Section Toggle */}
                <div className="flex items-center justify-between border-t border-slate-800/50 pt-4 text-xs font-semibold">
                  <button
                    onClick={() => setExpandedJobId(isExpanded ? null : job.id)}
                    className="inline-flex items-center gap-1.5 text-slate-400 hover:text-slate-200 focus:outline-none"
                  >
                    {isExpanded ? (
                      <>
                        Hide Details <ChevronUp className="h-4 w-4" />
                      </>
                    ) : (
                      <>
                        View Description <ChevronDown className="h-4 w-4" />
                      </>
                    )}
                  </button>

                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => handleStartTailoring(job.id, job.title, job.company)}
                      disabled={tailorState === 'running'}
                      className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold shadow-sm transition-all focus:outline-none ${
                        tailorState === 'running'
                          ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30'
                          : tailorState === 'done'
                          ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                          : 'bg-gradient-to-r from-sky-500 to-indigo-500 hover:from-sky-400 hover:to-indigo-400 text-white shadow-[0_0_15px_-3px_rgba(14,165,233,0.15)]'
                      } disabled:opacity-50 disabled:cursor-not-allowed`}
                    >
                      {tailorState === 'running' ? (
                        <>
                          <svg className="animate-spin h-3.5 w-3.5" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                          </svg>
                          Analyzing...
                        </>
                      ) : tailorState === 'done' ? (
                        <>
                          <CheckCircle className="h-3.5 w-3.5" />
                          Application Ready
                        </>
                      ) : (
                        <>
                          <Sparkles className="h-3.5 w-3.5" />
                          Tailor Application <ArrowRight className="h-3.5 w-3.5" />
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {/* Expandable description text block */}
                {isExpanded && (
                  <div className="pt-4 border-t border-slate-800/40 text-sm text-slate-300 leading-relaxed font-sans max-h-96 overflow-y-auto bg-slate-950/40 p-4 rounded-xl space-y-4">
                    <h4 className="text-xs font-bold tracking-wider text-slate-400 uppercase">Job Description Plain Text</h4>
                    <p className="whitespace-pre-wrap">{job.description_text || 'No plain text description loaded.'}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {activeTailorJob && tailorData && (
        <TailorPanel
          jobId={activeTailorJob.id}
          jobTitle={activeTailorJob.title}
          companyName={activeTailorJob.company}
          data={tailorData}
          onApply={async () => {
            const response = await fetch(`${apiUrl}/api/v1/applications/${tailorData.application_id}/dispatch`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
              },
              body: JSON.stringify({
                job_url: activeTailorJob.url,
                mode: tailorData.mode || 'Autonomous',
                portal_name: null,
                requires_review: false,
              }),
            });
            const detail = await response.json().catch(() => ({}));
            if (!response.ok) {
              throw new Error(detail.detail || 'Failed to queue the browser application.');
            }
            alert('Application queued. The browser worker will open the portal and continue the application.');
            setActiveTailorJob(null);
            setTailorData(null);
          }}
          onClose={() => {
            setActiveTailorJob(null);
            setTailorData(null);
          }}
        />
      )}
    </div>
  );
};
