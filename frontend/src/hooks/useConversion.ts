/**
 * Hook: lógica de inicio de conversión (upload, progreso, errores y límites).
 * Usado por Convert.tsx.
 */
import { useCallback } from 'react';
import { apiService, ApiError } from '../services/api';
import type { User } from '../types';
import type { FileWithProgress } from './useFileSelection';

export interface UseConversionOptions {
    setSelectedFile: React.Dispatch<React.SetStateAction<FileWithProgress | null>>;
    setShowLimitModal: (show: boolean) => void;
    setShowUpgradeModal: (show: boolean) => void;
    setUpgradeModalContent?: (content: { title: string; description: string } | null) => void;
    isAnonymous: boolean;
    sessionId: string | null;
    syncFromCreditsRemaining: (n: number) => void;
    user: User | null;
    setUser: (u: User | null) => void;
}

export function useConversion(options: UseConversionOptions) {
    const {
        setSelectedFile,
        setShowLimitModal,
        setShowUpgradeModal,
        setUpgradeModalContent,
        isAnonymous,
        sessionId,
        syncFromCreditsRemaining,
        user,
        setUser,
    } = options;

    const isAdminUnlimited = user?.is_superuser === true || user?.can_access_admin_panel === true || (user?.is_premium === true && user?.premium_plan_id !== 'Básico');

    const startConversion = useCallback(
        async (selectedFile: FileWithProgress | null, targetFormat: string) => {
            if (!selectedFile) return;
            if (!isAnonymous && user && !isAdminUnlimited && (user.free_conversion_count ?? 0) >= 5) {
                if (setUpgradeModalContent) {
                    setUpgradeModalContent(null); // Use defaults
                }
                setShowUpgradeModal(true);
                return;
            }

            setSelectedFile((prev) => (prev ? { ...prev, status: 'uploading', progress: 0 } : null));

            try {
                const uploadInterval = setInterval(() => {
                    setSelectedFile((prev) => {
                        if (!prev || prev.progress >= 50) {
                            clearInterval(uploadInterval);
                            return prev;
                        }
                        return { ...prev, progress: prev.progress + 10 };
                    });
                }, 200);

                const apiOptions = isAnonymous && sessionId ? { anonymousSessionId: sessionId } : undefined;
                const response = await apiService.uploadAndConvert(
                    selectedFile.file,
                    targetFormat,
                    apiOptions
                );

                clearInterval(uploadInterval);

                if (isAnonymous && response.credits_remaining !== undefined) {
                    syncFromCreditsRemaining(response.credits_remaining);
                }
                if (!isAnonymous && user && response.credits_remaining !== undefined && !isAdminUnlimited) {
                    if (user.premium_plan_id === 'Básico') {
                        const used = 50 - response.credits_remaining;
                        setUser({ ...user, monthly_conversion_count: used });
                    } else {
                        const used = 5 - response.credits_remaining;
                        setUser({ ...user, free_conversion_count: used });
                    }
                }

                setSelectedFile((prev) =>
                    prev
                        ? {
                            ...prev,
                            status: 'converting',
                            progress: 60,
                            conversionId: response.conversion_id,
                            creditsRemaining: response.credits_remaining,
                            isAnonymous,
                        }
                        : null
                );

                const convertInterval = setInterval(() => {
                    setSelectedFile((prev) => {
                        if (!prev || prev.progress >= 100) {
                            clearInterval(convertInterval);
                            return prev ? { ...prev, status: 'completed', progress: 100 } : null;
                        }
                        return { ...prev, progress: prev.progress + 10 };
                    });
                }, 300);
            } catch (error: unknown) {
                console.error('Conversion failed:', error);
                const detail =
                    error instanceof ApiError
                        ? error.detail
                        : (error as { detail?: string; message?: string })?.detail ??
                        (error as Error)?.message ??
                        '';
                if (detail === 'anonymous_limit_reached') {
                    setShowLimitModal(true);
                    setSelectedFile((prev) => (prev ? { ...prev, status: 'idle' } : null));
                } else if (detail === 'auth_limit_reached') {
                    if (setUpgradeModalContent) setUpgradeModalContent(null);
                    setShowUpgradeModal(true);
                    setSelectedFile((prev) => (prev ? { ...prev, status: 'idle' } : null));
                } else if (detail === 'premium_format_required') {
                    if (setUpgradeModalContent) {
                        setUpgradeModalContent({
                            title: 'Este formato requiere un plan Premium',
                            description: 'Los formatos avanzados como CAD o JATS están disponibles exclusivamente para nuestros usuarios Premium.'
                        });
                    }
                    setShowUpgradeModal(true);
                    setSelectedFile((prev) => (prev ? { ...prev, status: 'idle' } : null));
                } else {
                    setSelectedFile((prev) =>
                        prev
                            ? {
                                ...prev,
                                status: 'error',
                                errorMessage:
                                    typeof detail === 'string' ? detail : 'Conversion failed. Please try again.',
                            }
                            : null
                    );
                }
            }
        },
        [
            isAnonymous,
            sessionId,
            isAdminUnlimited,
            user,
            setUser,
            syncFromCreditsRemaining,
            setSelectedFile,
            setShowLimitModal,
            setShowUpgradeModal,
            setUpgradeModalContent,
        ]
    );

    return { startConversion, isAdminUnlimited };
}
