import * as http from 'http';
import { WebSocketServer } from 'ws';
import dotenv from 'dotenv';

dotenv.config();

const PORT = parseInt(process.env.PORT || '3001');

// Simple WebSocket server that accepts connections but doesn't do sync yet
const server = http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    res.end('Y-WebSocket Collaboration Server');
});

const wss = new WebSocketServer({ server });

wss.on('connection', (ws, req) => {
    const url = new URL(req.url!, `http://${req.headers.host}`);
    const pathParts = url.pathname.split('/').filter(Boolean);
    const docName = pathParts[0] || 'default';
    const token = url.searchParams.get('token');

    console.log(`[Connection] Document: ${docName}, Has token: ${!!token}`);

    // Just keep connection alive without processing Yjs messages for now
    ws.on('message', (message) => {
        // Echo back to acknowledge receipt
        ws.send(message);
    });

    ws.on('close', () => {
        console.log(`[Disconnect] Document: ${docName}`);
    });

    ws.on('error', (error) => {
        console.error('[WebSocket Error]:', error.message);
    });
});

server.listen(PORT, '0.0.0.0', () => {
    console.log(`\nSimple WebSocket Server running:`);
    console.log(`  > WebSocket: ws://0.0.0.0:${PORT}`);
    console.log(`  > Ready for connections`);
    console.log(`  > Note: Collaboration temporarily disabled\n`);
});
