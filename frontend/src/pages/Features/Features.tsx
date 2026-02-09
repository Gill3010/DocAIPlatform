import { Layers, FileText, Bot, History, Zap } from 'lucide-react';
import './Features.css';

export const Features = () => {
    const features = [
        {
            icon: FileText,
            title: 'Conversión de documentos',
            description: 'Convierte entre múltiples formatos: PDF, DOCX, imágenes, JATS XML y otros. Sube tu archivo, elige el formato de salida y descarga el resultado.',
        },
        {
            icon: Zap,
            title: 'Herramientas PDF',
            description: 'Merge, split y otras utilidades para trabajar con PDFs directamente desde el navegador.',
        },
        {
            icon: History,
            title: 'Historial',
            description: 'Accede al historial de tus conversiones cuando inicias sesión. Descarga de nuevo los archivos convertidos cuando los necesites.',
        },
        {
            icon: Bot,
            title: 'Asistente IA',
            description: 'Un asistente integrado que te ayuda con preguntas sobre la plataforma y el uso de las herramientas de conversión.',
        },
        {
            icon: Layers,
            title: 'Formatear manuscrito',
            description: 'Herramienta especializada para formatear manuscritos según estándares editoriales y preparar documentos para publicación.',
        },
    ];

    return (
        <div className="features-page">
            <header className="features-header">
                <Layers size={32} className="features-header__icon" aria-hidden />
                <h1 className="features-page__title">Características</h1>
                <p className="features-page__intro">
                    DocAI combina conversión de documentos, herramientas PDF y asistente IA en una sola plataforma.
                </p>
            </header>

            <ul className="features-list">
                {features.map((f) => {
                    const Icon = f.icon;
                    return (
                        <li key={f.title} className="features-item">
                            <div className="features-item__icon-wrap">
                                <Icon size={22} className="features-item__icon" aria-hidden />
                            </div>
                            <div className="features-item__content">
                                <h2 className="features-item__title">{f.title}</h2>
                                <p className="features-item__desc">{f.description}</p>
                            </div>
                        </li>
                    );
                })}
            </ul>
        </div>
    );
};
