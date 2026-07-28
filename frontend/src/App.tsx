import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './features/dashboard/Dashboard';
import { Profile } from './features/profiles/Profile';
import { AuthForm } from './features/auth/AuthForm';
import { useHealthCheck, HealthBadge } from './components/HealthCheck';
import {
  Search,
  Briefcase,
  Settings,
  HelpCircle,
  Bell,
  CheckCircle2,
} from 'lucide-react';

export const App: React.FC = () => {
  const [token, setToken] = useState<string | null>(null);
  const [currentSection, setCurrentSection] = useState('dashboard');
  const { health } = useHealthCheck();

  // Load token from localStorage on initial render
  useEffect(() => {
    const savedToken = localStorage.getItem('jobgraph_jwt');
    if (savedToken) {
      setToken(savedToken);
    }
  }, []);

  const handleAuthSuccess = (jwtToken: string) => {
    localStorage.setItem('jobgraph_jwt', jwtToken);
    setToken(jwtToken);
    setCurrentSection('dashboard');
  };

  const handleLogOut = () => {
    localStorage.removeItem('jobgraph_jwt');
    setToken(null);
    setCurrentSection('dashboard');
  };

  // Render auth screens exclusively if JWT token is missing
  if (!token) {
    return <AuthForm onAuthSuccess={handleAuthSuccess} />;
  }

  const renderContent = () => {
    switch (currentSection) {
      case 'dashboard':
        return <Dashboard health={health} />;
      case 'profile':
        return <Profile token={token} />;
      case 'discovery':
        return (
          <div className="bg-slate-950/20 border border-slate-800/60 rounded-xl p-8 max-w-4xl space-y-6">
            <div className="flex items-center gap-3 border-b border-slate-800 pb-5">
              <Search className="h-6 w-6 text-sky-400" />
              <div>
                <h2 className="text-xl font-bold text-white">Job Discovery</h2>
                <p className="text-xs text-slate-500">Intelligent background crawler matching from ATS connectors</p>
              </div>
            </div>
            <div className="p-16 border-2 border-dashed border-slate-800 rounded-xl text-center">
              <div className="h-12 w-12 rounded-full bg-slate-900 flex items-center justify-center text-slate-500 mx-auto mb-4 border border-slate-800">
                <Search className="h-6 w-6" />
              </div>
              <h3 className="text-base font-semibold text-slate-200">No Job Listings Loaded</h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto mt-2 leading-relaxed">
                Connect your Greenhouse and Lever APIs or configure search keywords to initiate automatic candidate crawling.
              </p>
            </div>
          </div>
        );
      case 'applications':
        return (
          <div className="bg-slate-950/20 border border-slate-800/60 rounded-xl p-8 max-w-4xl space-y-6">
            <div className="flex items-center gap-3 border-b border-slate-800 pb-5">
              <Briefcase className="h-6 w-6 text-sky-400" />
              <div>
                <h2 className="text-xl font-bold text-white">Applications Funnel</h2>
                <p className="text-xs text-slate-500">Track current and historic automated job submission runs</p>
              </div>
            </div>
            <div className="p-16 border-2 border-dashed border-slate-800 rounded-xl text-center">
              <div className="h-12 w-12 rounded-full bg-slate-900 flex items-center justify-center text-slate-500 mx-auto mb-4 border border-slate-800">
                <Briefcase className="h-6 w-6" />
              </div>
              <h3 className="text-base font-semibold text-slate-200">No Active Submissions</h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto mt-2 leading-relaxed">
                Matched job listings will trigger automatic tailoring and headless Playwright submits. Your running applications list will populate here.
              </p>
            </div>
          </div>
        );
      case 'settings':
        return (
          <div className="bg-slate-950/20 border border-slate-800/60 rounded-xl p-8 max-w-4xl space-y-6">
            <div className="flex items-center gap-3 border-b border-slate-800 pb-5">
              <Settings className="h-6 w-6 text-sky-400" />
              <div>
                <h2 className="text-xl font-bold text-white">Platform Settings</h2>
                <p className="text-xs text-slate-500">Configure credentials, target locations, LLM settings, and local rates</p>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-400">Gemini LLM Key Status</label>
                <div className="flex items-center justify-between bg-slate-900/60 border border-slate-800 px-4 py-2.5 rounded-lg text-sm text-slate-300">
                  <span>Sourced from Environment</span>
                  <span className="flex items-center gap-1 text-emerald-400 font-semibold text-xs bg-emerald-500/10 px-1.5 py-0.5 rounded">
                    <CheckCircle2 className="h-3 w-3" /> Valid
                  </span>
                </div>
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-400">Playwright Run Mode</label>
                <div className="bg-slate-900/60 border border-slate-800 px-4 py-2.5 rounded-lg text-sm text-slate-300">
                  Headless (Default Background Running)
                </div>
              </div>
            </div>
          </div>
        );
      default:
        return <Dashboard health={health} />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 font-sans flex">
      {/* Sidebar - fixed on desktop, absolute overlay on mobile */}
      <Sidebar currentSection={currentSection} onSectionChange={setCurrentSection} onLogOut={handleLogOut} />

      {/* Main Content Area */}
      <div className="flex-1 lg:pl-64 flex flex-col min-h-screen">
        {/* Top Header */}
        <header className="h-16 border-b border-slate-800/70 bg-slate-900/80 backdrop-blur-md flex items-center justify-between px-6 lg:px-8 shrink-0 sticky top-0 z-20">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-slate-400 capitalize bg-slate-800 px-2.5 py-1 rounded-full border border-slate-700/60">
              Section: {currentSection}
            </span>
          </div>

          <div className="flex items-center gap-4">
            {/* Connection Check Indicator */}
            <HealthBadge status={health.status} />

            <button className="p-2 text-slate-400 hover:text-slate-200 transition-colors rounded-lg hover:bg-slate-800">
              <Bell className="h-5 w-5" />
            </button>
            <button className="p-2 text-slate-400 hover:text-slate-200 transition-colors rounded-lg hover:bg-slate-800">
              <HelpCircle className="h-5 w-5" />
            </button>
          </div>
        </header>

        {/* Dynamic Content Viewport */}
        <main className="flex-1 p-6 md:p-8 lg:p-10 max-w-7xl w-full mx-auto pb-16">
          {renderContent()}
        </main>
      </div>
    </div>
  );
};
