import { useRef, useEffect } from 'react';
import { Settings, Moon, Sun, Globe } from 'lucide-react';
import { useAppStore } from '../../stores/appStore';
import './SettingsMenu.css';

interface SettingsMenuProps {
    isOpen: boolean;
    onToggle: () => void;
    onClose: () => void;
}

export const SettingsMenu = ({ isOpen, onToggle, onClose }: SettingsMenuProps) => {
    const { theme, setTheme } = useAppStore();
    const menuRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!isOpen) return;
        function handleClickOutside(e: MouseEvent) {
            if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
                onClose();
            }
        }
        function handleEscape(e: KeyboardEvent) {
            if (e.key === 'Escape') onClose();
        }
        document.addEventListener('click', handleClickOutside);
        document.addEventListener('keydown', handleEscape);
        return () => {
            document.removeEventListener('click', handleClickOutside);
            document.removeEventListener('keydown', handleEscape);
        };
    }, [isOpen, onClose]);

    return (
        <div ref={menuRef} className="settings-menu">
            <button
                type="button"
                className="settings-menu__trigger"
                onClick={onToggle}
                aria-label="Configuración"
                aria-expanded={isOpen}
                aria-haspopup="menu"
            >
                <Settings size={20} strokeWidth={2} />
            </button>
            {isOpen && (
                <div
                    className="settings-menu__dropdown"
                    role="menu"
                    onClick={(e) => e.stopPropagation()}
                >
                    <div className="settings-menu__arrow" aria-hidden />
                    <div className="settings-menu__section">
                        <span className="settings-menu__section-title">Tema</span>
                        <div className="settings-menu__options">
                            <button
                                type="button"
                                role="menuitemradio"
                                aria-checked={theme === 'light'}
                                className={`settings-menu__option ${theme === 'light' ? 'settings-menu__option--active' : ''}`}
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setTheme('light');
                                }}
                            >
                                <Sun size={18} />
                                <span>Claro</span>
                            </button>
                            <button
                                type="button"
                                role="menuitemradio"
                                aria-checked={theme === 'dark'}
                                className={`settings-menu__option ${theme === 'dark' ? 'settings-menu__option--active' : ''}`}
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setTheme('dark');
                                }}
                            >
                                <Moon size={18} />
                                <span>Oscuro</span>
                            </button>
                        </div>
                    </div>
                    <div className="settings-menu__section">
                        <span className="settings-menu__section-title">Idioma</span>
                        <div className="settings-menu__options">
                            <button
                                type="button"
                                role="menuitemradio"
                                aria-checked={true}
                                className="settings-menu__option settings-menu__option--active"
                                disabled
                                title="Próximamente"
                            >
                                <Globe size={18} />
                                <span>Español</span>
                            </button>
                            <button
                                type="button"
                                role="menuitemradio"
                                aria-checked={false}
                                className="settings-menu__option"
                                disabled
                                title="Próximamente"
                            >
                                <Globe size={18} />
                                <span>English</span>
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
