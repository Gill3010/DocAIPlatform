import { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { FileType, ArrowRight, CheckCircle2, AlertCircle, RefreshCw, X, ArrowLeft } from 'lucide-react';
import { apiService } from '../../services/api';
import { useAppStore } from '../../stores/appStore';
import { useAnonymousSession } from '../../hooks/useAnonymousSession';
import { useFileSelection } from '../../hooks/useFileSelection';
import { useConversion } from '../../hooks/useConversion';
import { extensionMatchesUrlFrom } from '../../hooks/useConvertFormats';
import { FileDropZone } from '../../components/FileDropZone/FileDropZone';
import { ConversionLimitModal } from '../../components/ConversionLimitModal/ConversionLimitModal';
import { UpgradeModal } from '../../components/UpgradeModal/UpgradeModal';
import { SOURCE_LABELS, TARGET_LABELS } from '../../constants/conversions';
import './Convert.css';

export const Convert = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const urlFrom = searchParams.get('from') ?? '';
    const urlTo = searchParams.get('to') ?? '';
    const { token, user, setUser } = useAppStore();
    const { sessionId, syncFromCreditsRemaining } = useAnonymousSession();
    const isAnonymous = !token;

    const [showLimitModal, setShowLimitModal] = useState(false);
    const [showUpgradeModal, setShowUpgradeModal] = useState(false);
    const [upgradeModalContent, setUpgradeModalContent] = useState<{ title: string; description: string } | null>(null);

    const {
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
        getAcceptForUrlFrom,
    } = useFileSelection(urlFrom, urlTo);

    const { startConversion } = useConversion({
        setSelectedFile,
        setShowLimitModal,
        setShowUpgradeModal,
        setUpgradeModalContent,
        isAnonymous,
        sessionId,
        syncFromCreditsRemaining,
        user,
        setUser,
    });

    const fromLabel = urlFrom ? (SOURCE_LABELS[urlFrom] ?? urlFrom.toUpperCase()) : '';
    const toLabel = urlTo ? (TARGET_LABELS[urlTo] ?? urlTo.toUpperCase()) : '';
    const showHint = Boolean(fromLabel && toLabel);

    const currentStep = !selectedFile ? 1 : selectedFile.status === 'idle' ? 2 : 3;
    const stepLabels: Record<number, string> = {
        1: 'Subir archivo',
        2: 'Confirmar y convertir',
        3: 'Resultado',
    };

    return (
        <div className="convert-page">
            <div className="convert-header">
                <h2>Convertidor de Documentos</h2>
                <p>Sube tu archivo y elige el formato de salida</p>
            </div>

            <p className="convert-step-indicator" aria-live="polite">
                Paso {currentStep} de 3: {stepLabels[currentStep]}
            </p>

            <div className="convert-container">
                {!selectedFile ? (
                    <FileDropZone
                        onDragEnter={handleDrag}
                        onDragLeave={handleDrag}
                        onDragOver={handleDrag}
                        onDrop={handleDrop}
                        onFileChange={handleFileChange}
                        isDragActive={dragActive}
                        accept={getAcceptForUrlFrom() || undefined}
                        inputId="file-upload"
                        hintText={showHint ? `Convierte tu archivo ${fromLabel} a ${toLabel}` : undefined}
                    />
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
                                    {(() => {
                                        const ext = selectedFile.file.name.split('.').pop()?.toLowerCase() ?? '';
                                        const fileMatchesChosen = urlFrom && urlTo && extensionMatchesUrlFrom(ext, urlFrom);
                                        const chosenInList = urlTo && availableFormats.some((f) => f.id === urlTo);
                                        const singleFormatMode = fileMatchesChosen && chosenInList;
                                        const targetLabelShort = urlTo ? (TARGET_LABELS[urlTo] ?? urlTo.toUpperCase()) : '';
                                        if (singleFormatMode && targetLabelShort) {
                                            return (
                                                <>
                                                    <div className="convert-simple-row">
                                                        <button type="button" className="back-btn" onClick={reset}>
                                                            <ArrowLeft size={20} />
                                                            Volver
                                                        </button>
                                                    </div>
                                                    <p className="convert-simple-hint">Se convertirá a <strong>{targetLabelShort}</strong></p>
                                                    <button className="convert-btn" onClick={() => startConversion(selectedFile, targetFormat)}>
                                                        Convertir a {targetLabelShort}
                                                        <ArrowRight size={20} />
                                                    </button>
                                                </>
                                            );
                                        }
                                        return (
                                            <>
                                                <div className="convert-simple-row">
                                                    <button type="button" className="back-btn" onClick={reset}>
                                                        <ArrowLeft size={20} />
                                                        Volver
                                                    </button>
                                                </div>
                                                <div className="format-selector">
                                                    <p className="label">Convertir a:</p>
                                                    {availableFormats.length > 0 ? (
                                                        <div className="format-grid">
                                                            {availableFormats.map((f) => {
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
                                                <button className="convert-btn" onClick={() => startConversion(selectedFile, targetFormat)}>
                                                    Convertir Ahora
                                                    <ArrowRight size={20} />
                                                </button>
                                            </>
                                        );
                                    })()}
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
                                                <div className="success-msg__row">
                                                    <span className="success-msg__icon" aria-hidden>
                                                        <CheckCircle2 size={24} />
                                                    </span>
                                                    <span className="success-msg__text">¡Archivo convertido exitosamente!</span>
                                                </div>
                                                {selectedFile.creditsRemaining !== undefined && (
                                                    <p className="credits-info">
                                                        {(() => {
                                                            const isUnlimited = user?.is_superuser || user?.can_access_admin_panel || (user?.is_premium && user?.premium_plan_id !== 'Básico');
                                                            if (isUnlimited) return 'Conversiones ilimitadas';

                                                            const remaining = selectedFile.creditsRemaining!;
                                                            if (user?.premium_plan_id === 'Básico') {
                                                                return `${remaining} de 50 conversiones mensuales restantes`;
                                                            }

                                                            const limit = isAnonymous ? 3 : 5;
                                                            return `${Math.min(remaining, limit)} de ${limit} conversiones gratuitas restantes`;
                                                        })()}
                                                        {!user?.is_premium && !user?.is_superuser && !user?.can_access_admin_panel && isAnonymous && selectedFile.creditsRemaining! < 3 && (
                                                            ' — Regístrate para 2 más'
                                                        )}
                                                    </p>
                                                )}
                                            </div>
                                            <div className="btn-group">
                                                <button
                                                    className="download-btn"
                                                    onClick={async () => {
                                                        if (selectedFile.conversionId) {
                                                            try {
                                                                const dlOptions = selectedFile.isAnonymous && sessionId
                                                                    ? { anonymousSessionId: sessionId }
                                                                    : undefined;
                                                                const blob = await apiService.downloadConvertedFile(
                                                                    selectedFile.conversionId,
                                                                    dlOptions
                                                                );
                                                                const url = window.URL.createObjectURL(blob);
                                                                const a = document.createElement('a');
                                                                a.href = url;
                                                                a.download = `${selectedFile.file.name.split('.')[0]}_converted.${targetFormat}`;
                                                                document.body.appendChild(a);
                                                                a.click();
                                                                window.URL.revokeObjectURL(url);
                                                                document.body.removeChild(a);
                                                            } catch {
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
                                                <button
                                                    className="collab-btn"
                                                    disabled={!selectedFile.conversionId}
                                                    onClick={async () => {
                                                        if (!selectedFile.conversionId) return;
                                                        try {
                                                            const doc = await apiService.createDocumentFromConversion(selectedFile.conversionId);
                                                            navigate(`/collab/${doc.id}`);
                                                        } catch (error) {
                                                            console.error('Failed to create document:', error);
                                                            alert('Error al abrir el editor. Asegúrate de estar registrado.');
                                                        }
                                                    }}
                                                >
                                                    Abrir en Editor Colaborativo
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

            <ConversionLimitModal
                isOpen={showLimitModal}
                onClose={() => setShowLimitModal(false)}
                anonymousSessionId={sessionId}
            />
            <UpgradeModal
                isOpen={showUpgradeModal}
                onClose={() => setShowUpgradeModal(false)}
                title={upgradeModalContent?.title}
                description={upgradeModalContent?.description}
            />
        </div>
    );
};
