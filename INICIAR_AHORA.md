# 🚀 Comandos de Inicio - DocAI Platform

## 📋 Checklist Rápido

Antes de iniciar, ejecuta estos comandos para verificar recursos:

```bash
# Verificar espacio en disco
df -h

# Verificar memoria RAM
free -h
```

---

## 🔧 Paso 1: Instalar Dependencias Backend

```bash
cd ~/backend
source venv/bin/activate
pip install pypdf python-docx Pillow
```

**Tiempo estimado:** 30-60 segundos

---

## 🗄️ Paso 2: Actualizar Base de Datos

```bash
cd ~/backend
python update_db.py
```

**Salida esperada:** `✓ Database tables updated successfully!`

---

## ▶️ Paso 3: Levantar Backend

```bash
cd ~/backend
source venv/bin/activate
export PYTHONPATH=$PYTHONPATH:$(pwd)
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**URLs importantes:**
- API: http://localhost:8000
- Docs: http://localhost:8000/api/v1/docs
- Health: http://localhost:8000/health

---

## ▶️ Paso 4: Levantar Frontend (Nueva Terminal)

```bash
cd ~/frontend
npm run dev -- --host
```

**URL:** http://localhost:5173

---

## 🧪 Paso 5: Probar

1. Abre http://localhost:5173
2. Inicia sesión con tu usuario
3. Ve a la página **"Convert"**
4. Sube un archivo (ej: imagen PNG)
5. Selecciona formato de destino (ej: PDF)
6. Click en **"Convert Now"**
7. Espera la conversión (verás la barra de progreso)
8. Click en **"Download Result"**

---

## 🔍 Verificar que Todo Funciona

### Test 1: Backend Disponible
```bash
curl http://localhost:8000/health
```
**Esperado:** `{"status":"healthy"}`

### Test 2: Ver Formatos Soportados
```bash
curl http://localhost:8000/api/v1/convert/supported-formats
```

### Test 3: Ver API Docs
Abre en navegador: http://localhost:8000/api/v1/docs

Deberías ver la sección **"convert"** con 5 endpoints:
- POST /api/v1/convert/upload
- GET /api/v1/convert/history
- GET /api/v1/convert/download/{conversion_id}
- GET /api/v1/convert/supported-formats
- GET /api/v1/convert/status/{conversion_id}

---

## ⚡ Inicio Rápido (Script Automático)

Si prefieres usar el script de inicio:

```bash
./start.sh
```

Luego selecciona:
- Opción 1: Iniciar Backend
- Opción 2: Iniciar Frontend (en otra terminal)

---

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'pypdf'"
```bash
cd ~/backend
source venv/bin/activate
pip install pypdf python-docx Pillow
```

### Error: "Table conversions not found"
```bash
cd ~/backend
python update_db.py
```

### Frontend no carga
```bash
cd ~/frontend
npm install
npm run dev -- --host
```

### Backend crashea por RAM
```bash
# Verificar SWAP está activo
swapon --show

# Si no hay swap, crear uno
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 📊 Monitoreo del Sistema

### Ver logs del Backend
Los logs aparecen directamente en la terminal donde corriste uvicorn

### Ver uso de recursos en tiempo real
```bash
htop
```

### Ver archivos generados
```bash
# Uploads
ls -lh ~/backend/storage/uploads/

# Convertidos
ls -lh ~/backend/storage/converted/
```

---

## ✅ Lista de Verificación Final

- [ ] Backend corriendo en puerto 8000
- [ ] Frontend corriendo en puerto 5173
- [ ] Puedo hacer login
- [ ] Puedo ver la página Convert
- [ ] Puedo subir un archivo
- [ ] La conversión se completa
- [ ] Puedo descargar el resultado
- [ ] Veo mis créditos restantes

---

## 🎯 Próximo Objetivo

Una vez que todo funcione, el siguiente paso es:

**Fase 5: Implementar página de Historial**
- Crear componente `/history`
- Mostrar todas las conversiones del usuario
- Permitir re-descargar archivos antiguos

---

**¡Listo para arrancar!** 🚀
