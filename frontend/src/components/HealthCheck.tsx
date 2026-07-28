import React, { useEffect, useState } from 'react';
import { ShieldAlert, AlertTriangle } from 'lucide-react';

export interface HealthStatus {
  status: 'healthy' | 'unhealthy' | 'offline';
  database: 'healthy' | 'unhealthy' | 'unknown';
  storage: 'healthy' | 'unhealthy' | 'unknown';
}

// eslint-disable-next-line react-refresh/only-export-components
export function useHealthCheck(intervalMs = 10000) {
  const [health, setHealth] = useState<HealthStatus>({
    status: 'offline',
    database: 'unknown',
    storage: 'unknown',
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    const meta = import.meta as unknown as { env?: { VITE_API_URL?: string } };
    const apiUrl = meta.env?.VITE_API_URL || 'http://localhost:8000';

    async function checkHealth() {
      try {
        const response = await fetch(`${apiUrl}/health`);
        if (!response.ok) {
          throw new Error('Health check responded with error');
        }
        const data = await response.json();
        if (active) {
          setHealth({
            status: data.status || 'unhealthy',
            database: data.database || 'unhealthy',
            storage: data.storage || 'unhealthy',
          });
          setLoading(false);
        }
      } catch (_error) {
        if (active) {
          setHealth({
            status: 'offline',
            database: 'unhealthy',
            storage: 'unhealthy',
          });
          setLoading(false);
        }
      }
    }

    checkHealth();
    const interval = setInterval(checkHealth, intervalMs);

    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [intervalMs]);

  return { health, loading };
}

interface HealthBadgeProps {
  status: 'healthy' | 'unhealthy' | 'offline';
}

export const HealthBadge: React.FC<HealthBadgeProps> = ({ status }) => {
  if (status === 'healthy') {
    return (
      <div className="flex items-center gap-1.5 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-full text-xs font-semibold text-emerald-400">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
        Backend: Online
      </div>
    );
  }

  if (status === 'unhealthy') {
    return (
      <div className="flex items-center gap-1.5 bg-amber-500/10 border border-amber-500/20 px-3 py-1 rounded-full text-xs font-semibold text-amber-400">
        <AlertTriangle className="h-3.5 w-3.5 text-amber-400 shrink-0" />
        Backend: Degraded
      </div>
    );
  }

  return (
    <div className="flex items-center gap-1.5 bg-rose-500/10 border border-rose-500/20 px-3 py-1 rounded-full text-xs font-semibold text-rose-400">
      <ShieldAlert className="h-3.5 w-3.5 text-rose-400 shrink-0" />
      Backend: Offline
    </div>
  );
};
