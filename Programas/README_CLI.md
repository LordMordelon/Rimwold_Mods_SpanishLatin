# Sistema de Compilación de Traducciones - Guía Rápida

## 🎯 Resumen del Sistema

El CLI ahora soporta **dos tipos de traducciones**:

1. **Traducciones Normales** (`Archivo Traducciones/`)
   - Contenido NUEVO que los mods añaden al juego
   - Se copian a: `Common/Languages/SpanishLatin/`

2. **Traducciones Vanilla** (`Archivo Traducciones Vanilla/`)
   - Modificaciones al contenido BASE de RimWorld
   - Se copian a: `Mods/Nombre_Mod/Languages/SpanishLatin/`
   - Se activan SOLO si el mod está instalado (via LoadFolders.xml)

---

## 📁 Estructura Esperada

```
Proyecto/
├── Archivo Traducciones/
│   ├── Vanilla Gravship Expanded - Chapter 1/  ← Contenido nuevo del mod
│   ├── Achtung!/
│   └── ... (100+ mods)
│
└── Archivo Traducciones Vanilla/
    ├── Vanilla Gravship Expanded - Chapter 1/  ← Cambios a Vanilla
    │   ├── About/
    │   │   └── About.xml                       ← packageId CRÍTICO
    │   └── SpanishLatin (Español...)/
    │       ├── DefInjected/
    │       └── Keyed/
    └── ... (otros mods que alteran Vanilla)
```

---

## 🚀 Uso del CLI

### Comando Básico

```bash
python cli_compilador.py \
  --origen "C:/Users/amaro/Desktop/Proyecto/Archivo Traducciones" \
  --destino "C:/Program Files (x86)/Steam/steamapps/common/RimWorld/Mods/Pack Traducciones [Español Latino]" \
  --limpiar-destino \
  --eliminar-comentarios
```

### Con Idioma Específico

```bash
python cli_compilador.py \
  --origen "C:/Users/amaro/Desktop/Proyecto/Archivo Traducciones" \
  --destino "C:/RimWorld/Mods/Pack Traducciones [ES]" \
  --idioma "SpanishLatin (Español(Latinoamérica))" \
  --limpiar-destino \
  --eliminar-comentarios
```

---

## 📤 Output Generado

```
Pack Traducciones [Español Latino]/
│
├── About/
│   └── About.xml                    ← Metadata del pack
│
├── Common/                          ⭐ NUEVO
│   └── Languages/
│       └── SpanishLatin/
│           ├── DefInjected/          ← Mods normales (100+)
│           └── Keyed/
│
├── Mods/                            ⭐ NUEVO
│   └── Vanilla_Gravship_Expanded_-_Chapter_1/
│       └── Languages/
│           └── SpanishLatin/
│               ├── DefInjected/      ← Solo cambios a Vanilla
│               └── Keyed/
│
└── LoadFolders.xml                  ⭐ NUEVO
    ```xml
    <loadFolders>
      <v1.6>
        <li>Common</li>
        <li IfModActive="epicduck.rimworld.vanillgravship">
          Mods/Vanilla_Gravship_Expanded_-_Chapter_1
        </li>
      </v1.6>
    </loadFolders>
    ```
```

---

## 🔄 Flujo de Compilación

```
[1/4] Procesando traducciones normales desde: Archivo Traducciones
  → Mods procesados: 127
  → Archivos copiados: 3,847

[2/4] Procesando parches Vanilla desde: Archivo Traducciones Vanilla
  → Mods Vanilla procesados: 1
  → Archivos copiados: 45

[3/4] Reorganizando estructura a Common/
  → Contenido movido a Common/Languages/

[4/4] Generando LoadFolders.xml
  → LoadFolders.xml generado con 1 entradas condicionales

════════════════════════════════════════════════════════════
RESUMEN:
  Total mods normales: 127
  Total mods Vanilla: 1
  Total archivos copiados: 3,892
  Errores: 0
════════════════════════════════════════════════════════════
```

---

## ⚙️ Opciones del CLI

| Opción | Descripción | Recomendado |
|--------|-------------|-------------|
| `--origen` | Ruta a "Archivo Traducciones" | ✅ Requerido |
| `--destino` | Ruta al Pack final | ✅ Requerido |
| `--idioma` | Carpeta idioma (auto-detect si solo 1) | 🟡 Opcional |
| `--limpiar-destino` | Borra Pack anterior antes de compilar | ✅ Sí |
| `--eliminar-comentarios` | Quita comentarios XML, reduce tamaño | ✅ Sí |
| `--comprimir` | Crea .tar del resultado | ❌ No (deprecated) |
| `--update-about` | Actualiza About.xml con forceLoadAfter | 🟡 Opcional |
| `--reporte` | Genera reporte de mods procesados | ✅ Sí (default) |
| `--sin-reporte` | NO generar reporte | ❌ No |

---

## 🐛 Troubleshooting

### Error: "No se encontró packageId en [Mod], se omitirá en LoadFolders.xml"

**Causa:** El mod en `Archivo Traducciones Vanilla` no tiene `About/About.xml` o el packageId está vacío.

**Solución:**
1. Verifica que existe: `Archivo Traducciones Vanilla/ModName/About/About.xml`
2. Abre el XML y confirma que tiene:
   ```xml
   <packageId>ejemplo.packageid.aqui</packageId>
   ```
3. El packageId debe ser EXACTO al del mod original (busca en Steam Workshop)

---

### Error: "Origen no válido"

**Causa:** La ruta a "Archivo Traducciones" no existe.

**Solución:**
```bash
# Windows
--origen "C:/Users/amaro/Desktop/Proyecto/Archivo Traducciones"

# Nota: Usar / en lugar de \
```

---

### Warning: "No se encontró carpeta 'Archivo Traducciones Vanilla'"

**Causa:** Es normal si no tienes mods que alteren Vanilla.

**Solución:** 
- Si NO necesitas parches Vanilla → ignora este mensaje
- Si SÍ necesitas parches → crea la carpeta: `Archivo Traducciones Vanilla/`

---

## 📋 Checklist Pre-Compilación

Antes de ejecutar el CLI:

- [ ] `Archivo Traducciones/` existe con mods
- [ ] Si usas Vanilla patches: `Archivo Traducciones Vanilla/` existe
- [ ] Cada mod Vanilla tiene `About/About.xml` con packageId
- [ ] PackageID es exacto al mod original (sin variaciones)
- [ ] Ruta destino tiene permisos de escritura
- [ ] Si `--limpiar-destino`: tienes backup del Pack anterior

---

## 🎓 Ejemplo Completo

```bash
# 1. Navegar al directorio de programas
cd "c:\Users\amaro\Desktop\Proyecto\Programas"

# 2. Ejecutar compilación
python cli_compilador.py \
  --origen "C:/Users/amaro/Desktop/Proyecto/Archivo Traducciones" \
  --destino "C:/Program Files (x86)/Steam/steamapps/common/RimWorld/Mods/Pack Traducciones [Español Latino]" \
  --idioma "SpanishLatin (Español(Latinoamérica))" \
  --limpiar-destino \
  --eliminar-comentarios \
  --update-about

# 3. Verificar output
# → Revisa que exista: Pack/.../Common/
# → Revisa que exista: Pack/.../Mods/ (si hay Vanilla patches)
# → Revisa que exista: Pack/.../LoadFolders.xml
```

---

## 🔗 Referencias

- **Documentación completa:** [Documentacion/INDEX.md](../Documentacion/INDEX.md)
- **Flujo del sistema:** [Documentacion/FLUJO_GENERAL.md](../Documentacion/FLUJO_GENERAL.md)
- **Detalles técnicos:** [Documentacion/PROGRAMAS.md](../Documentacion/PROGRAMAS.md)
- **Mantenimiento:** [Documentacion/MANTENIMIENTO.md](../Documentacion/MANTENIMIENTO.md)

---

**Última actualización:** 17 de febrero de 2026  
**Versión:** 2.0.0
