import React, { useState, useEffect, useCallback } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  ShieldQuestion,
  Plus,
  RefreshCw,
  Download,
  Trash2,
  X,
  AlertCircle,
  Globe,
} from 'lucide-react';
import { BrowserProfileManager } from './BrowserProfileManager';

interface PortalSession {
  id: string;
  portal_name: string;
  status: string;
  last_verified_at: string;
}

interface AccountHubProps {
  token: string;
}

const STATUS_CONFIG = {
  Healthy: { color: 'emerald', icon: ShieldCheck, label: 'Connected' },
  'Reconnect Required': { color: 'rose', icon: ShieldAlert, label: 'Reconnect Required' },
  'Verification Needed': { color: 'amber', icon: ShieldQuestion, label: 'Verification Needed' },
};

const PORTAL_NAMES = ['LinkedIn', 'Greenhouse', 'Lever', 'Workday', 'Naukri', 'Indeed'];

const API_BASE = import.meta.env?.VITE_API_URL || 'http://localhost:8000';

export const AccountHub: React.FC<AccountHubProps> = ({ token }) => {
  const [portals, setPortals] = useState<PortalSession[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [selectedPortal, setSelectedPortal] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [popupStatus, setPopupStatus] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'portals' | 'profiles'>('portals');

  const fetchVault = useCallback(async () => {
    try {
      const resp = await fetch(`${API_BASE}/api/v1/vault`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      setPortals(data);
    } catch (err) {
      setError(`Failed to load vault: ${err}`);
    }
  }, [token]);

  useEffect(() => {
    fetchVault();
  }, [fetchVault]);

  const handleOpenLoginWindow = async () => {
    if (!selectedPortal) return;
    setError(null);
    setLoading(true);

    try {
      const resp = await fetch(`${API_BASE}/api/v1/vault/browser-login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ portal_name: selectedPortal }),
      });

      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`);
      }

      const data = await resp.json();
      setPopupStatus(data.message);
      setShowModal(false);
      await fetchVault();
    } catch (err) {
      setError(`Could not load portal login metadata: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (portalName: string) => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(`${API_BASE}/api/v1/vault/${portalName}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      await fetchVault();
    } catch (err) {
      setError(`Failed to delete portal: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const config = STATUS_CONFIG[status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG['Verification Needed'];
    return (
      <span
        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-${config.color}-500/10 text-${config.color}-400 border border-${config.color}-500/20`}
      >
        <config.icon className="h-3 w-3" />
        {config.label}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Account Hub</h1>
          <p className="text-sm text-slate-400 mt-1">Manage your connected job portal sessions</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-sky-500/15 text-sky-400 border border-sky-500/30 rounded-xl font-medium text-sm hover:bg-sky-500/25 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Connect New Portal
        </button>
      </div>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-4 flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-rose-400 shrink-0" />
          <span className="text-sm text-rose-300">{error}</span>
          <button onClick={() => setError(null)} className="ml-auto text-rose-400 hover:text-rose-300">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {popupStatus && (
        <div className="bg-sky-500/10 border border-sky-500/30 rounded-xl p-4 text-sm text-sky-300">
          {popupStatus}
        </div>
      )}

      <div className="flex gap-2 border-b border-slate-800/50 pb-2">
        <button
          onClick={() => setActiveTab('portals')}
          className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
            activeTab === 'portals'
              ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent'
          }`}
        >
          <ShieldCheck className="h-4 w-4 inline mr-1.5" />
          Portals
        </button>
        <button
          onClick={() => setActiveTab('profiles')}
          className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
            activeTab === 'profiles'
              ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent'
          }`}
        >
          <Globe className="h-4 w-4 inline mr-1.5" />
          Browser Profiles
        </button>
      </div>

      {activeTab === 'portals' && portals.length === 0 && (
        <div className="bg-slate-950/40 border border-slate-800/60 rounded-xl p-8 text-center">
          <ShieldCheck className="h-12 w-12 text-slate-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-300 mb-2">No Connected Portals</h3>
          <p className="text-sm text-slate-500 mb-4">Connect a job portal to get started with session management.</p>
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-sky-500/15 text-sky-400 border border-sky-500/30 rounded-xl font-medium text-sm hover:bg-sky-500/25 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Connect Your First Portal
          </button>
        </div>
      )}

      {activeTab === 'portals' && portals.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {portals.map((portal) => (
            <div
              key={portal.id}
              className="bg-slate-950/40 border border-slate-800/60 rounded-xl p-5 space-y-4 hover:border-slate-700 transition-colors"
            >
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-white">{portal.portal_name}</h3>
                {getStatusBadge(portal.status)}
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between text-slate-400">
                  <span>Last Verified</span>
                  <span className="text-slate-300">
                    {new Date(portal.last_verified_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2 pt-2 border-t border-slate-800/50">
                <button
                  onClick={() => handleDelete(portal.portal_name)}
                  className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded-lg font-medium text-xs hover:bg-rose-500/20 transition-colors"
                >
                  <Trash2 className="h-3 w-3" />
                  Delete
                </button>
                <button
                  onClick={() => {
                    setSelectedPortal(portal.portal_name);
                    setShowModal(true);
                  }}
                  className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 bg-sky-500/10 text-sky-400 border border-sky-500/20 rounded-lg font-medium text-xs hover:bg-sky-500/20 transition-colors"
                >
                  <RefreshCw className="h-3 w-3" />
                  Reconnect
                </button>
                <button className="px-3 py-2 bg-slate-800/50 text-slate-400 border border-slate-700/50 rounded-lg font-medium text-xs hover:bg-slate-800 transition-colors">
                  <Download className="h-3 w-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'profiles' && <BrowserProfileManager token={token} />}

      {showModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 w-full max-w-md space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-white">Connect New Portal</h2>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Portal Name</label>
              <select
                value={selectedPortal}
                onChange={(e) => setSelectedPortal(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500"
              >
                <option value="">Select a portal...</option>
                {PORTAL_NAMES.map((name) => (
                  <option key={name} value={name}>
                    {name}
                  </option>
                ))}
              </select>
            </div>

            <p className="text-sm text-slate-400">
              A secure local browser profile will open for this portal. Sign in normally in that window; no cookies need to be copied.
            </p>

            <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-200">
              Your sign-in remains in the local browser profile and is reused by future discovery and applications. Security checks remain under your control.
            </div>

            {error && (
              <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-3 text-sm text-rose-300">
                {error}
              </div>
            )}

            <div className="flex items-center gap-3 pt-2">
              <button
                onClick={() => setShowModal(false)}
                className="flex-1 px-4 py-2.5 bg-slate-800 text-slate-300 border border-slate-700 rounded-xl font-medium text-sm hover:bg-slate-700 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleOpenLoginWindow}
                disabled={loading || !selectedPortal}
                className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-sky-500/15 text-sky-400 border border-sky-500/30 rounded-xl font-medium text-sm hover:bg-sky-500/25 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : <Globe className="h-4 w-4" />}
                Open Secure Login
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};