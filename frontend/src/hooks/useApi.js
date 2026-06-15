import { useState, useCallback } from 'react';

const BASE = '/api';

export function useApi() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const request = useCallback(async (path, options = {}) => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(`${BASE}${path}`, {
        headers: { 'Content-Type': 'application/json', ...options.headers },
        ...options,
      });
      if (!r.ok) {
        const text = await r.text();
        throw new Error(text || `HTTP ${r.status}`);
      }
      const contentType = r.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await r.json();
      }
      return await r.text();
    } catch (e) {
      setError(e.message);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  return { request, loading, error };
}
