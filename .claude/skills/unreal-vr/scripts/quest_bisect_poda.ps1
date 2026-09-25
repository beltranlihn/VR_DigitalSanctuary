<#
    quest_bisect_poda.ps1 - Aisla si el cuelgue lo causa la PODA POR GOTA (A4) del shader.

    EL PROBLEMA. Con el build del 2026-09-25 (tarde) la app se cuelga: imagen congelada,
    sonido avanzando, GPU en 0 de presion, proceso vivo. El log del motor termina en
    ensures de xrLocateHandJointsEXT / XR_ERROR_TIME_INVALID, que son SINTOMA (el rastreo
    de manos recibe un tiempo de display invalido porque el bucle de cuadro ya se paro),
    no causa. Cambiaron dos cosas en ese build: la poda del shader y el evento Perf8.

    POR QUE NO HACE FALTA RECONSTRUIR. El modo 8 apaga la poda EN ESTE MISMO BUILD, asi
    que el A/B se hace por consola dentro de una sola sesion:
      fase 1 = modo 8 (poda APAGADA) -> si aguanta, el codigo viejo esta sano.
      fase 2 = modo 0 (poda ENCENDIDA) -> si se cuelga aca, la poda es la causa.

    EL DETECTOR. No depende de que mires: cada $Probe segundos se dispara el mismo modo
    otra vez y se exige el eco del PrintString en logcat. Si el game thread esta trabado
    el eco no llega. Asi el script dice SOLO cual fase murio y a los cuantos segundos.
    (Es el control positivo de siempre: el print del Blueprint es la prueba de vida.)

    OJO: los primeros segundos de cada arranque corren en modo 0 (lo pone BeginPlay), asi
    que si la poda cuelga al instante se va a ver antes de la fase 1. El script lo aclara.

    Dos trampas de PowerShell 5.1 que este archivo esquiva (igual que sus hermanos):
      1. NADA de $ErrorActionPreference='Stop' con exes nativos.
      2. Archivo en ASCII puro: PS 5.1 lee los .ps1 como ANSI.

    Uso:  .\quest_bisect_poda.ps1
          .\quest_bisect_poda.ps1 -Seconds 90
#>
param(
    [string]$Package = 'com.almadigital.TESTMESHES',
    [int]$Seconds = 75,
    [int]$Probe = 5,
    [int]$Delay = 20,
    # 🔴 2026-09-25: NO LANZAR LA APP POR INTENT. Arrancarla con 'am force-stop' + 'am start'
    # la deja sin una sesion de VR bien establecida y aparece el APP_CMD_LOST_FOCUS ->
    # APP_CMD_PAUSE -> deadlock del camino de suspension de UE en Android (imagen
    # congelada, sonido siguiendo, GPU en 0, proceso vivo). Beltran lo aislo abriendo la
    # app A MANO desde la biblioteca del visor: asi no se cuelga.
    # Por eso el default es ENGANCHARSE a la app que ya corre. -Lanzar la lanza igual.
    [switch]$Lanzar
)

$ErrorActionPreference = 'Continue'

$adb = Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe'
if (-not (Test-Path $adb)) { Write-Host "ERROR: no encuentro adb en $adb" -ForegroundColor Red; exit 1 }

function Adb { & $adb @args 2>&1 | Out-String }
function Say([string]$t, [string]$c = 'Yellow') { Write-Host $t -ForegroundColor $c }

# Dispara el modo y devuelve $true si el Blueprint contesta. Es la prueba de vida.
function Latido([int]$m) {
    Adb logcat -c | Out-Null
    Adb shell "am broadcast -a android.intent.action.RUN -e cmd 'ke * Perf$m'" | Out-Null
    Start-Sleep -Seconds 2
    return [bool]((Adb logcat -d) -split "`n" | Select-String -Pattern "PERF: modo $m")
}

# Corre una fase entera latiendo. Devuelve los segundos que sobrevivio, o -1 si llego al final.
function Fase([int]$m, [string]$etiqueta) {
    Say ""
    Say ">>> FASE: modo $m - $etiqueta  ($Seconds s)" 'Green'
    if (-not (Latido $m)) {
        Say "    el modo $m no contesto ni al entrar: la app ya estaba trabada." 'Red'
        return 0
    }
    $t = 0
    while ($t -lt $Seconds) {
        Start-Sleep -Seconds $Probe
        $t += $Probe
        if (-not (Latido $m)) {
            Say "    SE COLGO a los $t s de esta fase (el Blueprint dejo de contestar)." 'Red'
            return $t
        }
        Write-Host "    vivo a los $t s"
    }
    Say "    sobrevivio los $Seconds s completos." 'Cyan'
    return -1
}

if ((Adb devices) -notmatch "`tdevice") { Say 'ERROR: no hay ninguna Quest conectada.' 'Red'; exit 1 }

Write-Host ''
Say "PONETE EL VISOR AHORA. La app arranca en $Delay segundos."
Say 'Son unos 3 minutos. NO te saques el casco hasta el final.'
Say 'MIRA EL SECUENCIADOR DE FRENTE todo el tiempo: es el caso que cuelga.'
Say 'Si ves que la cadena cambia de forma o le falta un pedazo entre fases, anotalo:'
Say 'eso seria un bug de la poda aparte del cuelgue.'
for ($t = $Delay; $t -gt 0; $t--) {
    if ($t -le 5 -or $t % 5 -eq 0) { Write-Host "   $t..." }
    Start-Sleep -Seconds 1
}

Say ''
if ($Lanzar) {
    Say 'Lanzando la app por intent (OJO: es lo que colgaba, ver la cabecera)...' 'Gray'
    Adb shell "am force-stop $Package" | Out-Null
    Start-Sleep -Seconds 2
    Adb shell "am start -n $Package/com.epicgames.unreal.GameActivity" | Out-Null
} else {
    Say 'Esperando la app que ABRISTE VOS desde la biblioteca del visor...' 'Gray'
}
$vivo = $false
for ($i = 0; $i -lt 90; $i++) {
    if ((Adb shell "pidof $Package").Trim()) { $vivo = $true; break }
    Start-Sleep -Seconds 1
}
if (-not $vivo) {
    Say 'ERROR: la app no esta corriendo. Abrila desde la biblioteca del visor' 'Red'
    Say 'y volve a correr el script (o usa -Lanzar para que la lance el script).' 'Red'
    exit 1
}
Say "App viva. Dale unos segundos a la estacion si recien la abriste." 'Gray'
Start-Sleep -Seconds 5

$r8 = Fase 8 'poda APAGADA (el codigo de siempre)'
$r0 = Fase 0 'poda ENCENDIDA (A4)'

Write-Host ''
Say '=== VEREDICTO ===' 'Cyan'
if ($r8 -ge 0 -and $r0 -lt 0) {
    Say '  Colgo SIN la poda y aguanto CON la poda: el resultado esta al reves de la'
    Say '  hipotesis. La poda no es la causa; mirar que mas trajo el build.' 'Red'
}
elseif ($r8 -lt 0 -and $r0 -ge 0) {
    Say "  La poda APAGADA aguanto y la ENCENDIDA colgo a los $r0 s." 'Red'
    Say '  LA PODA ES LA CAUSA. Se reescribe sin escrituras con indice dinamico'
    Say '  (mascara de bits en vez de compactar el arreglo) o se revierte al backup.'
}
elseif ($r8 -lt 0 -and $r0 -lt 0) {
    Say "  Las dos fases aguantaron los $Seconds s. El cuelgue no se reprodujo:" 'Yellow'
    Say '  hace falta mas tiempo, o depende de algo de la interaccion (sostener una'
    Say '  esfera cerca de la cara, completar una vuelta del secuenciador).' 'Yellow'
}
else {
    Say '  Colgaron las DOS fases. No es la poda: es algo comun a las dos.' 'Red'
}
Write-Host ''
Say "  modo 8 (sin poda):  $(if ($r8 -lt 0) { 'sobrevivio' } else { "colgo a los $r8 s" })" 'Gray'
Say "  modo 0 (con poda):  $(if ($r0 -lt 0) { 'sobrevivio' } else { "colgo a los $r0 s" })" 'Gray'
