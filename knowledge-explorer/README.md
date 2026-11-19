# YouTube Knowledge Explorer — Frontend

A focused, lightweight search-and-watch interface built with React, Vite, and Tailwind CSS. It connects to the Python FastAPI RAG backend to retrieve and play relevant YouTube transcript segments at the exact timestamp.

## Standalone Development

### 1. Setup Environment
```bash
cp .env.example .env
```
Ensure `VITE_KNOWLEDGE_API_URL` points to your running FastAPI service (default: `http://localhost:8000`).

### 2. Install & Run
```bash
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## Integrating into CodeClash (or any React app)

The feature is completely decoupled from any specific routing, auth, or global state.

### 1. Copy Feature Folder
Copy `src/features/knowledge-explorer/` directly into your CodeClash project:
```
codeclash/
└── src/
    └── features/
        └── knowledge-explorer/
```

### 2. Mount Component
Import and render `<KnowledgeExplorer />` inside your learning or resources page:

```jsx
import { KnowledgeExplorer } from './features/knowledge-explorer/KnowledgeExplorer';

export function ResourcesPage() {
  return (
    <div className="p-6">
      <KnowledgeExplorer
        apiBaseUrl="/api/knowledge"   {/* Direct URL or CodeClash backend proxy */}
        defaultLimit={5}
        showDomainFilter={true}
        onResultSelect={(item) => console.log('Selected video:', item.video_id)}
      />
    </div>
  );
}
```

### Configurable Props

| Prop | Type | Default | Description |
|---|---|---|---|
| `apiBaseUrl` | `string` | `import.meta.env.VITE_KNOWLEDGE_API_URL` | Base URL of the RAG search endpoint |
| `defaultLimit` | `number` | `5` | Number of results to request (1–10) |
| `showDomainFilter` | `boolean` | `true` | Show or hide the domain pill selector |
| `initialDomain` | `string` | `'all'` | Initial domain selection (`all`, `backend`, `dsa`, `ai`, `sql`, `other`) |
| `className` | `string` | `''` | Additional Tailwind utility classes for wrapper |
| `onResultSelect` | `function` | `undefined` | Callback `(item) => void` triggered when a result is selected |
