# Recomendaciones: Menú de configuración y menú “Más”

Recomendaciones de implementación para el menú de configuración (engranaje), el menú “Más” (grid) y su evolución futura.

---

## 1. Lo implementado

### Menú de configuración (ícono engranaje)

- **Ubicación**: Barra superior, donde antes estaba el cambio de tema.
- **Contenido**:
  - **Tema**: Claro / Oscuro (funcional con `setTheme` del store).
  - **Idioma**: Español / English (solo visual; botones deshabilitados con `title="Próximamente"`).
- **Comportamiento**: Clic abre/cierra el dropdown; cierre al hacer clic fuera o con Escape.
- **Accesibilidad**: `aria-label="Configuración"`, `aria-expanded`, `aria-haspopup="menu"`, `role="menu"` y `menuitemradio` en opciones de tema.

### Menú “Más” (ícono grid / cuatro puntos)

- **Ubicación**: A la derecha del engranaje en la barra superior.
- **Opciones**: Precios, Seguridad, Características, Nosotros (con íconos: Tag, Lock, Layers, Heart).
- **Enlaces**: Por ahora `#precios`, `#seguridad`, etc. Se pueden cambiar por rutas cuando existan.
- **Estilo**: Dropdown con flecha superior; ítems como enlaces con ícono + texto.

### Responsive

- Botones del header con `min-width/height: 44px` para área táctil en móvil.
- Dropdowns con `min-width` y alineados a la derecha del disparador; en móvil se mantiene el ancho mínimo y el `right: 0`.
- `header-right` con `gap` reducido en media query 768px para no saturar la barra.

---

## 2. Usabilidad

- **Un solo menú abierto**: Si se desea que al abrir uno se cierre el otro, se puede subir el estado “menú abierto” al layout (por ejemplo `openMenu: 'settings' | 'more' | null`) y pasarlo a ambos componentes.
- **Teclado**: Escape cierra el menú; se puede añadir navegación con flechas (↑↓) y Enter para elegir opción.
- **Focus trap**: En pantallas pequeñas, opcionalmente encerrar el foco dentro del dropdown mientras esté abierto (y devolverlo al botón al cerrar).

---

## 3. Escalabilidad

- **Configuración**: Añadir nuevas opciones (notificaciones, unidad de medida, etc.) como nuevas `<div class="settings-menu__section">` con título y botones/links.
- **Más**: Los ítems viven en el array `MORE_ITEMS`; para añadir “Blog” o “Soporte” basta con un nuevo objeto `{ id, label, icon, href }`.
- **Idioma**: Cuando se implemente i18n:
  - Añadir `locale` (ej. `'es' | 'en'`) al store y `setLocale`.
  - En SettingsMenu, quitar `disabled` de los botones de idioma y usar `locale` + `setLocale`.
  - Sustituir textos fijos por claves de traducción.

---

## 4. Experiencia de usuario

- **Feedback visual**: Los triggers tienen hover y focus visible (borde/outline primario); la opción de tema activa usa `settings-menu__option--active`.
- **Idioma “próximamente”**: Los botones de idioma están deshabilitados y con `title="Próximamente"` para que el usuario entienda que la función llegará después.
- **Rutas del menú Más**: Cuando existan páginas para Precios, Seguridad, etc., cambiar `href` a rutas tipo `/precios`, `/seguridad` y registrarlas en el router.

---

## 5. Opciones de implementación futura

| Mejora | Descripción |
|--------|-------------|
| **Estado global de menú abierto** | Un único estado en el layout para que solo un dropdown esté abierto a la vez. |
| **Navegación por teclado** | Flechas ↑↓ para moverse entre ítems, Enter para activar, Escape para cerrar. |
| **i18n** | Librería (ej. react-i18next) + `locale` en store; activar botones de idioma y traducir toda la app. |
| **Rutas del menú Más** | Crear páginas o secciones para Precios, Seguridad, Características, Nosotros y enlazarlas desde `MORE_ITEMS`. |
| **Persistencia de preferencias** | El tema ya se persiste en el store; el idioma se puede persistir igual al activar i18n. |

Con esto, la implementación actual queda responsive, accesible y preparada para crecer en opciones y en idioma.
