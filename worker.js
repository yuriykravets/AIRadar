export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Keep the FastAPI service separate; Cloudflare serves the frontend and
    // optionally proxies API requests to the backend URL configured as a var.
    if (url.pathname.startsWith('/api/') && env.BACKEND_URL) {
      const backendUrl = new URL(url.pathname + url.search, env.BACKEND_URL);
      return fetch(new Request(backendUrl, request));
    }

    if (url.pathname.startsWith('/api/')) {
      return Response.json(
        { error: 'Backend is not configured. Set BACKEND_URL in Wrangler.' },
        { status: 503 }
      );
    }

    // FastAPI serves frontend assets at /static/* locally. Wrangler's assets
    // directory is already the contents of that folder, so map the same
    // browser paths to the deployed asset root.
    if (url.pathname.startsWith('/static/')) {
      url.pathname = url.pathname.slice('/static'.length) || '/';
      return env.ASSETS.fetch(new Request(url, request));
    }

    return env.ASSETS.fetch(request);
  },
};
