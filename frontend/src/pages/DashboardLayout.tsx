import { Outlet } from 'react-router-dom';
import { Menu } from 'lucide-react';
import { Sidebar } from '../components/Sidebar/Sidebar';
import { ThemeToggle } from '../components/ThemeToggle/ThemeToggle';
import { useAppStore } from '../stores/appStore';
import './DashboardLayout.css';

export const DashboardLayout = () => {
    const { sidebarCollapsed, toggleSidebar, user } = useAppStore();

    return (
        <div className="dashboard-layout">
            <Sidebar />
            <main className={`main-content ${sidebarCollapsed ? 'expanded' : ''}`}>
                <header className="main-header">
                    <div className="header-left">
                        <button
                            className="mobile-menu-toggle"
                            onClick={toggleSidebar}
                            aria-label="Toggle menu"
                        >
                            <Menu size={24} />
                        </button>
                        <h1 className="page-title">Welcome, {user?.full_name || 'User'}!</h1>
                    </div>
                    <div className="header-right">
                        <ThemeToggle />
                    </div>
                </header>
                <div className="content-area">
                    <Outlet />
                </div>
            </main>
        </div>
    );
};
