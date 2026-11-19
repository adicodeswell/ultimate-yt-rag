import React, { useState } from 'react';

export function VideoPlayer({ item }) {
  const [copied, setCopied] = useState(false);

  if (!item || !item.video_id) {
    return (
      <div className="w-full aspect-video bg-zinc-900 border border-zinc-800 rounded-lg flex items-center justify-center text-zinc-500 text-sm">
        Select a video segment to begin playback.
      </div>
    );
  }

  const startSec = Math.max(0, Math.floor(Number(item.start) || 0));
  const embedUrl = `https://www.youtube-nocookie.com/embed/${encodeURIComponent(item.video_id)}?start=${startSec}&autoplay=1`;
  const watchUrl = item.video_url || `https://www.youtube.com/watch?v=${item.video_id}&t=${startSec}s`;

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(watchUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback if clipboard API is restricted
    }
  };

  return (
    <div className="space-y-3">
      {/* 16:9 Video Frame */}
      <div className="relative w-full aspect-video bg-black rounded-lg overflow-hidden border border-zinc-800 shadow-md">
        <iframe
          key={`${item.video_id}-${startSec}`}
          src={embedUrl}
          title={item.title || 'YouTube video player'}
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
          className="w-full h-full border-0"
        />
      </div>

      {/* Meta Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-b border-zinc-800/80 pb-3">
        <div>
          <h2 className="text-sm font-semibold text-zinc-100 line-clamp-1">
            {item.title}
          </h2>
          <p className="text-xs text-zinc-400 mt-0.5">
            Playing segment: <span className="font-mono text-zinc-300">{item.start_formatted} - {item.end_formatted}</span>
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleCopyLink}
            className="px-2.5 py-1 text-xs font-medium text-zinc-300 hover:text-white bg-zinc-800 hover:bg-zinc-700 rounded border border-zinc-700 transition-colors"
          >
            {copied ? '✓ Copied' : 'Copy link'}
          </button>

          <a
            href={watchUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="px-2.5 py-1 text-xs font-medium text-zinc-300 hover:text-white bg-zinc-800 hover:bg-zinc-700 rounded border border-zinc-700 transition-colors flex items-center gap-1"
          >
            Open on YouTube ↗
          </a>
        </div>
      </div>
    </div>
  );
}
