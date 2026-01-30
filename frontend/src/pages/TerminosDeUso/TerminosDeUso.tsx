import { Link } from 'react-router-dom';
import './TerminosDeUso.css';

export const TerminosDeUso = () => {
    return (
        <div className="legal-page">
            <h1 className="legal-page-title">Términos de uso</h1>
            <p className="legal-page-intro">
                Los términos de uso de esta plataforma están en proceso de actualización.
                Para más información, póngase en contacto con Innova Proyectos.
            </p>
            <Link to="/dashboard" className="legal-page-back">
                Volver al inicio
            </Link>
        </div>
    );
};
