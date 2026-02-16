import { Upload } from 'lucide-react';
import './FileDropZone.css';

export interface FileDropZoneProps {
    onDragEnter: (e: React.DragEvent) => void;
    onDragLeave: (e: React.DragEvent) => void;
    onDragOver: (e: React.DragEvent) => void;
    onDrop: (e: React.DragEvent) => void;
    onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    isDragActive: boolean;
    accept?: string;
    inputId?: string;
    /** Texto opcional bajo el párrafo principal (ej. "Convierte tu archivo X a Y") */
    hintText?: React.ReactNode;
}

/**
 * Zona de arrastrar y soltar (o clic) para seleccionar archivo.
 * Usado por Convert.tsx.
 */
export function FileDropZone({
    onDragEnter,
    onDragLeave,
    onDragOver,
    onDrop,
    onFileChange,
    isDragActive,
    accept,
    inputId = 'file-upload',
    hintText,
}: FileDropZoneProps) {
    return (
        <div
            className={`file-drop-zone ${isDragActive ? 'file-drop-zone--active' : ''}`}
            onDragEnter={onDragEnter}
            onDragLeave={onDragLeave}
            onDragOver={onDragOver}
            onDrop={onDrop}
        >
            <div className="file-drop-zone__icon-wrap">
                <Upload size={64} className="file-drop-zone__icon" aria-hidden />
            </div>
            <div className="file-drop-zone__text">
                <h3>Haz clic o arrastra el archivo aquí</h3>
                <p>PNG, JPG, JPEG, PDF, DOCX, TXT, XML, HTML, DXF, DWG, PPTX, XLSX hasta 10MB</p>
                {hintText && <p className="file-drop-zone__hint">{hintText}</p>}
            </div>
            <div className="file-drop-zone__badges">
                <span className="file-drop-zone__badge">PNG/JPG</span>
                <span className="file-drop-zone__badge">PDF</span>
                <span className="file-drop-zone__badge">DOCX</span>
                <span className="file-drop-zone__badge">TXT</span>
                <span className="file-drop-zone__badge">XML</span>
                <span className="file-drop-zone__badge">HTML</span>
            </div>
            <input
                type="file"
                id={inputId}
                className="file-drop-zone__input"
                accept={accept || undefined}
                onChange={onFileChange}
                aria-label="Seleccionar archivo"
            />
            <label htmlFor={inputId} className="file-drop-zone__btn">
                Seleccionar Archivo
            </label>
        </div>
    );
}
