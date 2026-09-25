<#
    quest_culpable.ps1 - Cual de los comandos del banco cuelga la app.

    EL HECHO (2026-09-25, aislado por Beltran): la app abierta A MANO desde la biblioteca
    del visor corre sin colgarse. Se cuelga cuando el script empieza a MEDIR FASES:
    imagen congelada, sonido siguiendo, GPU en 0 de presion, proceso vivo, y el log del
    motor termina en ensures de xrLocateHandJointsEXT / XR_ERROR_TIME_INVALID (sintoma de
    que el bucle de cuadro ya se paro, no causa).

    "El script" son cinco comandos distintos. Este los manda DE A UNO y verifica que la
    app siga viva despues de cada uno, asi que el primero que falle es el culpable:
      1. ke * Perf0            (el KismetEvent que cambia el modo)
      2. ke * Perf8            (idem, la rama sin poda)
      3. r.GPUStatsEnabled 1
      4. r.GPUCsvStatsEnabled 1
      5. CsvProfile Start / Stop

    LA PRUEBA DE VIDA. No usa el PrintString del Blueprint, porque si el sospechoso es
    justamente 'ke' el probe se confundiria con lo que se esta probando. Usa el eco de una
    cvar de solo lectura (xr.OpenXRFBFoveationLevel): si el motor contesta, esta vivo.

    REQUISITO: la app tiene que estar YA ABIERTA desde la biblioteca del visor, con el
    casco puesto y el secuenciador a la vista. El script no la lanza (lanzarla por intent
    es lo que causaba el otro cuelgue).

    Dos trampas de PowerShell 5.1 que este archivo esquiva (igual que sus hermanos):
      1. NADA de $ErrorActionPreference='Stop' con exes nativos.
      2. Archivo en ASCII puro: PS 5.1 lee los .ps1 como ANSI.

    Uso:  .\quest_culpable.ps1
#>
param(
    [string]$Package = 'com.almadigital.TESTMESHES',
    [int]$Espera = 6
)

$ErrorActionPreference = 'Continue'

$adb = Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe'
if (-not (Test-Path $adb)) { Write-Host "ERROR: no encuentro adb en $adb" -ForegroundColor Red; exit 1 }

function Adb { & $adb @args 2>&1 | Out-String }
function Say([string]$t, [string]$c = 'Yellow') { Write-Host $t -ForegroundColor $c }
function Cmd([string]$c) { Adb shell "am broadcast -a android.intent.action.RUN -e cmd '$c'" | Out-Null }

# Prueba de vida: el motor contesta el valor de una cvar. No toca Blueprints.
function Vivo {
    Adb logcat -c | Out-Null
    Cmd 'xr.OpenXRFBFoveationLevel'
    Start-Sleep -Seconds 3
    return [bool]((Adb logcat -d) -split "`n" | Select-String -Pattern 'OpenXRFBFoveationLevel = ')
}

if ((Adb devices) -notmatch "`tdevice") { Say 'ERROR: no hay ninguna Quest conectada.' 'Red'; exit 1 }
if (-not (Adb shell "pidof $Package").Trim()) {
    Say 'ERROR: la app no esta corriendo.' 'Red'
    Say 'Abrila desde la biblioteca del visor, ponete el casco, y volve a correr esto.' 'Red'
    exit 1
}

Write-Host ''
Say 'Ponete el visor y mira el secuenciador. Empiezo en 10 segundos.'
Say 'Son unos 2 minutos. Si la imagen se congela, decilo, pero el script lo detecta solo.'
for ($t = 10; $t -gt 0; $t--) { if ($t -le 5 -or $t % 5 -eq 0) { Write-Host "   $t..." }; Start-Sleep -Seconds 1 }

Write-Host ''
Say 'Linea de base: la app tiene que contestar ANTES de tocar nada.' 'Gray'
if (-not (Vivo)) {
    Say 'ERROR: no contesta ni antes de empezar. O ya estaba trabada, o el probe no sirve.' 'Red'
    Say 'Sin una linea de base valida, todo lo que siga no significa nada. Abortando.' 'Red'
    exit 1
}
Say '  contesta. Linea de base OK.' 'Green'

# Cada sospechoso: el comando, y cuanto esperar despues antes de revisar.
$sospechosos = @(
    @{ n = 'ke * Perf0            (KismetEvent, modo con poda)'; c = 'ke * Perf0'; w = $Espera }
    @{ n = 'ke * Perf8            (KismetEvent, modo sin poda)'; c = 'ke * Perf8'; w = $Espera }
    @{ n = 'r.GPUStatsEnabled 1'; c = 'r.GPUStatsEnabled 1'; w = $Espera }
    @{ n = 'r.GPUCsvStatsEnabled 1'; c = 'r.GPUCsvStatsEnabled 1'; w = $Espera }
    @{ n = 'CsvProfile Start'; c = 'CsvProfile Start'; w = 15 }
    @{ n = 'CsvProfile Stop'; c = 'CsvProfile Stop'; w = $Espera }
)

$culpable = $null
foreach ($s in $sospechosos) {
    Write-Host ''
    Say (">>> " + $s.n) 'Cyan'
    Cmd $s.c
    Start-Sleep -Seconds $s.w
    if (Vivo) {
        Say '    sigue viva.' 'Green'
    } else {
        Say '    LA APP DEJO DE CONTESTAR ACA.' 'Red'
        $culpable = $s
        break
    }
}

Write-Host ''
Say '=== VEREDICTO ===' 'Cyan'
if ($culpable) {
    Say ("  El culpable es: " + $culpable.c) 'Red'
    Say '  Ese comando se saca del banco y se busca otra forma de conseguir el dato.'
} else {
    Say '  Los cinco comandos pasaron y la app sigue viva.' 'Green'
    Say '  Entonces no es un comando suelto: es la REPETICION (el banco los alterna cada'
    Say '  20 s durante varios minutos) o el tiempo acumulado. Siguiente paso: dejar'
    Say '  CsvProfile corriendo y alternar modos varias veces hasta reproducirlo.'
}
Write-Host ''
Say ("  pid al terminar: '" + (Adb shell "pidof $Package").Trim() + "'") 'Gray'
