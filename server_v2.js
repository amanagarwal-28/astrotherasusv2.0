const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 3000;
const MIME = {
  '.html': 'text/html', '.js': 'application/javascript',
  '.css': 'text/css', '.json': 'application/json',
  '.png': 'image/png', '.ico': 'image/x-icon'
};

http.createServer(function (req, res) {
  var urlPath = req.url === '/' ? '/index_rebound.html' : req.url;
  var filePath = path.join(__dirname, urlPath);
  var ext = path.extname(filePath);

  fs.readFile(filePath, function (err, data) {
    if (err) {
      res.writeHead(404); res.end('Not found: ' + urlPath);
      return;
    }
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'text/plain' });
    res.end(data);
  });
}).listen(PORT, function () {
  console.log('');
  console.log('  ╔══════════════════════════════════════╗');
  console.log('  ║   ASTRO THESAURUS v2.0               ║');
  console.log('  ║   Frontend: http://localhost:3000     ║');
  console.log('  ║   API:      http://localhost:8000     ║');
  console.log('  ╚══════════════════════════════════════╝');
  console.log('');
  console.log('  Make sure api_server.py is running!');
  console.log('');
});
