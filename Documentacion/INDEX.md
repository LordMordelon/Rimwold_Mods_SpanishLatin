# Documentación del Sistema de Traducciones - Proyecto Rimworld

## 📋 Índice y Guía de Lectura

Esta documentación describe el funcionamiento completo del ecosistema de programas que generan el Pack de Traducciones en Español Latino para RimWorld.

### Archivos de Documentación

1. **[FLUJO_GENERAL.md](FLUJO_GENERAL.md)** ⭐ START HERE
   - Visión general del sistema
   - Cómo se conectan todos los programas
   - Flujo de datos desde entrada hasta salida final
   - Diagrama del pipeline completo

2. **[PROGRAMAS.md](PROGRAMAS.md)** 
   - Descripción detallada de cada programa
   - Funcionalidad específica
   - Archivos de configuración
   - Parámetros y opciones

3. **[FLUJO_VISUAL.md](FLUJO_VISUAL.md)**
   - Diagrama visual del flujo de datos
   - Mapeo de entradas/salidas
   - Dependencias entre programas

4. **[MANTENIMIENTO.md](MANTENIMIENTO.md)** ⚠️ IMPORTANTE PARA AGENTES
   - Instrucciones obligatorias de actualización
   - Checklist de validación
   - Cómo mantener esta documentación actualizada
   - Procedimiento para cambios futuros

---

## 🎯 Quick Start para Agentes

Si eres un **agente de desarrollo** que necesita entender este sistema:

1. Lee **FLUJO_GENERAL.md** primero (5 min)
2. Consulta **PROGRAMAS.md** para detalles específicos (10 min)
3. Revisa **MANTENIMIENTO.md** ANTES de hacer cambios (5 min)

---

## 📁 Estructura del Proyecto

```
Proyecto/
├── Archivo Traducciones/          ← Datos fuente (carpetas de mods)
│   ├── Mod A/
│   │   └── SpanishLatin.../
│   ├── Mod B/
│   │   └── SpanishLatin.../
│   └── ... (100+ mods)
│
├── Pack Traducciones [Español Latino]/    ← SALIDA (generada automáticamente)
│   ├── About/
│   ├── Languages/
│   │   └── SpanishLatin/
│   │       ├── DefInjected/
│   │       └── Keyed/
│   └── LoadFolders.xml ⭐ (A IMPLEMENTAR)
│
├── Programas/                      ← Sistema de automatización
│   ├── extractor.py               ← Extrae traducciones de mods
│   ├── compilador.py              ← Compila traducciones al Pack
│   ├── cli_compilador.py          ← CLI para compilador
│   ├── extractor_metadatos.py     ← Extrae metadatos de Workshop
│   ├── generar_release_notes.py   ← Genera notas de versión
│   ├── compilador_config.json     ← Config compilador
│   └── extractor_config.json      ← Config extractor
│
└── Documentacion/                  ← Esta carpeta
    ├── INDEX.md                    ← Guía de lectura
    ├── FLUJO_GENERAL.md           ← Visión general
    ├── PROGRAMAS.md               ← Detalles técnicos
    ├── FLUJO_VISUAL.md            ← Diagramas
    └── MANTENIMIENTO.md           ← Para agentes
```

---

## ⚙️ El Sistema en 30 Segundos

**Pipeline:**
```
Mod Source (Steam Workshop)
    ↓
extractor.py (Extrae traducciones)
    ↓
Archivo Traducciones/ (Repositorio local)
    ↓
compilador.py / cli_compilador.py (Compila)
    ↓
Pack Traducciones [Español Latino]/ (Producto final)
```

**Resultado esperado:** Un mod .zip que incluya todas las traducciones al español latino, ready para instalación en Steam Workshop o directo en RimWorld.

---

## 🔄 Ciclo de Vida

1. **EXTRACCIÓN** → `extractor.py` analiza mods reales
2. **ALMACENAMIENTO** → Archivos guardados en `Archivo Traducciones/`
3. **COMPILACIÓN** → `compilador.py` genera el Pack final
4. **DISTRIBUCIÓN** → Pack comprimido para Steam/descargas
5. **ACTUALIZACIÓN** → Versiones nuevas documentadas en MANTENIMIENTO.md

---

## 🎓 Para Agentes que Hacen Cambios

**SIEMPRE que modifiques:**
- Programas Python (extractor.py, compilador.py, etc.)
- Configuraciones JSON
- Estructura de carpetas
- Lógica de procesamiento

**OBLIGATORIO:**
1. Documenta tu cambio en [MANTENIMIENTO.md](MANTENIMIENTO.md)
2. Actualiza la sección "Cambios Recientes"
3. Incluye razón, fecha, autor y checklist de validación
4. NO dejes cambios sin documentar

---

**Última actualización:** 17 de febrero de 2026

Para preguntas o desviaciones, consulta MANTENIMIENTO.md
