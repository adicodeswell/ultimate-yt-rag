import React from 'react';

export function TranscriptViewer({ item }) {
  if (!item || !item.text) {
    return null;
  }

  return (
    <div className="bg-zinc-900/60 border border-zinc-800/80 rounded-lg p-3.5 space-y-2">
      <div className="flex items-center justify-between text-xs text-zinc-400">
        <span className="font-semibold text-zinc-300">Relevant Transcript Excerpt</span>
        <span className="font-mono text-zinc-500">
          [{item.start_formatted} - {item.end_formatted}]
        </span>
      </div>

      <p className="text-xs text-zinc-300 leading-relaxed whitespace-pre-line font-normal">
        {item.text}
      </p>
    </div>
  );
}
