import { Link, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, RefreshCw, FileEdit, FolderClock, Bot, Settings, ChevronLeft, ChevronRight, User as UserIcon, LogOut, ChevronUp } from 'lucide-react';
import { useAppStore } from '../../stores/appStore';
import { useState, useRef, useEffect } from 'react';
import './Sidebar.css';

export const Sidebar = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { sidebarCollapsed, toggleSidebar, user, logout } = useAppStore();
    const [userMenuOpen, setUserMenuOpen] = useState(false);
    const menuRef = useRef<HTMLDivElement>(null);

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
        navigate('/login');
    };

    const menuItems = [
        { path: '/dashboard', icon: LayoutDashboard, label: 'Panel Principal' },
        { path: '/convert', icon: RefreshCw, label: 'Convertir Archivos' },
        { path: '/format-manuscript', icon: FileEdit, label: 'Formatear Manuscrito' },
        { path: '/history', icon: FolderClock, label: 'Historial' },
        { path: '/settings', icon: Settings, label: 'Configuración' },
    ];

    return (
        <aside className={`sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
            <div className="sidebar-header">
                {!sidebarCollapsed && (
                    <h2 className="sidebar-logo">
                        <span className="logo-icon">✨</span>
                        DocAI
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
                            title={sidebarCollapsed ? item.label : undefined}
                        >
                            <Icon className="nav-icon" size={20} />
                            {!sidebarCollapsed && <span className="nav-label">{item.label}</span>}
                        </Link>
                    );
                })}
            </nav>

            {user && (
                <div className="sidebar-footer" ref={menuRef}>
                    <button 
                        className="user-info-button"
                        onClick={() => setUserMenuOpen(!userMenuOpen)}
                        title={sidebarCollapsed ? user.email : undefined}
                    >
                        <div className="user-avatar">
                            {user.full_name?.charAt(0).toUpperCase() || user.email.charAt(0).toUpperCase()}
                        </div>
                        {!sidebarCollapsed && (
                            <>
                                <div className="user-details">
                                    <p className="user-name">{user.full_name || 'Usuario'}</p>
                                    <p className="user-email">{user.email}</p>
                                    <p className="user-credits">
                                        {Math.max(0, 10 - user.free_conversion_count)} créditos disponibles
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
                                    navigate('/settings');
                                }}
                            >
                                <UserIcon size={16} />
                                <span>Editar Perfil</span>
                            </button>
                            <button 
                                className="user-menu-item logout"
                                onClick={handleLogout}
                            >
                                <LogOut size={16} />
                                <span>Cerrar Sesión</span>
                            </button>
                        </div>
                    )}
                </div>
            )}
        </aside>
    );
};
