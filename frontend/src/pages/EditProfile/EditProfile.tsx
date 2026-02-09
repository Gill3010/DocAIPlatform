import { useState, useEffect, useRef } from 'react';
import type { FormEvent } from 'react';
import { Camera, Eye, EyeOff, Loader2 } from 'lucide-react';
import { apiService, getAvatarUrl } from '../../services/api';
import { useAppStore } from '../../stores/appStore';
import type { User } from '../../types';
import './EditProfile.css';

export const EditProfile = () => {
    const { setUser } = useAppStore();
    const [profile, setProfile] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [avatarUploading, setAvatarUploading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const [fullName, setFullName] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showNewPassword, setShowNewPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);

    const fileInputRef = useRef<HTMLInputElement>(null);

    const isEmailAuth = profile?.auth_provider === 'email' || !profile?.auth_provider;

    useEffect(() => {
        let cancelled = false;
        const load = async () => {
            try {
                setLoading(true);
                setError('');
                const data = await apiService.getProfile();
                if (!cancelled) {
                    setProfile(data);
                    setFullName(data.full_name ?? '');
                }
            } catch (err: unknown) {
                if (!cancelled) {
                    setError(err instanceof Error ? err.message : 'Error al cargar el perfil');
                }
            } finally {
                if (!cancelled) setLoading(false);
            }
        };
        load();
        return () => { cancelled = true; };
    }, []);

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        if (newPassword && newPassword !== confirmPassword) {
            setError('Las contraseñas no coinciden');
            return;
        }
        if (newPassword && newPassword.length < 8) {
            setError('La contraseña debe tener al menos 8 caracteres');
            return;
        }
        try {
            setSaving(true);
            const payload: { full_name?: string; password?: string } = { full_name: fullName.trim() || undefined };
            if (newPassword.trim()) payload.password = newPassword.trim();
            const updated = await apiService.updateProfile(payload);
            setProfile(updated);
            setUser(updated);
            setNewPassword('');
            setConfirmPassword('');
            setSuccess('Perfil actualizado correctamente');
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Error al guardar');
        } finally {
            setSaving(false);
        }
    };

    const handleAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        if (!file.type.startsWith('image/')) {
            setError('Selecciona una imagen (JPEG, PNG, GIF o WebP)');
            return;
        }
        if (file.size > 5 * 1024 * 1024) {
            setError('La imagen no debe superar 5 MB');
            return;
        }
        setError('');
        setSuccess('');
        try {
            setAvatarUploading(true);
            const updated = await apiService.uploadAvatar(file);
            setProfile(updated);
            setUser(updated);
            setSuccess('Foto de perfil actualizada');
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Error al subir la foto');
        } finally {
            setAvatarUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const avatarUrl = getAvatarUrl(profile?.avatar_url);
    const displayName = profile?.full_name?.trim() || profile?.email || 'Usuario';
    const initial = displayName.charAt(0).toUpperCase();

    if (loading) {
        return (
            <div className="edit-profile edit-profile--loading">
                <Loader2 size={32} className="edit-profile__spinner" aria-hidden />
                <p>Cargando perfil…</p>
            </div>
        );
    }

    if (!profile) {
        return (
            <div className="edit-profile edit-profile--error">
                <p>{error || 'No se pudo cargar el perfil.'}</p>
            </div>
        );
    }

    return (
        <div className="edit-profile">
            <h2 className="edit-profile__title">Mi perfil</h2>
            <p className="edit-profile__subtitle">Actualiza tu nombre, foto y contraseña</p>

            <form className="edit-profile__form" onSubmit={handleSubmit}>
                {/* Avatar */}
                <div className="edit-profile__section">
                    <label className="edit-profile__label">Foto de perfil</label>
                    <div className="edit-profile__avatar-wrap">
                        <div className="edit-profile__avatar">
                            {avatarUrl ? (
                                <img
                                    key={profile?.avatar_url ?? 'avatar'}
                                    src={avatarUrl}
                                    alt=""
                                    className="edit-profile__avatar-img"
                                />
                            ) : (
                                <span className="edit-profile__avatar-initial">{initial}</span>
                            )}
                            {avatarUploading && (
                                <div className="edit-profile__avatar-overlay">
                                    <Loader2 size={28} className="edit-profile__avatar-spinner" />
                                </div>
                            )}
                        </div>
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept="image/jpeg,image/png,image/gif,image/webp"
                            className="edit-profile__file-input"
                            aria-label="Subir foto de perfil"
                            onChange={handleAvatarChange}
                            disabled={avatarUploading}
                        />
                        <button
                            type="button"
                            className="edit-profile__avatar-btn"
                            onClick={() => fileInputRef.current?.click()}
                            disabled={avatarUploading}
                            title="Cambiar foto"
                        >
                            <Camera size={18} />
                            <span>Cambiar foto</span>
                        </button>
                    </div>
                </div>

                {/* Nombre */}
                <div className="edit-profile__section">
                    <label htmlFor="edit-profile-name" className="edit-profile__label">Nombre</label>
                    <input
                        id="edit-profile-name"
                        type="text"
                        className="edit-profile__input"
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        placeholder="Tu nombre"
                        autoComplete="name"
                    />
                </div>

                {/* Email (solo lectura) */}
                <div className="edit-profile__section">
                    <label htmlFor="edit-profile-email" className="edit-profile__label">Correo electrónico</label>
                    <input
                        id="edit-profile-email"
                        type="email"
                        className="edit-profile__input edit-profile__input--readonly"
                        value={profile.email}
                        readOnly
                        disabled
                        aria-describedby="edit-profile-email-hint"
                    />
                    <p id="edit-profile-email-hint" className="edit-profile__hint">
                        El correo no se puede cambiar desde aquí.
                    </p>
                </div>

                {/* Contraseña (solo si login por email) */}
                {isEmailAuth && (
                    <div className="edit-profile__section edit-profile__section--password">
                        <span className="edit-profile__label">Cambiar contraseña</span>
                        <p className="edit-profile__hint">Deja en blanco si no quieres cambiarla.</p>
                        <div className="edit-profile__password-row">
                            <input
                                type={showNewPassword ? 'text' : 'password'}
                                className="edit-profile__input"
                                placeholder="Nueva contraseña"
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)}
                                autoComplete="new-password"
                                minLength={8}
                            />
                            <button
                                type="button"
                                className="edit-profile__password-toggle"
                                onClick={() => setShowNewPassword(!showNewPassword)}
                                aria-label={showNewPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                            >
                                {showNewPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                            </button>
                        </div>
                        <div className="edit-profile__password-row">
                            <input
                                type={showConfirmPassword ? 'text' : 'password'}
                                className="edit-profile__input"
                                placeholder="Confirmar nueva contraseña"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                autoComplete="new-password"
                            />
                            <button
                                type="button"
                                className="edit-profile__password-toggle"
                                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                aria-label={showConfirmPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                            >
                                {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                            </button>
                        </div>
                    </div>
                )}

                {!isEmailAuth && (
                    <p className="edit-profile__hint edit-profile__hint--social">
                        Iniciaste sesión con una red social. La contraseña se gestiona en tu cuenta de ese proveedor.
                    </p>
                )}

                {error && <p className="edit-profile__message edit-profile__message--error" role="alert">{error}</p>}
                {success && <p className="edit-profile__message edit-profile__message--success" role="status">{success}</p>}

                <button
                    type="submit"
                    className="edit-profile__submit"
                    disabled={saving}
                >
                    {saving ? (
                        <>
                            <Loader2 size={18} className="edit-profile__submit-spinner" />
                            Guardando…
                        </>
                    ) : (
                        'Guardar cambios'
                    )}
                </button>
            </form>
        </div>
    );
};
