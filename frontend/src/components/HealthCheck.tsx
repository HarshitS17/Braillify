import { useState, useEffect, useCallback } from 'react';
import type { HealthResponse } from '../types';
import { apiClient } from '../services/api';

type ConnectionStatus = 'checking' | 'connected' | 'disconnected';

export function HealthCheck() {
  const [status, setStatus] = useState<ConnectionStatus>('checking');
  const [healthData, setHealthData] = useState<HealthResponse | null>(null);

  const checkHealth = useCallback(async () => {
    setStatus('checking');
    try {
      const data = await apiClient.checkHealth();
      setHealthData(data);
      setStatus('connected');
    } catch (err) {
      setStatus('disconnected');
    }
  }, []);

  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  const statusConfig = {
    checking: {
      bgColor: 'bg-amber-100',
      dotColor: 'bg-amber-500',
      textColor: 'text-amber-800',
      label: 'Checking API',
    },
    connected: {
      bgColor: 'bg-emerald-100',
      dotColor: 'bg-emerald-500',
      textColor: 'text-emerald-800',
      label: 'Connected',
    },
    disconnected: {
      bgColor: 'bg-rose-100',
      dotColor: 'bg-rose-500',
      textColor: 'text-rose-800',
      label: 'Offline',
    },
  };

  const config = statusConfig[status];

  return (
    <div
      onClick={checkHealth}
      className={`flex items-center gap-2 px-2.5 py-1 rounded-full cursor-pointer transition-colors ${config.bgColor}`}
      role="status"
      aria-live="polite"
      title={healthData ? `Backend: ${healthData.service} v${healthData.version}` : 'Click to retry connection'}
    >
      <span
        className={`inline-block h-2 w-2 rounded-full ${config.dotColor} ${
          status === 'checking' ? 'animate-pulse' : ''
        }`}
        aria-hidden="true"
      />
      <span className={`text-xs font-semibold ${config.textColor}`}>
        {config.label}
      </span>
    </div>
  );
}
