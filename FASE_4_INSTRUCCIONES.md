# 🚀 Fase 4: Motor de Conversión - Instrucciones de Inicialización

## ✅ Lo que se implementó

### Backend
1. **Modelo de datos** (`Conversion`) para historial de conversiones
2. **Router completo** `/api/v1/convert` con 5 endpoints:
   - `POST /upload` - Subir y convertir archivo
   - `GET /history` - Obtener historial de conversiones
   - `GET /download/{id}` - Descargar archivo convertido
   - `GET /supported-formats` - Ver formatos soportados
   - `GET /status/{id}` - Consultar estado de conversión

3. **Funciones de conversión** ligeras y optimizadas para RAM limitada:
   - PNG/JPG/JPEG → PDF
   - PDF → PNG (placeholder)
   - PDF → TXT
   - TXT → DOCX
   - DOCX → TXT

4. **Sistema de créditos**: 10 conversiones gratis por usuario

### Frontend
1. Componente `Convert.tsx` conectado al backend real
2. Carga de archivos con validación
3. Barra de progreso real durante conversión
4. Descarga automática de archivos convertidos
5. Visualización de créditos restantes
6. Manejo de errores

---

## 📋 Pasos para Inicializar

### 1. Instalar nuevas dependencias del Backend

```bash
cd ~/backend
source venv/bin/activate
pip install pypdf python-docx Pillow
```

### 2. Actualizar la Base de Datos

Crear las nuevas tablas en SQLite:

```bash
cd ~/backend
python update_db.py
```

Deberías ver: `✓ Database tables updated successfully!`

### 3. Levantar el Backend

```bash
cd ~/backend
source venv/bin/activate
export PYTHONPATH=$PYTHONPATH:$(pwd)
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Verifica que el servidor esté corriendo:
- API Docs: http://localhost:8000/api/v1/docs
- Deberías ver los nuevos endpoints bajo la sección **"convert"**

### 4. Levantar el Frontend

En otra terminal:

```bash
cd ~/frontend
npm run dev -- --host
```

### 5. Probar la Funcionalidad

#### Opción A: Desde el Frontend
1. Abre http://localhost:5173
2. Inicia sesión con tu usuario
3. Ve a la página **Convert**
4. Arrastra un archivo o selecciónalo
5. Elige el formato de destino
6. Haz clic en "Convert Now"
7. Espera la conversión
8. Descarga el resultado

#### Opción B: Desde la API (usando cURL)

```bash
# 1. Login y obtener token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=tu@email.com&password=tupassword"

# Guarda el token que recibes

# 2. Ver formatos soportados
curl http://localhost:8000/api/v1/convert/supported-formats

# 3. Subir y convertir (ejemplo con imagen a PDF)
curl -X POST http://localhost:8000/api/v1/convert/upload?target_format=pdf \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -F "file=@/ruta/a/tu/imagen.png"

# 4. Descargar archivo convertido
curl -X GET http://localhost:8000/api/v1/convert/download/1 \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  --output resultado.pdf
```

---

## 🧪 Casos de Prueba Recomendados

1. **Conversión básica PNG → PDF**
   - Sube una imagen PNG pequeña
   - Convierte a PDF
   - Descarga y verifica

2. **Límite de conversiones**
   - Realiza 10 conversiones
   - Intenta una 11ª conversión
   - Deberías recibir error: "Free conversion limit reached"

3. **Archivo demasiado grande**
   - Intenta subir un archivo > 10MB
   - Deberías recibir error 413

4. **Formato no soportado**
   - Intenta convertir de .mp4 a .pdf
   - Deberías recibir error indicando formatos válidos

5. **Historial de conversiones**
   - Ve a la API docs: `/api/v1/convert/history`
   - Ejecuta el endpoint
   - Verifica que aparezcan tus conversiones

---

## 📁 Estructura de Archivos Creada

```
backend/
├── storage/
│   ├── uploads/          # Archivos originales subidos
│   └── converted/        # Archivos convertidos
├── app/
│   ├── models/
│   │   └── conversion.py # Modelo de conversiones
│   ├── routers/
│   │   └── convert.py    # Router de conversión
│   ├── schemas/
│   │   └── conversion.py # Schemas Pydantic
│   └── utils/
│       └── converter.py  # Funciones de conversión
└── update_db.py          # Script para actualizar DB
```

---

## 🔧 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'PIL'"
```bash
pip install Pillow
```

### Error: "ModuleNotFoundError: No module named 'pypdf'"
```bash
pip install pypdf python-docx
```

### Error: "Storage directory not found"
Las carpetas se crean automáticamente al levantar el backend.

### Conversión falla con PDF grande
- Verifica espacio en disco: `df -h`
- Verifica RAM disponible: `free -h`
- Considera implementar conversión asíncrona para archivos grandes

---

## 🎯 Próximos Pasos (Fase 5)

1. **Página de Historial** (`/history`)
   - Mostrar todas las conversiones del usuario
   - Opción de re-descargar archivos antiguos

2. **AI Assistant Chat**
   - Interfaz de chat interactiva
   - Integración con OpenAI API
   - Sistema de créditos para consultas

3. **Mejoras al Motor de Conversión**
   - Más formatos (XLSX, CSV, etc.)
   - Conversión asíncrona con jobs
   - Notificaciones push cuando termine

---

## 📊 Métricas de Éxito

- ✅ Backend con endpoints funcionando
- ✅ Frontend conectado al backend
- ✅ Conversiones completándose exitosamente
- ✅ Archivos descargándose correctamente
- ✅ Sistema de créditos funcionando
- ✅ Manejo de errores robusto

¡La Fase 4 está completa! 🎉
