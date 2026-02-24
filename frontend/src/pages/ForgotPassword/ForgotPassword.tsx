import { ThemeToggle } from '../../components/ThemeToggle/ThemeToggle';
import { ForgotPasswordForm } from '../../components/ForgotPasswordForm/ForgotPasswordForm';
import './ForgotPassword.css';

export const ForgotPassword = () => {
    return (
        <div className="forgot-password-page">
            <div className="theme-toggle-wrapper">
                <ThemeToggle />
            </div>
            <div className="forgot-password-card">
                <ForgotPasswordForm idPrefix="forgot-page" />
            </div>
        </div>
    );
};
