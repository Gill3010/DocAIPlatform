import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, Theme } from '../types';
import { removeToken } from '../services/storageService';

interface AppState {
    user: User | null;
    token: string | null;
    theme: Theme;
    sidebarCollapsed: boolean;
    isMetricsModalOpen: boolean;
    isLoginOverlayOpen: boolean;
    loginOverlayFrom: string;
    loginOverlayInitialMode: 'login' | 'register';

    setUser: (user: User | null) => void;
    setToken: (token: string | null) => void;
    setTheme: (theme: Theme) => void;
    toggleTheme: () => void;
    toggleSidebar: () => void;
    logout: () => void;
    openMetricsModal: () => void;
    closeMetricsModal: () => void;
    openLoginOverlay: (from: string, initialMode?: 'login' | 'register') => void;
    closeLoginOverlay: () => void;
}

export const useAppStore = create<AppState>()(
    persist(
        (set) => ({
            user: null,
            token: null,
            theme: 'light',
            sidebarCollapsed: false,
            isMetricsModalOpen: false,
            isLoginOverlayOpen: false,
            loginOverlayFrom: '/dashboard',
            loginOverlayInitialMode: 'login',

            setUser: (user) => set({ user }),
            setToken: (token) => set({ token }),
            setTheme: (theme) => {
                set({ theme });
                document.documentElement.setAttribute('data-theme', theme);
            },
            toggleTheme: () => set((state) => {
                const newTheme = state.theme === 'light' ? 'dark' : 'light';
                document.documentElement.setAttribute('data-theme', newTheme);
                return { theme: newTheme };
            }),
            toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
            logout: () => {
                removeToken();
                set({ user: null, token: null });
            },
            openMetricsModal: () => set({ isMetricsModalOpen: true }),
            closeMetricsModal: () => set({ isMetricsModalOpen: false }),
            openLoginOverlay: (from, initialMode = 'login') =>
                set({ isLoginOverlayOpen: true, loginOverlayFrom: from, loginOverlayInitialMode: initialMode }),
            closeLoginOverlay: () => set({ isLoginOverlayOpen: false }),
        }),
        {
            name: 'saas-app-storage',
            partialize: (state) => ({
                token: state.token,
                theme: state.theme,
                sidebarCollapsed: state.sidebarCollapsed,
            }),
        }
    )
);
