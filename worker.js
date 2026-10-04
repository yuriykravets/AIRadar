export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === '/robots.txt') {
      return new Response('User-agent: *\nAllow: /\n\nSitemap: https://ai-radar.zoidthe311.workers.dev/sitemap.xml\n', {
        headers: {'content-type': 'text/plain; charset=utf-8', 'cache-control': 'public, max-age=3600'},
      });
    }

    if (url.pathname === '/sitemap.xml') {
      return new Response('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://ai-radar.zoidthe311.workers.dev/</loc></url></urlset>', {
        headers: {'content-type': 'application/xml; charset=utf-8', 'cache-control': 'public, max-age=3600'},
      });
    }

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
