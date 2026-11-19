import React from 'react';
import { ResultCard } from './ResultCard';

export function ResultsList({ results, selectedResultId, onSelect, loading, error, onRetry }) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="p-4 rounded-lg border border-zinc-800 bg-zinc-900/40 animate-pulse">
            <div className="h-4 bg-zinc-800 rounded w-1/4 mb-3" />
            <div className="h-4 bg-zinc-800 rounded w-3/4 mb-2" />
            <div className="h-3 bg-zinc-800/60 rounded w-full" />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 rounded-lg border border-red-900/50 bg-red-950/20 text-center">
        <p className="text-sm text-red-300 mb-2">{error.message || 'Failed to load search results.'}</p>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="px-3 py-1 bg-zinc-800 hover:bg-zinc-700 text-xs font-medium text-zinc-200 rounded border border-zinc-700 transition-colors"
          >
            Retry
          </button>
        )}
      </div>
    );
  }

  if (results === null) {
    return (
      <div className="py-12 text-center text-zinc-500 border border-dashed border-zinc-800 rounded-lg">
        <p className="text-sm">Search a technical concept above to explore video segments.</p>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="py-12 text-center text-zinc-400 border border-zinc-800/80 bg-zinc-900/20 rounded-lg">
        <p className="text-sm font-medium text-zinc-300 mb-1">No matching segments found.</p>
        <p className="text-xs text-zinc-500">Try a broader search term or change your domain filter.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2.5">
      <div className="text-xs font-medium text-zinc-500 px-1">
        Results ({results.length})
      </div>
      {results.map((item) => (
        <ResultCard
          key={item.id}
          item={item}
          isSelected={item.id === selectedResultId}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}
