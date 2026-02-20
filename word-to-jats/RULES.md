# Word-to-JATS Conversion Platform - Reglas de Estilo

## Estilo de Código
- Tipado estricto: anotar parámetros y retornos de funciones.
- Usar `typing`: `List`, `Dict`, `Optional`, `Union`.
- Constantes en UPPER_SNAKE_CASE; clases en PascalCase; funciones en snake_case.

## Logging
- Logging estructurado en JSON para producción.
- Incluir: timestamp, level, message, correlation_id, component.

## Excepciones
- Capturar excepciones específicas; evitar `except:` vacío.
- Re-lanzar con contexto: `raise NewError("msg") from original`.
