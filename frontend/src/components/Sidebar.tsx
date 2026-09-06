import React, { useState } from 'react';
import {
  LayoutDashboard,
  User,
  Search,
  Briefcase,
  Settings as SettingsIcon,
  LogOut,
  Menu,
  X,
  Compass,
  Shield,
  GitBranch,
} from 'lucide-react';

interface SidebarProps {
  currentSection: string;
  onSectionChange: (section: string) => void;
  onLogOut: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentSection, onSectionChange, onLogOut }) => {
  const [isOpen, setIsOpen] = useState(false);

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'discovery', label: 'Job discovery', icon: Search },
    { id: 'applications', label: 'Applications', icon: Briefcase },
    { id: 'vault', label: 'Account Hub', icon: Shield },
    { id: 'dependency-graph', label: 'Dependency Graph', icon: GitBranch },
    { id: 'settings', label: 'Settings', icon: SettingsIcon },
  ];

  return (
    <>
      {/* Mobile Menu Button */}
      <div className="lg:hidden fixed top-0 left-0 right-0 h-16 bg-slate-850 border-b border-slate-800 flex items-center justify-between px-4 z-50 bg-slate-900/90 backdrop-blur-md">
        <div className="flex items-center gap-2">
          <Compass className="h-6 w-6 text-sky-400 animate-pulse" />
          <span className="font-bold text-lg bg-gradient-to-r from-sky-400 to-indigo-400 bg-clip-text text-transparent">
            JobGraph
          </span>
        </div>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="p-2 text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded-lg transition-colors focus:outline-none"
        >
          {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {/* Sidebar Overlay for Mobile */}
      {isOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-16 lg:top-0 bottom-0 left-0 w-64 bg-slate-950 border-r border-slate-800/80 z-40 transition-transform duration-300 transform lg:transform-none lg:z-30 flex flex-col justify-between ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="px-4 py-6">
          {/* Logo - Hidden on mobile because it's in the mobile top bar */}
          <div className="hidden lg:flex items-center gap-2.5 px-3 mb-8">
            <Compass className="h-7 w-7 text-sky-400" />
            <span className="font-extrabold text-xl bg-gradient-to-r from-sky-400 via-sky-300 to-indigo-400 bg-clip-text text-transparent tracking-wide">
              JobGraph
            </span>
          </div>

          {/* Navigation Items */}
          <nav className="space-y-1.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentSection === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    onSectionChange(item.id);
                    setIsOpen(false);
                  }}
                  className={`w-full flex items-center gap-3.5 px-4 py-3 rounded-xl font-medium text-sm transition-all duration-200 ${
                    isActive
                      ? 'bg-gradient-to-r from-sky-500/15 to-indigo-500/15 text-sky-400 border-l-2 border-sky-400 shadow-[0_0_15px_-3px_rgba(14,165,233,0.15)]'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50 border-l-2 border-transparent'
                  }`}
                >
                  <Icon className={`h-5 w-5 shrink-0 ${isActive ? 'text-sky-400' : 'text-slate-400'}`} />
                  {item.label}
                </button>
              );
            })}
            
            {/* Log Out button in sidebar */}
            <button
              onClick={() => {
                onLogOut();
                setIsOpen(false);
              }}
              className="w-full flex items-center gap-3.5 px-4 py-3 rounded-xl font-medium text-sm text-rose-400/80 hover:text-rose-300 hover:bg-rose-500/10 border-l-2 border-transparent transition-all duration-200"
            >
              <LogOut className="h-5 w-5 shrink-0" />
              Sign Out
            </button>
          </nav>
        </div>

        {/* User Status Card at Bottom of Sidebar */}
        <div className="p-4 border-t border-slate-800/50 bg-slate-950/50">
          <div className="flex items-center gap-3 px-2 py-1.5">
            <div className="relative">
              <div className="h-10 w-10 rounded-full bg-slate-800 flex items-center justify-center text-sky-400 font-bold border border-slate-700 shadow-inner">
                JG
              </div>
              <span className="absolute bottom-0 right-0 block h-2.5 w-2.5 rounded-full bg-emerald-500 ring-2 ring-slate-950" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-slate-200 truncate">Candidate Account</p>
              <p className="text-xs text-slate-500 truncate">local-first mode</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};
