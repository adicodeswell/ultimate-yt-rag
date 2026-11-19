import React from 'react';

const DOMAINS = [
  { id: 'all', label: 'All' },
  { id: 'backend', label: 'Backend' },
  { id: 'dsa', label: 'DSA' },
  { id: 'ai', label: 'AI' },
  { id: 'sql', label: 'SQL' },
  { id: 'other', label: 'Other' },
];

export function DomainFilter({ selectedDomain, onSelectDomain, disabled }) {
  return (
    <div className="flex flex-wrap gap-1.5 items-center">
      {DOMAINS.map((d) => {
        const isActive = (selectedDomain || 'all').toLowerCase() === d.id;
        return (
          <button
            key={d.id}
            type="button"
            disabled={disabled}
            onClick={() => onSelectDomain(d.id)}
            className={`px-2.5 py-1 text-xs font-medium rounded transition-colors ${
              isActive
                ? 'bg-zinc-200 text-zinc-950 font-semibold shadow-sm'
                : 'bg-zinc-900 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 border border-zinc-800'
            }`}
          >
            {d.label}
          </button>
        );
      })}
    </div>
  );
}
