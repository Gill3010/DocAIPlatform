import { Link } from 'react-router-dom';
import './DataDeletion.css';

export const DataDeletion = () => {
    return (
        <div className="legal-page">
            <h1 className="legal-page-title">Eliminación de datos</h1>
            <p className="legal-page-intro">
                DocAI Platform permite a los usuarios solicitar la eliminación de sus datos personales
                de nuestra plataforma en cualquier momento.
            </p>
            <h2 className="legal-page-section">¿Cómo solicitar la eliminación de mis datos?</h2>
            <ol className="legal-page-list">
                <li>
                    <strong>Mediante correo electrónico:</strong> Envíe un correo a{' '}
                    <a href="mailto:innovaproyectos507@gmail.com">innovaproyectos507@gmail.com</a>{' '}
                    con el asunto &quot;Solicitud de eliminación de datos&quot; e indique la dirección de correo
                    electrónico asociada a su cuenta. Procesaremos su solicitud en un plazo de 30 días.
                </li>
                <li>
                    <strong>Desde la aplicación:</strong> Si tiene una cuenta, inicie sesión, vaya a{' '}
                    <Link to="/settings">Configuración</Link> y contacte con soporte desde allí si
                    lo prefiere.
                </li>
            </ol>
            <p className="legal-page-intro">
                Una vez eliminados, sus datos personales (perfil, historial de conversiones, documentos
                subidos, etc.) no podrán ser recuperados. Si utilizó inicio de sesión con Facebook,
                también puede revocar el acceso desde la configuración de su cuenta de Facebook.
            </p>
            <Link to="/dashboard" className="legal-page-back">
                Volver al inicio
            </Link>
        </div>
    );
};
