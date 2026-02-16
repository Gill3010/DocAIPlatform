Prompt de Continuidad: Integración de Suscripciones DocAI
Contexto del Proyecto: Estamos desarrollando un SaaS de procesamiento de documentos (DocAI). El sistema de pagos (PayPal) ya está integrado, pero estamos refinando la lógica de planes y límites para los tres niveles: Gratuito, Básico ($9), Pro ($24) y Empresa ($79).

Estado Actual (Implementado):

Modelo de Datos: Tabla 
users
 actualizada con is_premium, premium_plan_id, monthly_conversion_count, last_billing_reset y subscription_end_date.
Lógica del Plan Básico: Se ha implementado el límite de 50 conversiones mensuales (Backend y Frontend).
Reinicio Automático: Existe lógica en el backend para resetear el contador mensual cada 30 días basándose en last_billing_reset.
Asistente IA: Acceso ilimitado habilitado para todos los usuarios Premium (incluyendo Básico).
Frontend Sync: El Sidebar y el Dashboard ya muestran dinámicamente "X de 50" para el plan Básico y "∞" para los superiores.
OBJETIVO: Implementar las reglas de negocio faltantes.

Tareas Implementadas:

✅ Restricción de Formatos (Paywall de Formatos):
- Filtro en `conversion_service.py` y `convert.py` que bloquea formatos premium (XML/JATS, DWG/DXF) para usuarios gratuitos.
- Frontend muestra `UpgradeModal` con mensaje específico.

✅ Lógica de Expiración/Downgrade:
- Verificación automática en cada conversión. Si `subscription_end_date` ha pasado, el usuario vuelve a ser gratuito.

✅ Activación de Funciones Pro (Formateo de Manuscritos):
- Nueva ruta `/api/v1/manuscript/format` que valida el plan Pro/Empresa.
- Frontend habilitado con check de plan y modal de upgrade.

✅ Filtro de Historial por Plan:
- Ajuste en SQL: 30 días para Básico/Gratis, 1 año para Pro/Empresa.

✅ Plan Empresa (Multi-usuario):
- Modelo `Organization` creado y vinculado a `User`.
- Migración de base de datos ejecutada (`migrate_enterprise.py`).
Instrucciones para la IA:

Revisa 
backend/app/services/conversion_service.py
 para entender cómo se están contando los créditos actuales.
Asegúrate de que cualquier cambio en el Backend se refleje en los tipos de TypeScript en 
frontend/src/types/index.ts
.
Prioriza la Restricción de Formatos y la Lógica de Expiración, ya que son los huecos actuales en el modelo de negocio.