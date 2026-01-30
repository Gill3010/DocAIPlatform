# Recomendaciones UX/UI: Motor de búsqueda en el Dashboard

Recomendaciones de ubicación, diseño, interacción y accesibilidad para un buscador de conversiones en el panel principal, alineado con la línea gráfica existente.

---

## 1. Ubicación óptima del buscador

### Recomendación principal: **arriba de la sección "Conversiones disponibles"**

- **Visibilidad**: Es lo primero que el usuario ve al entrar en la zona de conversiones, sin competir con las stats.
- **Contexto**: El input está justo encima del contenido que filtra (cards), lo que refuerza la relación causa-efecto.
- **Flujo**: Stats → Buscador → Listado filtrado; el usuario entiende que puede buscar antes de recorrer.

### Alternativas consideradas

| Ubicación | Pros | Contras |
|-----------|------|--------|
| Debajo del título del dashboard | Muy visible | Rompe la jerarquía (stats primero) |
| Dentro del section-header (junto a "Ver todas") | Compacto | Poco espacio; el input puede quedar secundario |
| Sticky bajo el header | Siempre visible al hacer scroll | Ocupa espacio fijo y puede distraer |

**Conclusión**: Colocar el buscador como primer elemento de la sección "Conversiones disponibles", ancho completo, con el mismo padding que el resto del contenido.

---

## 2. Diseño del input

### Placeholder

- **Recomendado**: *"Buscar conversión: PDF a Word, Word, documento…"*
- **Alternativas**: *"¿Qué quieres convertir?"* (más conversacional), *"Buscar por formato o tipo…"* (más técnico).
- Objetivo: indicar que se puede buscar por tipo de conversión, formato de origen/destino o palabra clave, sin saturar.

### Iconografía

- **Icono principal**: Lupa (Search) a la izquierda del input.
- **Icono secundario (opcional)**: Tecla "K" o atajo a la derecha cuando el input no tiene foco, para power users.
- Mantener iconos de Lucide ya usados en el proyecto; tamaño ~20–24px; color `--color-text-tertiary` que pase a `--color-primary` en focus.

### Microcopys

- **Sin resultados**: *"No hay coincidencias. Prueba con «PDF», «Word» o «imagen»."*
- **Resultados**: *"X conversiones"* o *"X resultados"* junto al dropdown o debajo del input (evitar "resultados" si es 1).
- **Atajo teclado**: En el placeholder o en un pequeño texto bajo el input: *"Usa ↑↓ para moverte y Enter para elegir"* (solo en primera interacción o en un tooltip).

---

## 3. Interacción

### Búsqueda en tiempo real

- Actualizar resultados en cada cambio del input (sin botón "Buscar").
- Pequeño debounce (100–150 ms) opcional para evitar parpadeos en tecleo muy rápido; con listas cortas (<20 ítems) no es obligatorio.

### Autocompletado / dropdown de resultados

- Mostrar el dropdown cuando `query.length >= 1` (o desde el primer carácter).
- Lista de resultados: icono + "Origen → Destino" + etiqueta de categoría (opcional).
- Máximo 8–10 ítems visibles; scroll interno si hay más.
- Un clic en un resultado = navegar a `/convert?from=…&to=…` (mismo destino que el card).

### Resaltado de coincidencias

- Opción A: Resaltar en negrita o color primario las porciones del texto que coinciden con la query (ej. "**PDF** a **Word**").
- Opción B: Sin resaltado si la lista es corta y el texto ya es claro (menos ruido visual).
- **Recomendación**: Resaltado sutil (font-weight o color) para reforzar por qué aparece el resultado.

### Filtrado del listado de cards

- Misma query que el dropdown: filtrar los cards visibles en la página.
- Si hay query y hay resultados: mostrar solo los cards que coinciden y, si se quiere, un subtítulo "X resultados".
- Si hay query y no hay resultados: mostrar mensaje amigable y sugerencias (ej. "No hay coincidencias. Prueba con «PDF», «Word» o «imagen».").
- Si la query está vacía: mostrar todas las conversiones como ahora.

---

## 4. Teclado y accesibilidad

- **Focus visible**: Outline o ring con `--color-primary` (ya definido en variables).
- **Tab**: El input es focusable; el dropdown no necesita estar en orden Tab si la navegación interna es con flechas.
- **Flechas ↑/↓**: Navegar por resultados; el ítem seleccionado con fondo distinto (ej. `--color-surface-hover` o `--color-primary` con opacidad baja).
- **Enter**: Activar el resultado resaltado (ir a Convert).
- **Escape**: Limpiar query y cerrar dropdown; devolver foco al input.
- **ARIA**: `role="combobox"`, `aria-expanded`, `aria-controls` al ID del listbox, `aria-activedescendant` al ítem resaltado, `aria-label` en el input (ej. "Buscar tipo de conversión").
- **Sin resultados**: Mensaje asociado al input (`aria-describedby`) o `role="status"` para "No hay coincidencias".

---

## 5. Consistencia visual

- **Input**: Misma superficie que los cards (`--color-surface`), borde `--color-border`, `--radius-lg` o `--radius-xl`, padding con `--spacing-*`.
- **Dropdown**: Mismo `border-radius`, `--shadow-lg`, borde sutil; no introducir nuevos colores.
- **Tipografía**: `--font-size-base` en input y resultados; `--font-size-sm` en categoría o contador.
- **Transiciones**: `--transition-fast` para hover/focus y aparición del dropdown (opacity + transform suave).
- **Colores**: Solo primario para focus, hover de resultado y posibles resaltados; el resto neutros del sistema.

---

## 6. Sensación de velocidad y fluidez

- **Sin espera artificial**: Resultados inmediatos (o con debounce muy corto).
- **Dropdown**: Aparecer con una animación corta (ej. opacity 0→1, translateY -4px→0) para que se sienta reactivo.
- **Navegación por teclado**: Sin retraso; el ítem activo actualizarse en cada pulsación de flecha.
- **Al seleccionar**: Navegación instantánea (Link de React Router); no mostrar loading en el dashboard.

---

## 7. Evitar fricción y sobrecarga

- **Un solo campo**: No añadir filtros extra (por categoría, etc.) en esta primera versión; el texto ya filtra por tipo/origen/destino.
- **Dropdown no invasivo**: Máximo altura equivalente a ~8 ítems; el resto con scroll.
- **Vacío**: Con query vacía, no mostrar dropdown; al borrar, volver al listado completo.
- **Mensaje "sin resultados"**: Una sola línea con sugerencias; no bloqueos ni modales.

---

## 8. Resumen de decisiones implementadas

| Aspecto | Decisión |
|--------|----------|
| Ubicación | Arriba de "Conversiones disponibles", ancho completo |
| Placeholder | "Buscar conversión: PDF a Word, Word, documento…" |
| Icono | Lupa (Search) a la izquierda |
| Resultados | Dropdown bajo el input; máximo ~10 visibles |
| Teclado | ↑↓ navegar, Enter seleccionar, Escape cerrar/limpiar |
| Cards | Misma query filtra los cards visibles en la página |
| Sin resultados | Mensaje + sugerencias; mismo estilo que el sistema |

Con esto el usuario puede, desde el dashboard, localizar y elegir cualquier conversión en pocos segundos, con teclado o ratón, sin depender del scroll.
