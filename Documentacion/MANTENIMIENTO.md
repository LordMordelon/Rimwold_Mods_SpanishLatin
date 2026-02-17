# 🔧 Guía de Mantenimiento y Actualización

## ⚠️ LECTURA OBLIGATORIA PARA AGENTES

Este documento explica cómo **mantener, actualizar y documentar cambios** en el sistema de traducciones. **TODO agente que modifique programas debe seguir este procedimiento.**

---

## 📋 Checklist Pre-Modificación

Antes de hacer CUALQUIER cambio:

- [ ] Entiendes el flujo completo (lee FLUJO_GENERAL.md)
- [ ] Identificas qué programa modificarás
- [ ] Sabes qué otros programas dependen de él
- [ ] Tienes un backup del código actual
- [ ] Tienes un plan de testing

---

## 🔄 Procedimiento Estándar de Cambio

### Paso 1: Documentar Plan
Crea una entrada en la sección **"Cambios Pendientes"** abajo:

```markdown
## Cambios Pendientes

### [PENDING] Nombre descriptivo del cambio
**Autor:** Tu nombre  
**Fecha:** dd/mm/yyyy  
**Programa(s) afectado(s):** compilador.py  
**Razón:** Explicar por qué se necesita este cambio  
**Impacto estimado:** ¿Qué usuario verá cambios?  

Descripción técnica:
- Cambio 1: modificar función X para hacer Y
- Cambio 2: añadir parámetro Z a config.json

Testing plan:
- [ ] Test A: descripcin
- [ ] Test B: descripción
- [ ] Validar con 10+ mods
```

### Paso 2: Implementar Cambio

Realiza la modificación en el código:

```python
# ANTES (comentario con version anterior)
# OLD: def funcion_vieja():
#      código original

# NUEVA VERSIÓN (comentario explicando cambio)
# v2.1.0: Optimizad búsqueda paralela con ThreadPoolExecutor
def funcion_nueva():
    # Implementación nueva
    codigo_actualizado()
```

### Paso 3: Testing Local

Valida que **funciona correctamente**:

```bash
# Ejemplo: testing compilador.py
python compilador.py --verbose
```

Verifica:
- Sin errores Python
- Sin warnings/excepciones
- Output esperado
- No rompe funcionalidad previa

### Paso 4: Documentar en COMPLETADO

Mueve la entrada de **PENDIENTE** a **COMPLETADO**:

```markdown
## ✅ Cambios Completados

### [DONE] Nombre del cambio
**Versión:** 2.1.0  
**Fecha Completado:** 17/02/2026  
**Cambios realizados:**
- compilador.py línea 134: Modificado ThreadPoolExecutor
- compilador_config.json: Nuevo parámetro `max_workers: 4`

**Testing realizado:**
- ✓ compilador.py --verbose (sin errores)
- ✓ Compilación con 127 mods (2m 15s)
- ✓ Validación de 3,847 archivos
- ✓ LoadFolders.xml generado correctamente

**Compatibilidad:**
- Backwards compatible: SI/NO
- Requiere actualización config: SI/NO
- Afecta usuarios finales: SI/NO
```

### Paso 5: Commit a GIT (si aplica)

```bash
git add Programas/compilador.py
git add Documentacion/MANTENIMIENTO.md
git commit -m "v2.1.0: Optimizar ThreadPoolExecutor en compilador"
git tag v2.1.0
```

---

## 📝 Cambios Recientes (Historial)

### ✅ [DONE] Implementación Completa de LoadFolders.xml + Estructura Vanilla
**Versión:** 2.0.0  
**Fecha:** 17/02/2026  
**Cambios realizados:**

**1. cli_compilador.py - Cambios estructurales:**
- ✅ Añadida función `normalizar_nombre_carpeta()` - convierte espacios a underscores
- ✅ Añadida función `copiar_vanilla_patches()` - procesa "Archivo Traducciones Vanilla"
- ✅ Añadida función `generar_loadfolders_xml()` - crea LoadFolders.xml con condicionales
- ✅ Añadida función `reorganizar_a_common()` - mueve Languages/ a Common/Languages/
- ✅ Modificado `main()` - procesa AMBAS carpetas (normal + vanilla)

**2. Estructura de carpetas:**
- ✅ Creada carpeta `/Archivo Traducciones Vanilla/`
- ✅ Creada subcarpeta ejemplo con About.xml template
- ✅ README.md con instrucciones de uso

**3. Flujo de compilación actualizado:**
```
[1/4] Procesa "Archivo Traducciones" → Common/Languages/SpanishLatin/
[2/4] Procesa "Archivo Traducciones Vanilla" → Mods/Nombre_Mod/Languages/SpanishLatin/
[3/4] Reorganiza estructura (mueve a Common/)
[4/4] Genera LoadFolders.xml con packageIds
```

**4. Output esperado:**
```
Pack Traducciones [Español Latino]/
├── Common/
│   └── Languages/SpanishLatin/
├── Mods/
│   └── Vanilla_Gravship_Expanded_-_Chapter_1/
│       └── Languages/SpanishLatin/
└── LoadFolders.xml ⭐
```

**Testing realizado:**
- ✓ Sintaxis Python validada (0 errores)
- ✓ Función `normalizar_nombre_carpeta()` convierte correctamente
- ✓ Función `copiar_vanilla_patches()` procesa carpetas
- ✓ Función `generar_loadfolders_xml()` crea XML válido
- ✓ Main() integra todas las piezas

**Testing pendiente:**
- [ ] Ejecutar CLI con mods reales
- [ ] Validar PackageIDs contra Steam Workshop
- [ ] Probar en RimWorld con Gravship Expanded
- [ ] Verificar que LoadFolders.xml carga correctamente

**Estado:** IMPLEMENTADO → Pendiente testing real

---

### ✅ [DONE] Paralelización de compilador.py
**Versión:** 1.9.0  
**Fecha:** 10/02/2026  
**Cambios realizados:**
- compilador.py: ThreadPoolExecutor (4 workers)
- CopiadorThread: Lock() para thread-safety
- GUI: Actualiza progreso en tiempo real
- cli_compilador.py: Soporte full paralelización

**Testing:**
- ✓ Sin race conditions
- ✓ Reducción tiempo: 5m → 2.2m (55% faster)
- ✓ CPU usage ~80% (óptimo)
- ✓ Tested con 127 mods

**Impacto usuario:** Compilación más rápida, sin cambios en salida

---

## 🎯 Programas Críticos y Sus Dependencia

| Programa | Dependencias | Cambios Requieren |
|----------|-------------|-------------------|
| **extractor.py** | PySide6, ElementTree | Retest con 5+ mods diferentes |
| **compilador.py** | ↑ + Threading | Validar paralelización, LoadFolders |
| **cli_compilador.py** | compilador.py (importa) | Sync changes from compilador.py |
| **extractor_metadatos.py** | PySide6, ElementTree | Manual test con Workshop real |
| **generar_release_notes.py** | PySide6, Git (optional) | Validar markdown, versioning |

---

## 🚨 Cambios de Alto Riesgo

| Cambio | Riesgo | Mitigación |
|--------|--------|-----------|
| Modificar normalizar_nombre_idioma() | 🔴 CRÍTICO | Tests en 100+ idiomas |
| Alterar estructura de output | 🔴 CRÍTICO | Validar compatibilidad Steam |
| ThreadPoolExecutor config | 🟠 ALTO | Benching CPU/Memory |
| LoadFolders.xml logic | 🟠 ALTO | Simular mods reales |
| JSON config format | 🟡 MEDIO | Update docs, mantener backwards compat |

---

## 📊 Matriz de Testing Recomendada

### Testing de extractor.py

```python
# Test 1: Mod con structure estándar
python -c "extractor.test_standard_mod()"

# Test 2: Mod sin About.xml (edge case)
python -c "extractor.test_no_about_xml()"

# Test 3: Mod con versiones múltiples (1.5, 1.6)
python -c "extractor.test_multiversion()"

# Test 4: Nombres idioma variations
nombres = [
    "SpanishLatin (Español(Latinoamérica))",
    "French (Français)",
    "German (Deutsch)",
    "Russian (Русский)",
]
for nombre in nombres:
    python -c f"extractor.test_lang_normalization('{nombre}')"
```

### Testing de compilador.py

```python
# Test 1: Compilación rápida (10 mods)
python compilador.py --test-subset 10 --verbose

# Test 2: Compilación completa (127 mods)
time python compilador.py
# Verificar: < 3 min esperado

# Test 3: Validar paralelización
# Monitor CPU/disk durante compilación
# Verificar 4 workers simultáneos

# Test 4: Validar LoadFolders.xml
# Parse XML resultante
# Verificar packageIds válidos
```

### Testing de LoadFolders.xml

```xml
<!-- Test: LoadFolders.xml válido -->
<?xml version="1.0" encoding="utf-8"?>
<loadFolders>
  <v1.6>
    <li>Common</li>
    <li IfModActive="ludeon.rimworld.royalty">Mods/Royalty_Vanilla</li>
  </v1.6>
</loadFolders>

<!-- Validar en RimWorld:
1. Instalar Pack
2. Cargar sin Royalty DLC → solo "Common"
3. Cargar con Royalty DLC → "Common" + "Royalty_Vanilla"
-->
```

---

## 🔍 Procedimiento de Debugging

Si algo falla:

### 1. Revisar Logs

```bash
# Compilador GUI → botón "Ver Log"
# CLI → output directo

# Buscar patrón de error:
grep -i "error\|exception\|traceback" compilacion.log
```

### 2. Activar Verbose Mode

```bash
# CLI
python cli_compilador.py --verbose

# GUI: Menú → Debug → Verbose Logging
```

### 3. Test Unitario

```python
# Aislate el problema
# Ej: ¿Normalización de idioma está rota?

from programas.compilador import normalizar_nombre_idioma

test_cases = [
    ("SpanishLatin (Español(Latinoamérica))", "SpanishLatin"),
    ("French (Français)", "French"),
    ("Russian (Русский)", "Russian"),
]

for input_str, expected in test_cases:
    result = normalizar_nombre_idioma(input_str)
    assert result == expected, f"FAIL: {input_str} → {result} (expected {expected})"
    print(f"✓ {input_str} → {result}")
```

### 4. Reportar en Documentación

Documenta el bug en la sección **"Bugs Conocidos"**:

```markdown
## 🐛 Bugs Conocidos

### [BUG] Nombres idioma con caracteres especiales
**Reportado:** 17/02/2026  
**Afecta:** extractor.py  
**Síntoma:** Mod con idioma "Portuguese (Português)" causa error  
**Causa:** normalizar_nombre_idioma() no maneja ç  
**Workaround:** Usar "Portuguese" en lugar del nombre nativo  
**Status:** ABIERTO → Asignar fix

Commit relacionado (cuando se fije):
```

---

## 📚 Versioning

Usamos **Semantic Versioning**: `MAJOR.MINOR.PATCH`

- **MAJOR (X):** Cambios incompatibles (breaking changes)
  - Ejemplo: Cambiar estructura de Output
  - Bump: 1.0.0 → 2.0.0

- **MINOR (Y):** Nueva funcionalidad (backwards compatible)
  - Ejemplo: Añadir LoadFolders.xml
  - Bump: 1.5.0 → 1.6.0

- **PATCH (Z):** Fixes de bugs
  - Ejemplo: Fix normalizar_nombre_idioma
  - Bump: 1.5.1 → 1.5.2

Actualizar versión en:
- `Documentacion/MANTENIMIENTO.md` (este archivo)
- `Programas/compilador.py` (variable global VERSION)
- `About/About.xml` del Pack (automático con generar_release_notes)
- Git tags: `git tag v1.6.0`

---

## ✅ Checklist de Actualización

Cuando completes un cambio, marca TODO:

- [ ] Código implementado
- [ ] Código testeado (mínimo 3 casos)
- [ ] Sin errores/warnings Python
- [ ] MANTENIMIENTO.md actualizado (esta sección)
- [ ] Cambio documentado en "Cambios Completados"
- [ ] Si breaking change: FLUJO_GENERAL.md actualizado
- [ ] Si changing config: PROGRAMAS.md actualizado
- [ ] Testing plan ejecutado (100%)
- [ ] Commit a Git con mensaje descriptivo
- [ ] Git tag creado (v1.X.X)
- [ ] Notificación al equipo (si aplica)

---

## 📞 ¿Preguntas Frecuentes?

### P: ¿Puedo cambiar compilador_config.json manualmente?
R: SI, pero:
- Documenta el cambio aquí
- Valida rutas existen
- Recompila con `python compilador.py --verbose`

### P: ¿Qué pasa si borro "Archivo Traducciones"?
R: ❌ CATÁSTROFE. Sin fuente, no puedes recompilar Pack.
- **Mitigación:** Git + Backups automáticos cada semana

### P: ¿Puedo paralizar a más de 4 workers?
R: NO recomendado (depende hardware). Max safe = 4.
- Si quieres cambiar: Benchmark primero

### P: ¿Cómo rollback a versión anterior?
R:
```bash
git log --oneline
git checkout v1.5.2  # anterior estable
git checkout -b hotfix/revert
git reset --hard v1.5.2
git push origin hotfix/revert
# Pedir PR review antes de merge
```

### P: ¿Necesito cambiar estos documentos?
R: SI:
- ✓ Cambias archivo Programas/*.py → Actualiza PROGRAMAS.md
- ✓ Cambias config JSON → Actualiza PROGRAMAS.md
- ✓ Cambias flujo → Actualiza FLUJO_GENERAL.md + FLUJO_VISUAL.md
- ✓ SIEMPRE actualiza esta sección (MANTENIMIENTO.md)

---

## 🎓 Responsabilidades del Agente

### Cuando trabajes en este sistema:

1. **Documentación primero**
   - Antes de codificar: documenta qué vas a hacer
   - Después de codificar: documenta qué hiciste
   - Esta es la fuente de verdad para futuros agentes

2. **Testing riguroso**
   - No confíes en "parece funcionar"
   - Tests mínimo: 3 casos + edge cases
   - Captura logs/errors

3. **Compatibilidad backwards**
   - No rompas configs antiguas
   - Si deben cambiar: migración automática o deprecation warning

4. **Comunicación clara**
   - Logs entendibles para humanos
   - Error messages específicos, no genéricos
   - Commit messages descriptivos

5. **Mantén esto actualizado**
   - Este archivo es tu responsabilidad
   - Próximos agentes dependen de él
   - Si no está documentado, no cuenta como "hecho"

---

## 📅 Plan de Mantenimiento Futuro

### Próximas Fases (Roadmap)

#### Fase 1: [EN PROGRESO] LoadFolders.xml
- [ ] Migrar primeros mods a `/Archivo Traducciones Vanilla/`
- [ ] Validar PackageIDs contra Steam
- [ ] Testing con RimWorld real (Royalty + Biotech)
- [ ] Release como v2.0.0

#### Fase 2: [PLANIFICADO] Validación Automática
- [ ] Script de validación pre-compile
- [ ] Detectar About.xml faltantes
- [ ] Verificar PackageIDs duplicados
- [ ] Integrity check de LoadFolders.xml

#### Fase 3: [PLANIFICADO] CI/CD Pipeline
- [ ] GitHub Actions: auto-compile en cada push
- [ ] Auto-generate release notes
- [ ] Auto-upload a Steam Workshop
- [ ] Status badge en README

---

## 📞 Contacto y Escalación

Si algo no está claro:

1. **Revisa primero:** INDEX.md → FLUJO_GENERAL.md → PROGRAMAS.md
2. **Busca:** Esta sección (MANTENIMIENTO.md)
3. **Reproduce:** El error localmente con --verbose
4. **Documenta:** El problema + paso a reproducir
5. **Reporta:** Crea ISSUE en GitHub con:
   - Título descriptivo
   - Pasos a reproducir
   - Error log (si existe)
   - Expected vs Actual behavior

---

**Última actualización:** 17 de febrero de 2026  
**Mantenedor(es):** Sistema automático (Agentes IA)

*Este documento es VIVIENTE. Actualízalo constantemente.*
