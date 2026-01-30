import { Link } from 'react-router-dom';
import './PoliticaPrivacidad.css';

export const PoliticaPrivacidad = () => {
    return (
        <div className="legal-page">
            <h1 className="legal-page-title">Política de privacidad</h1>
            <p className="legal-page-intro">
                La política de privacidad de esta plataforma está en proceso de actualización.
                Para más información, póngase en contacto con Innova Proyectos.
            </p>
            <Link to="/dashboard" className="legal-page-back">
                Volver al inicio
            </Link>
        </div>
    );
};
