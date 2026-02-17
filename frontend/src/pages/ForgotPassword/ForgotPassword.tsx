import { useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { apiService, ApiError } from '../../services/api';
import { ThemeToggle } from '../../components/ThemeToggle/ThemeToggle';
import './ForgotPassword.css';

export const ForgotPassword = () => {
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

    return (
        <div className="forgot-password-page">
            <div className="theme-toggle-wrapper">
                <ThemeToggle />
            </div>
            <div className="forgot-password-card">
                <h2 className="forgot-password-title">¿Olvidaste tu contraseña?</h2>
                <p className="forgot-password-description">
                    Ingresa tu correo y te enviaremos un enlace para restablecerla.
                </p>

                {success ? (
                    <div className="forgot-password-success">
                        <p>Si existe una cuenta con ese email, recibirás un enlace para restablecer tu contraseña.</p>
                        <p className="forgot-password-check">Revisa tu bandeja de entrada y spam.</p>
                        <Link to="/login" className="forgot-password-btn">
                            Volver al inicio de sesión
                        </Link>
                    </div>
                ) : (
                    <form onSubmit={handleSubmit} className="forgot-password-form">
                        {error && (
                            <div className="forgot-password-error" role="alert">
                                {error}
                            </div>
                        )}
                        <div className="form-group">
                            <label htmlFor="forgot-email">Email</label>
                            <input
                                id="forgot-email"
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="tu@email.com"
                                required
                                autoComplete="email"
                                disabled={loading}
                            />
                        </div>
                        <button type="submit" className="forgot-password-btn btn-primary" disabled={loading}>
                            {loading ? 'Enviando…' : 'Enviar enlace'}
                        </button>
                    </form>
                )}

                <p className="forgot-password-footer">
                    <Link to="/login" className="link-button">
                        ← Volver al inicio de sesión
                    </Link>
                </p>
            </div>
        </div>
    );
};
