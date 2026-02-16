/**
 * Hook: estado y handlers para selección de archivo (drag, drop, input) y formato objetivo.
 * Usado por Convert.tsx.
 */
import { useState, useCallback } from 'react';
import type { LucideIcon } from 'lucide-react';
import { CONVERSION_MAP } from '../constants/conversions';
import { extensionMatchesUrlFrom, getAcceptForUrlFrom } from './useConvertFormats';

export interface FileWithProgress {
    file: File;
    progress: number;
    status: 'idle' | 'uploading' | 'converting' | 'completed' | 'error';
    targetFormat: string;
    conversionId?: number;
    errorMessage?: string;
    creditsRemaining?: number;
    isAnonymous?: boolean;
}

export type FormatOption = { id: string; name: string; icon: LucideIcon };

export function useFileSelection(urlFrom: string, urlTo: string) {
    const [dragActive, setDragActive] = useState(false);
    const [selectedFile, setSelectedFile] = useState<FileWithProgress | null>(null);
    const [targetFormat, setTargetFormat] = useState('pdf');
    const [availableFormats, setAvailableFormats] = useState<FormatOption[]>([]);

    const preferredTargetForFile = useCallback(
        (ext: string, formats: FormatOption[]): string => {
            if (!urlFrom || !urlTo || formats.length === 0) return formats[0]?.id ?? 'pdf';
            if (!extensionMatchesUrlFrom(ext, urlFrom)) return formats[0]?.id ?? 'pdf';
            const hasTarget = formats.some((f) => f.id === urlTo);
            return hasTarget ? urlTo : (formats[0]?.id ?? 'pdf');
        },
        [urlFrom, urlTo]
    );

    const handleDrag = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true);
        } else if (e.type === 'dragleave') {
            setDragActive(false);
        }
    }, []);

    const handleDrop = useCallback(
        (e: React.DragEvent) => {
            e.preventDefault();
            e.stopPropagation();
            setDragActive(false);
            if (e.dataTransfer.files?.[0]) {
                const file = e.dataTransfer.files[0];
                const ext = file.name.split('.').pop()?.toLowerCase() || '';
                if (urlFrom && !extensionMatchesUrlFrom(ext, urlFrom)) {
                    const expected = urlFrom === 'png' ? 'PNG, JPG o JPEG' : urlFrom.toUpperCase();
                    alert(`Selecciona un archivo en el formato esperado: ${expected}`);
                    return;
                }
                const formats = CONVERSION_MAP[ext] || [];
                const defaultTarget = preferredTargetForFile(ext, formats);
                setAvailableFormats(formats);
                setTargetFormat(defaultTarget);
                setSelectedFile({
                    file,
                    progress: 0,
                    status: 'idle',
                    targetFormat: defaultTarget,
                });
            }
        },
        [preferredTargetForFile, urlFrom]
    );

    const handleFileChange = useCallback(
        (e: React.ChangeEvent<HTMLInputElement>) => {
            if (e.target.files?.[0]) {
                const file = e.target.files[0];
                const ext = file.name.split('.').pop()?.toLowerCase() || '';
                if (urlFrom && !extensionMatchesUrlFrom(ext, urlFrom)) {
                    const expected = urlFrom === 'png' ? 'PNG, JPG o JPEG' : urlFrom.toUpperCase();
                    alert(`Selecciona un archivo en el formato esperado: ${expected}`);
                    e.target.value = '';
                    return;
                }
                const formats = CONVERSION_MAP[ext] || [];
                const defaultTarget = preferredTargetForFile(ext, formats);
                if (formats.length === 0) {
                    alert(
                        `Formato ${ext.toUpperCase()} no soportado. Formatos válidos: PNG, JPG, JPEG, PDF, TXT, DOCX, XML, HTML, DXF, DWG, PPTX, XLSX`
                    );
                    return;
                }
                setAvailableFormats(formats);
                setTargetFormat(defaultTarget);
                setSelectedFile({
                    file,
                    progress: 0,
                    status: 'idle',
                    targetFormat: defaultTarget,
                });
            }
        },
        [preferredTargetForFile, urlFrom]
    );

    const reset = useCallback(() => {
        setSelectedFile(null);
        setTargetFormat('pdf');
    }, []);

    return {
        selectedFile,
        setSelectedFile,
        targetFormat,
        setTargetFormat,
        availableFormats,
        dragActive,
        handleDrag,
        handleDrop,
        handleFileChange,
        reset,
        getAcceptForUrlFrom: () => getAcceptForUrlFrom(urlFrom),
    };
}
