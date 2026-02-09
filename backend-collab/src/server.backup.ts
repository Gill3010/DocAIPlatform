import * as Y from 'yjs';
import { WebSocketServer, WebSocket } from 'ws';
import * as http from 'http';
import jwt from 'jsonwebtoken';
import sqlite3 from 'sqlite3';
import { Pool } from 'pg';
import dotenv from 'dotenv';
import { open } from 'sqlite';
import * as encoding from 'lib0/encoding';
import * as decoding from 'lib0/decoding';
import * as syncProtocol from 'y-protocols/sync';
import * as awarenessProtocol from 'y-protocols/awareness';

dotenv.config();

const PORT = parseInt(process.env.PORT || '3001');
const JWT_SECRET = process.env.JWT_SECRET_KEY || 'your-super-secret-key-change-in-production';
const dbUrl = process.env.DATABASE_URL || 'sqlite://./collab.db';

let dbPool: any;
let isSQLite = false;

if (dbUrl.startsWith('postgresql://')) {
    dbPool = new Pool({ connectionString: dbUrl });
} else {
    isSQLite = true;
}

// Document cache: docName -> Y.Doc
const docs: Map<string, Y.Doc> = new Map();
// Connection tracking: docName -> Set<WebSocket>
const connections: Map<string, Set<WebSocket>> = new Map();

async function fetchDocument(docName: string): Promise<Uint8Array | null> {
    const docId = docName.split('_')[1];
    if (!docId) return null;

    try {
        if (isSQLite) {
            const db = await open({ filename: dbUrl.replace('sqlite://', ''), driver: sqlite3.Database });
            const res = await db.get('SELECT content FROM documents WHERE id = ?', [docId]);
            await db.close();
            return res?.content ? Buffer.from(res.content) : null;
        } else {
            const res = await dbPool.query('SELECT content FROM documents WHERE id = $1', [docId]);
            return res.rows[0]?.content || null;
        }
    } catch (err) {
        console.error(`Error fetching document ${docName}:`, err);
        return null;
    }
}

async function storeDocument(docName: string, update: Uint8Array): Promise<void> {
    const docId = docName.split('_')[1];
    if (!docId) return;

    try {
        if (isSQLite) {
            const db = await open({ filename: dbUrl.replace('sqlite://', ''), driver: sqlite3.Database });
            await db.run(
                'UPDATE documents SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                [Buffer.from(update), docId]
            );
            await db.close();
        } else {
            await dbPool.query(
                'UPDATE documents SET content = $1, updated_at = NOW() WHERE id = $2',
                [Buffer.from(update), docId]
            );
        }
    } catch (err) {
        console.error(`Error storing document ${docName}:`, err);
    }
}

function getYDoc(docName: string): Y.Doc {
    let doc = docs.get(docName);
    if (!doc) {
        doc = new Y.Doc();
        doc.gc = false; // Disable garbage collection for persistence
        docs.set(docName, doc);

        // Load initial state from DB
        fetchDocument(docName).then((state) => {
            if (state) {
                Y.applyUpdate(doc!, state);
            }
        });

        // Save updates to DB (debounced)
        let saveTimeout: NodeJS.Timeout | null = null;
        doc.on('update', () => {
            if (saveTimeout) clearTimeout(saveTimeout);
            saveTimeout = setTimeout(() => {
                const update = Y.encodeStateAsUpdate(doc!);
                storeDocument(docName, update);
            }, 5000);
        });
    }
    return doc;
}

function setupWSConnection(ws: WebSocket, req: http.IncomingMessage) {
    const url = new URL(req.url!, `http://${req.headers.host}`);
    
    // y-websocket sends the doc name in the path like: /?room=doc_X
    // But it actually uses the second parameter to WebsocketProvider as the document name
    // The URL is: ws://host:port/doc_X?token=...
    const pathParts = url.pathname.split('/').filter(Boolean);
    const docName = pathParts[0] || url.searchParams.get('room') || 'default';
    const token = url.searchParams.get('token');

    console.log(`[Connection] Document: ${docName}, Has token: ${!!token}`);

    // Verify JWT token
    if (token) {
        try {
            jwt.verify(token, JWT_SECRET);
            console.log(`[Auth] User authenticated for document ${docName}`);
        } catch (err) {
            console.log(`[Auth] Invalid token for document ${docName}, allowing anonymous access`);
        }
    } else {
        console.log(`[Auth] No token provided for document ${docName}, allowing anonymous access`);
    }

    const doc = getYDoc(docName);
    const awareness = new awarenessProtocol.Awareness(doc);

    // Track connection
    if (!connections.has(docName)) {
        connections.set(docName, new Set());
    }
    connections.get(docName)!.add(ws);

    ws.on('message', (message: Buffer) => {
        try {
            const decoder = decoding.createDecoder(message);
            const encoder = encoding.createEncoder();
            const messageType = decoding.readVarUint(decoder);

            switch (messageType) {
                case syncProtocol.messageYjsSyncStep1:
                    encoding.writeVarUint(encoder, syncProtocol.messageYjsSyncStep2);
                    syncProtocol.readSyncStep1(decoder, encoder, doc);
                    ws.send(encoding.toUint8Array(encoder));
                    break;
                case syncProtocol.messageYjsSyncStep2:
                    syncProtocol.readSyncStep2(decoder, doc, null);
                    break;
                case syncProtocol.messageYjsUpdate:
                    syncProtocol.readUpdate(decoder, doc, null);
                    // Broadcast to other clients
                    const update = encoding.toUint8Array(encoder);
                    connections.get(docName)?.forEach((client) => {
                        if (client !== ws && client.readyState === WebSocket.OPEN) {
                            client.send(message);
                        }
                    });
                    break;
                default:
                    // Handle awareness or other message types
                    // Broadcast to other clients
                    connections.get(docName)?.forEach((client) => {
                        if (client !== ws && client.readyState === WebSocket.OPEN) {
                            client.send(message);
                        }
                    });
                    break;
            }
        } catch (err) {
            console.error('Error handling message:', err);
        }
    });

    ws.on('close', () => {
        connections.get(docName)?.delete(ws);
        if (connections.get(docName)?.size === 0) {
            connections.delete(docName);
            // Optionally clean up doc after some timeout
        }
        awareness.destroy();
    });

    // Send initial sync
    const encoder = encoding.createEncoder();
    encoding.writeVarUint(encoder, syncProtocol.messageYjsSyncStep1);
    syncProtocol.writeSyncStep1(encoder, doc);
    ws.send(encoding.toUint8Array(encoder));

    // Awareness is handled by y-websocket client automatically
}

const server = http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    res.end('Y-WebSocket Collaboration Server');
});

const wss = new WebSocketServer({ server });

wss.on('connection', setupWSConnection);

server.listen(PORT, '0.0.0.0', () => {
    console.log(`\nY-WebSocket Collaboration Server running:`);
    console.log(`  > WebSocket: ws://0.0.0.0:${PORT}`);
    console.log(`  > Database: ${isSQLite ? 'SQLite' : 'PostgreSQL'}`);
    console.log(`  > Ready for connections\n`);
});
