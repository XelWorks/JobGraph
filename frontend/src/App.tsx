import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './features/dashboard/Dashboard';
import { Profile } from './features/profiles/Profile';
import { AuthForm } from './features/auth/AuthForm';
import { JobsFeed } from './features/jobs/JobsFeed';
import { Applications } from './features/applications/Applications';
import { AccountHub } from './features/vault/AccountHub';
import { DependencyGraph } from './features/graph/DependencyGraph';
import { AutonomyControlPanel } from './features/autonomy/AutonomyControlPanel';
import { useHealthCheck, HealthBadge } from './components/HealthCheck';
import {
  Settings,
  HelpCircle,
  Bell,
  CheckCircle2,
  Bot,
} from 'lucide-react';

const decodeJwt = (jwt: string): { exp?: number } | null => {
  try {
    const payload = jwt.split('.')[1];
    if (!payload) return null;
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/');
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=');
    return JSON.parse(atob(padded)) as { exp?: number };
  } catch {
    return null;
  }
};

export const App: React.FC = () => {
  const [token, setToken] = useState<string | null>(null);
  const [currentSection, setCurrentSection] = useState('dashboard');
  const { health } = useHealthCheck();

  // Load token from localStorage on initial render
  useEffect(() => {
    const savedToken = localStorage.getItem('jobgraph_jwt');
    if (savedToken) {
      const payload = decodeJwt(savedToken);
      const isExpired = payload && typeof payload.exp === 'number' && payload.exp * 1000 <= Date.now();
      if (isExpired) {
        localStorage.removeItem('jobgraph_jwt');
        setToken(null);
        return;
      }
      setToken(savedToken);
    }
  }, []);

  useEffect(() => {
    if (!token) return;

    const payload = decodeJwt(token);
    const isExpired = payload && typeof payload.exp === 'number' && payload.exp * 1000 <= Date.now();
    if (isExpired) {
      handleLogOut();
    }
  }, [token]);

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
        return <JobsFeed token={token} />;
      case 'applications':
        return <Applications token={token} />;
      case 'autonomy':
        return <AutonomyControlPanel token={token} />;
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
      case 'vault':
        return <AccountHub token={token} />;
      case 'dependency-graph':
        return <DependencyGraph token={token} />;
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
