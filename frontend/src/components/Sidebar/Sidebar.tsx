import { Link, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, RefreshCw, FileEdit, FileText, FolderClock, ChevronLeft, ChevronRight, User as UserIcon, LogOut, ChevronUp } from 'lucide-react';
import { useAppStore } from '../../stores/appStore';
import { getAvatarUrl } from '../../services/api';
import { useState, useRef, useEffect } from 'react';
import './Sidebar.css';

const SIDEBAR_COLLAPSED_WIDTH = 80;
const TOOLTIP_OFFSET = 12;

export const Sidebar = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { sidebarCollapsed, toggleSidebar, user, logout } = useAppStore();
    const [userMenuOpen, setUserMenuOpen] = useState(false);
    const [tooltip, setTooltip] = useState<{ text: string; top: number; left: number } | null>(null);
    const menuRef = useRef<HTMLDivElement>(null);
    const tooltipTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    const showTooltip = (el: HTMLElement, text: string) => {
        if (!sidebarCollapsed) return;
        tooltipTimerRef.current = setTimeout(() => {
            const rect = el.getBoundingClientRect();
            setTooltip({
                text,
                top: rect.top + rect.height / 2,
                left: SIDEBAR_COLLAPSED_WIDTH + TOOLTIP_OFFSET,
            });
        }, 200);
    };

    const hideTooltip = () => {
        if (tooltipTimerRef.current) {
            clearTimeout(tooltipTimerRef.current);
            tooltipTimerRef.current = null;
        }
        setTooltip(null);
    };

    // Close sidebar when clicking a menu item (both mobile and desktop)
    const handleMenuItemClick = () => {
        // If sidebar is expanded (not collapsed), close it
        if (!sidebarCollapsed) {
            toggleSidebar();
        }
    };

    // Close menu when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                setUserMenuOpen(false);
            }
        };

        if (userMenuOpen) {
            document.addEventListener('mousedown', handleClickOutside);
        }

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [userMenuOpen]);

    const handleLogout = () => {
        logout();
        navigate('/dashboard');
    };

    const menuItems = [
        { path: '/dashboard', icon: LayoutDashboard, label: 'Panel Principal' },
        { path: '/convert', icon: RefreshCw, label: 'Convertir Archivos' },
        { path: '/documents', icon: FileText, label: 'Mis Documentos' },
        { path: '/format-manuscript', icon: FileEdit, label: 'Formatear Manuscrito' },
        { path: '/history', icon: FolderClock, label: 'Historial' },
    ];

    return (
        <>
            {/* Backdrop overlay - closes sidebar when clicked */}
            {!sidebarCollapsed && (
                <div
                    className="sidebar-backdrop"
                    onClick={toggleSidebar}
                    aria-label="Cerrar menú"
                />
            )}

            <aside className={`sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
                <div className="sidebar-header">
                    {!sidebarCollapsed && (
                        <h2 className="sidebar-logo">
                            <span className="logo-icon">✨</span>
                            <span className="logo-text">
                                <span className="logo-brand">DocAI</span>
                                <span className="logo-tagline">Platform</span>
                            </span>
                        </h2>
                    )}
                    <button
                        className="sidebar-toggle"
                        onClick={toggleSidebar}
                        aria-label={sidebarCollapsed ? 'Expandir menú' : 'Colapsar menú'}
                        title={sidebarCollapsed ? 'Expandir menú' : 'Colapsar menú'}
                    >
                        {sidebarCollapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
                    </button>
                </div>

                <nav className="sidebar-nav">
                    {menuItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = location.pathname === item.path;

                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={`nav-item ${isActive ? 'active' : ''}`}
                                onMouseEnter={(e) => showTooltip(e.currentTarget, item.label)}
                                onMouseLeave={hideTooltip}
                                onClick={handleMenuItemClick}
                            >
                                <Icon className="nav-icon" size={20} />
                                {!sidebarCollapsed && <span className="nav-label">{item.label}</span>}
                            </Link>
                        );
                    })}
                </nav>

                {!user && (
                    <div className="sidebar-footer sidebar-footer--guest">
                        <Link
                            to="/login"
                            className="nav-item nav-item--login"
                            onMouseEnter={(e) => showTooltip(e.currentTarget, 'Iniciar sesión')}
                            onMouseLeave={hideTooltip}
                            onClick={handleMenuItemClick}
                        >
                            <UserIcon className="nav-icon" size={20} />
                            {!sidebarCollapsed && <span className="nav-label">Iniciar sesión</span>}
                        </Link>
                    </div>
                )}
                {user && (
                    <div className="sidebar-footer" ref={menuRef}>
                        <button
                            className="user-info-button"
                            onClick={() => setUserMenuOpen(!userMenuOpen)}
                            onMouseEnter={(e) => showTooltip(e.currentTarget, user.full_name || user.email)}
                            onMouseLeave={hideTooltip}
                        >
                            <div className="user-avatar">
                                {getAvatarUrl(user.avatar_url) ? (
                                    <img src={getAvatarUrl(user.avatar_url)!} alt="" className="user-avatar__img" />
                                ) : (
                                    user.full_name?.charAt(0).toUpperCase() || user.email.charAt(0).toUpperCase()
                                )}
                            </div>
                            {!sidebarCollapsed && (
                                <>
                                    <div className="user-details">
                                        <p className="user-name">{user.full_name || 'Usuario'}</p>
                                        <p className="user-email">{user.email}</p>
                                        <p className="user-credits">
                                            {(() => {
                                                const isUnlimited = user.is_superuser || (user.is_premium && user.premium_plan_id !== 'Básico');
                                                if (isUnlimited) {
                                                    return (
                                                        <span className="premium-label">
                                                            {user.premium_plan_id || 'Premium'} • <span className="infinity-symbol">∞</span> créditos
                                                        </span>
                                                    );
                                                }
                                                if (user.is_premium && user.premium_plan_id === 'Básico') {
                                                    const remaining = 50 - (user.monthly_conversion_count || 0);
                                                    return (
                                                        <span className="premium-label">
                                                            Básico • {Math.max(0, remaining)} créditos
                                                        </span>
                                                    );
                                                }
                                                return `${Math.max(0, 5 - user.free_conversion_count)} de 5 créditos`;
                                            })()}
                                        </p>
                                    </div>
                                    <ChevronUp
                                        size={16}
                                        className={`user-menu-icon ${userMenuOpen ? 'open' : ''}`}
                                    />
                                </>
                            )}
                        </button>

                        {userMenuOpen && !sidebarCollapsed && (
                            <div className="user-menu">
                                <button
                                    className="user-menu-item"
                                    onClick={() => {
                                        setUserMenuOpen(false);
                                        handleMenuItemClick();
                                        navigate('/settings');
                                    }}
                                >
                                    <UserIcon size={16} />
                                    <span>Editar Perfil</span>
                                </button>
                                <button
                                    className="user-menu-item logout"
                                    onClick={() => {
                                        setUserMenuOpen(false);
                                        handleMenuItemClick();
                                        handleLogout();
                                    }}
                                >
                                    <LogOut size={16} />
                                    <span>Cerrar Sesión</span>
                                </button>
                            </div>
                        )}
                    </div>
                )}
            </aside>

            {/* Tooltip flotante - position: fixed para no causar scroll */}
            {sidebarCollapsed && tooltip && (
                <div
                    className="sidebar-tooltip"
                    style={{
                        left: tooltip.left,
                        top: tooltip.top,
                    }}
                    role="tooltip"
                >
                    {tooltip.text}
                </div>
            )}
        </>
    );
};
