import { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../../services/api';
import { useAppStore } from '../../stores/appStore';
import './Login.css';

export const Login = () => {
    const navigate = useNavigate();
    const { setToken, setUser } = useAppStore();
    const [isLogin, setIsLogin] = useState(true);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [fullName, setFullName] = useState('');

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            if (isLogin) {
                const response = await apiService.login({ username: email, password });
                setToken(response.access_token);
                localStorage.setItem('token', response.access_token);
                navigate('/dashboard');
            } else {
                const user = await apiService.register({ email, password, full_name: fullName });
                setUser(user);
                // Auto-login after registration
                const response = await apiService.login({ username: email, password });
                setToken(response.access_token);
                localStorage.setItem('token', response.access_token);
                navigate('/dashboard');
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-container">
            <div className="login-card">
                <div className="login-header">
                    <h1 className="login-logo">
                        <span className="logo-icon">✨</span>
                        DocAI Platform
                    </h1>
                    <p className="login-subtitle">
                        {isLogin ? 'Welcome back!' : 'Create your account'}
                    </p>
                </div>

                {error && <div className="error-message">{error}</div>}

                <form onSubmit={handleSubmit} className="login-form">
                    <div className="form-group">
                        <label htmlFor="email">Email</label>
                        <input
                            id="email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="your@email.com"
                            required
                        />
                    </div>

                    {!isLogin && (
                        <div className="form-group">
                            <label htmlFor="fullName">Full Name</label>
                            <input
                                id="fullName"
                                type="text"
                                value={fullName}
                                onChange={(e) => setFullName(e.target.value)}
                                placeholder="John Doe"
                            />
                        </div>
                    )}

                    <div className="form-group">
                        <label htmlFor="password">Password</label>
                        <input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="••••••••"
                            required
                        />
                    </div>

                    <button type="submit" className="btn-primary" disabled={loading}>
                        {loading ? 'Please wait...' : isLogin ? 'Sign In' : 'Sign Up'}
                    </button>
                </form>

                <div className="login-footer">
                    <p>
                        {isLogin ? "Don't have an account? " : 'Already have an account? '}
                        <button
                            type="button"
                            className="link-button"
                            onClick={() => setIsLogin(!isLogin)}
                        >
                            {isLogin ? 'Sign Up' : 'Sign In'}
                        </button>
                    </p>
                </div>
            </div>
        </div>
    );
};
