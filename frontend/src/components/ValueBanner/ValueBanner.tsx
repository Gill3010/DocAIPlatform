import { useState, useEffect, useCallback } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useAppStore } from '../../stores/appStore';
import './ValueBanner.css';

interface Slide {
    image?: string;
    gradient?: string;
    title: string;
    description?: string;
}

const DEFAULT_SLIDES: Slide[] = [
    {
        gradient: 'linear-gradient(135deg, #0A2540 0%, #1F3C88 50%, #002B5B 100%)',
        title: 'Validación y alta precisión',
        description: 'Schema compliant para documentos estructurados',
    },
    {
        gradient: 'linear-gradient(135deg, #1F3C88 0%, #002B5B 50%, #0A2540 100%)',
        title: 'IA para múltiples formatos',
        description: 'PDF, DOCX, LaTeX, XML, EPUB, HTML y más',
    },
    {
        gradient: 'linear-gradient(135deg, #002B5B 0%, #0A2540 50%, #1F3C88 100%)',
        title: 'Procesamiento de manuscritos académicos',
        description: 'De documento a datos estructurados con IA',
    },
    {
        gradient: 'linear-gradient(135deg, #0A2540 0%, #002B5B 100%)',
        title: 'Dashboard y métricas de uso',
        description: 'Conversiones, tasa de éxito y control total',
    },
];

function getSlideImagePath(index: number): string {
    return `/banner/valor-${index + 1}.png`;
}

export function ValueBanner() {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [isPaused, setIsPaused] = useState(false);
    const { openMetricsModal } = useAppStore();

    const slides = DEFAULT_SLIDES.map((slide, i) => ({
        ...slide,
        image: slide.image ?? getSlideImagePath(i),
    }));

    const goTo = useCallback((index: number) => {
        setCurrentIndex((prev) => (index + slides.length) % slides.length);
    }, [slides.length]);

    useEffect(() => {
        if (isPaused) return;
        const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        if (prefersReduced) return;

        const id = setInterval(() => {
            setCurrentIndex((prev) => (prev + 1) % slides.length);
        }, 5000);
        return () => clearInterval(id);
    }, [isPaused, slides.length]);

    return (
        <section
            className="value-banner"
            aria-label="Descubre DocAI Platform"
            onMouseEnter={() => setIsPaused(true)}
            onMouseLeave={() => setIsPaused(false)}
            onFocus={() => setIsPaused(true)}
            onBlur={() => setIsPaused(false)}
        >
            <div className="value-banner__track">
                {slides.map((slide, index) => {
                    const bgStyle = slide.image && slide.gradient
                        ? {
                              backgroundImage: `linear-gradient(90deg, rgba(0,0,0,0.5) 0%, rgba(0,0,0,0.2) 100%), url(${slide.image}), ${slide.gradient}`,
                              backgroundSize: 'cover',
                              backgroundPosition: 'center',
                          }
                        : { background: slide.gradient };
                    return (
                    <div
                        key={index}
                        className={`value-banner__slide ${index === currentIndex ? 'value-banner__slide--active' : ''}`}
                        style={bgStyle}
                    >
                        <div className="value-banner__overlay" />
                        <div className="value-banner__content">
                            <p className="value-banner__title">{slide.title}</p>
                            {slide.description && (
                                <p className="value-banner__description">{slide.description}</p>
                            )}
                        </div>
                    </div>
                    );
                })}
            </div>

            <button
                type="button"
                className="value-banner__nav value-banner__nav--prev"
                onClick={() => goTo(currentIndex - 1)}
                aria-label="Slide anterior"
            >
                <ChevronLeft size={20} />
            </button>
            <button
                type="button"
                className="value-banner__nav value-banner__nav--next"
                onClick={() => goTo(currentIndex + 1)}
                aria-label="Slide siguiente"
            >
                <ChevronRight size={20} />
            </button>

            <div className="value-banner__dots" role="tablist" aria-label="Slides del cintillo">
                {slides.map((_, index) => (
                    <button
                        key={index}
                        type="button"
                        role="tab"
                        aria-selected={index === currentIndex}
                        aria-label={`Ir al slide ${index + 1}`}
                        className={`value-banner__dot ${index === currentIndex ? 'active' : ''}`}
                        onClick={() => goTo(index)}
                    />
                ))}
            </div>

            <button
                type="button"
                className="value-banner__metrics-link"
                onClick={openMetricsModal}
                aria-label="Ver mi resumen"
            >
                Ver mi resumen
            </button>
        </section>
    );
}
