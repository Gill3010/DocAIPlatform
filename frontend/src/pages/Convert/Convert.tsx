import { useState, useCallback } from 'react';
import { Upload, FileType, ArrowRight, CheckCircle2, AlertCircle, RefreshCw, X, FileText, Image, File, Globe, Ruler, GraduationCap } from 'lucide-react';
import { apiService } from '../../services/api';
import './Convert.css';

interface FileWithProgress {
    file: File;
    progress: number;
    status: 'idle' | 'uploading' | 'converting' | 'completed' | 'error';
    targetFormat: string;
    conversionId?: number;
    errorMessage?: string;
    creditsRemaining?: number;
}

// Conversiones soportadas por el backend (sistema modular)
const CONVERSION_MAP: Record<string, Array<{ id: string; name: string; icon: any }>> = {
    'png': [
        { id: 'pdf', name: 'Documento PDF', icon: FileText },
        { id: 'dxf', name: 'Archivo DXF (CAD)', icon: Ruler }
    ],
    'jpg': [
        { id: 'pdf', name: 'Documento PDF', icon: FileText },
        { id: 'dxf', name: 'Archivo DXF (CAD)', icon: Ruler }
    ],
    'jpeg': [
        { id: 'pdf', name: 'Documento PDF', icon: FileText },
        { id: 'dxf', name: 'Archivo DXF (CAD)', icon: Ruler }
    ],
    'pdf': [
        { id: 'docx', name: 'Documento Word', icon: File },
        { id: 'png', name: 'Imagen PNG', icon: Image },
        { id: 'txt', name: 'Texto Plano', icon: FileText }
    ],
    'txt': [
        { id: 'docx', name: 'Documento Word', icon: File }
    ],
    'docx': [
        { id: 'pdf', name: 'Documento PDF', icon: FileText },
        { id: 'txt', name: 'Texto Plano', icon: FileText },
        { id: 'xml', name: 'XML JATS (Artículo Científico)', icon: GraduationCap }
    ],
    'xml': [
        { id: 'html', name: 'Página HTML', icon: Globe },
        { id: 'docx', name: 'Documento Word', icon: File }
    ],
    'html': [
        { id: 'xml', name: 'Archivo XML', icon: FileText }
    ],
    'htm': [
        { id: 'xml', name: 'Archivo XML', icon: FileText }
    ],
    'dxf': [
        { id: 'png', name: 'Imagen PNG', icon: Image }
    ]
};

export const Convert = () => {
    const [dragActive, setDragActive] = useState(false);
    const [selectedFile, setSelectedFile] = useState<FileWithProgress | null>(null);
    const [targetFormat, setTargetFormat] = useState('pdf');
    const [availableFormats, setAvailableFormats] = useState<Array<{ id: string; name: string; icon: string }>>([]);

    const handleDrag = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            const file = e.dataTransfer.files[0];
            const ext = file.name.split('.').pop()?.toLowerCase() || '';
            const formats = CONVERSION_MAP[ext] || [];
            const defaultTarget = formats.length > 0 ? formats[0].id : 'pdf';
            
            setAvailableFormats(formats);
            setTargetFormat(defaultTarget);
            setSelectedFile({
                file,
                progress: 0,
                status: 'idle',
                targetFormat: defaultTarget
            });
        }
    }, []);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0];
            const ext = file.name.split('.').pop()?.toLowerCase() || '';
            const formats = CONVERSION_MAP[ext] || [];
            const defaultTarget = formats.length > 0 ? formats[0].id : 'pdf';
            
            if (formats.length === 0) {
                alert(`Formato ${ext.toUpperCase()} no soportado. Formatos válidos: PNG, JPG, JPEG, PDF, TXT, DOCX, XML, HTML, DXF`);
                return;
            }
            
            setAvailableFormats(formats);
            setTargetFormat(defaultTarget);
            setSelectedFile({
                file,
                progress: 0,
                status: 'idle',
                targetFormat: defaultTarget
            });
        }
    };

    const startConversion = async () => {
        if (!selectedFile) return;

        setSelectedFile(prev => prev ? { ...prev, status: 'uploading', progress: 0 } : null);

        try {
            // Simulate upload progress
            const uploadInterval = setInterval(() => {
                setSelectedFile(prev => {
                    if (!prev || prev.progress >= 50) {
                        clearInterval(uploadInterval);
                        return prev;
                    }
                    return { ...prev, progress: prev.progress + 10 };
                });
            }, 200);

            // Call real backend API
            const response = await apiService.uploadAndConvert(
                selectedFile.file,
                targetFormat
            );

            clearInterval(uploadInterval);

            // Update to converting status
            setSelectedFile(prev => prev ? { 
                ...prev, 
                status: 'converting', 
                progress: 60,
                conversionId: response.conversion_id,
                creditsRemaining: response.credits_remaining
            } : null);

            // Simulate conversion progress
            const convertInterval = setInterval(() => {
                setSelectedFile(prev => {
                    if (!prev || prev.progress >= 100) {
                        clearInterval(convertInterval);
                        return prev ? { ...prev, status: 'completed', progress: 100 } : null;
                    }
                    return { ...prev, progress: prev.progress + 10 };
                });
            }, 300);

        } catch (error: any) {
            console.error('Conversion failed:', error);
            setSelectedFile(prev => prev ? { 
                ...prev, 
                status: 'error',
                errorMessage: error.message || 'Conversion failed. Please try again.'
            } : null);
        }
    };

    const reset = () => {
        setSelectedFile(null);
        setTargetFormat('pdf');
    };

    return (
        <div className="convert-page">
            <div className="convert-header">
                <h2>Convertidor de Documentos</h2>
                <p>Sube tu archivo y elige el formato de salida</p>
            </div>

            <div className="convert-container">
                {!selectedFile ? (
                    <div
                        className={`drop-zone ${dragActive ? 'active' : ''}`}
                        onDragEnter={handleDrag}
                        onDragLeave={handleDrag}
                        onDragOver={handleDrag}
                        onDrop={handleDrop}
                    >
                        <div className="upload-icon-wrapper">
                            <Upload size={64} className="upload-icon" />
                        </div>
                            <div className="drop-text">
                                <h3>Haz clic o arrastra el archivo aquí</h3>
                                <p>PNG, JPG, PDF, DOCX, TXT, XML, HTML, DXF hasta 10MB</p>
                            </div>
                        <div className="supported-formats">
                            <span className="format-badge">PNG/JPG</span>
                            <span className="format-badge">PDF</span>
                            <span className="format-badge">DOCX</span>
                            <span className="format-badge">TXT</span>
                            <span className="format-badge">XML</span>
                            <span className="format-badge">HTML</span>
                        </div>
                        <input
                            type="file"
                            id="file-upload"
                            className="file-input"
                            onChange={handleFileChange}
                        />
                        <label htmlFor="file-upload" className="select-btn">
                            Seleccionar Archivo
                        </label>
                    </div>
                ) : (
                    <div className="processing-container">
                        <div className="file-preview-card">
                            <div className="file-info">
                                <div className="file-icon">
                                    <FileType size={32} />
                                </div>
                                <div className="file-details">
                                    <h4>{selectedFile.file.name}</h4>
                                    <p>{(selectedFile.file.size / 1024 / 1024).toFixed(2)} MB</p>
                                </div>
                                {selectedFile.status === 'idle' && (
                                    <button className="remove-file" onClick={reset}>
                                        <X size={20} />
                                    </button>
                                )}
                            </div>

                            {selectedFile.status === 'idle' ? (
                                <div className="conversion-settings">
                                    <div className="format-selector">
                                        <p className="label">Convertir a:</p>
                                        {availableFormats.length > 0 ? (
                                            <div className="format-grid">
                                                {availableFormats.map(f => {
                                                    const IconComponent = f.icon;
                                                    return (
                                                        <button
                                                            key={f.id}
                                                            className={`format-btn ${targetFormat === f.id ? 'active' : ''}`}
                                                            onClick={() => setTargetFormat(f.id)}
                                                        >
                                                            <span className="format-icon">
                                                                <IconComponent size={24} />
                                                            </span>
                                                            <span className="format-name">{f.name}</span>
                                                        </button>
                                                    );
                                                })}
                                            </div>
                                        ) : (
                                            <p className="no-formats-warning">⚠️ Este formato de archivo no tiene conversiones disponibles</p>
                                        )}
                                    </div>
                                    <button className="convert-btn" onClick={startConversion}>
                                        Convertir Ahora
                                        <ArrowRight size={20} />
                                    </button>
                                </div>
                            ) : (
                                <div className="progress-section">
                                    <div className="progress-status">
                                        <span>
                                            {selectedFile.status === 'uploading' ? 'Subiendo...' :
                                                selectedFile.status === 'converting' ? 'Procesando...' :
                                                    '¡Completado!'}
                                        </span>
                                        <span>{selectedFile.progress}%</span>
                                    </div>
                                    <div className="progress-bar-container">
                                        <div
                                            className="progress-bar"
                                            style={{ width: `${selectedFile.progress}%` }}
                                        ></div>
                                    </div>
                                    {selectedFile.status === 'completed' && (
                                        <div className="result-actions">
                                            <div className="success-msg">
                                                <div>
                                                    <CheckCircle2 size={24} className="text-success" />
                                                    <span>¡Archivo convertido exitosamente!</span>
                                                </div>
                                                {selectedFile.creditsRemaining !== undefined && (
                                                    <p className="credits-info">
                                                        {selectedFile.creditsRemaining} conversiones gratuitas restantes
                                                    </p>
                                                )}
                                            </div>
                                            <div className="btn-group">
                                                <button 
                                                    className="download-btn"
                                                    onClick={async () => {
                                                        if (selectedFile.conversionId) {
                                                            try {
                                                                const blob = await apiService.downloadConvertedFile(selectedFile.conversionId);
                                                                const url = window.URL.createObjectURL(blob);
                                                                const a = document.createElement('a');
                                                                a.href = url;
                                                                a.download = `${selectedFile.file.name.split('.')[0]}_converted.${targetFormat}`;
                                                                document.body.appendChild(a);
                                                                a.click();
                                                                window.URL.revokeObjectURL(url);
                                                                document.body.removeChild(a);
                                                            } catch (error) {
                                                                alert('Descarga fallida. Por favor intenta de nuevo.');
                                                            }
                                                        }
                                                    }}
                                                >
                                                    Descargar Resultado
                                                </button>
                                                <button className="new-btn" onClick={reset}>
                                                    <RefreshCw size={18} />
                                                    Nueva Conversión
                                                </button>
                                            </div>
                                        </div>
                                    )}
                                    {selectedFile.status === 'error' && (
                                        <div className="result-actions">
                                            <div className="error-msg">
                                                <div>
                                                    <AlertCircle size={24} className="text-error" />
                                                    <span>{selectedFile.errorMessage || 'Conversión fallida'}</span>
                                                </div>
                                            </div>
                                            <button className="new-btn" onClick={reset}>
                                                <RefreshCw size={18} />
                                                Intentar de Nuevo
                                            </button>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>

            <section className="conversion-info">
                <h3>Cómo funciona</h3>
                <div className="info-steps">
                    <div className="info-step">
                        <span className="step-num">1</span>
                        <p>Sube tu documento de forma segura a nuestro almacenamiento en la nube</p>
                    </div>
                    <div className="info-step">
                        <span className="step-num">2</span>
                        <p>Selecciona el formato objetivo e inicia el procesamiento</p>
                    </div>
                    <div className="info-step">
                        <span className="step-num">3</span>
                        <p>Descarga tu archivo convertido y guárdalo en el historial</p>
                    </div>
                </div>
            </section>
        </div>
    );
};
