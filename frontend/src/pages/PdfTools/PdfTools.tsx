import { useState, useMemo, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { FileText, Loader, CheckCircle, AlertCircle } from 'lucide-react';
import { apiService } from '../../services/api';
import { useAppStore } from '../../stores/appStore';
import { useAnonymousSession } from '../../hooks/useAnonymousSession';
import { ConversionLimitModal } from '../../components/ConversionLimitModal/ConversionLimitModal';
import { UpgradeModal } from '../../components/UpgradeModal/UpgradeModal';
import {
    PDF_TOOLS,
    PDF_TOOLS_LABEL,
    PDF_TOOL_ENDPOINT,
    PDF_TOOLS_OPERATIONAL,
} from '../../constants/conversions';
import './PdfTools.css';

const DOWNLOAD_NAMES: Record<string, string> = {
    merge: 'unido.pdf',
    compare: 'comparacion.txt',
    split: 'partes.zip',
    rotate: 'rotado.pdf',
    compress: 'comprimido.pdf',
    protect: 'protegido.pdf',
    unlock: 'desbloqueado.pdf',
    order: 'ordenado.pdf',
    'page-numbers': 'con_numeros.pdf',
    crop: 'recortado.pdf',
    watermark: 'con_marca_agua.pdf',
    repair: 'reparado.pdf',
    pdfa: 'pdfa.pdf',
    edit: 'editado.pdf',
    sign: 'firmado.pdf',
    scan: 'escaneado.pdf',
    redact: 'censurado.pdf',
    ocr: 'ocr.pdf',
};

export const PdfTools = () => {
    const [searchParams] = useSearchParams();
    const toolId = searchParams.get('tool') || '';
    const tool = useMemo(() => PDF_TOOLS.find((t) => t.id === toolId), [toolId]);
    const { token, user, setUser } = useAppStore();
    const { sessionId, syncFromCreditsRemaining } = useAnonymousSession();

    const [file, setFile] = useState<File | null>(null);
    const [files, setFiles] = useState<File[]>([]);
    const [fileB, setFileB] = useState<File | null>(null);
    const [password, setPassword] = useState('');
    const [angle, setAngle] = useState(90);
    const [pageOrder, setPageOrder] = useState('');
    const [watermarkText, setWatermarkText] = useState('');
    const [marginPt, setMarginPt] = useState(0);
    const [pagesPerFile, setPagesPerFile] = useState<number | ''>('');
    const [editText, setEditText] = useState('');
    const [editPageNumber, setEditPageNumber] = useState(1);
    const [editPosition, setEditPosition] = useState<'top' | 'center' | 'bottom'>('bottom');
    const [signerName, setSignerName] = useState('');
    const [signatureImageFile, setSignatureImageFile] = useState<File | null>(null);
    const [scanImages, setScanImages] = useState<File[]>([]);
    const [redactWords, setRedactWords] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);
    const [showLimitModal, setShowLimitModal] = useState(false);
    const [showUpgradeModal, setShowUpgradeModal] = useState(false);

    const isOperational = toolId && PDF_TOOLS_OPERATIONAL.includes(toolId);
    const endpoint = toolId ? PDF_TOOL_ENDPOINT[toolId] : '';

    useEffect(() => {
        setSuccess(false);
        setError('');
        setFile(null);
        setFiles([]);
        setFileB(null);
        setPassword('');
        setPageOrder('');
        setWatermarkText('');
        setEditText('');
        setSignerName('');
        setSignatureImageFile(null);
        setScanImages([]);
        setRedactWords('');
    }, [toolId]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setSuccess(false);
        if (!endpoint) return;

        if (endpoint === 'protect' || endpoint === 'unlock') {
            if (!password.trim()) {
                setError('La contraseña es obligatoria.');
                return;
            }
        }
        if (endpoint === 'order') {
            if (!pageOrder.trim()) {
                setError('Indica el orden de páginas (ej: 1,3,2,4).');
                return;
            }
        }
        if (endpoint === 'watermark') {
            if (!watermarkText.trim()) {
                setError('El texto de la marca de agua es obligatorio.');
                return;
            }
        }
        if (endpoint === 'edit') {
            if (!editText.trim()) {
                setError('El texto a añadir es obligatorio.');
                return;
            }
        }
        if (endpoint === 'sign') {
            if (!signerName.trim()) {
                setError('El nombre del firmante es obligatorio.');
                return;
            }
        }
        if (endpoint === 'redact') {
            if (!redactWords.trim()) {
                setError('Indica al menos una palabra o frase a censurar (separadas por comas).');
                return;
            }
        }

        const formData = new FormData();
        if (endpoint === 'merge') {
            if (files.length < 2) {
                setError('Se necesitan al menos 2 PDF para unir.');
                return;
            }
            files.forEach((f) => formData.append('files', f));
        } else if (endpoint === 'compare') {
            if (!file || !fileB) {
                setError('Se necesitan los dos PDF para comparar.');
                return;
            }
            formData.append('file_a', file);
            formData.append('file_b', fileB);
        } else if (endpoint === 'scan') {
            if (scanImages.length < 1) {
                setError('Se necesita al menos una imagen.');
                return;
            }
            scanImages.forEach((f) => formData.append('files', f));
        } else {
            if (endpoint !== 'scan' && !file) {
                setError('Selecciona un archivo PDF.');
                return;
            }
            if (endpoint !== 'scan') formData.append('file', file!);
            if (endpoint === 'rotate') formData.append('angle', String(angle));
            if (endpoint === 'protect' || endpoint === 'unlock') formData.append('password', password);
            if (endpoint === 'order') formData.append('page_order', pageOrder);
            if (endpoint === 'watermark') formData.append('text', watermarkText);
            if (endpoint === 'crop') formData.append('margin_pt', String(marginPt));
            if (endpoint === 'split' && pagesPerFile !== '') formData.append('pages_per_file', String(pagesPerFile));
            if (endpoint === 'edit') {
                formData.append('page_number', String(editPageNumber));
                formData.append('text', editText);
                formData.append('position', editPosition);
            }
            if (endpoint === 'sign') {
                formData.append('signer_name', signerName);
                if (signatureImageFile) formData.append('signature_image', signatureImageFile);
            }
            if (endpoint === 'redact') formData.append('words', redactWords);
        }

        setLoading(true);
        try {
            const { blob, creditsRemaining } = await apiService.pdfTool(endpoint, formData, {
                anonymousSessionId: token ? undefined : sessionId,
            });
            const name = DOWNLOAD_NAMES[endpoint] || 'resultado.pdf';
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = name;
            a.click();
            URL.revokeObjectURL(url);
            if (creditsRemaining !== undefined) {
                if (!token) {
                    syncFromCreditsRemaining(creditsRemaining);
                } else if (user && !user.is_superuser) {
                    setUser({ ...user, free_conversion_count: Math.max(0, 5 - creditsRemaining) });
                }
            }
            setSuccess(true);
        } catch (err: unknown) {
            const detail = (err as Error & { detail?: string })?.detail ?? (err instanceof Error ? err.message : 'Error al procesar.');
            setError(detail);
            if (detail === 'anonymous_limit_reached') setShowLimitModal(true);
            else if (detail === 'auth_limit_reached') setShowUpgradeModal(true);
        } finally {
            setLoading(false);
        }
    };

    const formNeedsPassword = endpoint === 'protect' || endpoint === 'unlock';
    const formNeedsTwoFiles = endpoint === 'compare';
    const formNeedsMultipleFiles = endpoint === 'merge';
    const formNeedsScanImages = endpoint === 'scan';

    return (
        <div className="pdf-tools-page">
            <ConversionLimitModal
                isOpen={showLimitModal}
                onClose={() => setShowLimitModal(false)}
                anonymousSessionId={sessionId}
            />
            <UpgradeModal
                isOpen={showUpgradeModal}
                onClose={() => setShowUpgradeModal(false)}
            />
            <header className="pdf-tools-header">
                <h1 className="pdf-tools-title">{PDF_TOOLS_LABEL}</h1>
                <p className="pdf-tools-subtitle">
                    Elige una herramienta y sube tu(s) archivo(s) PDF
                </p>
            </header>

            <div className="pdf-tools-layout">
                <nav className="pdf-tools-nav">
                    {PDF_TOOLS.map((t) => {
                        const op = PDF_TOOLS_OPERATIONAL.includes(t.id);
                        return (
                            <Link
                                key={t.id}
                                to={`/pdf-tools?tool=${t.id}`}
                                className={`pdf-tools-nav-item ${toolId === t.id ? 'active' : ''} ${!op ? 'coming-soon' : ''}`}
                            >
                                <t.icon size={18} />
                                <span>{t.name}</span>
                                {!op && <span className="badge">Próximamente</span>}
                            </Link>
                        );
                    })}
                </nav>

                <main className="pdf-tools-main">
                    {!tool ? (
                        <div className="pdf-tools-empty">
                            <FileText size={48} />
                            <p>Elige una herramienta en el menú</p>
                        </div>
                    ) : !isOperational ? (
                        <div className="pdf-tools-coming">
                            <h2>{tool.name}</h2>
                            <p>Esta herramienta estará disponible próximamente.</p>
                        </div>
                    ) : (
                        <div className="pdf-tools-form-wrap">
                            <h2>{tool.name}</h2>
                            <form onSubmit={handleSubmit} className="pdf-tools-form">
                                {formNeedsMultipleFiles && (
                                    <label>
                                        PDF a unir (mín. 2) — Ctrl+clic o Cmd+clic para elegir varios
                                        <input
                                            key={toolId}
                                            type="file"
                                            accept=".pdf"
                                            multiple
                                            onChange={(e) => setFiles(Array.from(e.target.files || []))}
                                        />
                                        {files.length > 0 && (
                                            <span className="pdf-tools-file-count">
                                                {files.length} archivo{files.length !== 1 ? 's' : ''} seleccionado{files.length !== 1 ? 's' : ''}
                                            </span>
                                        )}
                                    </label>
                                )}
                                {formNeedsScanImages && (
                                    <label>
                                        Imágenes (mín. 1)
                                        <input
                                            key={toolId}
                                            type="file"
                                            accept=".png,.jpg,.jpeg,.bmp,.tiff,.tif"
                                            multiple
                                            onChange={(e) => setScanImages(Array.from(e.target.files || []))}
                                        />
                                    </label>
                                )}
                                {formNeedsTwoFiles && (
                                    <>
                                        <label>
                                            Primer PDF
                                            <input
                                                key={`${toolId}-a`}
                                                type="file"
                                                accept=".pdf"
                                                onChange={(e) => setFile(e.target.files?.[0] || null)}
                                            />
                                        </label>
                                        <label>
                                            Segundo PDF
                                            <input
                                                key={`${toolId}-b`}
                                                type="file"
                                                accept=".pdf"
                                                onChange={(e) => setFileB(e.target.files?.[0] || null)}
                                            />
                                        </label>
                                    </>
                                )}
                                {!formNeedsMultipleFiles && !formNeedsTwoFiles && !formNeedsScanImages && (
                                    <label>
                                        {endpoint === 'unlock' ? 'PDF protegido (el que descargaste al protegerlo)' : endpoint === 'ocr' ? 'PDF escaneado' : 'Archivo PDF'}
                                        <input
                                            key={toolId}
                                            type="file"
                                            accept=".pdf"
                                            onChange={(e) => setFile(e.target.files?.[0] || null)}
                                        />
                                    </label>
                                )}
                                {endpoint === 'rotate' && (
                                    <label>
                                        Ángulo
                                        <select value={angle} onChange={(e) => setAngle(Number(e.target.value))}>
                                            <option value={90}>90°</option>
                                            <option value={180}>180°</option>
                                            <option value={270}>270°</option>
                                        </select>
                                    </label>
                                )}
                                {endpoint === 'split' && (
                                    <label>
                                        Páginas por archivo (vacío = 1 por archivo)
                                        <input
                                            type="number"
                                            min={1}
                                            value={pagesPerFile}
                                            onChange={(e) => setPagesPerFile(e.target.value === '' ? '' : Number(e.target.value))}
                                            placeholder="1"
                                        />
                                    </label>
                                )}
                                {formNeedsPassword && (
                                    <label>
                                        Contraseña
                                        <input
                                            type="password"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            placeholder={endpoint === 'protect' ? 'Nueva contraseña' : 'Contraseña actual'}
                                        />
                                    </label>
                                )}
                                {endpoint === 'order' && (
                                    <label>
                                        Orden de páginas (ej: 1,3,2,4)
                                        <input
                                            type="text"
                                            value={pageOrder}
                                            onChange={(e) => setPageOrder(e.target.value)}
                                            placeholder="1,2,3,4"
                                        />
                                    </label>
                                )}
                                {endpoint === 'watermark' && (
                                    <label>
                                        Texto de la marca de agua
                                        <input
                                            type="text"
                                            value={watermarkText}
                                            onChange={(e) => setWatermarkText(e.target.value)}
                                            placeholder="Ej: CONFIDENCIAL"
                                        />
                                    </label>
                                )}
                                {endpoint === 'crop' && (
                                    <label>
                                        Márgen a recortar (puntos)
                                        <input
                                            type="number"
                                            min={0}
                                            step={5}
                                            value={marginPt}
                                            onChange={(e) => setMarginPt(Number(e.target.value) || 0)}
                                        />
                                    </label>
                                )}
                                {endpoint === 'edit' && (
                                    <>
                                        <label>
                                            Página (número)
                                            <input
                                                type="number"
                                                min={1}
                                                value={editPageNumber}
                                                onChange={(e) => setEditPageNumber(Number(e.target.value) || 1)}
                                            />
                                        </label>
                                        <label>
                                            Texto a añadir
                                            <input
                                                type="text"
                                                value={editText}
                                                onChange={(e) => setEditText(e.target.value)}
                                                placeholder="Texto que aparecerá en el PDF"
                                            />
                                        </label>
                                        <label>
                                            Posición
                                            <select value={editPosition} onChange={(e) => setEditPosition(e.target.value as 'top' | 'center' | 'bottom')}>
                                                <option value="top">Arriba</option>
                                                <option value="center">Centro</option>
                                                <option value="bottom">Abajo</option>
                                            </select>
                                        </label>
                                    </>
                                )}
                                {endpoint === 'sign' && (
                                    <>
                                        <label>
                                            Nombre del firmante
                                            <input
                                                type="text"
                                                value={signerName}
                                                onChange={(e) => setSignerName(e.target.value)}
                                                placeholder="Ej: Juan Pérez"
                                            />
                                        </label>
                                        <label>
                                            Imagen de firma (opcional)
                                            <input
                                                key={toolId}
                                                type="file"
                                                accept=".png,.jpg,.jpeg"
                                                onChange={(e) => setSignatureImageFile(e.target.files?.[0] || null)}
                                            />
                                        </label>
                                    </>
                                )}
                                {endpoint === 'redact' && (
                                    <label>
                                        Palabras o frases a censurar (separadas por comas)
                                        <input
                                            type="text"
                                            value={redactWords}
                                            onChange={(e) => setRedactWords(e.target.value)}
                                            placeholder="Ej: confidencial, dato sensible"
                                        />
                                    </label>
                                )}
                                {error && (
                                    <div className="pdf-tools-error">
                                        <AlertCircle size={18} />
                                        {error}
                                    </div>
                                )}
                                {success && (
                                    <div className="pdf-tools-success">
                                        <CheckCircle size={18} />
                                        Descarga iniciada
                                    </div>
                                )}
                                <button type="submit" className="pdf-tools-submit" disabled={loading}>
                                    {loading ? (
                                        <>
                                            <Loader size={18} className="spin" />
                                            Procesando…
                                        </>
                                    ) : (
                                        'Procesar'
                                    )}
                                </button>
                            </form>
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
};
