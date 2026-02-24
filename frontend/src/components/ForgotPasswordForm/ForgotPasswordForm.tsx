import { useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { apiService, ApiError } from '../../services/api';
import './ForgotPasswordForm.css';

export interface ForgotPasswordFormProps {
    /** Prefix for form control ids (avoids duplicates when in overlay) */
    idPrefix?: string;
    /** When provided, "Volver" uses a button that calls this instead of Link to /login */
    onBack?: () => void;
}

export const ForgotPasswordForm = ({ idPrefix = 'forgot', onBack }: ForgotPasswordFormProps) => {
    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            await apiService.forgotPassword(email);
            setSuccess(true);
        } catch (err) {
            const msg = err instanceof ApiError ? err.detail : err instanceof Error ? err.message : 'Ocurrió un error';
            setError(msg);
        } finally {
            setLoading(false);
        }
    };

    const emailId = `${idPrefix}-email`;

    return (
        <div className="forgot-password-form-wrapper">
            <h2 className="forgot-password-form-title">¿Olvidaste tu contraseña?</h2>
            <p className="forgot-password-form-description">
                Ingresa tu correo y te enviaremos un enlace para restablecerla.
            </p>

            {success ? (
                <div className="forgot-password-form-success">
                    <p>Si existe una cuenta con ese email, recibirás un enlace para restablecer tu contraseña.</p>
                    <p className="forgot-password-form-check">Revisa tu bandeja de entrada y spam.</p>
                    {onBack ? (
                        <button type="button" className="forgot-password-form-btn" onClick={onBack}>
                            Volver al inicio de sesión
                        </button>
                    ) : (
                        <Link to="/login" className="forgot-password-form-btn">
                            Volver al inicio de sesión
                        </Link>
                    )}
                </div>
            ) : (
                <form onSubmit={handleSubmit} className="forgot-password-form-form">
                    {error && (
                        <div className="forgot-password-form-error" role="alert">
                            {error}
                        </div>
                    )}
                    <div className="form-group">
                        <label htmlFor={emailId}>Email</label>
                        <input
                            id={emailId}
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="tu@email.com"
                            required
                            autoComplete="email"
                            disabled={loading}
                        />
                    </div>
                    <button type="submit" className="forgot-password-form-btn btn-primary" disabled={loading}>
                        {loading ? 'Enviando…' : 'Enviar enlace'}
                    </button>
                </form>
            )}

            {!success && (
                <p className="forgot-password-form-footer">
                    {onBack ? (
                        <button type="button" className="forgot-password-form-btn forgot-password-form-btn--link" onClick={onBack}>
                            ← Volver al inicio de sesión
                        </button>
                    ) : (
                        <Link to="/login" className="forgot-password-form-btn forgot-password-form-btn--link">
                            ← Volver al inicio de sesión
                        </Link>
                    )}
                </p>
            )}
        </div>
    );
};
