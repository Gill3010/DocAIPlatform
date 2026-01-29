import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, RefreshCw, FileEdit, FolderClock, Bot, Settings, ChevronLeft, ChevronRight } from 'lucide-react';
import { useAppStore } from '../../stores/appStore';
import './Sidebar.css';

export const Sidebar = () => {
    const location = useLocation();
    const { sidebarCollapsed, toggleSidebar, user } = useAppStore();

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
                <div className="sidebar-footer">
                    <div className="user-info">
                        <div className="user-avatar">
                            {user.full_name?.charAt(0).toUpperCase() || user.email.charAt(0).toUpperCase()}
                        </div>
                        {!sidebarCollapsed && (
                            <div className="user-details">
                                <p className="user-name">{user.full_name || 'Usuario'}</p>
                                <p className="user-email">{user.email}</p>
                                <p className="user-credits">
                                    {Math.max(0, 10 - user.free_conversion_count)} créditos disponibles
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </aside>
    );
};
