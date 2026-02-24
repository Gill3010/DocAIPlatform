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
            // Plan Básico: 50 conversiones/mes (monthly_conversion_count). Gratuito: 5 (free_conversion_count)
            const isBasicPlan = user?.premium_plan_id === 'Básico';
            const limitReached = isAdminUnlimited
                ? false
                : isBasicPlan
                    ? (user?.monthly_conversion_count ?? 0) >= 50
                    : (user?.free_conversion_count ?? 0) >= 5;
            if (!isAnonymous && user && limitReached) {
                if (setUpgradeModalContent) {
                    setUpgradeModalContent(null);
                }
                setShowUpgradeModal(true);
                return;
            }

            setSelectedFile((prev) => (prev ? { ...prev, status: 'uploading', progress: 0 } : null));

            try {
                const apiOptions = isAnonymous && sessionId ? { anonymousSessionId: sessionId } : undefined;
                const response = await apiService.uploadAndConvert(
                    selectedFile.file,
                    targetFormat,
                    apiOptions
                );

                if (isAnonymous && response.credits_remaining !== undefined) {
                    syncFromCreditsRemaining(response.credits_remaining);
                }
                if (
                    response.status === 'completed' &&
                    !isAnonymous &&
                    user &&
                    response.credits_remaining !== undefined &&
                    !isAdminUnlimited
                ) {
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

                if (response.status === 'completed') {
                    setSelectedFile((prev) =>
                        prev ? { ...prev, status: 'completed', progress: 100 } : null
                    );
                } else {
                    // status === 'processing': poll hasta completed/failed (evita timeout 504)
                    const pollStatus = async () => {
                        const opts =
                            isAnonymous && sessionId ? { anonymousSessionId: sessionId } : undefined;
                        for (let i = 0; i < 120; i++) {
                            await new Promise((r) => setTimeout(r, 1500));
                            const st = await apiService.getConversionStatus(
                                response.conversion_id,
                                opts
                            );
                            if (st.status === 'completed') {
                                if (
                                    !isAnonymous &&
                                    user &&
                                    !isAdminUnlimited &&
                                    setUser
                                ) {
                                    if (user.premium_plan_id === 'Básico') {
                                        setUser({
                                            ...user,
                                            monthly_conversion_count:
                                                (user.monthly_conversion_count ?? 0) + 1,
                                        });
                                    } else {
                                        setUser({
                                            ...user,
                                            free_conversion_count:
                                                (user.free_conversion_count ?? 0) + 1,
                                        });
                                    }
                                }
                                setSelectedFile((prev) =>
                                    prev ? { ...prev, status: 'completed', progress: 100 } : null
                                );
                                return;
                            }
                            if (st.status === 'failed') {
                                setSelectedFile((prev) =>
                                    prev
                                        ? {
                                              ...prev,
                                              status: 'error',
                                              errorMessage:
                                                  st.error_message ||
                                                  'Conversion failed. Please try again.',
                                          }
                                        : null
                                );
                                return;
                            }
                            setSelectedFile((prev) =>
                                prev ? { ...prev, progress: Math.min(95, 60 + i * 3) } : null
                            );
                        }
                        setSelectedFile((prev) =>
                            prev
                                ? {
                                      ...prev,
                                      status: 'error',
                                      errorMessage:
                                          'Conversion is taking longer than expected. Please check your history.',
                                  }
                                : null
                        );
                    };
                    pollStatus();
                }
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
                    const isNetworkError =
                        (typeof detail === 'string' && detail.toLowerCase().includes('failed to fetch')) ||
                        (error instanceof TypeError && (error as Error).message?.includes('fetch'));
                    const errorMsg = isNetworkError
                        ? 'Error de conexión. Verifica tu internet o intenta más tarde.'
                        : typeof detail === 'string'
                            ? detail
                            : 'Conversion failed. Please try again.';
                    setSelectedFile((prev) =>
                        prev
                            ? { ...prev, status: 'error', errorMessage: errorMsg }
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
