# Prompt: Integración de sistema de pagos

---

## Rol y contexto

Eres un arquitecto de software senior especializado en sistemas escalables, integraciones de pago y diseño modular. Debes **diseñar e implementar** la integración de pagos en una aplicación existente sin modificar la lógica actual de límites freemium ni el flujo de registro/upgrade.

---

## Contexto del sistema actual (NO MODIFICAR)

### Stack
- **Backend:** FastAPI, SQLAlchemy (async), SQLite (configurable vía `DATABASE_URL`). Estructura: `app/routers/`, `app/services/`, `app/models/`, `app/core/` (config, exceptions, security).
- **Frontend:** React, React Router, API base en `src/services/api`, ruta `/pricing` ya existe.
- **API:** Prefijo `/api/v1`. Routers: auth, convert, pdf-tools, users, ai, admin, documents.

### Flujo freemium (intocable)
1. Usuario **anónimo** tiene **3 usos gratuitos** (conversiones, consultas al asistente IA o uso de herramientas PDF; mismo pool).
2. Al alcanzar el límite anónimo, el sistema obliga a **registrarse** (modal/redirección).
3. Tras **registro**, el usuario obtiene **2 usos adicionales** (total **5** para usuario registrado).
4. Los créditos se rastrean en: `User.free_conversion_count` (y `ai_message_count` donde aplique) y en `AnonymousSession.conversions_count`. Límites en `app/core/config.py`: `FREE_TIER_CONVERSIONS_LIMIT = 5`, `ANONYMOUS_CONVERSIONS_LIMIT = 3`, `FREE_TIER_AI_CREDITS = 5`, `ANONYMOUS_AI_LIMIT = 3`.
5. Al consumir los **5 usos**, el backend responde con excepciones `AuthLimitReached` / `AICreditsExhausted` (403, `detail`: `auth_limit_reached` o mensaje de créditos agotados). El frontend muestra `UpgradeModal` y redirige a **/pricing**.
6. La página **Pricing** (`frontend/src/pages/Pricing/Pricing.tsx`) muestra planes (Gratuito, Básico, Pro, Empresa) con precios estáticos; los botones de compra están **disabled** con texto "Próximamente" / "Elegir Pro".

### Restricción crítica
- **No** cambiar la lógica de conteo de créditos, límites, registro ni el comportamiento de `AuthLimitReached` / `AnonymousLimitReached` / `AICreditsExhausted`.
- **No** reestructurar el flujo actual: anónimo → registro → 5 créditos → redirección a pricing. La integración de pagos debe **completar** el flujo desde la página de precios, no sustituirlo.

---

## Objetivo

Integrar un **sistema de pagos** que permita a los usuarios que han agotado sus 5 usos gratuitos (y son redirigidos a /pricing) **elegir un plan de pago y pagar**, con los siguientes métodos:

1. **PayPal** (cuenta activa ya disponible).
2. **Pagos con tarjeta:** Visa, Mastercard, American Express (implementar vía proveedor que soporte estos medios; por ejemplo Stripe o el que consideres adecuado manteniendo PCI compliance).

El resultado del pago debe vincularse al usuario (y opcionalmente a un “plan” o suscripción) para que el sistema pueda **elevar o eliminar** el límite de créditos para ese usuario (por ejemplo, tratando a usuarios con plan de pago activo como “premium” con créditos ilimitados o según reglas de negocio que definas de forma coherente con los planes mostrados en la UI).

---

## Requisitos técnicos obligatorios

- **Arquitectura modular:** La lógica de pagos debe vivir en módulos/servicios desacoplados del core (conversiones, auth, créditos). El core solo debe “consultar” si el usuario tiene acceso premium (por ejemplo, flag o servicio de suscripciones), sin depender de implementación concreta de PayPal o tarjeta.
- **No romper funcionalidades actuales:** Tests existentes, flujo anónimo → registro → 5 créditos y redirección a /pricing deben seguir funcionando. No modificar la semántica de `free_conversion_count`, `AnonymousSession`, ni los endpoints que ya comprueban límites.
- **Escalabilidad:** Diseño que permita añadir más métodos de pago o más planes sin reescribir el core.
- **Rendimiento:** No introducir latencia innecesaria en rutas críticas (conversión, IA, PDF). Las comprobaciones de “usuario premium” deben ser rápidas (p. ej. caché o campo derivado si es aceptable).
- **Seguridad:** Cumplimiento PCI donde aplique (no almacenar datos de tarjeta completos; usar tokens, SDKs oficiales, webhooks). Secrets en variables de entorno (`.env`), no en código.
- **Estados de pago:** Gestionar de forma explícita al menos: pendiente, aprobado/completado, fallido, reembolsado (y si aplica: cancelado, disputado). Persistir estado por transacción/suscripción.
- **Manejo de errores y reintentos:** Errores de red o del proveedor de pago deben manejarse con reintentos configurables donde sea idempotente; respuestas HTTP y mensajes al usuario claros; logging para diagnóstico.

---

## Criterios de éxito

1. Usuario que llega a /pricing puede elegir un plan de pago (por ejemplo Pro) y completar el pago con **PayPal** o con **tarjeta** (Visa, Mastercard, Amex).
2. Tras pago aprobado, el usuario obtiene acceso premium (créditos ilimitados o según el plan) sin cambiar el flujo existente de los 5 créditos gratuitos para quienes no pagan.
3. Backend expone una forma estable de saber si un usuario tiene plan activo (endpoint o campo en perfil/sesión) y la lógica de límites (en `conversion_service`, `ai_service`, `pdf_tools`) considera este estado además de `is_superuser` y `free_conversion_count`.
4. Los estados de pago (pendiente, aprobado, fallido, reembolsado) están almacenados y, si aplica, visibles en panel de admin o en historial de usuario.
5. Webhooks (o mecanismo equivalente) del proveedor de pago están implementados y actualizan el estado en la base de datos.
6. No se han modificado la lógica ni los contratos existentes de créditos freemium (anónimo 3, registrado 5, redirección a pricing); solo se ha añadido la capa de pagos y la noción de “usuario premium”.

---

## Formato de respuesta esperado

1. **Diseño (resumen):**
   - Diagrama o descripción de componentes: frontend (pricing/checkout), backend (routers, servicios, modelos), proveedores (PayPal, tarjeta).
   - Dónde se integra la comprobación “usuario premium” en el flujo actual (qué servicios/endpoints tocan y de qué forma).
   - Modelo de datos nuevo (tablas/entidades para suscripciones, transacciones, estados).

2. **Implementación:**
   - Listado de archivos nuevos y archivos modificados (con rutas relativas al repo: `backend/`, `frontend/`).
   - Cambios en `main.py` (incluir router de pagos si aplica), config (nuevas variables), y en los puntos donde se comprueba el límite de créditos para considerar “premium”.
   - Código completo de los módulos nuevos y los cambios mínimos necesarios en los existentes (sin reescribir lógica freemium ya existente).
   - Configuración de webhooks (ruta, verificación de firma, idempotencia).
   - Variables de entorno a documentar (por ejemplo `PAYPAL_*`, `STRIPE_*` o las que uses).

3. **Seguridad y PCI:**
   - Confirmación de que no se almacenan datos sensibles de tarjeta; uso de tokens/checkout hosted o SDK oficial; manejo de secretos.

4. **Manejo de errores y reintentos:**
   - Estrategia aplicada (reintentos, timeouts, respuestas al usuario) y dónde se implementa.

5. **Testing:**
   - Cómo comprobar el flujo sin afectar tests actuales; sugerencia de tests para creación de intención de pago, webhook de éxito/fallo y comprobación de acceso premium.

6. **Pasos de despliegue:**
   - Orden de migraciones, variables de entorno, configuración de webhooks en los dashboards de PayPal y del proveedor de tarjeta.

---

## Restricciones adicionales

- No eliminar ni refactorizar el flujo de `ConversionLimitModal`, `UpgradeModal`, ni la redirección a `/pricing`.
- No cambiar la semántica de los códigos 403 ni los `detail` existentes (`auth_limit_reached`, `anonymous_limit_reached`) para usuarios no premium; solo añadir la vía de “premium” para evitar el límite.
- Mantener compatibilidad con la base de datos existente: usar migraciones (por ejemplo Alembic) para nuevas tablas; no eliminar columnas usadas por el freemium actual.
- El frontend debe seguir accesible en español (textos de pricing, checkout, mensajes de error de pago).

---

Entregar el diseño y la implementación siguiendo el formato anterior, de forma que un desarrollador pueda aplicar los cambios en el repositorio sin ambigüedades.
