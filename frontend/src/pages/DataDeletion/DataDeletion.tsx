import { Link } from 'react-router-dom';
import './DataDeletion.css';

export const DataDeletion = () => {
    return (
        <div className="legal-page">
            <h1 className="legal-page-title">Eliminación de datos</h1>
            <p className="legal-page-intro">
                DocAI Platform, operado por <strong>Innova Proyectos</strong>, permite a los usuarios solicitar
                la eliminación de sus datos personales en cualquier momento. Esta página describe qué datos se
                eliminan y cómo puede solicitar la eliminación.
            </p>

            <h2 className="legal-page-section">¿Qué datos se eliminan?</h2>
            <p className="legal-page-intro">
                Al solicitar la eliminación, se eliminarán los datos asociados a su cuenta, entre ellos:
            </p>
            <ul className="legal-page-list">
                <li>Perfil (email, nombre, contraseña)</li>
                <li>Historial de conversiones de documentos</li>
                <li>Documentos creados para edición colaborativa</li>
                <li>Registro de uso del asistente IA (conversaciones)</li>
                <li>Sesión anónima vinculada (si aplica)</li>
            </ul>
            <p className="legal-page-intro">
                Una vez eliminados, estos datos <strong>no podrán ser recuperados</strong>.
            </p>

            <h2 className="legal-page-section">¿Cómo solicitar la eliminación?</h2>
            <ol className="legal-page-list">
                <li>
                    <strong>Mediante correo electrónico:</strong> Envíe un correo a{' '}
                    <a href="mailto:innovaproyectos507@gmail.com">innovaproyectos507@gmail.com</a>{' '}
                    con el asunto «Solicitud de eliminación de datos» e indique la dirección de correo
                    electrónico asociada a su cuenta. Procesaremos su solicitud en un plazo de 30 días.
                </li>
                <li>
                    <strong>Desde la aplicación:</strong> Si tiene una cuenta, inicie sesión, vaya a{' '}
                    <Link to="/settings">Mi perfil</Link> y contacte con soporte desde allí si lo prefiere.
                </li>
            </ol>

            <h2 className="legal-page-section">Inicio de sesión con Google o Facebook</h2>
            <p className="legal-page-intro">
                Si utilizó inicio de sesión con <strong>Google</strong> o <strong>Facebook</strong>,
                también puede revocar el acceso desde la configuración de su cuenta en esos proveedores.
                Esto no elimina sus datos en DocAI Platform; para eliminarlos debe realizar la solicitud
                por correo como se indica arriba.
            </p>
            <ul className="legal-page-list">
                <li><strong>Google:</strong> <a href="https://myaccount.google.com/permissions" target="_blank" rel="noopener noreferrer">Cuenta de Google → Seguridad → Acceso de terceros</a></li>
                <li><strong>Facebook:</strong> <a href="https://www.facebook.com/settings?tab=applications" target="_blank" rel="noopener noreferrer">Configuración → Aplicaciones y sitios web</a></li>
            </ul>

            <Link to="/dashboard" className="legal-page-back">
                Volver al inicio
            </Link>
        </div>
    );
};
