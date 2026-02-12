# Recomendaciones de diseño y UX – Dashboard y CTA

## Cambios implementados

1. **Botón "Regístrate" en el header**  
   - Visible solo para usuarios no autenticados.  
   - Ocupa la posición que antes tenía "Preguntar al asistente".  
   - Enlaza a `/login` con `state: { mode: 'register' }` (formulario de registro existente).  
   - Desaparece al iniciar sesión o registrarse (condicionado por `token`).

2. **Botón "Preguntar al asistente" reubicado**  
   - En el **Dashboard**: dentro de la sección "Tu resumen", a la derecha del título, manteniendo visibilidad y relevancia.  
   - En **otras páginas** (Convertir, Historial, etc.): se mantiene en el header para usuarios autenticados.  
   - El FAB del asistente sigue disponible en todas las vistas.

3. **Sección de resumen más compacta**  
   - Misma información: conversiones totales, créditos gratis, tasa de éxito, tiempo promedio.  
   - Menos padding, tipografía algo más pequeña en las tarjetas (`StatsCard` con variante `compact`).  
   - Título "Tu resumen" y trigger del asistente en una sola fila para ahorrar espacio vertical.

---

## Recomendaciones de diseño y jerarquía visual

### Jerarquía

- **Regístrate**: CTA principal para anónimos; mismo peso visual que el trigger del asistente (botón relleno, color primario/CTA).  
- **Preguntar al asistente**: CTA secundario pero destacado (naranja del sistema); en el resumen compite solo con el título, no con las métricas.  
- **Métricas**: Lectura rápida; variante compacta evita que dominen la pantalla y dejan más espacio a "Conversiones disponibles".

### UX

- Un solo CTA principal por contexto: en header para anónimos = "Regístrate"; en dashboard = "Tu resumen" + trigger del asistente.  
- El botón "Regístrate" desaparece al autenticarse, evitando ruido y confusión.  
- En móvil, el título del resumen y el trigger del asistente se apilan en columna para no comprimir el contenido.

### Gráficos (Chart.js u otra librería)

Para una siguiente iteración se recomienda:

- **Tasa de éxito**: gráfico de anillo o barra horizontal (ej. 85% de 100%) para leer el porcentaje de un vistazo.  
- **Créditos**: barra de progreso (usados / total) o indicador tipo “gauge” para mostrar cuánto queda.  
- **Conversiones totales / tiempo promedio**: mantener como número grande; opcionalmente una mini sparkline si se añade historial temporal.  

Ventajas: misma información en menos espacio, más escaneable; se puede usar una sola dependencia (p. ej. Chart.js o Recharts) y reutilizar el mismo componente para varias métricas.

### Accesibilidad

- "Regístrate" y "Preguntar al asistente" tienen `aria-label` o texto visible claro.  
- La sección de resumen tiene `aria-labelledby` y `role="region"`.  
- En viewports muy pequeños, el texto "Regístrate" se oculta visualmente pero se mantiene accesible para lectores de pantalla (patrón sr-only).

---

## Cómo probar

1. **Anónimo**: abrir la app sin sesión → header muestra "Regístrate"; en Dashboard, "Tu resumen" con trigger "Preguntar al asistente" y métricas compactas.  
2. **Registro**: clic en "Regístrate" → redirige al formulario de registro en `/login`.  
3. **Autenticado**: tras login, el header ya no muestra "Regístrate"; en Dashboard sigue el trigger en la sección de resumen; en otras páginas el trigger sigue en el header.
