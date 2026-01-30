# Recomendaciones UX/UI: Header con buscador como acción principal

Recomendaciones y decisiones de diseño aplicadas al rediseño del header del dashboard: eliminación del saludo de bienvenida y colocación del buscador como elemento principal de acción.

---

## 1. Estructura del header superior

### Decisión aplicada: **Header condicional por ruta**

- **En la ruta del dashboard** (`/` o `/dashboard`): el header muestra **solo el buscador** en la zona donde antes estaba el saludo. El título "Bienvenido, {nombre}!" se elimina.
- **En el resto de rutas** (Convertir, Historial, Formatear manuscrito, etc.): el header muestra un **título de página** derivado de la ruta (ej. "Convertir", "Historial"), sin saludo.

### Jerarquía visual del header

| Elemento        | Posición   | Comportamiento en dashboard |
|----------------|------------|-----------------------------|
| Menú (móvil)   | Izquierda  | Siempre visible             |
| **Buscador**   | Centro     | Ocupa el espacio del saludo |
| Theme toggle   | Derecha    | Siempre visible             |

Con esto el header pasa de ser informativo ("Bienvenido") a ser **accionable** ("Buscar conversión").

---

## 2. Integración del input en el header

### Tamaño y alineación

- **Ancho**: El input del buscador usa `flex: 1` dentro del header-left, con `max-width: 640px` en desktop para no ocupar toda la pantalla y mantener legibilidad.
- **En móvil**: `max-width: none` para que el buscador use todo el ancho disponible.
- **Alineación**: Mismo eje vertical que el botón de menú y el theme toggle; el input mantiene la altura y el radio de bordes del sistema (`--radius-xl`).

### Jerarquía

- El buscador es el **único elemento principal** en la zona central del header en dashboard: sin título junto a él, sin competencia visual.
- Se mantienen la misma línea gráfica (variables CSS), tipografías y colores; solo cambia el contenido del header, no el estilo del layout.

### Identificación como búsqueda

- Icono de lupa a la izquierda del input.
- Placeholder: *"Buscar conversión: PDF a Word, Word, documento…"*.
- `type="search"` y `aria-label="Buscar tipo de conversión"` para accesibilidad.

---

## 3. Reemplazar el saludo sin que el diseño se sienta vacío

### Enfoque aplicado

- **Sustitución directa**: El espacio del saludo lo ocupa el buscador, no se deja hueco vacío.
- **Sin texto adicional**: No se añade un subtítulo tipo "Encuentra tu conversión" debajo del input en el header para no duplicar el mensaje del placeholder y mantener el header limpio.
- **Contenido debajo**: Las stats y los cards de conversiones siguen inmediatamente en el content-area; el usuario tiene una acción clara (buscar) y contenido bajo el header.

### Si en el futuro se quisiera más contexto

- Una línea breve bajo el input, solo en desktop: *"Escribe para filtrar o elige una conversión abajo"*.
- O un hint que aparezca solo la primera vez (tooltip o banner suave) y luego se oculte.

---

## 4. Microinteracciones que refuerzan el uso del buscador

### Ya implementadas

- **Focus visible**: Borde y ring con `--color-primary` al hacer focus en el input.
- **Icono**: La lupa pasa a color primario cuando el input tiene focus (`:focus-within`).
- **Dropdown**: Aparece con una animación corta al escribir; resultados con hover y resaltado por teclado (↑↓ Enter).
- **Teclado**: Escape cierra y limpia; Enter selecciona el resultado resaltado.

### Ideas opcionales para más adelante

- **Auto-focus suave**: En desktop, dar focus al input al entrar en el dashboard (con un pequeño delay para no interferir con lectores de pantalla).
- **Atajo de teclado**: Mostrar en el placeholder o en un hint "Ctrl+K o ⌘K para buscar" y hacer que ese atajo abra/focus el buscador desde cualquier página del layout.
- **Contador en tiempo real**: Junto al input, texto tipo "X conversiones" que se actualice al filtrar (ya existe en el content-area; podría duplicarse en el header si se prioriza aún más la búsqueda).

---

## 5. Consistencia y escalabilidad

### Estado compartido (contexto)

- **DashboardSearchContext**: El `query` del buscador vive en el Layout cuando se está en dashboard. El header (ConversionSearch) y el contenido (Dashboard) comparten el mismo estado vía contexto.
- **Ventajas**: Un solo origen de verdad; al filtrar en el header, los cards del dashboard se actualizan; al volver de otra ruta al dashboard, la búsqueda se mantiene si se desea.

### Rutas y títulos

- **getPageTitle(pathname)**: Centraliza el título del header para rutas que no son dashboard. Añadir nuevas rutas implica solo extender este mapa.
- El buscador solo se muestra cuando `pathname === '/dashboard' || pathname === '/'`, por lo que el comportamiento es predecible y escalable.

### Estilos

- El componente ConversionSearch no cambia; solo se ubica en el header y se aplica la clase contenedora `.header-search` en el Layout para controlar ancho y márgenes.
- Variables del sistema (`--spacing-*`, `--radius-xl`, `--color-primary`, etc.) se siguen usando en el header y en el buscador.

---

## 6. Objetivo final

- **Modo acción**: Al entrar en el dashboard, el usuario ve primero el buscador en el header; no un saludo, sino una herramienta lista para usar.
- **Menos ruido**: Se elimina la redundancia entre el saludo del header y el nombre en el menú lateral.
- **Más eficiencia**: Un solo punto de entrada para encontrar una conversión (el buscador en la parte superior), con resultados en tiempo real y navegación por teclado.
- **Experiencia coherente**: Misma línea gráfica, mismo componente de búsqueda y mismo estado compartido entre header y contenido, con un diseño que se puede extender (títulos por ruta, atajos, hints) sin romper la estructura actual.
