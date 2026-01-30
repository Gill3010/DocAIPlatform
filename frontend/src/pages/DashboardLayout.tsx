import { useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { Menu } from 'lucide-react';
import { Sidebar } from '../components/Sidebar/Sidebar';
import { ThemeToggle } from '../components/ThemeToggle/ThemeToggle';
import { AIAssistantFAB } from '../components/AIAssistantFAB/AIAssistantFAB';
import { Footer } from '../components/Footer/Footer';
import { useAppStore } from '../stores/appStore';
import { apiService } from '../services/api';
import './DashboardLayout.css';

export const DashboardLayout = () => {
    const { sidebarCollapsed, toggleSidebar, user, token, setUser } = useAppStore();

    useEffect(() => {
        // If we have a token but no user data, fetch the user info
        const loadUserData = async () => {
            if (token && !user) {
                try {
                    const userData = await apiService.getUserStats();
                    setUser({
                        email: userData.user.email,
                        full_name: userData.user.name,
                        free_conversion_count: userData.credits.used,
                        is_active: true,
                        is_superuser: false,
                        id: 0,
                        created_at: new Date().toISOString()
                    });
                } catch (error) {
                    console.error('Failed to load user data:', error);
                }
            }
        };

        loadUserData();
    }, [token, user, setUser]);

    return (
        <div className="dashboard-layout">
            <Sidebar />
            <main className={`main-content ${sidebarCollapsed ? 'expanded' : ''}`}>
                <header className="main-header">
                    <div className="header-left">
                        <button
                            className="mobile-menu-toggle"
                            onClick={toggleSidebar}
                            aria-label="Alternar menú"
                        >
                            <Menu size={24} />
                        </button>
                        <h1 className="page-title">Bienvenido, {user?.full_name || 'Usuario'}!</h1>
                    </div>
                    <div className="header-right">
                        <ThemeToggle />
                    </div>
                </header>
                <div className="content-area">
                    <Outlet />
                </div>
                <Footer />
            </main>
            <AIAssistantFAB />
        </div>
    );
};
