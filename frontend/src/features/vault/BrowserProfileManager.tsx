import React, { useState, useEffect, useCallback } from 'react';
import {
  Globe,
  RefreshCw,
  Download,
  Trash2,
  X,
  Save,
  AlertCircle,
  CheckCircle2,
  AlertTriangle,
  Clock,
} from 'lucide-react';

interface BrowserProfile {
  id: string;
  profile_name: string;
  engine: string;
  user_agent: string;
  cookie_status: string;
  storage_status: string;
  last_verified_at: string;
  health: string;
}

interface BrowserProfileManagerProps {
  token: string;
}

const API_BASE = import.meta.env?.VITE_API_URL || 'http://localhost:8000';

const HEALTH_CONFIG = {
  Healthy: { color: 'emerald', icon: CheckCircle2, label: 'Healthy' },
  'Cookies Valid': { color: 'sky', icon: CheckCircle2, label: 'Cookies Valid' },
  'Storage Present': { color: 'amber', icon: AlertTriangle, label: 'Storage Present' },
};

const COOKIE_STATUS_CONFIG = {
  valid: { color: 'emerald', label: 'Valid' },
  expired: { color: 'rose', label: 'Expired' },
  missing: { color: 'amber', label: 'Missing' },
};

const STORAGE_STATUS_CONFIG = {
  present: { color: 'emerald', label: 'Present' },
  missing: { color: 'rose', label: 'Missing' },
  partial: { color: 'amber', label: 'Partial' },
};

export const BrowserProfileManager: React.FC<BrowserProfileManagerProps> = ({ token }) => {
  const [profiles, setProfiles] = useState<BrowserProfile[]>([]);
  const [showExportModal, setShowExportModal] = useState(false);
  const [selectedProfile, setSelectedProfile] = useState<BrowserProfile | null>(null);
  const [exportFormat, setExportFormat] = useState('json');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchProfiles = useCallback(async () => {
    try {
      const resp = await fetch(`${API_BASE}/api/v1/vault/profiles`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      setProfiles(data);
    } catch (err) {
      setError(`Failed to load browser profiles: ${err}`);
    }
  }, [token]);

  useEffect(() => {
    fetchProfiles();
  }, [fetchProfiles]);

  const handleExportCookies = async () => {
    if (!selectedProfile) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(
        `${API_BASE}/api/v1/vault/${selectedProfile.profile_name}/export-cookies`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ format: exportFormat }),
        }
      );
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${selectedProfile.profile_name}-cookies.${exportFormat}`;
      a.click();
      URL.revokeObjectURL(url);
      setShowExportModal(false);
    } catch (err) {
      setError(`Failed to export cookies: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteProfile = async (profileName: string) => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(`${API_BASE}/api/v1/vault/profiles/${profileName}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      await fetchProfiles();
    } catch (err) {
      setError(`Failed to delete profile: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  const handleReconnect = async (profileName: string) => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(
        `${API_BASE}/api/v1/vault/${profileName}/reconnect`,
        {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      await fetchProfiles();
    } catch (err) {
      setError(`Failed to reconnect profile: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  const getHealthBadge = (health: string) => {
    const config = HEALTH_CONFIG[health as keyof typeof HEALTH_CONFIG] || HEALTH_CONFIG['Storage Present'];
    return (
      <span
        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-${config.color}-500/10 text-${config.color}-400 border border-${config.color}-500/20`}
      >
        <config.icon className="h-3 w-3" />
        {config.label}
      </span>
    );
  };

  const getCookieBadge = (status: string) => {
    const config = COOKIE_STATUS_CONFIG[status as keyof typeof COOKIE_STATUS_CONFIG] || COOKIE_STATUS_CONFIG.missing;
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-${config.color}-500/10 text-${config.color}-400`}>
        {config.label}
      </span>
    );
  };

  const getStorageBadge = (status: string) => {
    const config = STORAGE_STATUS_CONFIG[status as keyof typeof STORAGE_STATUS_CONFIG] || STORAGE_STATUS_CONFIG.missing;
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-${config.color}-500/10 text-${config.color}-400`}>
        {config.label}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">Browser Profiles</h2>
          <p className="text-sm text-slate-400 mt-1">Inspect and manage browser profile sessions</p>
        </div>
        <button
          onClick={fetchProfiles}
          className="inline-flex items-center gap-2 px-3 py-2 bg-slate-800/50 text-slate-300 border border-slate-700/50 rounded-xl font-medium text-sm hover:bg-slate-700/50 transition-colors"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
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

      {profiles.length === 0 ? (
        <div className="bg-slate-950/40 border border-slate-800/60 rounded-xl p-8 text-center">
          <Globe className="h-12 w-12 text-slate-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-300 mb-2">No Browser Profiles</h3>
          <p className="text-sm text-slate-500 mb-4">Connect a portal in Account Hub to see browser profiles here.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {profiles.map((profile) => (
            <div
              key={profile.id}
              className="bg-slate-950/40 border border-slate-800/60 rounded-xl p-5 space-y-4 hover:border-slate-700 transition-colors"
            >
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-white">{profile.profile_name}</h3>
                {getHealthBadge(profile.health)}
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between text-slate-400">
                  <span>Engine</span>
                  <span className="text-slate-300">{profile.engine}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Cookies</span>
                  {getCookieBadge(profile.cookie_status)}
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Storage</span>
                  {getStorageBadge(profile.storage_status)}
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Last Verified</span>
                  <span className="text-slate-300 flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {new Date(profile.last_verified_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>User-Agent</span>
                  <span className="text-slate-300 text-xs font-mono truncate max-w-[60%]" title={profile.user_agent}>
                    {profile.user_agent}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2 pt-2 border-t border-slate-800/50">
                <button
                  onClick={() => handleReconnect(profile.profile_name)}
                  className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 bg-sky-500/10 text-sky-400 border border-sky-500/20 rounded-lg font-medium text-xs hover:bg-sky-500/20 transition-colors"
                >
                  <RefreshCw className="h-3 w-3" />
                  Reconnect
                </button>
                <button
                  onClick={() => {
                    setSelectedProfile(profile);
                    setExportFormat('json');
                    setShowExportModal(true);
                  }}
                  className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-lg font-medium text-xs hover:bg-emerald-500/20 transition-colors"
                >
                  <Download className="h-3 w-3" />
                  Export
                </button>
                <button
                  onClick={() => handleDeleteProfile(profile.profile_name)}
                  className="px-3 py-2 bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded-lg font-medium text-xs hover:bg-rose-500/20 transition-colors"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showExportModal && selectedProfile && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 w-full max-w-md space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-white">Export Cookies</h2>
              <button onClick={() => setShowExportModal(false)} className="text-slate-400 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>

            <p className="text-sm text-slate-400">
              Export cookies for <span className="text-white font-medium">{selectedProfile.profile_name}</span>
            </p>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Format</label>
              <select
                value={exportFormat}
                onChange={(e) => setExportFormat(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500"
              >
                <option value="json">JSON</option>
                <option value="csv">CSV</option>
                <option value="netscape">Netscape</option>
              </select>
            </div>

            {error && (
              <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-3 text-sm text-rose-300">
                {error}
              </div>
            )}

            <div className="flex items-center gap-3 pt-2">
              <button
                onClick={() => setShowExportModal(false)}
                className="flex-1 px-4 py-2.5 bg-slate-800 text-slate-300 border border-slate-700 rounded-xl font-medium text-sm hover:bg-slate-700 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleExportCookies}
                disabled={loading}
                className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 rounded-xl font-medium text-sm hover:bg-emerald-500/25 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                Export
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};