import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, Theme } from '../types';

interface AppState {
    user: User | null;
    token: string | null;
    theme: Theme;
    sidebarCollapsed: boolean;

    setUser: (user: User | null) => void;
    setToken: (token: string | null) => void;
    setTheme: (theme: Theme) => void;
    toggleTheme: () => void;
    toggleSidebar: () => void;
    logout: () => void;
}

export const useAppStore = create<AppState>()(
    persist(
        (set) => ({
            user: null,
            token: null,
            theme: 'light',
            sidebarCollapsed: false,

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
            logout: () => set({ user: null, token: null }),
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
