import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { apiService } from '../../services/api';
import './VerifyEmail.css';

/**
 * Página de verificación de email.
 * Lee el token de la URL (?token=...), llama al backend y muestra éxito o error.
 */
export const VerifyEmail = () => {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
    const [message, setMessage] = useState('');

    useEffect(() => {
        const token = searchParams.get('token');
        if (!token) {
            setStatus('error');
            setMessage('Enlace inválido. Falta el token de verificación.');
            return;
        }

        apiService
            .verifyEmail(token)
            .then((res) => {
                setStatus('success');
                setMessage(res.message || 'Email verificado. Ya puedes iniciar sesión.');
            })
            .catch((err) => {
                setStatus('error');
                setMessage(err?.detail || err?.message || 'El enlace ha expirado o ya fue usado.');
            });
    }, [searchParams]);

    return (
        <div className="verify-email-page">
            <div className="verify-email-card">
                {status === 'loading' && (
                    <p className="verify-email-message" role="status">
                        Verificando tu correo…
                    </p>
                )}
                {status === 'success' && (
                    <>
                        <div className="verify-email-icon verify-email-icon--success" aria-hidden>
                            ✓
                        </div>
                        <h2 className="verify-email-title">¡Correo verificado!</h2>
                        <p className="verify-email-message">{message}</p>
                        <Link to="/login" className="verify-email-btn">
                            Iniciar sesión
                        </Link>
                    </>
                )}
                {status === 'error' && (
                    <>
                        <div className="verify-email-icon verify-email-icon--error" aria-hidden>
                            ✕
                        </div>
                        <h2 className="verify-email-title">Error de verificación</h2>
                        <p className="verify-email-message">{message}</p>
                        <Link to="/login" className="verify-email-btn">
                            Volver al inicio de sesión
                        </Link>
                    </>
                )}
            </div>
        </div>
    );
};
