import { useState, useRef, useCallback } from 'react';
import { searchKnowledge } from './knowledgeApi';

export function useKnowledgeSearch({ apiBaseUrl = '', defaultLimit = 5, initialDomain = 'all', onResultSelect }) {
  const [query, setQuery] = useState('');
  const [domain, setDomain] = useState(initialDomain);
  const [results, setResults] = useState(null);
  const [selectedResultId, setSelectedResultId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const abortControllerRef = useRef(null);

  const selectResult = useCallback((item) => {
    if (!item) {
      setSelectedResultId(null);
      return;
    }
    setSelectedResultId(item.id);
    if (onResultSelect) {
      onResultSelect(item);
    }
  }, [onResultSelect]);

  const executeSearch = useCallback(async (searchQuery = query, searchDomain = domain) => {
    const trimmed = (searchQuery || '').trim();
    if (!trimmed) {
      setError({ message: 'Enter a search query.' });
      return;
    }

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setLoading(true);
    setError(null);

    try {
      const data = await searchKnowledge({
        apiBaseUrl,
        query: trimmed,
        domain: searchDomain,
        limit: defaultLimit,
        signal: controller.signal,
      });

      const newResults = data.results || [];
      setResults(newResults);

      if (newResults.length > 0) {
        selectResult(newResults[0]);
      } else {
        selectResult(null);
      }
    } catch (err) {
      if (err.name === 'AbortError') return;
      setError({ message: err.message || 'An unexpected error occurred.' });
      setResults([]);
      selectResult(null);
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl, defaultLimit, query, domain, selectResult]);

  const selectedResult = results?.find((r) => r.id === selectedResultId) || null;

  return {
    query,
    setQuery,
    domain,
    setDomain,
    results,
    selectedResult,
    selectedResultId,
    selectResult,
    loading,
    error,
    executeSearch,
  };
}
