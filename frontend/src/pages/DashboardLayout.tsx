import { useEffect, useState } from 'react';
import { Outlet, Link } from 'react-router-dom';
import { Menu, UserPlus } from 'lucide-react';
import { Sidebar } from '../components/Sidebar/Sidebar';
import { SettingsMenu } from '../components/SettingsMenu/SettingsMenu';
import { MoreMenu } from '../components/MoreMenu/MoreMenu';
import { AIAssistantTrigger } from '../components/AIAssistantTrigger/AIAssistantTrigger';
import { AIAssistantFAB } from '../components/AIAssistantFAB/AIAssistantFAB';
import { MetricsModal } from '../components/MetricsModal/MetricsModal';
import { Footer } from '../components/Footer/Footer';
import { useAppStore } from '../stores/appStore';
import { apiService } from '../services/api';
import { DashboardSearchContext } from '../contexts/DashboardSearchContext';
import { AssistantProvider } from '../contexts/AssistantContext';
import './DashboardLayout.css';

export const DashboardLayout = () => {
    const { sidebarCollapsed, toggleSidebar, user, token, setUser, isMetricsModalOpen } = useAppStore();

    const [searchQuery, setSearchQuery] = useState('');
    const [openHeaderMenu, setOpenHeaderMenu] = useState<'settings' | 'more' | null>(null);
    const [isAssistantOpen, setIsAssistantOpen] = useState(() => {
        try {
            return typeof window !== 'undefined' && localStorage.getItem('docai-assistant-open') === 'true';
        } catch {
            return false;
        }
    });

    useEffect(() => {
        try {
            localStorage.setItem('docai-assistant-open', String(isAssistantOpen));
        } catch {
            /* ignore */
        }
    }, [isAssistantOpen]);

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

    const isAnonymous = !token;

    return (
        <AssistantProvider value={{ isOpen: isAssistantOpen, setOpen: setIsAssistantOpen }}>
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
                            <Link to="/dashboard" className="header-logo" aria-label="Ir al inicio - DocAI Platform">
                                <span className="header-logo__icon">✨</span>
                                <span className="header-logo__text">
                                    <span className="header-logo__brand">DocAI</span>
                                    <span className="header-logo__tagline">Platform</span>
                                </span>
                            </Link>
                        </div>
                        <div className="header-right">
                            {isAnonymous ? (
                                <Link
                                    to="/login"
                                    state={{ mode: 'register' }}
                                    className="header-register-btn"
                                    aria-label="Ir a registro"
                                >
                                    <UserPlus size={20} strokeWidth={2} />
                                    <span className="header-register-btn__label">Regístrate</span>
                                </Link>
                            ) : (
                                <AIAssistantTrigger
                                    onClick={() => setIsAssistantOpen((v) => !v)}
                                    isOpen={isAssistantOpen}
                                />
                            )}
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
                <div
                    className="main-below-header"
                    onClick={() => {
                        if (!sidebarCollapsed && window.matchMedia('(max-width: 768px)').matches) {
                            toggleSidebar();
                        }
                    }}
                >
                    {isAnonymous && (
                        <div className="assistant-bar-below-header" aria-label="Asistente IA">
                            <AIAssistantTrigger
                                onClick={() => setIsAssistantOpen((v) => !v)}
                                isOpen={isAssistantOpen}
                            />
                        </div>
                    )}
                    <DashboardSearchContext.Provider value={{ query: searchQuery, setQuery: setSearchQuery }}>
                        <div className="content-area">
                            <Outlet />
                        </div>
                    </DashboardSearchContext.Provider>
                    <Footer />
                </div>
            </main>
            <AIAssistantFAB isOpen={isAssistantOpen} onOpenChange={setIsAssistantOpen} />
            {isMetricsModalOpen && <MetricsModal />}
        </div>
        </AssistantProvider>
    );
};
