import { useEffect, useState, useMemo } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Menu } from 'lucide-react';
import { Sidebar } from '../components/Sidebar/Sidebar';
import { SettingsMenu } from '../components/SettingsMenu/SettingsMenu';
import { MoreMenu } from '../components/MoreMenu/MoreMenu';
import { ConversionSearch } from '../components/ConversionSearch/ConversionSearch';
import { AIAssistantTrigger } from '../components/AIAssistantTrigger/AIAssistantTrigger';
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
        '/terms-of-use': 'Términos de uso',
        '/privacy-policy': 'Política de privacidad',
        '/pdf-tools': 'Herramientas PDF',
        '/pricing': 'Precios',
        '/security': 'Seguridad',
        '/features': 'Características',
        '/about': 'Nosotros',
        '/settings': 'Mi perfil',
        '/documents': 'Mis Documentos'
    };
    return titles[pathname] ?? 'Inicio';
}

export const DashboardLayout = () => {
    const { sidebarCollapsed, toggleSidebar, user, token, setUser } = useAppStore();
    const location = useLocation();
    const pathname = location.pathname;
    const isDashboard = pathname === '/dashboard' || pathname === '/';

    const [searchQuery, setSearchQuery] = useState('');
    const [openHeaderMenu, setOpenHeaderMenu] = useState<'settings' | 'more' | null>(null);
    const [isAssistantOpen, setIsAssistantOpen] = useState(false);
    const conversionTypes = useMemo(() => getDashboardConversions(), []);
    const filteredConversions = useMemo(
        () => filterConversionsByQuery(conversionTypes, searchQuery),
        [conversionTypes, searchQuery]
    );

    useEffect(() => {
        // If we have a token but no user data, fetch profile (incl. is_superuser, can_access_admin_panel)
        const loadUserData = async () => {
            if (token && !user) {
                try {
                    const profile = await apiService.getProfile();
                    setUser(profile);
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
            <main className={`main-content ${sidebarCollapsed ? 'expanded' : ''} ${isAssistantOpen ? 'assistant-open' : ''}`}>
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
                        <AIAssistantTrigger
                            onClick={() => setIsAssistantOpen((v) => !v)}
                            isOpen={isAssistantOpen}
                        />
                        <SettingsMenu
                            isOpen={openHeaderMenu === 'settings'}
                            onToggle={() => setOpenHeaderMenu((v) => (v === 'settings' ? null : 'settings'))}
                            onClose={() => setOpenHeaderMenu(null)}
                        />
                        <MoreMenu
                            isOpen={openHeaderMenu === 'more'}
                            onToggle={() => setOpenHeaderMenu((v) => (v === 'more' ? null : 'more'))}
                            onClose={() => setOpenHeaderMenu(null)}
                        />
                    </div>
                </header>
                <div className="main-below-header">
                    <DashboardSearchContext.Provider value={{ query: searchQuery, setQuery: setSearchQuery }}>
                        <div className="content-area">
                            <Outlet />
                        </div>
                    </DashboardSearchContext.Provider>
                    <Footer />
                </div>
            </main>
            <AIAssistantFAB isOpen={isAssistantOpen} onOpenChange={setIsAssistantOpen} />
        </div>
    );
};
