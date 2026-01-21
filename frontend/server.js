const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');
const { parse } = require('url');

const sslKeyPath = process.env.SSL_KEY_PATH || '/app/ssl/server.key';
const sslCertPath = process.env.SSL_CERT_PATH || '/app/ssl/server.crt';
const port = parseInt(process.env.PORT, 10) || 443;
const hostname = process.env.HOSTNAME || '0.0.0.0';
const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://blacklist-app:2542';

const NextServer = require('next/dist/server/next-server').default;
const nextConfig = require('./.next/required-server-files.json');

process.env.__NEXT_PRIVATE_STANDALONE_CONFIG = JSON.stringify(nextConfig.config);

const nextServer = new NextServer({
  dir: __dirname,
  dev: false,
  hostname,
  port,
  conf: {
    ...nextConfig.config,
    distDir: '.next',
  },
  customServer: true,
  minimalMode: false,
});

const handler = nextServer.getRequestHandler();

const getContentType = (ext) => ({
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.json': 'application/json',
}[ext] || 'application/octet-stream');

const proxyRequest = (req, res, targetPath) => {
  const parsedApi = new URL(apiUrl);
  const options = {
    hostname: parsedApi.hostname,
    port: parsedApi.port || 80,
    path: targetPath,
    method: req.method,
    headers: { ...req.headers, host: parsedApi.host },
  };

  const proxyReq = http.request(options, (proxyRes) => {
    res.writeHead(proxyRes.statusCode, proxyRes.headers);
    proxyRes.pipe(res);
  });

  proxyReq.on('error', (err) => {
    console.error('Proxy error:', err.message);
    res.writeHead(502);
    res.end('Bad Gateway');
  });

  req.pipe(proxyReq);
};

const httpsOptions = {
  key: fs.readFileSync(sslKeyPath),
  cert: fs.readFileSync(sslCertPath),
};

https.createServer(httpsOptions, async (req, res) => {
  const parsedUrl = parse(req.url, true);
  const { pathname } = parsedUrl;

  if (pathname.startsWith('/api/')) {
    return proxyRequest(req, res, req.url);
  }

  if (pathname === '/health' || pathname === '/metrics') {
    return proxyRequest(req, res, pathname);
  }

  if (pathname.startsWith('/uiview/')) {
    const targetPath = pathname.replace('/uiview', '');
    return proxyRequest(req, res, targetPath);
  }

  if (pathname.startsWith('/_next/static/')) {
    const relativePath = pathname.replace('/_next/static/', '');
    const filePath = path.join(__dirname, '.next', 'static', relativePath);
    
    if (fs.existsSync(filePath)) {
      const ext = path.extname(filePath);
      res.setHeader('Content-Type', getContentType(ext));
      res.setHeader('Cache-Control', 'public, max-age=31536000, immutable');
      fs.createReadStream(filePath).pipe(res);
      return;
    }
  }

  if (pathname.startsWith('/') && !pathname.startsWith('/_next') && !pathname.startsWith('/api')) {
    const publicPath = path.join(__dirname, 'public', pathname);
    if (fs.existsSync(publicPath) && fs.statSync(publicPath).isFile()) {
      const ext = path.extname(publicPath);
      res.setHeader('Content-Type', getContentType(ext));
      res.setHeader('Cache-Control', 'public, max-age=86400');
      fs.createReadStream(publicPath).pipe(res);
      return;
    }
  }

  try {
    await handler(req, res, parsedUrl);
  } catch (err) {
    console.error('Error:', err);
    res.statusCode = 500;
    res.end('Internal Server Error');
  }
}).listen(port, hostname, () => {
  console.log(`> HTTPS server ready on https://${hostname}:${port}`);
  console.log(`> API proxy: ${apiUrl}`);
});
