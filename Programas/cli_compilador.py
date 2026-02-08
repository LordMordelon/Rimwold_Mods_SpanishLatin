import argparse
import os
import re
import shutil
import sys
import traceback
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError


def normalizar_nombre_idioma(nombre: str) -> str:
    if not isinstance(nombre, str):
        return ""
    nombre = nombre.strip()
    corte = nombre.find(" (")
    if corte != -1:
        return nombre[:corte].strip()
    s = nombre
    while True:
        open_idx = s.rfind("(")
        close_idx = s.rfind(")")
        if open_idx != -1 and close_idx != -1 and close_idx > open_idx:
            s = s[:open_idx].rstrip()
        else:
            break
    return s.strip()


def indent_xml(elem, level=0, space="  "):
    i = "\n" + level * space
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + space
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            indent_xml(subelem, level + 1, space)
        if not subelem.tail or not subelem.tail.strip():
            subelem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def detectar_idiomas(origen: str):
    idiomas_encontrados = set()
    carpetas_a_ignorar = {
        "about", "defs", "assemblies", "patches", "textures", "sounds", "common",
        "ideasshared", "licenses", "source", "src", "docs", "examples", ".git",
        ".vs", "1.0", "1.1", "1.2", "1.3", "1.4", "1.5"
    }

    for mod_folder in os.listdir(origen):
        ruta_mod = os.path.join(origen, mod_folder)
        if not os.path.isdir(ruta_mod):
            continue
        try:
            for subfolder in os.listdir(ruta_mod):
                ruta_subfolder = os.path.join(ruta_mod, subfolder)
                if os.path.isdir(ruta_subfolder) and subfolder.lower() not in carpetas_a_ignorar:
                    idiomas_encontrados.add(subfolder)
        except OSError:
            continue

    return sorted(idiomas_encontrados)


def obtener_package_id(ruta_mod: str):
    about_dir = os.path.join(ruta_mod, "About")
    if not os.path.isdir(about_dir):
        return None

    candidatos = [
        f for f in os.listdir(about_dir)
        if f.lower().startswith("about") and f.lower().endswith(".xml")
    ]
    candidatos.sort(key=len)

    for nombre in candidatos:
        ruta = os.path.join(about_dir, nombre)
        try:
            tree = ET.parse(ruta)
            root = tree.getroot()
            pid = root.find("packageId")
            if pid is not None and pid.text:
                return pid.text.strip().lower()
        except Exception:
            continue

    return None


def copiar_traducciones(origen, destino_root, nombre_subcarpeta, limpiar_destino, eliminar_comentarios):
    destino_languages = os.path.join(destino_root, "Languages")
    os.makedirs(destino_languages, exist_ok=True)

    nombre_destino = normalizar_nombre_idioma(nombre_subcarpeta)
    ruta_destino_subcarpeta = os.path.join(destino_languages, nombre_destino)

    if limpiar_destino and os.path.isdir(ruta_destino_subcarpeta):
        shutil.rmtree(ruta_destino_subcarpeta)

    mods_a_procesar = [
        d for d in os.listdir(origen)
        if os.path.isdir(os.path.join(origen, d, nombre_subcarpeta))
    ]

    if not mods_a_procesar:
        return [], 0, []

    archivos_copiados = 0
    errores = []

    for mod in mods_a_procesar:
        ruta_mod = os.path.join(origen, mod)
        ruta_idioma = os.path.join(ruta_mod, nombre_subcarpeta)

        archivos_del_mod = []
        for carpeta_raiz, _, archivos in os.walk(ruta_idioma):
            for archivo in archivos:
                if archivo.endswith(".xml"):
                    archivos_del_mod.append((carpeta_raiz, archivo))

        for carpeta_raiz, archivo in archivos_del_mod:
            ruta_origen = os.path.join(carpeta_raiz, archivo)
            ruta_relativa = os.path.relpath(carpeta_raiz, ruta_idioma)
            ruta_destino_base = os.path.join(destino_languages, nombre_destino)
            ruta_destino_carpeta = os.path.join(ruta_destino_base, ruta_relativa)
            os.makedirs(ruta_destino_carpeta, exist_ok=True)
            nuevo_nombre = f"[{mod}]_{os.path.splitext(archivo)[0]}.xml"
            ruta_destino_archivo = os.path.join(ruta_destino_carpeta, nuevo_nombre)

            if eliminar_comentarios:
                try:
                    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=False))
                    with open(ruta_origen, "rb") as f:
                        raw_data = f.read()

                    try:
                        content = raw_data.decode("utf-8-sig")
                    except UnicodeDecodeError:
                        content = raw_data.decode("utf-16")

                    content = content.strip()
                    if content.startswith("<?xml"):
                        content = content.split("?>", 1)[-1].strip()

                    content = re.sub(
                        r"<(/?(?:color|size|b|i)(?:\s+[^>]*?)?)>",
                        r"&lt;\1&gt;",
                        content,
                        flags=re.IGNORECASE,
                    )

                    root = ET.fromstring(content, parser=parser)
                    tree = ET.ElementTree(root)
                    root[:] = sorted(root, key=lambda child: child.tag)
                    indent_xml(root)
                    tree.write(ruta_destino_archivo, encoding="utf-8", xml_declaration=True)
                except ParseError as e:
                    errores.append({
                        "archivo": ruta_origen,
                        "motivo": f"XML invalido: {e}",
                        "trace": traceback.format_exc(),
                    })
                    shutil.copy2(ruta_origen, ruta_destino_archivo)
                except Exception as e:
                    errores.append({
                        "archivo": ruta_origen,
                        "motivo": f"Error procesando XML: {e}",
                        "trace": traceback.format_exc(),
                    })
                    shutil.copy2(ruta_origen, ruta_destino_archivo)
            else:
                try:
                    shutil.copy2(ruta_origen, ruta_destino_archivo)
                except Exception as e:
                    errores.append({
                        "archivo": ruta_origen,
                        "motivo": f"Error copiando archivo: {e}",
                        "trace": traceback.format_exc(),
                    })
                    continue

            archivos_copiados += 1

    return mods_a_procesar, archivos_copiados, errores


def actualizar_about_xml(destino_root, origen, mods_procesados):
    rutas_posibles = [
        os.path.join(destino_root, "About", "about.xml"),
        os.path.join(destino_root, "About", "About.xml"),
        os.path.join(os.path.dirname(destino_root), "About", "about.xml"),
        os.path.join(os.path.dirname(destino_root), "About", "About.xml"),
    ]

    ruta_about = None
    for r in rutas_posibles:
        if os.path.isfile(r):
            ruta_about = r
            break

    if not ruta_about:
        return False, "No se encontro About/about.xml (o About/About.xml) para actualizar."

    tree = ET.parse(ruta_about)
    root = tree.getroot()

    force_load = root.find("forceLoadAfter")
    if force_load is None:
        force_load = ET.SubElement(root, "forceLoadAfter")

    force_load.clear()

    ids_mods = []
    for mod_name in mods_procesados:
        ruta_mod = os.path.join(origen, mod_name)
        pid = obtener_package_id(ruta_mod)

        has_published_id = False
        for p in [
            os.path.join(ruta_mod, "PublishedFileId.txt"),
            os.path.join(ruta_mod, "About", "PublishedFileId.txt"),
        ]:
            if os.path.isfile(p):
                has_published_id = True
                break

        if pid and has_published_id:
            ids_mods.append(pid)

    ids_mods = sorted(list(set(ids_mods)))

    for pid in ids_mods:
        li = ET.SubElement(force_load, "li")
        li.text = pid

    indent_xml(root)
    tree.write(ruta_about, encoding="utf-8", xml_declaration=True)

    return True, f"About.xml actualizado con {len(ids_mods)} entradas."


def comprimir_resultado(destino_root, nombre_subcarpeta):
    destino_languages = os.path.join(destino_root, "Languages")
    nombre_destino = normalizar_nombre_idioma(nombre_subcarpeta)
    ruta_carpeta_origen = os.path.join(destino_languages, nombre_destino)

    if not os.path.isdir(ruta_carpeta_origen):
        return False, f"La carpeta a comprimir no existe: {ruta_carpeta_origen}"

    nombre_archivo_salida = os.path.join(destino_languages, nombre_destino)
    archivo_comprimido = shutil.make_archive(
        base_name=nombre_archivo_salida,
        format="tar",
        root_dir=destino_languages,
        base_dir=nombre_destino,
    )

    shutil.rmtree(ruta_carpeta_origen)

    return True, archivo_comprimido


def generar_reporte(destino_root, mods_procesados, errores=None, titulo="Reporte de Mods Procesados"):
    if not mods_procesados:
        return False, "No hay mods procesados para generar reporte."

    errores = errores or []

    ruta_reportes = os.path.join(destino_root, "Reportes")
    os.makedirs(ruta_reportes, exist_ok=True)

    nombre_archivo = "reporte_mods.txt"
    ruta_archivo = os.path.join(ruta_reportes, nombre_archivo)

    with open(ruta_archivo, "w", encoding="utf-8") as f:
        f.write(f"{titulo} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total de mods encontrados: {len(mods_procesados)}\n\n")
        f.write("Lista de mods:\n")
        for mod in sorted(mods_procesados):
            f.write(f"- {mod}\n")

        if errores:
            f.write("\n" + "=" * 50 + "\n")
            f.write("Errores de compilacion:\n\n")
            for idx, err in enumerate(errores, start=1):
                f.write(f"{idx}. Archivo: {err.get('archivo', 'N/A')}\n")
                f.write(f"   Motivo: {err.get('motivo', 'N/A')}\n")
                f.write("   Trace:\n")
                f.write(err.get("trace", "") + "\n")

    return True, f"Reporte generado en: {ruta_archivo}"


def generar_reporte_errores(destino_root, errores):
    if not errores:
        return False, "No hay errores para generar reporte."

    ruta_reportes = os.path.join(destino_root, "Reportes")
    os.makedirs(ruta_reportes, exist_ok=True)

    nombre_archivo = "errores_compilacion.txt"
    ruta_archivo = os.path.join(ruta_reportes, nombre_archivo)

    with open(ruta_archivo, "w", encoding="utf-8") as f:
        f.write(f"Errores de compilacion - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")
        for idx, err in enumerate(errores, start=1):
            f.write(f"{idx}. Archivo: {err.get('archivo', 'N/A')}\n")
            f.write(f"   Motivo: {err.get('motivo', 'N/A')}\n")
            f.write("   Trace:\n")
            f.write(err.get("trace", "") + "\n")

    return True, f"Reporte de errores generado en: {ruta_archivo}"


def main():
    parser = argparse.ArgumentParser(description="Compilador CLI de traducciones RimWorld")
    parser.add_argument("--origen", required=True, help="Ruta a 'Archivo Traducciones'")
    parser.add_argument("--destino", required=True, help="Ruta a la carpeta del pack de traducciones")
    parser.add_argument("--idioma", default="", help="Nombre exacto de la carpeta de idioma a procesar")
    parser.add_argument("--limpiar-destino", action="store_true", help="Elimina la carpeta de idioma antes de copiar")
    parser.add_argument("--eliminar-comentarios", action="store_true", help="Elimina comentarios XML y ordena tags")
    parser.add_argument("--comprimir", action="store_true", help="Comprime la carpeta resultante en .tar")
    parser.add_argument("--update-about", action="store_true", help="Actualiza About/about.xml con forceLoadAfter")
    parser.add_argument("--reporte", action="store_true", help="Genera un reporte de mods compilados (default)")
    parser.add_argument("--sin-reporte", action="store_true", help="No generar reporte de mods compilados")
    parser.add_argument("--reporte-titulo", default="Reporte de Mods Procesados", help="Titulo del reporte")

    args = parser.parse_args()

    origen = args.origen
    destino = args.destino

    if not os.path.isdir(origen):
        print(f"Origen no valido: {origen}")
        return 2

    if not os.path.isdir(destino):
        print(f"Destino no valido: {destino}")
        return 2

    idioma = args.idioma.strip()
    if not idioma:
        idiomas = detectar_idiomas(origen)
        if len(idiomas) == 1:
            idioma = idiomas[0]
        else:
            print("No se especifico idioma y se encontraron multiples opciones:")
            for item in idiomas:
                print(f"- {item}")
            return 2

    mods_procesados, archivos_copiados, errores = copiar_traducciones(
        origen,
        destino,
        idioma,
        limpiar_destino=args.limpiar_destino,
        eliminar_comentarios=args.eliminar_comentarios,
    )

    print(f"Mods procesados: {len(mods_procesados)}")
    print(f"Archivos copiados: {archivos_copiados}")
    if errores:
        print(f"Errores detectados: {len(errores)}")

    if archivos_copiados == 0:
        print("No se encontraron archivos XML para copiar.")
        return 1

    if args.update_about:
        ok, mensaje = actualizar_about_xml(destino, origen, mods_procesados)
        if ok:
            print(mensaje)
        else:
            print(f"ADVERTENCIA: {mensaje}")

    if args.comprimir:
        ok, mensaje = comprimir_resultado(destino, idioma)
        print(mensaje)
        if not ok:
            return 1

    if not args.sin_reporte:
        ok, mensaje = generar_reporte(destino, mods_procesados, errores=errores, titulo=args.reporte_titulo)
        print(mensaje)
        if not ok:
            return 1

        if errores:
            ok_err, mensaje_err = generar_reporte_errores(destino, errores)
            print(mensaje_err)
            if not ok_err:
                return 1
        else:
            ruta_errores = os.path.join(destino, "Reportes", "errores_compilacion.txt")
            if os.path.isfile(ruta_errores):
                os.remove(ruta_errores)

    print(f"Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
