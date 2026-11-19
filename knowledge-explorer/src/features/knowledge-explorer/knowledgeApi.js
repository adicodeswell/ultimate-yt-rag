export async function searchKnowledge({ apiBaseUrl = '', query, domain, limit = 5, signal }) {
  const normalizedDomain = domain && domain.toLowerCase() !== 'all' ? domain.toLowerCase() : null;

  const url = `${apiBaseUrl.replace(/\/+$/, '')}/search`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: query.trim(),
      domain: normalizedDomain,
      limit,
    }),
    signal,
  });

  const data = await response.json();

  if (!response.ok) {
    const errorMsg = data?.error?.message || 'Failed to fetch search results.';
    const errorCode = data?.error?.code || 'UNKNOWN_ERROR';
    const err = new Error(errorMsg);
    err.code = errorCode;
    throw err;
  }

  return data;
}
