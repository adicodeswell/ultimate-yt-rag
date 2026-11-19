import React from 'react';
import { KnowledgeExplorer } from './features/knowledge-explorer/KnowledgeExplorer';

export function App() {
  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col justify-start">
      <KnowledgeExplorer />
    </main>
  );
}

export default App;
