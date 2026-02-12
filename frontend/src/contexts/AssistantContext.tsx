import { createContext, useContext, type ReactNode } from 'react';

interface AssistantContextValue {
    isOpen: boolean;
    setOpen: (open: boolean | ((prev: boolean) => boolean)) => void;
}

const AssistantContext = createContext<AssistantContextValue | null>(null);

export function AssistantProvider({
    children,
    value
}: {
    children: ReactNode;
    value: AssistantContextValue;
}) {
    return (
        <AssistantContext.Provider value={value}>
            {children}
        </AssistantContext.Provider>
    );
}

export function useAssistant() {
    const ctx = useContext(AssistantContext);
    return ctx;
}
