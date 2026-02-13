import { Link } from 'react-router-dom';
import './PrivacyPolicy.css';

export const PrivacyPolicy = () => {
    return (
        <div className="legal-page">
            <h1 className="legal-page-title">Política de privacidad</h1>
            <p className="legal-page-intro">
                Última actualización: febrero 2025. Innova Proyectos («nosotros») opera DocAI Platform.
                Esta política describe qué datos recopilamos, para qué los usamos y cómo los protegemos.
            </p>

            <h2 className="legal-page-section">1. Datos que recopilamos</h2>
            <p className="legal-page-intro">
                Según cómo use la Plataforma, podemos recopilar:
            </p>
            <ul className="legal-page-list">
                <li><strong>Cuenta:</strong> correo electrónico, nombre, contraseña (almacenada de forma cifrada mediante hash).</li>
                <li><strong>Inicio de sesión social:</strong> si usa Google o Facebook, recibimos su email y nombre de esos proveedores.</li>
                <li><strong>Documentos convertidos:</strong> los archivos que sube para conversión se procesan temporalmente en nuestros servidores.</li>
                <li><strong>Historial de conversiones:</strong> formatos, estado y metadatos de las conversiones realizadas.</li>
                <li><strong>Conversaciones con el asistente IA:</strong> los mensajes que envía al asistente para poder responder.</li>
                <li><strong>Uso anónimo:</strong> identificador de sesión para usuarios que no inician sesión (límite de conversiones).</li>
            </ul>

            <h2 className="legal-page-section">2. Proveedores externos</h2>
            <p className="legal-page-intro">
                Utilizamos servicios de terceros que pueden recibir datos en el marco del servicio:
            </p>
            <ul className="legal-page-list">
                <li><strong>OpenAI:</strong> para el asistente de IA (preguntas sobre documentos). Las conversaciones se envían a sus modelos para generar respuestas.</li>
                <li><strong>Google:</strong> para el inicio de sesión con cuenta de Google (OAuth). Reciben solicitudes de autenticación.</li>
                <li><strong>Meta (Facebook):</strong> para el inicio de sesión con Facebook (OAuth). Reciben solicitudes de autenticación.</li>
            </ul>
            <p className="legal-page-intro">
                Estos proveedores tienen sus propias políticas de privacidad. Le recomendamos revisarlas si desea conocer
                cómo tratan sus datos.
            </p>

            <h2 className="legal-page-section">3. Uso de los datos</h2>
            <p className="legal-page-intro">
                Usamos los datos para:
            </p>
            <ul className="legal-page-list">
                <li>Proporcionar y mejorar el servicio (conversiones, herramientas PDF, asistente IA).</li>
                <li>Gestionar su cuenta y autenticación.</li>
                <li>Enviar comunicaciones necesarias (por ejemplo, confirmaciones, soporte).</li>
                <li>Cumplir obligaciones legales y resolver incidencias de seguridad.</li>
            </ul>
            <p className="legal-page-intro">
                No vendemos sus datos personales a terceros. No usamos sus datos para publicidad personalizada.
            </p>

            <h2 className="legal-page-section">4. Seguridad</h2>
            <p className="legal-page-intro">
                Las contraseñas se almacenan con hash (no en texto plano). Las comunicaciones se realizan por
                canales cifrados (HTTPS). Los archivos se procesan en servidores seguros y se eliminan según
                nuestra política de retención.
            </p>

            <h2 className="legal-page-section">5. Retención</h2>
            <p className="legal-page-intro">
                Conservamos los datos mientras su cuenta esté activa y sea necesario para prestar el servicio.
                Puede solicitar la eliminación de sus datos en cualquier momento (consulte nuestra página de{' '}
                <Link to="/data-deletion">Eliminación de datos</Link>).
            </p>

            <h2 className="legal-page-section">6. Sus derechos</h2>
            <p className="legal-page-intro">
                Puede acceder, rectificar o solicitar la eliminación de sus datos. Para ejercer estos derechos o
                formular preguntas sobre privacidad, contacte a{' '}
                <a href="mailto:innovaproyectos507@gmail.com">innovaproyectos507@gmail.com</a>.
            </p>

            <h2 className="legal-page-section">7. Cambios</h2>
            <p className="legal-page-intro">
                Podemos actualizar esta política. Los cambios relevantes se publicarán aquí y, si procede, se le
                informará por correo.
            </p>

            <Link to="/dashboard" className="legal-page-back">
                Volver al inicio
            </Link>
        </div>
    );
};
