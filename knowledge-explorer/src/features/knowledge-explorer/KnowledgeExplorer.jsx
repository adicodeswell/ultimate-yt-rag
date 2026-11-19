import React from 'react';
import { useKnowledgeSearch } from './useKnowledgeSearch';
import { SearchBar } from './SearchBar';
import { DomainFilter } from './DomainFilter';
import { ResultsList } from './ResultsList';
import { VideoPlayer } from './VideoPlayer';
import { TranscriptViewer } from './TranscriptViewer';

export function KnowledgeExplorer({
  apiBaseUrl = import.meta.env.VITE_KNOWLEDGE_API_URL || 'http://localhost:8000',
  defaultLimit = 5,
  showDomainFilter = true,
  initialDomain = 'all',
  className = '',
  onResultSelect,
}) {
  const {
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
  } = useKnowledgeSearch({
    apiBaseUrl,
    defaultLimit,
    initialDomain,
    onResultSelect,
  });

  const handleDomainSelect = (newDomain) => {
    setDomain(newDomain);
    if (query.trim()) {
      executeSearch(query, newDomain);
    }
  };

  return (
    <div className={`w-full max-w-7xl mx-auto px-4 py-6 ${className}`}>
      {/* Header */}
      <header className="mb-6">
        <h1 className="text-xl font-bold tracking-tight text-zinc-100 flex items-center gap-2">
          <span>YouTube Knowledge Explorer</span>
        </h1>
        <p className="text-xs text-zinc-400 mt-1">
          Search technical concepts to find and play original video segments at the relevant timestamp.
        </p>
      </header>

      {/* Main Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Controls & Results */}
        <section className="lg:col-span-5 space-y-4">
          <SearchBar
            query={query}
            onQueryChange={setQuery}
            onSearch={() => executeSearch(query, domain)}
            loading={loading}
          />

          {showDomainFilter && (
            <DomainFilter
              selectedDomain={domain}
              onSelectDomain={handleDomainSelect}
              disabled={loading}
            />
          )}

          <div className="pt-2">
            <ResultsList
              results={results}
              selectedResultId={selectedResultId}
              onSelect={selectResult}
              loading={loading}
              error={error}
              onRetry={() => executeSearch(query, domain)}
            />
          </div>
        </section>

        {/* Right Column: Player & Excerpt */}
        <section className="lg:col-span-7 space-y-4 lg:sticky lg:top-6">
          <div className="bg-zinc-900/40 border border-zinc-800/80 rounded-xl p-4 space-y-4">
            <VideoPlayer item={selectedResult} />
            <TranscriptViewer item={selectedResult} />
          </div>
        </section>
      </div>
    </div>
  );
}

export default KnowledgeExplorer;
