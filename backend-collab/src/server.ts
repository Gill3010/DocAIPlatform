import * as Y from 'yjs';
import { WebSocketServer, WebSocket } from 'ws';
import * as http from 'http';
import jwt from 'jsonwebtoken';
import dotenv from 'dotenv';
import * as encoding from 'lib0/encoding';
import * as decoding from 'lib0/decoding';
import * as syncProtocol from 'y-protocols/sync';
import * as awarenessProtocol from 'y-protocols/awareness';

dotenv.config();

const PORT = parseInt(process.env.PORT || '3001');
const JWT_SECRET = process.env.JWT_SECRET_KEY || 'your-super-secret-key-change-in-production';

// Document cache: docName -> Y.Doc
const docs: Map<string, Y.Doc> = new Map();
// Connection tracking: docName -> Set<WebSocket>
const connections: Map<string, Set<WebSocket>> = new Map();
// Awareness per document
const awarenessMap: Map<string, awarenessProtocol.Awareness> = new Map();

function getYDoc(docName: string): Y.Doc {
    let doc = docs.get(docName);
    if (!doc) {
        doc = new Y.Doc();
        docs.set(docName, doc);
        console.log(`[Created] New document: ${docName}`);
    }
    return doc;
}

function getAwareness(docName: string): awarenessProtocol.Awareness {
    let awareness = awarenessMap.get(docName);
    if (!awareness) {
        const doc = getYDoc(docName);
        awareness = new awarenessProtocol.Awareness(doc);
        awarenessMap.set(docName, awareness);
    }
    return awareness;
}

function closeConn(docName: string, conn: WebSocket) {
    const conns = connections.get(docName);
    if (conns) {
        conns.delete(conn);
        console.log(`[Disconnect] Document: ${docName}, Remaining connections: ${conns.size}`);
        
        // Clean up if no more connections
        if (conns.size === 0) {
            connections.delete(docName);
            const doc = docs.get(docName);
            if (doc) {
                console.log(`[Cleanup] Destroying document: ${docName}`);
                docs.delete(docName);
                awarenessMap.delete(docName);
                doc.destroy();
            }
        }
    }
}

function send(conn: WebSocket, message: Uint8Array) {
    if (conn.readyState !== WebSocket.OPEN) return;
    conn.send(message, (err) => {
        if (err) console.error('[Send Error]:', err.message);
    });
}

const server = http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    res.end('Y-WebSocket Collaboration Server (Memory Only)');
});

const wss = new WebSocketServer({ server });

wss.on('connection', (conn, req) => {
    const url = new URL(req.url!, `http://${req.headers.host}`);
    const docName = url.pathname.substring(1) || 'default';
    const token = url.searchParams.get('token');

    // Optional: validate JWT token
    if (token && JWT_SECRET !== 'your-super-secret-key-change-in-production') {
        try {
            jwt.verify(token, JWT_SECRET);
        } catch (err) {
            console.error('[Auth] Invalid token');
            conn.close();
            return;
        }
    }

    console.log(`[Connection] Document: ${docName}, Token: ${token ? 'Yes' : 'No'}`);

    const doc = getYDoc(docName);
    const awareness = getAwareness(docName);
    
    let conns = connections.get(docName);
    if (!conns) {
        conns = new Set();
        connections.set(docName, conns);
    }
    conns.add(conn);

    console.log(`[Active] Document: ${docName}, Total connections: ${conns.size}`);

    // Send sync step 1
    const encoderSync = encoding.createEncoder();
    encoding.writeVarUint(encoderSync, syncProtocol.messageYjsSyncStep1);
    syncProtocol.writeSyncStep1(encoderSync, doc);
    send(conn, encoding.toUint8Array(encoderSync));

    // Send awareness states (message type 1 for awareness)
    const awarenessStates = awareness.getStates();
    if (awarenessStates.size > 0) {
        const awarenessEncoder = encoding.createEncoder();
        encoding.writeVarUint(awarenessEncoder, 1); // Awareness message type
        encoding.writeVarUint8Array(
            awarenessEncoder,
            awarenessProtocol.encodeAwarenessUpdate(awareness, Array.from(awarenessStates.keys()))
        );
        send(conn, encoding.toUint8Array(awarenessEncoder));
    }

    conn.on('message', (message: any) => {
        try {
            const buf = new Uint8Array(message);
            const decoder = decoding.createDecoder(buf);
            const messageType = decoding.readVarUint(decoder);

            switch (messageType) {
                case syncProtocol.messageYjsSyncStep1: {
                    const encoder = encoding.createEncoder();
                    encoding.writeVarUint(encoder, syncProtocol.messageYjsSyncStep2);
                    syncProtocol.readSyncStep1(decoder, encoder, doc);
                    send(conn, encoding.toUint8Array(encoder));
                    break;
                }
                case syncProtocol.messageYjsSyncStep2: {
                    syncProtocol.readSyncStep2(decoder, doc, 'server');
                    break;
                }
                case syncProtocol.messageYjsUpdate: {
                    const update = decoding.readVarUint8Array(decoder);
                    Y.applyUpdate(doc, update, 'server');
                    
                    // Broadcast to other connections
                    conns?.forEach((c) => {
                        if (c !== conn && c.readyState === WebSocket.OPEN) {
                            const encoder = encoding.createEncoder();
                            encoding.writeVarUint(encoder, syncProtocol.messageYjsUpdate);
                            encoding.writeVarUint8Array(encoder, update);
                            send(c, encoding.toUint8Array(encoder));
                        }
                    });
                    break;
                }
                case 1: { // Awareness message type
                    const awarenessUpdate = decoding.readVarUint8Array(decoder);
                    awarenessProtocol.applyAwarenessUpdate(awareness, awarenessUpdate, conn);
                    
                    // Broadcast to other connections
                    conns?.forEach((c) => {
                        if (c !== conn && c.readyState === WebSocket.OPEN) {
                            const encoder = encoding.createEncoder();
                            encoding.writeVarUint(encoder, 1); // Awareness message type
                            encoding.writeVarUint8Array(encoder, awarenessUpdate);
                            send(c, encoding.toUint8Array(encoder));
                        }
                    });
                    break;
                }
                default: {
                    console.warn(`[Unknown] Message type: ${messageType}`);
                }
            }
        } catch (err: any) {
            console.error('[Message Error]:', err.message);
        }
    });

    conn.on('close', () => {
        closeConn(docName, conn);
    });

    conn.on('error', (error) => {
        console.error('[WebSocket Error]:', error.message);
        closeConn(docName, conn);
    });
});

server.listen(PORT, '0.0.0.0', () => {
    console.log(`\n✅ Y-WebSocket Collaboration Server (Memory Only)`);
    console.log(`   > WebSocket: ws://0.0.0.0:${PORT}`);
    console.log(`   > Storage: In-memory (no persistence)`);
    console.log(`   > JWT Auth: ${JWT_SECRET !== 'your-super-secret-key-change-in-production' ? 'Enabled' : 'Optional'}`);
    console.log(`   > Ready for Yjs sync\n`);
});
