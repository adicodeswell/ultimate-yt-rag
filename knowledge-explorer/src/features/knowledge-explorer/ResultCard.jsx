import React from 'react';

export function ResultCard({ item, isSelected, onSelect }) {
  return (
    <button
      type="button"
      onClick={() => onSelect(item)}
      className={`w-full text-left p-3.5 rounded-lg border transition-all text-sm group ${
        isSelected
          ? 'bg-zinc-800/90 border-zinc-400 shadow-sm ring-1 ring-zinc-400'
          : 'bg-zinc-900/60 border-zinc-800/80 hover:bg-zinc-850 hover:border-zinc-700'
      }`}
    >
      <div className="flex items-start justify-between gap-2 mb-1.5">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono font-semibold text-zinc-400 bg-zinc-800 px-1.5 py-0.5 rounded border border-zinc-700">
            #{item.rank}
          </span>
          <span className="text-xs font-mono text-zinc-400">
            {item.start_formatted} - {item.end_formatted}
          </span>
        </div>

        {item.domains && item.domains.length > 0 && (
          <div className="flex gap-1 flex-wrap justify-end">
            {item.domains.map((dom) => (
              <span
                key={dom}
                className="text-[11px] uppercase tracking-wider text-zinc-400 bg-zinc-800/60 px-1.5 py-0.5 rounded"
              >
                {dom}
              </span>
            ))}
          </div>
        )}
      </div>

      <h3 className={`font-medium line-clamp-1 mb-1.5 ${isSelected ? 'text-zinc-100 font-semibold' : 'text-zinc-200'}`}>
        {item.title}
      </h3>

      <p className="text-xs text-zinc-400 line-clamp-2 leading-relaxed">
        {item.text}
      </p>
    </button>
  );
}
