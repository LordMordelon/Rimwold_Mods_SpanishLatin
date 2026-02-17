# Archivo Traducciones Vanilla

## 📌 Propósito

Esta carpeta contiene traducciones que **modifican contenido del juego base (Vanilla)** de RimWorld. Estos archivos se cargan **condicionalmente** solo si el mod que altera Vanilla está instalado en el usuario.

## 🏗️ Estructura

```
Archivo Traducciones Vanilla/
├── Mod_Name_Vanilla_Patches/
│   ├── About/
│   │   └── About.xml                    ← Metadatos (packageId CRÍTICO)
│   │
│   └── SpanishLatin (Español(Latinoamérica))/
│       ├── DefInjected/
│       │   ├── ThingDef/
│       │   │   └── [Mod_Name]_ThingDef.xml
│       │   └── ... (otras Defs)
│       │
│       └── Keyed/
│           └── [Mod_Name]_Keys.xml
│
└── Another_Mod_Vanilla_Patches/
    ├── About/
    │   └── About.xml                    ← Metadatos (packageId CRÍTICO)
    │
    └── SpanishLatin (Español(Latinoamérica))/
        └── ... (estructura igual)
```

## 📝 Nominación de Carpetas

**Formato:** `ModName_Vanilla_Patches`

Ejemplos:
- `Royalty_Vanilla_Patches` ← para "Ludeon.RimWorld.Royalty"
- `VFE_Core_Vanilla_Patches` ← para "OskarPotocki.VanillaFactionsExpanded.Core"
- `EPOE_Vanilla_Patches` ← para "vanya.tools.expandedprostheticsandorganengineering"

## ⚠️ About.xml Requerido

Cada carpeta **DEBE** tener un `About/About.xml` con el PackageID **exacto** del mod original:

```xml
<?xml version="1.0" encoding="utf-8"?>
<ModMetaData>
  <name>Royalty Vanilla Patches (Spanish)</name>
  <author>Tu nombre</author>
  <packageId>ludeon.rimworld.royalty</packageId>
  <description>Traducciones de contenido Vanilla modificado por Royalty</description>
  <supportedVersions>
    <li>1.6</li>
  </supportedVersions>
</ModMetaData>
```

**❗ CRÍTICO:** El `packageId` debe ser **exactamente igual** al del mod original (sin "_vanilla_patches" o variantes).

## 🔗 Integración con LoadFolders.xml

El compilador lee estos About.xml y **automáticamente** genera líneas en `LoadFolders.xml`:

```xml
<li IfModActive="ludeon.rimworld.royalty">Mods/Royalty_Vanilla_Patches</li>
```

## ✅ Validación Antes de Compilar

Antes de compilar:
- [ ] Cada carpeta tiene `About/About.xml`
- [ ] PackageID en About.xml = PackageID mod original
- [ ] Carpeta tiene `SpanishLatin (Español(Latinoamérica))/`
- [ ] Archivos XML están dentro de `DefInjected/` o `Keyed/`
- [ ] Nombres de archivo usan prefijo `[ModName]_`

## 📌 Notas

- **NO mezcles** contenido normal de mods con Vanilla patches
  - Si el mod añade contenido nuevo → `Archivo Traducciones/`
  - Si solo altera Vanilla → `Archivo Traducciones Vanilla/`
  - Si hace ambas → crear DEUX carpetas

- El compilador procesa **ambas** carpetas al mismo tiempo
- Los PackageIDs de Vanilla patches se detectan automáticamente
- LoadFolders.xml se genera solo (no editar manualmente)

---

**Última actualización:** 17 de febrero de 2026
