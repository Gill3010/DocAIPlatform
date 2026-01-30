import { useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { LayoutGrid, Tag, Lock, Layers, Heart } from 'lucide-react';
import './MoreMenu.css';

const MORE_ITEMS = [
    { id: 'precios', label: 'Precios', icon: Tag, href: '#precios' },
    { id: 'seguridad', label: 'Seguridad', icon: Lock, href: '#seguridad' },
    { id: 'caracteristicas', label: 'Características', icon: Layers, href: '#caracteristicas' },
    { id: 'nosotros', label: 'Nosotros', icon: Heart, href: '#nosotros' },
] as const;

interface MoreMenuProps {
    isOpen: boolean;
    onToggle: () => void;
    onClose: () => void;
}

export const MoreMenu = ({ isOpen, onToggle, onClose }: MoreMenuProps) => {
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
        <div ref={menuRef} className="more-menu">
            <button
                type="button"
                className="more-menu__trigger"
                onClick={onToggle}
                aria-label="Más opciones"
                aria-expanded={isOpen}
                aria-haspopup="menu"
            >
                <LayoutGrid size={20} strokeWidth={2} />
            </button>
            {isOpen && (
                <div
                    className="more-menu__dropdown"
                    role="menu"
                    onClick={(e) => e.stopPropagation()}
                >
                    <div className="more-menu__arrow" aria-hidden />
                    <ul className="more-menu__list">
                        {MORE_ITEMS.map((item) => {
                            const Icon = item.icon;
                            return (
                                <li key={item.id} role="none">
                                    <Link
                                        to={item.href}
                                        className="more-menu__item"
                                        role="menuitem"
                                        onClick={onClose}
                                    >
                                        <Icon size={18} className="more-menu__item-icon" />
                                        <span>{item.label}</span>
                                    </Link>
                                </li>
                            );
                        })}
                    </ul>
                </div>
            )}
        </div>
    );
};
