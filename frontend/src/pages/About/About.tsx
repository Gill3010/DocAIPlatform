import { Heart } from 'lucide-react';
import './About.css';

export const About = () => {
    return (
        <div className="about-page">
            <header className="about-header">
                <Heart size={32} className="about-header__icon" aria-hidden />
                <h1 className="about-page__title">Nosotros</h1>
                <p className="about-page__intro">
                    DocAI es una plataforma de conversión de documentos y herramientas PDF, desarrollada por Innova Proyectos.
                </p>
            </header>

            <section className="about-section">
                <h2 className="about-section__title">Sobre la plataforma</h2>
                <p className="about-section__text">
                    Nuestro objetivo es ofrecer herramientas sencillas y fiables para convertir y gestionar documentos:
                    múltiples formatos de entrada y salida, formateo de manuscritos, herramientas PDF y un asistente
                    de IA integrado para ayudarte en el día a día.
                </p>
            </section>

            <section className="about-section">
                <h2 className="about-section__title">Innova Proyectos</h2>
                <p className="about-section__text">
                    Somos un equipo enfocado en soluciones digitales que facilitan el trabajo con documentos.
                    DocAI forma parte de nuestro compromiso por ofrecer productos útiles y accesibles.
                </p>
            </section>

            <section className="about-section">
                <h2 className="about-section__title">Contacto</h2>
                <p className="about-section__text">
                    Para consultas comerciales, soporte o colaboraciones, puedes ponerte en contacto con nosotros
                    a través de los canales indicados en la web o en el pie de página de la plataforma.
                </p>
            </section>
        </div>
    );
};
