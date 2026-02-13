import { Link } from 'react-router-dom';
import './Footer.css';

export const Footer = () => {
    return (
        <footer className="footer-cintillo" role="contentinfo">
            <div className="footer-cintillo-inner">
                <p className="footer-ownership">
                    © 2026 <span className="footer-app-name">DocAI Platform</span>. Desarrollado por{' '}
                    <a
                        href="https://innova-proyectos.web.app/"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="footer-brand-link"
                    >
                        Innova Proyectos
                    </a>
                    .
                </p>
                <nav className="footer-legal" aria-label="Enlaces legales">
                    <Link to="/terms-of-use" className="footer-link">
                        Términos de uso
                    </Link>
                    <span className="footer-separator" aria-hidden="true">·</span>
                    <Link to="/privacy-policy" className="footer-link">
                        Política de privacidad
                    </Link>
                    <span className="footer-separator" aria-hidden="true">·</span>
                    <Link to="/data-deletion" className="footer-link">
                        Eliminación de datos
                    </Link>
                </nav>
            </div>
        </footer>
    );
};
