# Recomendaciones de diseño y arquitectura – Rediseño Dashboard DocAI Platform

Este documento recoge recomendaciones de diseño, UX/UI y arquitectura para los cambios estructurales descritos: **reubicar el resumen de métricas en el menú de usuario**, **crear el ítem "Métricas"** y **ocupar el espacio actual con un cintillo/carrusel de valor**. La lógica funcional existente se mantiene intacta.

---

## 1. Reubicación del resumen en el menú de usuario

### 1.1 Patrón recomendado: "Métricas" como entrada → modal/drawer

En lugar de renderizar todo el `MetricsSummary` dentro del dropdown del menú (que quedaría saturado y difícil de usar en móvil), se recomienda:

| Enfoque | Descripción | Pros | Contras |
|---------|-------------|------|---------|
| **A. Ítem → Modal/Drawer** | "Métricas" abre un modal/drawer con el resumen completo | Mejor UX, espacio amplio, sin sobrecargar el menú | Un clic adicional |
| **B. Ítem → Página dedicada** | Navegar a `/dashboard/metrics` con el resumen | Escalable, URL compartible | Abandona el contexto actual |
| **C. Ítem → Submenú expandible** | Desplegar métricas en línea dentro del menú | Todo en un solo lugar | Menú demasiado alto, mala experiencia en móvil |

**Recomendación principal: Enfoque A (Modal/Drawer)**. Es el más equilibrado entre proximidad (menú de usuario) y espacio útil.

### 1.2 Orden de opciones en el menú

```
┌─────────────────────────────┐
│  👤 Editar Perfil           │
│  📊 Métricas                │  ← Nuevo (antes de Cerrar sesión)
│  ─────────────────────────  │
│  🚪 Cerrar Sesión           │
└─────────────────────────────┘
```

- **Métricas** antes de **Cerrar Sesión** para agrupar acciones de cuenta y dejar la salida al final.
- Usar icono `BarChart3` o `Activity` para mantener consistencia con el diseño actual.

### 1.3 Usuario anónimo

- El menú de usuario solo aparece con `user` definido.
- Usuarios anónimos no tienen ese menú; las métricas anónimas siguen mostrándose donde las tengas actualmente (por ejemplo, en un banner o mini-resumen temporal).
- Si quieres que anónimos vean métricas de sesión, puedes añadir un enlace "Ver tu resumen" en otro lugar (header o cintillo) que abra el mismo componente en modal.

---

## 2. Mejores prácticas UX/UI al mover el componente

### 2.1 No ocultar la información crítica

- El menú se cierra al hacer clic fuera. Si las métricas están solo ahí, el usuario podría no descubrirlas.
- **Sugerencia:** Añadir un micro-hint en el área de usuario del sidebar (ej. badge numérico "créditos" o indicador sutil) que invite a abrir "Métricas".
- Ya tienes créditos en `user-details` del sidebar; mantener esa info visible refuerza el valor del ítem "Métricas" como "ver todo".

### 2.2 Accesibilidad

- El ítem "Métricas" debe ser focusable y activable con teclado.
- El modal/drawer debe:
  - Cerrarse con `Escape`.
  - Tener `focus trap` para que el tab no salga del modal.
  - Restaurar el focus al botón que abrió al cerrar (`aria-describedby`, `role="dialog"`).
- Si usas drawer desde la derecha, en móvil puede ser más natural que un modal centrado.

### 2.3 Transiciones

- El menú usa `slideUpFade`. El modal/drawer puede usar una transición similar (`opacity` + `transform`) de 200–300 ms para mantener coherencia visual.

### 2.4 Mobile-first

- En móvil el sidebar se oculta o se superpone. El menú de usuario está en el pie del sidebar.
- **Opción:** Añadir también un acceso a "Métricas" desde el header (icono o enlace) para usuarios que no abren el sidebar en móvil.

---

## 3. Uso del espacio actual para el cintillo

### 3.1 Contenedor heredado

El bloque actual es:

```css
.dashboard-metrics {
  background: var(--color-bg-secondary);
  border-radius: var(--radius-xl);
  padding: var(--spacing-xl);
  border: 1px solid var(--color-border-light);
}
```

Puedes reutilizar esta caja (o una variante) como contenedor del cintillo sin cambiar la estructura general del layout. Por ejemplo:

- Renombrar semánticamente a `dashboard-value-banner` o `dashboard-hero`.
- Mantener las mismas variables de espaciado y bordes para consistencia.

### 3.2 Altura y proporciones

- Relación de aspecto sugerida para slides: **16:9** o **21:9** (formato hero).
- Altura fija recomendada: ~200–280 px en desktop; en móvil, ~160–200 px.
- Evitar banners excesivamente altos que empujen las conversiones fuera del viewport inicial.

### 3.3 Imágenes en el escritorio

Dado que ya tienes las imágenes localmente:

- Crear carpeta `frontend/public/banner/` o `frontend/src/assets/banner/`.
- Nombres descriptivos: `valor-1-conversiones.png`, `valor-2-colaboracion.png`, etc.
- Formato: WebP (con fallback PNG) para buen rendimiento.
- Resolución sugerida: 1200×400 px o 1600×450 px para evitar escalado pesado.

---

## 4. Carrusel vs alternativas

### 4.1 Carrusel clásico

**Pros:**
- Reutiliza el mismo espacio para varios mensajes.
- Sensación de "producto vivo".

**Contras:**
- Autoplay molesta si es muy agresivo.
- Parte del contenido queda oculto.
- Accesibilidad delicada (movimiento, pausa, controles).
- Más complejidad (estado, animaciones, librerías).

### 4.2 Alternativas recomendadas

| Alternativa | Descripción | Cuándo recomendarla |
|-------------|-------------|----------------------|
| **Grid de 4 cards** | 4 imágenes/cards en una fila (2×2 en tablet, 1 columna en móvil) | Mejor equilibrio: todo visible, sin animación, más sencillo |
| **Banner estático único** | Una imagen que rota o se cambia por A/B testing | Menos distracción, enfoque claro |
| **Hero con mosaico** | Imagen principal + 3 mini-thumbnails que actúan como "secciones" | Estético, menos carrusel |
| **Carrusel ligero (CSS)** | Carrusel con solo CSS (`scroll-snap`) y opción de pausa | Buen compromiso si insistes en carrusel |

### 4.3 Recomendación principal: grid de 4 cards

**Motivos:**
1. Las 4 imágenes se ven de un vistazo; no hay espera ni autoplay.
2. Escalable: puedes añadir o quitar cards sin cambiar el patrón.
3. Mejor accesibilidad: sin movimiento automático.
4. Menor complejidad: sin librerías adicionales, menos estado.
5. En móvil, apiladas en columna mantienen la jerarquía.

Estructura visual sugerida:

```
┌──────────────────┬──────────────────┬──────────────────┬──────────────────┐
│  Imagen 1        │  Imagen 2        │  Imagen 3        │  Imagen 4        │
│  + overlay       │  + overlay       │  + overlay       │  + overlay       │
│  "Convierte      │  "PDF, Word,     │  "Colabora en    │  "Métricas       │
│   en segundos"   │   Excel..."      │   tiempo real"   │   de uso"        │
└──────────────────┴──────────────────┴──────────────────┴──────────────────┘
```

### 4.4 Si usas carrusel

Si prefieres carrusel:

- No usar autoplay por defecto, o que sea >= 5 s con opción de pausa visible.
- Indicadores (dots) y flechas con etiquetas accesibles.
- `prefers-reduced-motion` para desactivar animaciones.
- Implementación ligera: `scroll-snap` en CSS o un componente mínimo en React; evitar Swiper u otras librerías pesadas si no las necesitas.

---

## 5. Detalles de implementación del cintillo

### 5.1 Overlay y legibilidad

- Overlay semitransparente (`rgba(0,0,0,0.4)` o similar) sobre las imágenes para que el texto blanco sea legible.
- Contraste mínimo: WCAG AA (4.5:1 para texto normal).
- Evitar texto sobre zonas muy claras o con mucho detalle.

### 5.2 Mensajes por slide/card

Sugerencia de mensajes orientados al valor (adaptables a tu copy):

1. **Conversiones** – "Convierte documentos en segundos".
2. **Formatos** – "PDF, Word, Excel, imágenes y más".
3. **Colaboración** – "Edita y colabora en tiempo real".
4. **Transparencia** – "Métricas y control de tu uso".

### 5.3 Componente reutilizable

```
components/
  ValueBanner/
    ValueBanner.tsx      # Grid de 4 cards o carrusel
    ValueBanner.css
    ValueBannerCard.tsx   # Card individual con overlay + texto
```

Props sugeridas:

```ts
interface ValueBannerProps {
  variant: 'grid' | 'carousel';  // para alternar en el futuro
  items: Array<{
    image: string;
    title: string;
    description?: string;
    overlayOpacity?: number;
  }>;
}
```

---

## 6. Arquitectura propuesta (sin tocar lógica)

### 6.1 Flujo actual preservado

```
Dashboard.tsx
  ├── loadStats() [sin cambios]
  ├── stats, chartData [sin cambios]
  └── <MetricsSummary stats={...} chartData={...} /> [mover de ubicación, no de lógica]
```

### 6.2 Nueva estructura

```
Dashboard.tsx
  ├── loadStats() [igual]
  ├── stats, chartData [igual]
  ├── <ValueBanner />  [reemplaza el <section className="dashboard-metrics"> en ese espacio]
  └── (MetricsSummary se usa solo dentro de MetricsModal)

Sidebar.tsx
  └── user-menu
        ├── Editar Perfil
        ├── Métricas → abre <MetricsModal />
        └── Cerrar Sesión

components/
  MetricsModal/
    MetricsModal.tsx   # Modal/Drawer que recibe stats + chartData
    MetricsModal.css
```

### 6.3 Datos para el modal

- `Dashboard` ya tiene `stats` y `chartData`.
- Opciones:
  - **A)** Pasar `stats` y `chartData` por contexto (ej. `MetricsContext`) para que `MetricsModal` los consuma.
  - **B)** Renderizar `MetricsModal` en `DashboardLayout` y pasar props vía estado global (Zustand) o contexto.
  - **C)** Que `MetricsModal` llame a `apiService.getUserStats()` / `getAnonymousStats()` al abrir (refresca datos, un poco de latencia).

**Recomendación:** Opción A o B para reutilizar datos ya cargados; C solo si necesitas siempre datos al momento de abrir.

---

## 7. Resumen de prioridades

| Prioridad | Acción | Impacto |
|-----------|--------|---------|
| 1 | Añadir ítem "Métricas" al menú de usuario | Alto |
| 2 | Crear `MetricsModal` con `MetricsSummary` | Alto |
| 3 | Sustituir el bloque de métricas por `ValueBanner` (grid o carrusel) | Alto |
| 4 | Subir imágenes a `public/banner/` y configurar `ValueBanner` | Medio |
| 5 | (Opcional) Acceso a Métricas desde header en móvil | Medio |

---

## 8. Checklist de implementación

- [x] Crear `MetricsModal` que reciba `stats` y `chartData` (vía hook `useDashboardMetrics`)
- [x] Añadir ítem "Métricas" en `Sidebar` con icono `BarChart3`
- [x] Pasar datos al modal (hook interno en `MetricsModal`)
- [x] Crear `ValueBanner` como cintillo carrusel con 4 slides
- [ ] Copiar imágenes a `frontend/public/banner/` (valor-1.jpg a valor-4.jpg)
- [x] Definir títulos y descripciones por slide
- [x] Mantener lógica de stats en `useDashboardMetrics` (extraída y reutilizada)
- [ ] Probar en móvil (menú + modal)
- [x] Respetar `prefers-reduced-motion` (autoplay desactivado)

---

*Implementación completada. Las imágenes deben copiarse a `frontend/public/banner/`.*
