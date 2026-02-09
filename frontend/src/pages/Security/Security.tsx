import { Link } from 'react-router-dom';
import { Lock, Shield, FileCheck, Key } from 'lucide-react';
import './Security.css';

export const Security = () => {
    const items = [
        {
            icon: Lock,
            title: 'Conexión segura',
            text: 'Toda la comunicación con la plataforma se realiza mediante HTTPS. Los archivos se transmiten cifrados.',
        },
        {
            icon: FileCheck,
            title: 'Procesamiento de archivos',
            text: 'Los documentos que subes se procesan en el servidor de forma temporal y se eliminan tras la conversión según nuestra política de retención.',
        },
        {
            icon: Key,
            title: 'Autenticación',
            text: 'Soporte para inicio de sesión con email y contraseña, y con proveedores externos (Google, Facebook) mediante OAuth 2.0.',
        },
        {
            icon: Shield,
            title: 'Privacidad y cumplimiento',
            text: 'Respetamos tu privacidad. Puedes consultar nuestra Política de privacidad y Términos de uso para más detalles sobre el tratamiento de datos.',
        },
    ];

    return (
        <div className="security-page">
            <header className="security-header">
                <Lock size={32} className="security-header__icon" aria-hidden />
                <h1 className="security-page__title">Seguridad</h1>
                <p className="security-page__intro">
                    En DocAI la seguridad y la privacidad de tus datos son una prioridad.
                </p>
            </header>

            <div className="security-grid">
                {items.map((item) => {
                    const Icon = item.icon;
                    return (
                        <article key={item.title} className="security-card">
                            <Icon size={24} className="security-card__icon" aria-hidden />
                            <h2 className="security-card__title">{item.title}</h2>
                            <p className="security-card__text">{item.text}</p>
                        </article>
                    );
                })}
            </div>

            <p className="security-footer">
                Para más información sobre cómo manejamos tus datos, visita la{' '}
                <Link to="/privacy-policy" className="security-link">Política de privacidad</Link>
                {' '}y los{' '}
                <Link to="/terms-of-use" className="security-link">Términos de uso</Link>.
            </p>
        </div>
    );
};
