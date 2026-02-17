# Archivo Traducciones Vanilla

## 📌 Propósito

Esta carpeta contiene traducciones que **modifican contenido del juego base (Vanilla)** de RimWorld. Estos archivos se cargan **condicionalmente** solo si el mod que altera Vanilla está instalado en el usuario.

## 🏗️ Estructura

```
Archivo Traducciones Vanilla/
├── Vanilla Gravship Expanded - Chapter 1/   ← Nombre original (con espacios)
│   ├── About/
│   │   ├── About_3609835606.xml             ← packageId CRÍTICO
│   │   └── PublishedFileId.txt
│   │
│   └── SpanishLatin (Español(Latinoamérica))/
│       ├── DefInjected/
│       │   └── ... (archivos que modifican Vanilla)
│       │
│       └── Keyed/
│           └── ... (keys que modifican Vanilla)
│
└── Otro Mod Ejemplo/
    ├── About/
    │   └── About.xml                        ← packageId CRÍTICO
    │
    └── SpanishLatin (Español(Latinoamérica))/
        └── ... (estructura igual)
```

## 📝 Nominación de Carpetas

**IMPORTANTE:** Usa el **nombre exacto** del mod tal como aparece en `Archivo Traducciones/`

El compilador automáticamente convertirá espacios a underscores al generar el Pack final.

Ejemplos:
- `Vanilla Gravship Expanded - Chapter 1` → Se convierte a `Vanilla_Gravship_Expanded_-_Chapter_1` en Output
- `Royalty` → Se convierte a `Royalty` en Output
- `VFE Core` → Se convierte a `VFE_Core` en Output

**Recomendación:** Copia textualmente la carpeta del mod desde `Archivo Traducciones/` manteniendo su nombre original.

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

**Input:** `Vanilla Gravship Expanded - Chapter 1/` con packageId `vanillaexpanded.gravship`

**Output generado:**
```xml
<li IfModActive="vanillaexpanded.gravship">
  Mods/Vanilla_Gravship_Expanded_-_Chapter_1
</li>
```

**Nota:** Los espacios y caracteres especiales del nombre se convierten a underscores automáticamente.

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
