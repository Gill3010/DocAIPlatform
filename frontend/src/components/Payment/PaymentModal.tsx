import { useState } from 'react';
import { PayPalScriptProvider, PayPalButtons } from "@paypal/react-paypal-js";
import { X } from 'lucide-react';
import './PaymentModal.css';

interface PaymentModalProps {
    plan: { id: string; name: string; price: number; currency?: string };
    onClose: () => void;
    onSuccess: () => void;
}

export const PaymentModal = ({ plan, onClose, onSuccess }: PaymentModalProps) => {
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);

    if (success) {
        return (
            <div className="payment-modal-overlay">
                <div className="payment-modal success-modal">
                    <div className="success-icon">✅</div>
                    <h2>¡Suscripción Exitosa!</h2>
                    <p>Bienvenido al plan <strong>{plan.name}</strong>. Tu cuenta ha sido actualizada.</p>
                    <button className="btn-primary" onClick={onClose} style={{ marginTop: '20px' }}>Empezar</button>
                </div>
            </div>
        );
    }

    return (
        <div className="payment-modal-overlay">
            <div className="payment-modal">
                <button className="payment-modal-close" onClick={onClose} disabled={loading}><X /></button>
                <h2 className="payment-modal-title">Suscribirse a {plan.name}</h2>
                <div className="payment-modal-price">{plan.price} {plan.currency || 'USD'} / mes</div>

                <div className="payment-body">
                    {error && <div className="error-banner">{error}</div>}

                    {loading && <div className="loading-overlay">Procesando pago...</div>}

                    {/* PayPal Only */}
                    {!loading && (
                        <>
                            <p style={{ textAlign: 'center', marginBottom: '20px', color: '#666' }}>
                                Paga de forma segura con PayPal. Puedes usar tu saldo PayPal o <strong>tarjeta de crédito/débito</strong> sin crear cuenta.
                            </p>

                            <PayPalScriptProvider options={{
                                clientId: import.meta.env.VITE_PAYPAL_CLIENT_ID || "",
                                currency: "USD",
                                intent: "capture"
                            }}>
                                <PayPalButtons
                                    style={{ layout: "vertical" }}
                                    createOrder={async (_data, _actions) => {
                                        const token = localStorage.getItem('token');
                                        const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/payments/create-paypal-order`, {
                                            method: 'POST',
                                            headers: {
                                                'Content-Type': 'application/json',
                                                'Authorization': `Bearer ${token || ''}`,
                                            },
                                            body: JSON.stringify({
                                                amount: plan.price,
                                                currency: plan.currency || "USD",
                                                plan_id: plan.id
                                            })
                                        });
                                        if (!res.ok) throw new Error("Could not create paypal order");
                                        const order = await res.json();
                                        return order.id;
                                    }}
                                    onApprove={async (data, _actions) => {
                                        setLoading(true);
                                        const token = localStorage.getItem('token');
                                        try {
                                            const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/payments/capture-paypal-order`, {
                                                method: 'POST',
                                                headers: {
                                                    'Content-Type': 'application/json',
                                                    'Authorization': `Bearer ${token || ''}`,
                                                },
                                                body: JSON.stringify({ orderID: data.orderID })
                                            });
                                            if (!res.ok) throw new Error("Capture failed");
                                            setSuccess(true);
                                            onSuccess();
                                        } catch (e) {
                                            setError("Error al procesar el pago. Por favor contacta a soporte.");
                                        } finally {
                                            setLoading(false);
                                        }
                                    }}
                                />
                            </PayPalScriptProvider>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};
