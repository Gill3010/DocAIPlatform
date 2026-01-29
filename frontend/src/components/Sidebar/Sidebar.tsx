import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, RefreshCw, FolderClock, Bot, Settings, ChevronLeft, ChevronRight } from 'lucide-react';
import { useAppStore } from '../../stores/appStore';
import './Sidebar.css';

export const Sidebar = () => {
    const location = useLocation();
    const { sidebarCollapsed, toggleSidebar, user } = useAppStore();

    const menuItems = [
        { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
        { path: '/convert', icon: RefreshCw, label: 'Convert Files' },
        { path: '/history', icon: FolderClock, label: 'History' },
        { path: '/ai-assistant', icon: Bot, label: 'AI Assistant' },
        { path: '/settings', icon: Settings, label: 'Settings' },
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
                    aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
                    title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
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
                                <p className="user-name">{user.full_name || 'User'}</p>
                                <p className="user-email">{user.email}</p>
                                <p className="user-credits">
                                    {3 - user.free_conversion_count} free conversions left
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </aside>
    );
};
