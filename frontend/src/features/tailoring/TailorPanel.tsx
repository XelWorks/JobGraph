import React from 'react';
import {
  X,
  Download,
  Sparkles,
  FileText,
  CheckCircle,
  ChevronRight,
  Play,
  Loader
} from 'lucide-react';

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

interface TailorPanelProps {
  jobId: string;
  jobTitle: string;
  companyName: string;
  data: TailorDetailResponse;
  onApply: () => Promise<void>;
  onClose: () => void;
}

export const TailorPanel: React.FC<TailorPanelProps> = ({
  jobTitle,
  companyName,
  data,
  onApply,
  onClose
}) => {
  const [activeTab, setActiveSection] = React.useState<'resume' | 'cover-letter'>('resume');
  const [applying, setApplying] = React.useState(false);

  const handleDownload = (url: string | null, label: string) => {
    if (!url) {
      alert("Download URL is not available. Please try re-triggering tailoring.");
      return;
    }
    // Print secure download generation success logs
    console.log(`[JobGraph Client] Secure pre-signed download URL generated for ${label}: ${url}`);
    window.open(url, '_blank');
  };

  const handleApply = async () => {
    setApplying(true);
    try {
      await onApply();
    } finally {
      setApplying(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex justify-end animate-fadeIn">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-slate-950/70 backdrop-blur-sm transition-opacity" 
        onClick={onClose}
      />

      {/* Drawer Container */}
      <div className="relative w-full max-w-5xl h-full bg-slate-950 border-l border-slate-800 shadow-2xl flex flex-col z-10 animate-slideLeft">
        
        {/* Panel Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-slate-800/80 bg-slate-950 shrink-0">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Application Tailoring Workspace</h2>
              <p className="text-xs text-slate-400">
                Custom resume and cover letter matching <span className="font-semibold text-slate-200">{jobTitle}</span> at <span className="font-semibold text-slate-200">{companyName}</span>
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-slate-900 border border-slate-800 rounded-xl text-slate-400 hover:text-white transition-all outline-none"
          >
            <X className="h-4.5 w-4.5" />
          </button>
        </div>

        {/* Workspace Sub-Header / Tabs */}
        <div className="flex items-center justify-between px-6 py-3 bg-slate-900/40 border-b border-slate-800/60 shrink-0">
          <div className="flex gap-2">
            <button
              onClick={() => setActiveSection('resume')}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all ${
                activeTab === 'resume'
                  ? 'bg-sky-500/10 border border-sky-500/30 text-sky-400'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 border border-transparent'
              }`}
            >
              Resume Side-by-Side Comparison
            </button>
            <button
              onClick={() => setActiveSection('cover-letter')}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all ${
                activeTab === 'cover-letter'
                  ? 'bg-sky-500/10 border border-sky-500/30 text-sky-400'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 border border-transparent'
              }`}
            >
              Tailored Cover Letter
            </button>
          </div>

          <div className="flex gap-3">
            {activeTab === 'resume' ? (
              <button
                onClick={() => handleDownload(data.tailored_resume_url, 'Tailored Resume PDF')}
                disabled={!data.tailored_resume_url}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-sky-500 to-indigo-500 hover:from-sky-400 hover:to-indigo-400 text-white rounded-lg text-xs font-bold transition-all disabled:opacity-50"
              >
                <Download className="h-3.5 w-3.5" /> Download Resume PDF
              </button>
            ) : (
              <button
                onClick={() => handleDownload(data.cover_letter_url, 'Tailored Cover Letter PDF')}
                disabled={!data.cover_letter_url}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-sky-500 to-indigo-500 hover:from-sky-400 hover:to-indigo-400 text-white rounded-lg text-xs font-bold transition-all disabled:opacity-50"
              >
                <Download className="h-3.5 w-3.5" /> Download Cover Letter PDF
              </button>
            )}
            <button
              onClick={handleApply}
              disabled={applying || !data.tailored_resume_url}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/15 hover:bg-emerald-500/25 border border-emerald-500/30 text-emerald-400 rounded-lg text-xs font-bold transition-all disabled:opacity-50"
            >
              {applying ? <Loader className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5 fill-current" />}
              Apply Now
            </button>
          </div>
        </div>

        {/* Dynamic Workspace Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-6 min-h-0 bg-slate-950/40">
          {activeTab === 'resume' ? (
            <div className="space-y-6">
              
              {/* Summary custom block */}
              {data.tailored_data?.summary && (
                <div className="bg-slate-900/30 border border-slate-800 rounded-xl p-5 space-y-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-sky-400 flex items-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5" /> Tailored Professional Summary
                  </h3>
                  <p className="text-sm text-slate-300 leading-relaxed font-sans italic">
                    "{data.tailored_data.summary}"
                  </p>
                </div>
              )}

              {/* Skills side-by-side list */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-slate-900/10 border border-slate-800/60 rounded-xl p-5 space-y-3">
                  <h4 className="text-xs font-bold tracking-wider uppercase text-slate-400">Original Profile Skills</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {data.original_data.skills.map((skill, i) => (
                      <span key={i} className="text-xs bg-slate-900 border border-slate-800 px-2.5 py-1 rounded text-slate-400">
                        {skill}
                      </span>
                    ))}
                    {data.original_data.skills.length === 0 && (
                      <span className="text-xs text-slate-500 italic">No skills registered on profile.</span>
                    )}
                  </div>
                </div>

                <div className="bg-sky-950/10 border border-sky-950/40 rounded-xl p-5 space-y-3">
                  <h4 className="text-xs font-bold tracking-wider uppercase text-sky-400 flex items-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5 animate-pulse" /> Gemini ATS-Ranked Skills
                  </h4>
                  <div className="flex flex-wrap gap-1.5">
                    {(data.tailored_data?.skills ?? []).map((skill, i) => (
                      <span key={i} className="text-xs bg-sky-950/30 border border-sky-500/20 px-2.5 py-1 rounded text-sky-300 font-medium">
                        {skill}
                      </span>
                    ))}
                    {(!data.tailored_data || data.tailored_data.skills.length === 0) && (
                      <span className="text-xs text-slate-500 italic">No tailored skills returned.</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Experience side-by-side comparison */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-white border-b border-slate-800 pb-2">Professional Experience Alignment</h3>
                
                {data.original_data.experiences.map((origExp, index) => {
                  const tailoredExp = data.tailored_data?.experience.find(
                    (e) => e.company.toLowerCase() === origExp.company.toLowerCase() || e.role.toLowerCase() === origExp.role.toLowerCase()
                  ) || data.tailored_data?.experience[index];

                  return (
                    <div key={index} className="grid grid-cols-1 lg:grid-cols-2 gap-6 border-b border-slate-900 pb-6 last:border-b-0">
                      
                      {/* Left: Original Experience */}
                      <div className="bg-slate-900/10 border border-slate-800/40 rounded-xl p-5 space-y-3">
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="text-sm font-bold text-slate-200">{origExp.role}</h4>
                            <p className="text-xs text-slate-400 font-semibold">{origExp.company}</p>
                          </div>
                          <span className="text-[10px] bg-slate-900 text-slate-500 px-2 py-0.5 rounded border border-slate-850">
                            {origExp.dates}
                          </span>
                        </div>
                        <div className="space-y-2">
                          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Original Description</span>
                          <p className="text-xs text-slate-400 whitespace-pre-wrap leading-relaxed">
                            {origExp.description || "No description provided."}
                          </p>
                        </div>
                      </div>

                      {/* Right: Tailored Experience */}
                      <div className="bg-sky-950/5 border border-sky-950/20 rounded-xl p-5 space-y-3">
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="text-sm font-bold text-white inline-flex items-center gap-1">
                              {tailoredExp?.role || origExp.role}
                            </h4>
                            <p className="text-xs text-sky-400 font-semibold">{tailoredExp?.company || origExp.company}</p>
                          </div>
                          <span className="text-[10px] bg-sky-950/20 text-sky-400 px-2 py-0.5 rounded border border-sky-500/10">
                            {tailoredExp?.dates || origExp.dates}
                          </span>
                        </div>
                        <div className="space-y-2">
                          <span className="text-[10px] font-bold text-sky-400 uppercase tracking-wider flex items-center gap-1">
                            <Sparkles className="h-3 w-3" /> Tailored Impact Accomplishments
                          </span>
                          <ul className="space-y-2 list-none text-xs text-slate-300 pl-1 leading-relaxed">
                            {tailoredExp?.bullets.map((bullet, idx) => (
                              <li key={idx} className="flex gap-2 items-start">
                                <ChevronRight className="h-3.5 w-3.5 text-sky-400 shrink-0 mt-0.5" />
                                <span>{bullet}</span>
                              </li>
                            ))}
                            {(!tailoredExp || tailoredExp.bullets.length === 0) && (
                              <li className="text-slate-500 italic">No tailored bullet accomplishments generated.</li>
                            )}
                          </ul>
                        </div>
                      </div>

                    </div>
                  );
                })}
              </div>

            </div>
          ) : (
            /* Cover letter tab */
            <div className="space-y-6 max-w-3xl mx-auto">
              <div className="bg-slate-900/30 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
                
                {/* Email Subject envelope */}
                <div className="px-6 py-4 bg-slate-900 border-b border-slate-800 flex items-center gap-3">
                  <FileText className="h-4.5 w-4.5 text-slate-400" />
                  <div className="text-xs font-semibold text-slate-400">
                    Subject: <span className="text-slate-200 font-bold ml-1">{data.cover_letter?.subject || "Job Application"}</span>
                  </div>
                </div>

                {/* Cover letter content */}
                <div className="p-8 space-y-4 text-sm text-slate-300 leading-relaxed font-sans whitespace-pre-wrap bg-slate-950/50">
                  {data.cover_letter?.body || "Cover letter has not been customized."}
                </div>

              </div>
            </div>
          )}
        </div>

        {/* Panel Footer */}
        <div className="p-6 border-t border-slate-800/80 bg-slate-950 shrink-0 flex items-center justify-between text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-emerald-500" />
            <span>Pre-signed keys expire after 15 minutes to guarantee security</span>
          </div>
          <button
            onClick={onClose}
            className="px-5 py-2.5 bg-slate-900 hover:bg-slate-850 border border-slate-800 rounded-xl text-slate-200 font-semibold transition-all hover:text-white"
          >
            Close Workspace
          </button>
        </div>

      </div>
    </div>
  );
};
