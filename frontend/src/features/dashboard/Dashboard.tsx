import React from 'react';
import {
  Briefcase,
  Layers,
  Sparkles,
  ArrowUpRight,
  TrendingUp,
  Database,
  CloudLightning,
  Flame,
  CheckCircle,
  Clock
} from 'lucide-react';

export interface HealthStatus {
  status: 'healthy' | 'unhealthy' | 'offline';
  database: 'healthy' | 'unhealthy' | 'unknown';
  storage: 'healthy' | 'unhealthy' | 'unknown';
}

interface DashboardProps {
  health?: HealthStatus;
}

export const Dashboard: React.FC<DashboardProps> = ({ health }) => {
  const stats = [
    { label: 'Jobs Matched', value: '142', icon: Layers, trend: '+18% this week', trendType: 'up' },
    { label: 'Resumes Tailored', value: '24', icon: Sparkles, trend: '+4 today', trendType: 'up' },
    { label: 'Applications Submitted', value: '12', icon: Briefcase, trend: '+2 yesterday', trendType: 'up' },
    { label: 'Success/Match Rate', value: '84%', icon: TrendingUp, trend: 'Optimal matching', trendType: 'neutral' },
  ];

  const recentApplications = [
    { company: 'Acme Corp', position: 'Senior Full Stack Engineer', status: 'In Review', date: 'Jul 26, 2026', match: '92%' },
    { company: 'GlobalTech Solutions', position: 'Backend Platform Engineer', status: 'Applied', date: 'Jul 24, 2026', match: '88%' },
    { company: 'AI Labs Inc', position: 'Generative AI Developer', status: 'Tailoring', date: 'Jul 23, 2026', match: '95%' },
    { company: 'DataSphere', position: 'Software Engineer (SaaS)', status: 'Matched', date: 'Jul 21, 2026', match: '81%' },
  ];

  const backendStatus = health ? (health.status === 'healthy' ? 'Online' : health.status === 'unhealthy' ? 'Degraded' : 'Offline') : 'Online';
  const dbStatus = health ? (health.database === 'healthy' ? 'Connected' : 'Disconnected') : 'Connected';
  const storageStatus = health ? (health.storage === 'healthy' ? 'Available' : 'Unavailable') : 'Available';

  const services = [
    { 
      name: 'FastAPI Backend', 
      status: backendStatus, 
      isHealthy: health ? health.status === 'healthy' : true,
      isOffline: health ? health.status === 'offline' : false,
      desc: 'Sinks routes and dispatches background runner tasks', 
      type: 'system' 
    },
    { 
      name: 'PostgreSQL DB', 
      status: dbStatus, 
      isHealthy: health ? health.database === 'healthy' : true,
      isOffline: health ? health.status === 'offline' : false,
      desc: 'Caches profiles, job boards, and application logs', 
      type: 'database' 
    },
    { 
      name: 'MinIO Storage', 
      status: storageStatus, 
      isHealthy: health ? health.storage === 'healthy' : true,
      isOffline: health ? health.status === 'offline' : false,
      desc: 'Secure local object store for customized resumes/artifacts', 
      type: 'storage' 
    },
  ];

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden bg-slate-950/40 rounded-2xl border border-slate-800/80 p-6 md:p-8">
        <div className="absolute top-0 right-0 -mt-4 -mr-4 w-56 h-56 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-2xl">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20 mb-4">
            <Flame className="h-3.5 w-3.5" /> Core Setup Confirmed
          </span>
          <h1 className="text-2xl md:text-3.5xl font-extrabold tracking-tight text-white mb-2 leading-tight">
            Elevate Your Job Hunt with <span className="bg-gradient-to-r from-sky-400 via-sky-300 to-indigo-400 bg-clip-text text-transparent">JobGraph</span>
          </h1>
          <p className="text-sm md:text-base text-slate-400 leading-relaxed">
            Welcome to your open-source, privacy-first AI job automation dashboard. All data is kept securely on your local machine, optimizing your applications using stateful agentic workflows.
          </p>
        </div>
      </div>

      {/* Statistics Banner Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, i) => {
          const Icon = stat.icon;
          return (
            <div
              key={i}
              className="bg-slate-950/20 hover:bg-slate-950/40 border border-slate-800/50 hover:border-slate-800 rounded-xl p-5 transition-all duration-300 group"
            >
              <div className="flex items-start justify-between mb-4">
                <span className="text-sm font-medium text-slate-400 group-hover:text-slate-300 transition-colors">
                  {stat.label}
                </span>
                <div className="p-2.5 bg-slate-900 rounded-lg border border-slate-800/60 group-hover:border-slate-700/80 group-hover:bg-slate-950 text-sky-400 transition-all">
                  <Icon className="h-5 w-5" />
                </div>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold tracking-tight text-white">{stat.value}</span>
                <span className={`text-xs font-medium ${
                  stat.trendType === 'up' ? 'text-emerald-400' : 'text-slate-400'
                }`}>
                  {stat.trend}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Funnel Tracking */}
        <div className="lg:col-span-2 bg-slate-950/20 border border-slate-800/60 rounded-xl p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-base font-bold text-white">Application Funnel</h3>
                <p className="text-xs text-slate-500">Live pipeline status of automatic applications</p>
              </div>
              <button className="inline-flex items-center gap-1 text-xs font-semibold text-sky-400 hover:text-sky-300 transition-colors">
                View Funnel <ArrowUpRight className="h-3.5 w-3.5" />
              </button>
            </div>

            <div className="space-y-3">
              {recentApplications.map((app, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between p-3 bg-slate-900/30 hover:bg-slate-900/60 border border-slate-800/40 rounded-xl transition-all"
                >
                  <div className="min-w-0 flex-1 pr-4">
                    <p className="text-sm font-semibold text-slate-200 truncate">{app.position}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-slate-400 font-medium truncate">{app.company}</span>
                      <span className="h-1 w-1 rounded-full bg-slate-700" />
                      <span className="text-xs text-slate-500">{app.date}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs px-2.5 py-1 rounded-full font-medium bg-slate-800/80 border border-slate-700/50 text-slate-300">
                      Match: <span className="text-sky-400 font-semibold">{app.match}</span>
                    </span>
                    <span className={`text-xs px-2.5 py-1 rounded-full font-semibold border ${
                      app.status === 'Applied'
                        ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                        : app.status === 'In Review'
                        ? 'bg-indigo-500/10 border-indigo-500/20 text-indigo-400'
                        : app.status === 'Tailoring'
                        ? 'bg-amber-500/10 border-amber-500/20 text-amber-400'
                        : 'bg-slate-800 border-slate-700 text-slate-300'
                    }`}>
                      {app.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Local Services Status Card */}
        <div className="bg-slate-950/20 border border-slate-800/60 rounded-xl p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2.5 mb-6">
              <Database className="h-5 w-5 text-sky-400" />
              <div>
                <h3 className="text-base font-bold text-white">Infrastructure Status</h3>
                <p className="text-xs text-slate-500">Validation indicators of local services</p>
              </div>
            </div>

            <div className="space-y-4">
              {services.map((service, i) => (
                <div key={i} className="flex items-start gap-3 p-3 bg-slate-900/20 border border-slate-800/30 rounded-xl">
                  {service.type === 'system' ? (
                    <CloudLightning className="h-5 w-5 text-sky-400 shrink-0 mt-0.5" />
                  ) : service.type === 'database' ? (
                    <Database className="h-5 w-5 text-indigo-400 shrink-0 mt-0.5" />
                  ) : (
                    <Database className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
                  )}
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-semibold text-slate-200">{service.name}</p>
                      <span className={`inline-flex items-center gap-1 text-xs font-semibold px-1.5 py-0.5 rounded ${
                        service.isOffline
                          ? 'text-rose-400 bg-rose-500/10 border border-rose-500/20'
                          : service.isHealthy
                          ? 'text-emerald-400 bg-emerald-500/10 border border-emerald-500/20'
                          : 'text-amber-400 bg-amber-500/10 border border-amber-500/20'
                      }`}>
                        <span className={`h-1.5 w-1.5 rounded-full ${
                          service.isOffline
                            ? 'bg-rose-400'
                            : service.isHealthy
                            ? 'bg-emerald-400 animate-pulse'
                            : 'bg-amber-400 animate-pulse'
                        }`} />
                        {service.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1 leading-normal">{service.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-800/40 text-center">
            <span className="text-xs text-slate-500">JobGraph Framework v0.1 • Localhost Deployment</span>
          </div>
        </div>
      </div>

      {/* Task & Process Outline */}
      <div className="bg-slate-950/20 border border-slate-800/60 rounded-xl p-6">
        <h3 className="text-base font-bold text-white mb-2">Automated Funnel Lifecycle</h3>
        <p className="text-xs text-slate-500 mb-6">How the platform intelligently processes applications locally</p>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { step: '1', title: 'ATS Discovery', desc: 'Scans Glassdoor, Lever, Greenhouse boards for job postings.', icon: Clock, color: 'text-sky-400' },
            { step: '2', title: 'Agent Matching', desc: 'LangGraph parses candidate profile with job post details.', icon: CheckCircle, color: 'text-indigo-400' },
            { step: '3', title: 'Local Tailoring', desc: 'Generates professional resume versions via Gemini.', icon: Sparkles, color: 'text-purple-400' },
            { step: '4', title: 'Playwright Run', desc: 'Fills and submits job application forms autonomously.', icon: Briefcase, color: 'text-emerald-400' }
          ].map((item, i) => {
            const Icon = item.icon;
            return (
              <div key={i} className="relative p-4 bg-slate-900/25 border border-slate-800/50 rounded-xl">
                <span className={`absolute top-3 right-4 font-black text-3xl opacity-10 ${item.color}`}>
                  0{item.step}
                </span>
                <Icon className={`h-5 w-5 mb-3.5 ${item.color}`} />
                <h4 className="text-sm font-semibold text-slate-200 mb-1">{item.title}</h4>
                <p className="text-xs text-slate-500 leading-normal">{item.desc}</p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
