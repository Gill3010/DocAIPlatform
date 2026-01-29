import { useState, useCallback } from 'react';
import { Upload, FileText, CheckCircle2, AlertCircle } from 'lucide-react';
import './FormatManuscript.css';

export const FormatManuscript = () => {
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [isDragging, setIsDragging] = useState(false);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);

        const files = Array.from(e.dataTransfer.files);
        if (files.length > 0) {
            setSelectedFile(files[0]);
        }
    }, []);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (files && files.length > 0) {
            setSelectedFile(files[0]);
        }
    };

    const handleRemoveFile = () => {
        setSelectedFile(null);
    };

    const formatFileSize = (bytes: number) => {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    };

    return (
        <div className="format-manuscript-page">
            <div className="format-header">
                <div>
                    <h2>Formatear Manuscrito</h2>
                    <p>Sube tu manuscrito y aplica formato profesional automáticamente</p>
                </div>
                <div className="format-status">
                    <span className="status-badge coming-soon">Próximamente</span>
                </div>
            </div>

            {/* Upload Area */}
            <div className="format-upload-section">
                {!selectedFile ? (
                    <div
                        className={`upload-zone ${isDragging ? 'dragging' : ''}`}
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                    >
                        <Upload className="upload-icon" size={64} />
                        <h3>Selecciona tu manuscrito</h3>
                        <p>Arrastra y suelta tu archivo aquí, o haz clic para seleccionar</p>
                        <div className="supported-formats">
                            <span className="format-badge">DOCX</span>
                            <span className="format-badge">TXT</span>
                            <span className="format-badge">PDF</span>
                        </div>
                        <input
                            type="file"
                            id="file-input"
                            accept=".docx,.txt,.pdf"
                            onChange={handleFileSelect}
                            className="file-input-hidden"
                        />
                        <label htmlFor="file-input" className="upload-btn">
                            Seleccionar Archivo
                        </label>
                    </div>
                ) : (
                    <div className="file-selected-container">
                        <div className="file-selected-card">
                            <div className="file-icon-container">
                                <FileText size={48} />
                            </div>
                            <div className="file-details">
                                <h4>{selectedFile.name}</h4>
                                <p className="file-size">{formatFileSize(selectedFile.size)}</p>
                                <div className="file-status">
                                    <CheckCircle2 size={20} className="status-icon success" />
                                    <span>Archivo listo para formatear</span>
                                </div>
                            </div>
                            <button onClick={handleRemoveFile} className="remove-file-btn">
                                ✕
                            </button>
                        </div>

                        {/* Placeholder for format options - Coming Soon */}
                        <div className="format-options-placeholder">
                            <div className="placeholder-icon">
                                <AlertCircle size={32} />
                            </div>
                            <h3>Opciones de Formato</h3>
                            <p>Los parámetros de formato se configurarán próximamente</p>
                            <div className="placeholder-items">
                                <div className="placeholder-item">📄 Márgenes y espaciado</div>
                                <div className="placeholder-item">📝 Fuente y tamaño</div>
                                <div className="placeholder-item">📑 Numeración de páginas</div>
                                <div className="placeholder-item">📊 Encabezados y pies</div>
                            </div>
                        </div>

                        <button className="format-btn" disabled>
                            <FileText size={20} />
                            Formatear Manuscrito (Próximamente)
                        </button>
                    </div>
                )}
            </div>

            {/* Info Section */}
            <div className="format-info-section">
                <div className="info-card">
                    <h4>¿Qué es el formato de manuscritos?</h4>
                    <p>
                        El formateo automático de manuscritos aplica estándares profesionales
                        a tu documento, incluyendo márgenes, fuentes, espaciado y estructura
                        según las normas editoriales más comunes.
                    </p>
                </div>
                <div className="info-card">
                    <h4>Formatos soportados</h4>
                    <ul>
                        <li>DOCX - Microsoft Word</li>
                        <li>TXT - Texto plano</li>
                        <li>PDF - Documento portable</li>
                    </ul>
                </div>
            </div>
        </div>
    );
};
