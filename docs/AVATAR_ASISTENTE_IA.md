# Avatar del Asistente de IA - Recursos e Integración

## Avatar implementado

Se generó un avatar personalizado para el asistente de IA con las siguientes características:

- **Estilo:** Robot amigable con gradiente neón azul eléctrico → magenta
- **Formato:** PNG con fondo transparente
- **Ubicación:** `/frontend/public/ai-assistant-avatar.png`
- **Tamaño visual:** 36×36px en FAB y header del chat (escalable)

### Dónde se usa

1. **Botón FAB (flotante):** Avatar cuando el chat está cerrado
2. **Header del chat:** Avatar junto al título "Asistente de IA"

---

## Recursos alternativos (web)

### Iconos SVG gratuitos (libre uso)

| Fuente | URL | Formato | Licencia |
|--------|-----|---------|----------|
| **SVG Repo** | https://www.svgrepo.com/svg/246584/robot-ai | SVG, PNG 256/512/1024 | CC0 (sin atribución) |
| **Icons8** | https://icons8.com/icons/set/ai-assistant | PNG, SVG | Gratis con atribución |
| **Flaticon** | https://www.flaticon.com/free-icon/ai-assistant_12941952 | PNG, SVG, EPS | Gratis con atribución |
| **IconScout** | https://iconscout.com/icons/ai-assistant | SVG, PNG | Varios estilos |
| **UXWing** | https://uxwing.com/robot-icon/ | SVG, PNG 512 | Sin atribución |

### Cómo sustituir el avatar actual

Para usar otro recurso:

1. **SVG:** Guardar en `/frontend/public/ai-assistant.svg` y cambiar la extensión en el componente.
2. **PNG:** Sustituir el archivo en `/frontend/public/ai-assistant-avatar.png` (recomendado 512×512).

---

## Integración en el código

### Componente modificado

- `frontend/src/components/AIAssistantFAB/AIAssistantFAB.tsx`
- `frontend/src/components/AIAssistantFAB/AIAssistantFAB.css`

### Clases CSS relevantes

- `.ai-fab-avatar` – Avatar en el botón FAB (36×36px)
- `.ai-chat-avatar` – Avatar en el header del chat (36×36px)

### Cambiar tamaño

```css
.ai-fab-avatar {
    width: 48px;   /* Más grande */
    height: 48px;
}
```

---

## Especificaciones visuales aplicadas

- Colores vibrantes (azul neón y magenta)
- Estilo tecnológico y moderno
- Fondo transparente
- Formato cuadrado 1:1
- Diseño amigable y de soporte
