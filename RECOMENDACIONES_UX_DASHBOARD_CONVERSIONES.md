# Recomendaciones UX/UI: Dashboard con conversiones por tipo

Este documento recoge las decisiones de diseño aplicadas al panel principal y las recomendaciones estratégicas para mantener claridad, escalabilidad y buena experiencia de usuario.

---

## 1. Estructura visual del panel principal

### Jerarquía de contenido

1. **Métricas (stats)** — Siguen en la parte superior para dar contexto rápido (conversiones totales, créditos, tasa de éxito, tiempo promedio).
2. **Conversiones disponibles** — Nueva sección con cada tipo de conversión como card individual, agrupado por categoría.
3. **Otras acciones** — Formatear manuscrito e Historial, con el mismo patrón de cards que ya usaba la app.

### Principios aplicados

- **De arriba a abajo**: de lo más informativo (métricas) a lo más accionable (conversiones y acciones).
- **Agrupación por categoría**: reduce carga cognitiva y permite escanear por tipo de tarea (documentos, imágenes/CAD, web/XML).
- **Enlace "Ver todas"**: acceso directo a la página Convertir para quien prefiera el flujo completo sin elegir un card concreto.

---

## 2. Organización de los cards de conversión

### Grid por categoría

- **Documentos**: Word ↔ PDF, Word ↔ Texto, Word ↔ XML, PDF → Word/PNG/Texto, Texto → Word.
- **Imágenes y CAD**: Imagen (PNG/JPG) → PDF, Imagen → DXF, DXF → PNG.
- **Web y XML**: XML → HTML, XML → Word, HTML → XML.

Cada categoría tiene un título en mayúsculas y espaciado (uppercase + letter-spacing) para diferenciarla sin competir con los títulos de sección.

### Tamaño y densidad

- Cards **compactos en fila** (icono + “Origen → Destino” + CTA “Convertir”) para que quepan varios en pantalla sin scroll excesivo.
- Grid **responsive**: `minmax(280px, 1fr)` en desktop, 2 columnas en tablet, 1 en móvil.
- **Sin duplicados**: PNG/JPG/JPEG se unifican en un solo card “Imagen (PNG/JPG) → …” para no repetir la misma opción tres veces.

### Buenas prácticas para no sobrecargar

- **Máximo ~13 cards** repartidos en 3 bloques; cada bloque es escaneable.
- **Un solo nivel de título** dentro de la sección (nombre de categoría), sin subtítulos extra.
- **Mismo componente** para todas las conversiones (mismo tamaño, mismo patrón) para consistencia y mantenimiento.
- **Colores por categoría** (document = cian, image = azul, web = morado) solo en el icono; el resto del card es neutro para no saturar.

---

## 3. Consistencia con el sistema de diseño

- **Variables CSS**: uso de `--color-surface`, `--color-border`, `--color-primary`, `--spacing-*`, `--radius-xl`, `--transition-base`, etc.
- **Tipografía**: `--font-size-sm` / `--font-size-xs` en labels y CTA; pesos 600 para títulos y CTAs.
- **Sombras y bordes**: `--shadow-lg` en hover, `border: 1px solid var(--color-border)` y cambio a `var(--color-primary)` en hover, alineado con `QuickActionCard` y `StatsCard`.
- **Gradientes**: mismos que en el resto de la app (`gradient-primary`, `gradient-info`, `gradient-warm`/`gradient-accent`) solo en el icono del card.
- **Accesibilidad**: el card es un enlace (`<Link>`); se mantiene contraste de texto y tamaño de área clicable adecuado.

---

## 4. Escalabilidad y mantenimiento

- **Fuente única de verdad**: `constants/conversions.ts` exporta `CONVERSION_MAP` (para la página Convertir) y `getDashboardConversions()` (para el dashboard). Añadir una conversión nueva es editar solo ese archivo (y el backend si aplica).
- **Categorías**: si en el futuro se añaden muchos formatos, se puede seguir ampliando `ConversionCategory` y `CONVERSION_CATEGORY_LABELS` sin cambiar la estructura del dashboard.
- **Componente reutilizable**: `ConversionCard` recibe `sourceLabel`, `targetLabel`, `icon`, `category`, `href`; si más adelante el destino lleva query params (ej. `?from=pdf&to=docx`), basta con cambiar la construcción de `href` en el Dashboard.

---

## 5. Mejoras de usabilidad implementadas

- **Menos fricción**: el usuario ve de un vistazo “Word → PDF”, “PDF → Word”, etc., y hace un solo clic para ir a convertir (mismo flujo que antes en Convertir, pero con mejor descubribilidad).
- **Velocidad de interacción**: cada card lleva directamente a `/convert`; en el futuro se puede pre-seleccionar origen/destino por query params para reducir un paso.
- **Claridad**: etiquetas “Origen → Destino” con flecha explícita; CTA “Convertir” en cada card.
- **No invasivo**: las stats y las otras acciones (Formatear, Historial) se mantienen; solo se sustituye el card genérico “Convertir archivos” por la rejilla de conversiones.

---

## 6. Recomendaciones adicionales (futuro)

1. **Query params en la URL**: usar `/convert?from=docx&to=pdf` para que, desde el dashboard, la página Convertir abra ya con formato origen/destino sugerido (y si se implementa preselección en el dropzone, con un paso menos).
2. **Búsqueda o filtro**: si el número de conversiones crece mucho, añadir un campo de búsqueda o filtro por categoría en la sección “Conversiones disponibles”.
3. **Analíticas**: registrar clics por tipo de conversión desde el dashboard para priorizar mejoras y contenido.
4. **Tooltips**: en iconos o en el par Origen → Destino, opcionalmente un tooltip con una frase muy corta (ej. “Convierte documentos Word a PDF”).

---

## Resumen de cambios técnicos

| Área | Cambio |
|------|--------|
| **Fuente de datos** | `frontend/src/constants/conversions.ts`: `CONVERSION_MAP`, `getDashboardConversions()`, categorías y labels. |
| **Convert** | Importa `CONVERSION_MAP` desde `constants/conversions.ts`. |
| **Nuevo componente** | `ConversionCard`: card compacto Origen → Destino con icono por categoría y enlace a `/convert`. |
| **Dashboard** | Sección “Conversiones disponibles” con bloques por categoría (Documentos, Imágenes y CAD, Web y XML) y enlace “Ver todas”; “Acciones Rápidas” pasa a “Otras acciones” con Formatear e Historial. |
| **Estilos** | Uso de variables y patrones existentes; grid responsive para los nuevos cards. |

Con esto se cumple el objetivo de mostrar cada tipo de conversión de forma individual en el panel principal, manteniendo la línea gráfica y preparando el sistema para futuras conversiones y mejoras de UX.
