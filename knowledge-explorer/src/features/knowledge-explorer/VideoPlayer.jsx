import React, { useState } from 'react';

export function VideoPlayer({ item }) {
  const [copied, setCopied] = useState(false);

  if (!item || !item.video_id) {
    return (
      <div className="w-full aspect-video bg-zinc-900/60 border border-zinc-800 rounded-lg flex items-center justify-center text-zinc-500 text-sm">
        Select a video segment to begin playback.
      </div>
    );
  }

  const startSec = Math.max(0, Math.floor(Number(item.start) || 0));
  const durationSec = Math.max(0, (item.end || 0) - (item.start || 0));
  const durationStr =
    durationSec >= 60
      ? `${(durationSec / 60).toFixed(1)} mins`
      : `${Math.round(durationSec)}s`;

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
    <div className="space-y-3.5">
      {/* 16:9 Video Frame */}
      <div className="relative w-full aspect-video bg-black rounded-lg overflow-hidden border border-zinc-800 shadow-lg">
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
      <div className="space-y-2.5 pt-1">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="space-y-1 flex-1 min-w-[240px]">
            <h2 className="text-base font-semibold text-zinc-100 leading-snug">
              {item.title}
            </h2>
            <div className="flex items-center gap-2 flex-wrap text-xs text-zinc-400">
              <span className="font-mono text-zinc-300 bg-zinc-800/80 px-2 py-0.5 rounded border border-zinc-700/60">
                Segment: {item.start_formatted} - {item.end_formatted}
              </span>
              <span className="text-zinc-500 font-mono">
                ({durationStr})
              </span>
              {item.domains && item.domains.length > 0 && (
                <div className="flex gap-1">
                  {item.domains.map((dom) => (
                    <span
                      key={dom}
                      className="text-[11px] uppercase tracking-wider text-zinc-400 bg-zinc-800 px-1.5 py-0.5 rounded"
                    >
                      {dom}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={handleCopyLink}
              className="px-3 py-1.5 text-xs font-medium text-zinc-300 hover:text-white bg-zinc-800 hover:bg-zinc-700 rounded-md border border-zinc-700 transition-colors"
            >
              {copied ? '✓ Copied' : 'Copy link'}
            </button>

            <a
              href={watchUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-1.5 text-xs font-medium text-zinc-300 hover:text-white bg-zinc-800 hover:bg-zinc-700 rounded-md border border-zinc-700 transition-colors flex items-center gap-1"
            >
              Open on YouTube ↗
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
