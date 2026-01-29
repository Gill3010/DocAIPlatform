# 🔍 ANÁLISIS EXHAUSTIVO DE INFRAESTRUCTURA AWS
**Fecha:** 29 de Enero, 2026  
**Proyecto:** DocAI Platform  
**Objetivo:** Diagnosticar problemas de conectividad SSH y optimizar recursos

---

## 📊 1. DIAGNÓSTICO ACTUAL

### 🖥️ Configuración del Servidor

| Recurso | Actual | Estado | Crítico |
|---------|--------|--------|---------|
| **Tipo de Instancia** | t2.micro / t3.micro | ⚠️ Limitado | No detectado |
| **RAM Total** | 914 MB | ⚠️ Insuficiente | Sí |
| **RAM Disponible** | 127 MB (13.8%) | 🔴 CRÍTICO | **SÍ** |
| **RAM en Uso** | 786 MB (86%) | 🔴 CRÍTICO | **SÍ** |
| **SWAP Activo** | 1GB (607MB usado) | ⚠️ Alto uso | Sí |
| **Disco Total** | 6.8 GB | ⚠️ Pequeño | No |
| **Disco Usado** | 5.7 GB (84%) | ⚠️ Alto | Casi |
| **Disco Libre** | 1.1 GB | ⚠️ Poco espacio | Pronto |
| **CPU Load Average** | 0.60 (1min) | ✅ Aceptable | No |

---

## 🚨 2. PROBLEMAS CRÍTICOS IDENTIFICADOS

### 🔴 NIVEL CRÍTICO

#### 1. **Out of Memory (OOM) Killer Activado**
```
Jan 29 12:27:40: Out of memory: Killed process 30134 (swapoff)
```
- ⚠️ **Impacto:** El sistema está matando procesos por falta de RAM
- ⚠️ **Consecuencia:** Servicios pueden caer sin previo aviso
- ⚠️ **Causa raíz:** Solo 914MB de RAM total es INSUFICIENTE

#### 2. **Memoria RAM Casi Agotada**
- Solo **127MB libres** (13.8% disponible)
- **607MB de SWAP activo** (59% del swap usado)
- El sistema está usando SWAP constantemente = **RENDIMIENTO DEGRADADO**

#### 3. **Conexiones SSH con "Broken Pipe"**
```
ssh_dispatch_run_fatal: Connection from IP port X: Broken pipe [preauth]
```
- ⚠️ **Causa:** Cuando el sistema se queda sin RAM, SSH no puede mantener conexiones
- ⚠️ **Resultado:** Desconexiones inesperadas, imposible trabajar de forma estable

#### 4. **Disco al 84% de Capacidad**
- Solo **1.1GB libres**
- Riesgo de llenar disco con logs o archivos temporales

### ⚠️ NIVEL ALTO

#### 5. **Cursor Server Consumiendo 28% de RAM (263MB)**
- Es el proceso que más memoria consume
- **Recomendación:** Considerar trabajar localmente y solo desplegar

#### 6. **Uvicorn (Backend) Consumiendo 47.9% CPU**
- Alto uso de CPU puede causar lentitud
- Con modo `--reload` activo consume más recursos

---

## 📊 3. DISTRIBUCIÓN DE RECURSOS

### Memoria RAM (914MB total):

```
┌─────────────────────────────────────────┐
│ Cursor Server:        263MB (28.7%)  ⚠️│
│ Backend Python:        96MB (10.5%)  ⚠️│
│ Frontend Node/Vite:    88MB  (9.6%)  ⚠️│
│ System + Others:      340MB (37.2%)  ⚠️│
│ LIBRE:                127MB (13.9%)  🔴│
│ SWAP EN USO:          607MB          🔴│
└─────────────────────────────────────────┘
```

### Disco (6.8GB total):

```
┌─────────────────────────────────────────┐
│ Cursor Server:        342MB (5.0%)    ⚠️│
│ node_modules:         164MB (2.4%)    ✅│
│ Backend:              141MB (2.1%)    ✅│
│ Sistema + Otros:     5.1GB (75%)      ⚠️│
│ LIBRE:               1.1GB (16%)      ⚠️│
└─────────────────────────────────────────┘
```

---

## 💡 4. RECOMENDACIONES PRIORITARIAS

### 🎯 ACCIÓN INMEDIATA (Hoy)

#### Opción A: Aumentar RAM (RECOMENDADO)
**Cambiar a t3.small o t3a.small**

| Tipo | vCPU | RAM | Costo/mes | Free Tier | Recomendación |
|------|------|-----|-----------|-----------|---------------|
| **t2.micro** | 1 | 1GB | $0 | ✅ 750h/mes | Actual (INSUFICIENTE) |
| **t3.micro** | 2 | 1GB | $0 | ✅ 750h/mes | Misma RAM, mejor CPU |
| **t3.small** | 2 | 2GB | ~$15/mes | ❌ | **IDEAL para desarrollo** |
| **t3a.small** | 2 | 2GB | ~$13/mes | ❌ | Más económico, AMD |
| **t4g.small** | 2 | 2GB | ~$12/mes | ❌ | ARM, más barato |

**✅ MEJOR OPCIÓN: t3.small (2GB RAM)**
- **Beneficio:** 2x más RAM = Sin OOM Killer
- **Costo:** ~$0.50/día = **$15/mes**
- **Justificación:** Estabilidad garantizada, SSH confiable

#### Opción B: Optimizar Instancia Actual (Temporal)

1. **Detener Cursor Server cuando no lo uses:**
```bash
pkill -f cursor-server
```
**Ahorro:** 263MB de RAM (28%)

2. **Reducir procesos de desarrollo:**
```bash
# Solo levantar backend O frontend cuando necesites
# No ambos simultáneamente si no es necesario
```

3. **Deshabilitar auto-reload en producción:**
```bash
# En vez de --reload, usar sin reload
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

---

## 🎯 5. PLAN DE MIGRACIÓN PROGRESIVA

### Fase 1: Optimización Inmediata (Sin costo)

**Día 1-2: Liberar RAM**
```bash
# 1. Limpiar cache del sistema
sudo sync; echo 3 | sudo tee /proc/sys/vm/drop_caches

# 2. Detener servicios no esenciales
sudo systemctl disable snapd
sudo systemctl stop snapd

# 3. Limpiar paquetes no usados
sudo apt autoremove -y
sudo apt clean

# 4. Limitar logs del sistema
sudo journalctl --vacuum-time=2d
```

**Resultado esperado:** +50-100MB de RAM libre

### Fase 2: Aumentar SWAP (Sin costo)

```bash
# Aumentar SWAP a 2GB
sudo swapoff /swapfile
sudo rm /swapfile
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

**Resultado esperado:** Menos crashes, pero SWAP es lento

### Fase 3: Upgrade de Instancia (Costo: $15/mes)

**Procedimiento sin pérdida de datos:**

1. **Crear snapshot del disco EBS** (Gratis)
```bash
# Desde AWS Console:
EC2 → Volumes → Seleccionar volumen → Actions → Create Snapshot
```

2. **Detener instancia** (no terminar)
```bash
# AWS Console: Instance → Stop (NO Terminate)
```

3. **Cambiar tipo de instancia**
```bash
# AWS Console:
Instance → Actions → Instance Settings → Change Instance Type
Seleccionar: t3.small
```

4. **Iniciar instancia**
```bash
# AWS Console: Instance → Start
```

5. **Verificar que todo funciona**
```bash
ssh ubuntu@tu-ip
free -h  # Deberías ver ~2GB de RAM
```

**Tiempo total:** 10-15 minutos  
**Downtime:** 5-10 minutos

---

## 💰 6. ESTRATEGIA PARA USAR CRÉDITOS AWS

### Créditos Disponibles en Free Tier

**Año 1 (12 meses):**
- ✅ t2.micro/t3.micro: 750 horas/mes (GRATIS)
- ✅ 30GB de EBS: GRATIS
- ✅ 5GB de S3: GRATIS
- ✅ 15GB de bandwidth: GRATIS

**Después del Free Tier:**
- ❌ t2.micro: ~$9/mes
- ❌ t3.small: ~$15/mes
- ❌ t3.medium: ~$30/mes

### Opciones para Reducir Costos

#### Opción 1: Usar créditos promocionales
- Si tienes créditos de AWS Educate/Activate: **ÚSALOS AHORA**
- Permiten usar instancias mayores sin costo

#### Opción 2: Reserved Instances (Si proyecto a largo plazo)
- Compromiso de 1 año = 40% descuento
- t3.small: $15/mes → $9/mes

#### Opción 3: Spot Instances (Solo para desarrollo)
- Hasta 90% descuento
- **NO recomendado:** Pueden terminarse sin aviso

#### Opción 4: Desarrollo Local + Despliegue en producción
- **Desarrollar:** En tu máquina local (RAM ilimitada)
- **Desplegar:** En AWS solo cuando esté listo
- **Ahorro:** Solo pagas cuando la instancia está encendida

---

## 🛡️ 7. BUENAS PRÁCTICAS AWS

### Seguridad

1. **Configurar CloudWatch Alarms (GRATIS en Free Tier)**
```yaml
Alarmas recomendadas:
- CPU > 80% por 5 minutos
- Memoria disponible < 200MB
- Disco > 90%
- StatusCheckFailed (instancia caída)
```

2. **Backup automático**
```bash
# Crear snapshots semanales del EBS
AWS Console → EBS → Lifecycle Manager
```

### Optimización

3. **Elastic IP (Gratuita si está asociada)**
- Evita cambio de IP al reiniciar
- **Costo:** $0 si está en uso, $3.6/mes si no está asociada

4. **Security Groups bien configurados**
```yaml
Puertos necesarios:
- 22 (SSH): Solo tu IP
- 8000 (Backend): 0.0.0.0/0 o solo IP del frontend
- 5173 (Frontend): 0.0.0.0/0
```

5. **Monitoring con scripts**
```bash
# Crear script de monitoreo
cat > /home/ubuntu/monitor.sh << 'EOF'
#!/bin/bash
echo "=== $(date) ==="
free -h | grep Mem
df -h / | tail -1
uptime
echo "---"
EOF

# Ejecutar cada hora
crontab -e
# Agregar: 0 * * * * /home/ubuntu/monitor.sh >> /home/ubuntu/monitor.log
```

---

## 📋 8. RESUMEN EJECUTIVO Y DECISIÓN

### 🔴 Problema Principal
Tu instancia t2.micro con **1GB de RAM es INSUFICIENTE** para:
- Cursor Server (263MB)
- Backend FastAPI (96MB)
- Frontend Vite (88MB)
- Sistema operativo (340MB)

**Total necesario:** ~800MB + overhead = **1.2GB mínimo**

### ✅ Solución Recomendada

**OPCIÓN 1 (IDEAL): Upgrade a t3.small**
- **Costo:** $15/mes (~$0.50/día)
- **Beneficio:** Sin OOM Killer, SSH estable, desarrollo fluido
- **Downtime:** 5-10 minutos
- **ROI:** Tu tiempo vale más que $15/mes

**OPCIÓN 2 (TEMPORAL): Optimizar actual**
- Detener Cursor Server cuando no uses
- Solo correr backend O frontend, no ambos
- Aumentar SWAP a 2GB
- **Costo:** $0
- **Limitación:** Sigue siendo inestable

### 🎯 Recomendación Final

**Para un proyecto SaaS profesional:**
1. **Hoy:** Aplicar optimizaciones (Fase 1 y 2)
2. **Esta semana:** Upgrade a t3.small
3. **Mes próximo:** Evaluar t3.medium si crece

**Justificación económica:**
- 1 hora de tu tiempo = más de $15
- SSH inestable = pérdida de productividad
- OOM Killer = riesgo de perder datos

---

## 📞 SIGUIENTE PASO INMEDIATO

¿Quieres que ejecute las optimizaciones gratuitas AHORA (Fase 1 y 2)?
Esto te dará más estabilidad mientras decides si hacer el upgrade.

---

**Preparado por:** AI Assistant  
**Para:** DocAI Platform Development Team  
**Última actualización:** 2026-01-29
