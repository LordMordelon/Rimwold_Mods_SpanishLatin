@echo off
REM ============================================================
REM Script de Compilacion - Pack Traducciones [Español Latino]
REM Versión: 2.0.0
REM ============================================================

echo.
echo ============================================================
echo   COMPILADOR DE TRADUCCIONES RIMWORLD
echo   Version 2.0.0 - Soporte Vanilla Patches
echo ============================================================
echo.

REM Configuración de rutas
set ORIGEN=C:/Users/amaro/Desktop/Proyecto/Archivo Traducciones
set DESTINO=C:/Program Files (x86)/Steam/steamapps/common/RimWorld/Mods/Pack Traducciones [Español Latino]
set IDIOMA=SpanishLatin (Español(Latinoamérica))

echo [CONFIG] Origen:  %ORIGEN%
echo [CONFIG] Destino: %DESTINO%
echo [CONFIG] Idioma:  %IDIOMA%
echo.

REM Preguntar confirmación
set /p CONFIRMAR="¿Iniciar compilacion? (S/N): "
if /i not "%CONFIRMAR%"=="S" (
    echo Compilacion cancelada.
    pause
    exit /b
)

echo.
echo [START] Iniciando compilacion...
echo.

REM Ejecutar CLI con opciones recomendadas
python cli_compilador.py ^
  --origen "%ORIGEN%" ^
  --destino "%DESTINO%" ^
  --idioma "%IDIOMA%" ^
  --limpiar-destino ^
  --eliminar-comentarios ^
  --update-about

REM Verificar resultado
if %ERRORLEVEL% equ 0 (
    echo.
    echo ============================================================
    echo   COMPILACION EXITOSA
    echo ============================================================
    echo.
    echo El pack ha sido generado en:
    echo %DESTINO%
    echo.
    echo Estructura generada:
    echo   - Common/Languages/SpanishLatin/  ^(Mods normales^)
    echo   - Mods/^<NombreMod^>/              ^(Parches Vanilla^)
    echo   - LoadFolders.xml                 ^(Carga condicional^)
    echo.
) else (
    echo.
    echo ============================================================
    echo   ERROR EN COMPILACION
    echo ============================================================
    echo.
    echo Codigo de error: %ERRORLEVEL%
    echo Revisa los mensajes anteriores para mas detalles.
    echo.
)

pause
