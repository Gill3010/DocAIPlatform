# 🤖 Proyecto: DocAI Platform - Plan de Implementación y Continuidad

Este documento sirve como guía maestra para retomar el desarrollo del proyecto sin perder el ritmo ni el contexto técnico.

## 🛠 1. Contexto de Infraestructura (CRÍTICO)
*   **Servidor:** AWS Free Tier (t3.micro/t2.micro).
*   **Recursos:** 1GB RAM total. Se ha configurado un **SWAP de 1GB** para evitar caídas.
*   **Almacenamiento:** ~1.6GB disponibles en disco. Evitar instalaciones de librerías de sistema pesadas (ej. LibreOffice completo).
*   **Base de Datos:** SQLite (Async) con SQLAlchemy. Ubicación: `backend/sql_app.db`.

## 📍 2. Estado Actual del Proyecto (Checklist)

### ✅ Fase 1: Configuración (100%)
- [x] Optimización de RAM y Swap.
- [x] Estructura de monorepo (Backend/Frontend).
- [x] Git sincronizado con GitHub.

### ✅ Fase 2: Backend (100%)
- [x] Auth JWT (Login/Registro).
- [x] Modelos de Usuario y Esquemas Pydantic.
- [x] Conexión asíncrona a DB.

### ✅ Fase 3: Frontend & UI (75%)
- [x] Sistema de Temas (Dark/Light).
- [x] Sidebar y Navegación Responsive (Mobile/Desktop).
- [x] Dashboard con métricas e iconos Lucide.
- [x] **Componente de Conversión (UI):** Interfaz terminada con simulación de progreso.

### ✅ Fase 4: Motor de Conversión Backend (100%)
- [x] Modelo de Conversion en DB.
- [x] Schemas Pydantic para conversión.
- [x] Router `/api/v1/convert` con endpoints completos.
- [x] Funciones de conversión ligeras (PNG→PDF, PDF→TXT, DOCX↔TXT).
- [x] Sistema de créditos funcionando (10 conversiones gratis).
- [x] Frontend conectado con backend real.

### ✅ Fase 5: Funcionalidades SaaS Avanzadas (100%)
- [x] Página de Historial con filtros y estadísticas.
- [x] Descarga de archivos convertidos desde historial.
- [x] AI Assistant Chat con interfaz profesional.
- [x] Router de AI con integración OpenAI GPT-4.
- [x] Endpoint de estadísticas reales del usuario.
- [x] Dashboard actualizado con métricas de la BD.

---

## 🚀 3. Tareas Pendientes (Roadmap)

### ~~Prioridad Alta: Motor de Conversión Real~~ ✅ COMPLETADO
1.  ~~**Endpoint de Subida:** Crear `/api/v1/convert/upload` en FastAPI.~~
2.  **Integración S3:** Configurar AWS S3 para almacenamiento externo (opcional para más adelante).
3.  ~~**Primer Converter:** Implementar lógica para PDF -> Word o PNG -> PDF.~~

### ~~Prioridad Media: Funcionalidades SaaS~~ ✅ COMPLETADO
4.  ~~**Historial:** Implementar página `/history` consumiendo datos de la DB.~~
5.  ~~**AI Assistant Chat:** UI de chat interactiva conectada a OpenAI.~~
6.  ~~**Sistema de Créditos:** Restar créditos reales al completar una conversión.~~

### Prioridad Baja: Configuración y Pagos
7.  **Ajustes de Perfil:** Cambio de contraseña y datos personales.
8.  **Pasarela de Pagos:** Integración con Stripe/PayPal para suscripciones Premium.

---

## 💻 4. Comandos para Re-arrancar

### Levantar Backend
```bash
cd backend
source venv/bin/activate
export PYTHONPATH=$PYTHONPATH:$(pwd)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Levantar Frontend
```bash
cd frontend
npm run dev -- --host
```

---

## 📌 5. Notas Técnicas para el Siguiente Desarrollador
- El Frontend usa **Zustand** para el estado (ubicado en `src/stores/appStore.ts`).
- Los iconos son de la librería **lucide-react**.
- El Backend usa `asyncpg` preparado para PostgreSQL, pero actualmente corre en `aiosqlite`.
- **IMPORTANTE:** Si el servidor se cae, revisar `df -h` (espacio en disco) y `free -h` (RAM).
