import { Moon, Sun } from 'lucide-react';
import { useAppStore } from '../../stores/appStore';
import './ThemeToggle.css';

export const ThemeToggle = () => {
    const { theme, toggleTheme } = useAppStore();

    return (
        <button
            className="theme-toggle"
            onClick={toggleTheme}
            aria-label="Toggle theme"
            title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
        >
            {theme === 'light' ? (
                <Moon size={20} strokeWidth={2} />
            ) : (
                <Sun size={20} strokeWidth={2} />
            )}
        </button>
    );
};
