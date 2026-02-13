import { Link } from 'react-router-dom';
import './TermsOfUse.css';

export const TermsOfUse = () => {
    return (
        <div className="legal-page">
            <h1 className="legal-page-title">Términos de uso</h1>
            <p className="legal-page-intro">
                Última actualización: febrero 2025. Al utilizar DocAI Platform («la Plataforma»),
                usted acepta los siguientes términos. Si no está de acuerdo, no use el servicio.
            </p>

            <h2 className="legal-page-section">1. Servicio</h2>
            <p className="legal-page-intro">
                DocAI Platform es un servicio en línea operado por <strong>Innova Proyectos</strong> que ofrece:
            </p>
            <ul className="legal-page-list">
                <li><strong>Conversión de documentos:</strong> conversión entre formatos (PDF, Word, Excel, PowerPoint, imágenes, texto, etc.).</li>
                <li><strong>Herramientas PDF:</strong> unir, dividir, rotar, comprimir y otras operaciones sobre archivos PDF.</li>
                <li><strong>Asistente IA:</strong> ayuda con preguntas sobre documentos mediante inteligencia artificial.</li>
                <li><strong>Formateo de manuscritos:</strong> formato profesional para manuscritos.</li>
                <li><strong>Documentos colaborativos:</strong> creación y edición colaborativa de documentos.</li>
            </ul>

            <h2 className="legal-page-section">2. Registro y cuenta</h2>
            <p className="legal-page-intro">
                Puede usar la Plataforma de forma anónima (con límites) o registrándose con email y contraseña,
                o bien mediante Google o Facebook. Usted es responsable de mantener la confidencialidad de su cuenta
                y de todas las actividades que ocurran bajo ella.
            </p>

            <h2 className="legal-page-section">3. Uso aceptable</h2>
            <p className="legal-page-intro">
                Usted se compromete a usar la Plataforma de forma legal y ética. Está <strong>prohibido</strong>:
            </p>
            <ul className="legal-page-list">
                <li>Subir contenido ilegal, difamatorio o que viole derechos de terceros.</li>
                <li>Intentar vulnerar la seguridad del sistema o acceder a datos de otros usuarios.</li>
                <li>Utilizar la Plataforma para spam, fraude o actividades fraudulentas.</li>
                <li>Reutilizar, revender o redistribuir el servicio de forma masiva no autorizada.</li>
            </ul>

            <h2 className="legal-page-section">4. Límites y créditos</h2>
            <p className="legal-page-intro">
                La Plataforma opera bajo un modelo freemium. Los usuarios registrados y anónimos tienen un número
                limitado de créditos (conversiones y usos del asistente IA). El uso excesivo o abusivo puede resultar
                en restricciones o suspensión de la cuenta.
            </p>

            <h2 className="legal-page-section">5. Propiedad intelectual</h2>
            <p className="legal-page-intro">
                Usted conserva la propiedad de los documentos que sube. Al subir contenido, nos otorga los derechos
                necesarios para procesarlo (convertir, analizar) y prestar el servicio. La Plataforma, su diseño,
                logotipos y tecnología son propiedad de Innova Proyectos o sus licenciantes.
            </p>

            <h2 className="legal-page-section">6. Limitación de responsabilidad</h2>
            <p className="legal-page-intro">
                El servicio se presta «tal cual». Innova Proyectos no garantiza resultados concretos ni la ausencia
                de errores. No seremos responsables de daños indirectos, derivados o consecuentes. En la medida
                permitida por la ley, nuestra responsabilidad se limita al monto que el usuario haya pagado por
                el servicio en los últimos doce meses.
            </p>

            <h2 className="legal-page-section">7. Modificaciones</h2>
            <p className="legal-page-intro">
                Nos reservamos el derecho de modificar estos términos. Los cambios importantes se notificarán por
                correo o mediante un aviso en la Plataforma. El uso continuado tras la publicación constituye la
                aceptación de los nuevos términos.
            </p>

            <h2 className="legal-page-section">8. Contacto y jurisdicción</h2>
            <p className="legal-page-intro">
                Para consultas sobre estos términos, escriba a{' '}
                <a href="mailto:innovaproyectos507@gmail.com">innovaproyectos507@gmail.com</a>.
                Estos términos se rigen por las leyes de la República de Panamá. Cualquier conflicto será resuelto
                ante los tribunales competentes de Panamá.
            </p>

            <Link to="/dashboard" className="legal-page-back">
                Volver al inicio
            </Link>
        </div>
    );
};
