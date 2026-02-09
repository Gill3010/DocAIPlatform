import { Component, type ErrorInfo, type ReactNode } from 'react';
import './ErrorBoundary.css';

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

/**
 * Error Boundary: captura errores en el árbol de hijos y muestra una UI de fallback.
 * En desarrollo muestra el mensaje de error; en producción un mensaje genérico.
 */
export class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('ErrorBoundary caught:', error, errorInfo);
    }

    render() {
        if (this.state.hasError && this.state.error) {
            if (this.props.fallback) {
                return this.props.fallback;
            }
            const isDev = import.meta.env?.DEV;
            return (
                <div className="error-boundary" role="alert">
                    <div className="error-boundary__content">
                        <h2 className="error-boundary__title">Algo salió mal</h2>
                        <p className="error-boundary__message">
                            Ha ocurrido un error inesperado. Por favor recarga la página o vuelve al inicio.
                        </p>
                        {isDev && this.state.error && (
                            <pre className="error-boundary__detail">{this.state.error.message}</pre>
                        )}
                        <div className="error-boundary__actions">
                            <button
                                type="button"
                                className="error-boundary__btn"
                                onClick={() => window.location.reload()}
                            >
                                Recargar página
                            </button>
                            <button
                                type="button"
                                className="error-boundary__btn error-boundary__btn--secondary"
                                onClick={() => {
                                    this.setState({ hasError: false, error: null });
                                    window.location.href = '/';
                                }}
                            >
                                Ir al inicio
                            </button>
                        </div>
                    </div>
                </div>
            );
        }
        return this.props.children;
    }
}
