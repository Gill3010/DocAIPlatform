import { Link } from 'react-router-dom';
import './Footer.css';

export const Footer = () => {
    return (
        <footer className="footer-cintillo" role="contentinfo">
            <div className="footer-cintillo-inner">
                <p className="footer-ownership">
                    © 2026 Esta plataforma es propiedad de Innova Proyectos.
                </p>
                <nav className="footer-legal" aria-label="Enlaces legales">
                    <Link to="/terminos-de-uso" className="footer-link">
                        Términos de uso
                    </Link>
                    <span className="footer-separator" aria-hidden="true">·</span>
                    <Link to="/politica-privacidad" className="footer-link">
                        Política de privacidad
                    </Link>
                </nav>
            </div>
        </footer>
    );
};
