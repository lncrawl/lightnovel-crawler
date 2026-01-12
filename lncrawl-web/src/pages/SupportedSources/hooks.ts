import type { SourceItem } from '@/types';
import { stringifyError } from '@/utils/errors';
import axios from 'axios';
import { useCallback, useEffect, useState } from 'react';

export function useSupportedSources() {
  const [refreshId, setRefreshId] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();
  const [data, setData] = useState<SourceItem[]>([]);

  useEffect(() => {
    const fetchNovelSources = async () => {
      try {
        const res = await axios.get<SourceItem[]>('/api/novel/sources');
        const novelSources = new Map<string, number>();
        for (const source of res.data) {
          novelSources.set(source.domain, source.total_novels);
        }
        setData((prev) =>
          prev.map((source) => ({
            ...source,
            total_novels: novelSources.get(source.domain) ?? 0,
          }))
        );
      } catch (err) {
        console.error(stringifyError(err));
      }
    };

    const fetchSupportedSources = async () => {
      try {
        setError(undefined);
        const res = await axios.get<SourceItem[]>(
          '/api/meta/supported-sources'
        );
        setData(res.data.sort((a, b) => a.domain.localeCompare(b.domain)));
        fetchNovelSources();
      } catch (err) {
        setError(stringifyError(err));
      } finally {
        setLoading(false);
      }
    };

    fetchSupportedSources();
  }, [refreshId]);

  const refresh = useCallback(() => {
    setRefreshId((v) => v + 1);
  }, []);

  return { data, loading, error, refresh };
}
