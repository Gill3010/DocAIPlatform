import { useState, type FormEvent } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { apiService, ApiError } from '../../services/api';
import { ThemeToggle } from '../../components/ThemeToggle/ThemeToggle';
import { Eye, EyeOff } from 'lucide-react';
import './ResetPassword.css';

export const ResetPassword = () => {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const token = searchParams.get('token');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setError('');
        if (password !== confirmPassword) {
            setError('Las contraseñas no coinciden');
            return;
        }
        if (password.length < 8) {
            setError('La contraseña debe tener al menos 8 caracteres');
            return;
        }
        if (!token) {
            setError('Enlace inválido. Falta el token.');
            return;
        }
        setLoading(true);
        try {
            await apiService.resetPassword(token, password);
            setSuccess(true);
        } catch (err) {
            const msg = err instanceof ApiError ? err.detail : err instanceof Error ? err.message : 'Ocurrió un error';
            setError(msg);
        } finally {
            setLoading(false);
        }
    };

    if (!token) {
        return (
            <div className="reset-password-page">
                <div className="theme-toggle-wrapper">
                    <ThemeToggle />
                </div>
                <div className="reset-password-card">
                    <h2 className="reset-password-title">Enlace inválido</h2>
                    <p>Falta el token de restablecimiento. Solicita un nuevo enlace.</p>
                    <Link to="/auth/forgot-password" className="reset-password-btn">
                        Solicitar nuevo enlace
                    </Link>
                </div>
            </div>
        );
    }

    if (success) {
        return (
            <div className="reset-password-page">
                <div className="theme-toggle-wrapper">
                    <ThemeToggle />
                </div>
                <div className="reset-password-card">
                    <div className="reset-password-icon reset-password-icon--success">✓</div>
                    <h2 className="reset-password-title">Contraseña actualizada</h2>
                    <p>Ya puedes iniciar sesión con tu nueva contraseña.</p>
                    <Link
                        to="/login"
                        className="reset-password-btn"
                        onClick={() => navigate('/login', { replace: true })}
                    >
                        Iniciar sesión
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="reset-password-page">
            <div className="theme-toggle-wrapper">
                <ThemeToggle />
            </div>
            <div className="reset-password-card">
                <h2 className="reset-password-title">Nueva contraseña</h2>
                <p className="reset-password-description">Ingresa tu nueva contraseña.</p>

                <form onSubmit={handleSubmit} className="reset-password-form">
                    {error && (
                        <div className="reset-password-error" role="alert">
                            {error}
                        </div>
                    )}
                    <div className="form-group">
                        <label htmlFor="reset-password">Nueva contraseña</label>
                        <div className="password-input-wrapper">
                            <input
                                id="reset-password"
                                type={showPassword ? 'text' : 'password'}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                required
                                minLength={8}
                                autoComplete="new-password"
                                disabled={loading}
                            />
                            <button
                                type="button"
                                className="password-toggle"
                                onClick={() => setShowPassword(!showPassword)}
                                tabIndex={-1}
                                aria-label={showPassword ? 'Ocultar' : 'Mostrar'}
                            >
                                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                            </button>
                        </div>
                    </div>
                    <div className="form-group">
                        <label htmlFor="reset-confirm">Confirmar contraseña</label>
                        <input
                            id="reset-confirm"
                            type="password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            placeholder="••••••••"
                            required
                            autoComplete="new-password"
                            disabled={loading}
                        />
                    </div>
                    <button type="submit" className="reset-password-btn btn-primary" disabled={loading}>
                        {loading ? 'Actualizando…' : 'Actualizar contraseña'}
                    </button>
                </form>

                <p className="reset-password-footer">
                    <Link to="/login" className="link-button">← Volver al inicio de sesión</Link>
                </p>
            </div>
        </div>
    );
};
