import { createContext, useContext, useState, useCallback } from 'react';

interface DashboardSearchContextValue {
    query: string;
    setQuery: (value: string) => void;
}

export const DashboardSearchContext = createContext<DashboardSearchContextValue | null>(null);

export function DashboardSearchProvider({ children }: { children: React.ReactNode }) {
    const [query, setQuery] = useState('');
    const setQueryStable = useCallback((value: string) => setQuery(value), []);
    return (
        <DashboardSearchContext.Provider value={{ query, setQuery: setQueryStable }}>
            {children}
        </DashboardSearchContext.Provider>
    );
}

export function useDashboardSearch(): DashboardSearchContextValue {
    const ctx = useContext(DashboardSearchContext);
    if (!ctx) {
        return {
            query: '',
            setQuery: () => {}
        };
    }
    return ctx;
}
