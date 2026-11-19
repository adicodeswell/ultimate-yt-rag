import React from 'react';

export function SearchBar({ query, onQueryChange, onSearch, loading }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch();
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 w-full">
      <div className="relative flex-1">
        <input
          type="text"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          placeholder="Search technical concepts (e.g. TCP handshake, sliding window)..."
          className="w-full bg-zinc-900 border border-zinc-700 focus:border-zinc-400 focus:ring-1 focus:ring-zinc-400 text-zinc-100 placeholder-zinc-500 rounded-md px-3.5 py-2 text-sm outline-none transition-colors"
          disabled={loading}
        />
      </div>
      <button
        type="submit"
        disabled={loading || !query.trim()}
        className="px-4 py-2 bg-zinc-100 hover:bg-white text-zinc-900 font-medium text-sm rounded-md disabled:opacity-40 disabled:cursor-not-allowed transition-colors shrink-0"
      >
        {loading ? 'Searching...' : 'Search'}
      </button>
    </form>
  );
}
