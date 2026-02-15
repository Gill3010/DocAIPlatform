import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import * as Y from 'yjs';
import { WebsocketProvider } from 'y-websocket';
import { useAppStore } from '../../stores/appStore';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import { Collaboration as TiptapCollaboration } from '@tiptap/extension-collaboration';
import { CollaborationCursor } from '@tiptap/extension-collaboration-cursor';
import { Placeholder } from '@tiptap/extension-placeholder';
import { Users, Shield, Save, ArrowLeft, Bold, Italic, List, ListOrdered } from 'lucide-react';
import { apiService } from '../../services/api';
import { ShareModal } from '../../components/ShareModal/ShareModal';
import './Collaboration.css';

interface EditorWrapperProps {
    id: string;
    ydoc: Y.Doc;
    provider: WebsocketProvider;
    user: any;
    docData: any;
}

const EditorWrapper: React.FC<EditorWrapperProps> = ({ id, ydoc, provider, user, docData }) => {
    const editor = useEditor({
        extensions: [
            StarterKit.configure({
                history: false,
            }),
            Placeholder.configure({
                placeholder: 'Escribe algo increíble...',
            }),
            TiptapCollaboration.configure({
                document: ydoc,
            }),
            /*
            CollaborationCursor.configure({
                provider: provider,
                user: {
                    name: user?.full_name || 'Anonymous',
                    color: '#' + Math.floor(Math.random() * 16777215).toString(16),
                },
            }),
            */
        ],
    }, [provider, ydoc]);

    useEffect(() => {
        if (!editor || !docData) return;
        const canEdit = docData.current_user_role === 'owner' || docData.current_user_role === 'editor';
        editor.setEditable(canEdit);
    }, [editor, docData]);

    // Seed content if needed
    useEffect(() => {
        if (!editor || !docData) return;
        const type = ydoc.getXmlFragment('default');
        if (type.length === 0 && docData.initial_content) {
            editor.commands.setContent(docData.initial_content);
        }
    }, [editor, docData, ydoc]);

    if (!editor) return null;

    const canEdit = docData?.current_user_role === 'owner' || docData?.current_user_role === 'editor';

    return (
        <main className="collab-editor-container">
            {canEdit && (
                <div className="editor-toolbar">
                    <button onClick={() => editor.chain().focus().toggleBold().run()} className={editor.isActive('bold') ? 'is-active' : ''}><Bold size={18} /></button>
                    <button onClick={() => editor.chain().focus().toggleItalic().run()} className={editor.isActive('italic') ? 'is-active' : ''}><Italic size={18} /></button>
                    <button onClick={() => editor.chain().focus().toggleBulletList().run()} className={editor.isActive('bulletList') ? 'is-active' : ''}><List size={18} /></button>
                    <button onClick={() => editor.chain().focus().toggleOrderedList().run()} className={editor.isActive('orderedList') ? 'is-active' : ''}><ListOrdered size={18} /></button>
                </div>
            )}
            <div className={`tiptap-editor-wrapper ${!canEdit ? 'read-only' : ''}`}>
                <EditorContent editor={editor} />
            </div>
        </main>
    );
};

export const Collaboration = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const { token, user } = useAppStore();
    const [connected, setConnected] = useState(false);
    const [activeUsers, setActiveUsers] = useState<number>(0);
    const [provider, setProvider] = useState<WebsocketProvider | null>(null);
    const [ydoc, setYdoc] = useState<Y.Doc | null>(null);
    const [docData, setDocData] = useState<any>(null);
    const [isSharing, setIsSharing] = useState(false);

    useEffect(() => {
        if (!id || !token || !user) return;

        // Create a new Y.Doc for this session
        const newYdoc = new Y.Doc();
        
        // Desarrollo: conectar directo al collab (3001). Producción: nginx proxy /ws/collab
        const isDev = /^localhost$|^127\.0\.0\.1$/.test(window.location.hostname);
        const wsUrl = isDev
            ? 'ws://localhost:3001'
            : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/collab`;

        // Use standard y-websocket
        const wsProvider = new WebsocketProvider(wsUrl, `doc_${id}`, newYdoc, {
            params: { token },
            connect: true
        });

        wsProvider.on('status', (event: any) => {
            console.log('WS Status:', event.status);
            setConnected(event.status === 'connected');
        });

        wsProvider.awareness.on('change', () => {
            setActiveUsers(wsProvider.awareness.getStates().size);
        });

        wsProvider.awareness.setLocalStateField('user', {
            name: user.full_name || 'Anonymous',
            color: '#' + Math.floor(Math.random() * 16777215).toString(16),
        });

        setYdoc(newYdoc);
        setProvider(wsProvider);

        return () => {
            wsProvider.disconnect();
            // Important: only destroy after a small delay or if certain the editor is unmounted
            // For now, destroying here might be the cause if the component re-renders quickly
            // newYdoc.destroy(); 
        };
    }, [id, token, user?.id]); // Only re-run if id, token or user changes

    useEffect(() => {
        if (!id || !token) return;
        apiService.getDocument(parseInt(id)).then(setDocData).catch(console.error);
    }, [id, token]);

    return (
        <div className="collab-page">
            <header className="collab-header">
                <div className="header-left">
                    <button onClick={() => navigate(-1)} className="back-btn"><ArrowLeft size={20} /></button>
                    <h1>{docData?.title || `Documento #${id}`}</h1>
                    <div className={`status-badge ${connected ? 'connected' : 'disconnected'}`}>{connected ? 'Conectado' : 'Desconectado'}</div>
                </div>
                <div className="header-actions">
                    <div className="user-count"><Users size={18} /><span>{activeUsers} activos</span></div>
                    {(docData?.current_user_role === 'owner' || docData?.current_user_role === 'editor') && (
                        <button className="save-btn" title="El guardado es automático"><Save size={18} />Guardado</button>
                    )}
                    {docData?.current_user_role === 'owner' && (
                        <button className="perm-btn" onClick={() => setIsSharing(true)}><Shield size={18} />Permisos</button>
                    )}
                </div>
            </header>

            {provider && ydoc && id ? (
                <EditorWrapper id={id} ydoc={ydoc} provider={provider} user={user} docData={docData} />
            ) : (
                <div className="collab-page loading">
                    <div className="loading-spinner">Conectando con el editor...</div>
                </div>
            )}

            {isSharing && id && (
                <ShareModal documentId={parseInt(id)} onClose={() => setIsSharing(false)} />
            )}
        </div>
    );
};
