import { useEffect, useState, useMemo } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Menu } from 'lucide-react';
import { Sidebar } from '../components/Sidebar/Sidebar';
import { ThemeToggle } from '../components/ThemeToggle/ThemeToggle';
import { ConversionSearch } from '../components/ConversionSearch/ConversionSearch';
import { AIAssistantFAB } from '../components/AIAssistantFAB/AIAssistantFAB';
import { Footer } from '../components/Footer/Footer';
import { useAppStore } from '../stores/appStore';
import { apiService } from '../services/api';
import { DashboardSearchContext } from '../contexts/DashboardSearchContext';
import { getDashboardConversions } from '../constants/conversions';
import { filterConversionsByQuery } from '../utils/searchConversions';
import './DashboardLayout.css';

function getPageTitle(pathname: string): string {
    const titles: Record<string, string> = {
        '/convert': 'Convertir',
        '/history': 'Historial',
        '/format-manuscript': 'Formatear manuscrito',
        '/terminos-de-uso': 'Términos de uso',
        '/politica-privacidad': 'Política de privacidad',
        '/settings': 'Ajustes'
    };
    return titles[pathname] ?? 'Inicio';
}

export const DashboardLayout = () => {
    const { sidebarCollapsed, toggleSidebar, user, token, setUser } = useAppStore();
    const location = useLocation();
    const pathname = location.pathname;
    const isDashboard = pathname === '/dashboard' || pathname === '/';

    const [searchQuery, setSearchQuery] = useState('');
    const conversionTypes = useMemo(() => getDashboardConversions(), []);
    const filteredConversions = useMemo(
        () => filterConversionsByQuery(conversionTypes, searchQuery),
        [conversionTypes, searchQuery]
    );

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
                        {isDashboard ? (
                            <div className="header-search">
                                <ConversionSearch
                                    query={searchQuery}
                                    onQueryChange={setSearchQuery}
                                    filteredConversions={filteredConversions}
                                />
                            </div>
                        ) : (
                            <h1 className="page-title">{getPageTitle(pathname)}</h1>
                        )}
                    </div>
                    <div className="header-right">
                        <ThemeToggle />
                    </div>
                </header>
                <DashboardSearchContext.Provider value={{ query: searchQuery, setQuery: setSearchQuery }}>
                    <div className="content-area">
                        <Outlet />
                    </div>
                </DashboardSearchContext.Provider>
                <Footer />
            </main>
            <AIAssistantFAB />
        </div>
    );
};
