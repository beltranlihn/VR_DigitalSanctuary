<#
    quest_perfmodes.ps1 - BANCO DE MEDICION del material de blobs (estacion Attracting).

    QUE RESUELVE. Medir dos builds en dos sesiones distintas NO sirve: el 2026-09-25 el
    MISMO build sin optimizar dio 21,65 y 24,85 ms (~15% de ruido). La causa es el
    protocolo: en una escena fill-rate bound manda cuanta pantalla cubren las gotas, o sea
    hacia donde mirabas. Aca las N fases corren en UNA sola sesion, alternando el modo del
    material por consola, asi que comparten escena, pose y estado termico. Gotcha 379.

    COMO FUNCIONA. El material M_SlotChain_SC lee PerfMode de la coleccion MPC_Perf_SC.
    BP_PerfSwitch_SC (actor PerfSwitch en TestMeshes) tiene los eventos Perf0..Perf3 que
    escriben esa coleccion. Se disparan por consola con "ke * PerfN" ("ke" = KismetEvent,
    vive en UEngine::Exec_Dev bajo #if !UE_BUILD_SHIPPING -> funciona en Development).

    LOS MODOS
      0  actual        el material tal como esta autorado. Es la referencia.
      1  steps/2       la mitad de pasos de raymarch.
      2  sdf lisa      sin wobble ni decoracion (raymarch mas barato).
      3  gratis        el material sale al instante sin dibujar. Es el PISO.

    LA CUENTA QUE DECIDE:  (modo 0) - (modo 3) = lo que cuesta TODA la tecnica de blobs.
    Si ese numero es chico, el problema no son los blobs y hay que buscar en otro lado.
    Si es grande, dice exactamente cuanto presupuesto libera cambiar de tecnica.

    Dos trampas de PowerShell 5.1 que este archivo esquiva (igual que sus hermanos):
      1. NADA de $ErrorActionPreference='Stop' con exes nativos: adb escribe cosas
         inocuas en stderr y PS 5.1 las convierte en error terminante.
      2. Archivo en ASCII puro: PS 5.1 lee los .ps1 como ANSI y un acento rompe el parser.

    Uso:  .\quest_perfmodes.ps1
          .\quest_perfmodes.ps1 -Seconds 20
#>
param(
    [string]$Package = 'com.almadigital.TESTMESHES',
    [string]$Project = 'VR_Test',
    [int]$Seconds = 20,
    [int]$Delay = 25,
    [string]$OutDir = ''
)

$ErrorActionPreference = 'Continue'

# .../.claude/skills/unreal-vr/scripts/x.ps1 -> 5 niveles hasta la raiz del repo.
$repo = $PSCommandPath
1..5 | ForEach-Object { $repo = Split-Path $repo -Parent }
if (-not $OutDir) { $OutDir = Join-Path $repo 'perf' }

$adb = Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe'
if (-not (Test-Path $adb)) { Write-Host "ERROR: no encuentro adb en $adb" -ForegroundColor Red; exit 1 }

$savedDir = "/sdcard/Android/data/$Package/files/UnrealGame/$Project/$Project/Saved"
$csvDir = "$savedDir/Profiling/CSV"

function Adb { & $adb @args 2>&1 | Out-String }
function Send-Cmd([string]$c) { Adb shell "am broadcast -a android.intent.action.RUN -e cmd '$c'" | Out-Null }
function Say([string]$t, [string]$c = 'Yellow') { Write-Host $t -ForegroundColor $c }

# El CsvProfiler nombra los archivos Profile(2026...).csv y esos PARENTESIS rompen el pull.
function Renombrar-Ultimo([string]$destino) {
    $todos = @((Adb shell "ls -t $csvDir") -split "`n" | ForEach-Object { $_.Trim() } |
        Where-Object { $_ -match '\.csv$' -and $_ -notmatch '^modo' })
    if (-not $todos) { return $false }
    Adb shell "mv '$csvDir/$($todos[0])' '$csvDir/$destino'" | Out-Null
    return $true
}

# --- las fases. Se corren DOS VECES en orden inverso la segunda vuelta, para que una
#     deriva termica progresiva no se le cargue toda a la ultima fase. -----------------
$modos = @(
    @{ n = 'modo0_actual'; ev = 'Perf0' },
    @{ n = 'modo1_steps';  ev = 'Perf1' },
    @{ n = 'modo2_lisa';   ev = 'Perf2' },
    @{ n = 'modo3_gratis'; ev = 'Perf3' }
)
$orden = @($modos[0], $modos[1], $modos[2], $modos[3], $modos[3], $modos[2], $modos[1], $modos[0])

if ((Adb devices) -notmatch "`tdevice") { Say 'ERROR: no hay ninguna Quest conectada.' 'Red'; exit 1 }

Say 'Reiniciando la app para partir limpio...' 'Gray'
Adb shell "am force-stop $Package" | Out-Null
Adb shell "rm -rf $csvDir" | Out-Null
Start-Sleep -Seconds 2
Adb shell "am start -n $Package/com.epicgames.unreal.GameActivity" | Out-Null

$vivo = $false
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Seconds 1
    if ((Adb shell "pidof $Package").Trim()) { $vivo = $true; break }
}
if (-not $vivo) { Say 'ERROR: la app no arranco. Abrila a mano desde la biblioteca.' 'Red'; exit 1 }
Say "App viva (tardo $i s). Esperando que cargue la estacion..." 'Gray'
Start-Sleep -Seconds 10

# Control POSITIVO: si "ke" no llega al Blueprint, todo lo demas mide cualquier cosa.
Say 'Probando que el comando ke llegue al Blueprint...' 'Gray'
Adb logcat -c | Out-Null
Send-Cmd 'ke * Perf3'
Start-Sleep -Seconds 2
$eco = (Adb logcat -d) -split "`n" | Select-String -Pattern 'PERF: modo 3'
if (-not $eco) {
    Say 'ERROR: el comando ke NO llego al Blueprint (no aparece "PERF: modo 3" en el log).' 'Red'
    Say 'Sin eso las fases no cambian nada y la medicion seria basura. Abortando.' 'Red'
    exit 1
}
Say '  OK: el Blueprint responde.' 'Green'
Send-Cmd 'ke * Perf0'

Send-Cmd 'r.GPUStatsEnabled 1'
Send-Cmd 'r.GPUCsvStatsEnabled 1'

$total = $Delay + ($Seconds * $orden.Count) + ($orden.Count * 6)
Write-Host ''
Say "PONETE EL VISOR AHORA. Arranco en $Delay segundos."
Say "Son unos $total segundos con el casco puesto, en $($orden.Count) fases de $Seconds s."
Say 'IMPORTANTE: jugá PARECIDO todo el tiempo (agarrá esferas, colocalas, mirá la fila'
Say 'de gotas). Lo que se compara entre fases es el mismo tipo de vista.'
Say 'En algunas fases las gotas se van a ver distintas o directamente NO se van a ver:'
Say 'es a proposito, es la medicion.'
for ($t = $Delay; $t -gt 0; $t--) {
    if ($t -le 5 -or $t % 5 -eq 0) { Write-Host "   $t..." }
    Start-Sleep -Seconds 1
}

$k = 0
foreach ($f in $orden) {
    $k++
    $etiqueta = "$($f.n)_p$k"
    Send-Cmd "ke * $($f.ev)"
    Start-Sleep -Seconds 2
    Say ">>> fase $k/$($orden.Count): $($f.n) - $Seconds s" 'Green'
    Send-Cmd 'CsvProfile Start'
    Start-Sleep -Seconds $Seconds
    Send-Cmd 'CsvProfile Stop'
    Start-Sleep -Seconds 4
    if (-not (Renombrar-Ultimo "$etiqueta.csv")) { Say "  AVISO: la fase $k no dejo CSV." 'Red' }
}

Send-Cmd 'ke * Perf0'
Say 'LISTO. Sacate el visor. (El material vuelve al modo 0.)' 'Cyan'

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$k = 0
foreach ($f in $orden) {
    $k++
    $etiqueta = "$($f.n)_p$k"
    $destino = Join-Path $OutDir "$etiqueta.csv"
    if (Test-Path $destino) { Remove-Item $destino -Force }
    Adb pull "$csvDir/$etiqueta.csv" $destino | Out-Null
    if (Test-Path $destino) { Write-Host ("  $etiqueta.csv  (" + [int]((Get-Item $destino).Length / 1KB) + " KB)") }
    else { Say "  FALLO al traer $etiqueta.csv" 'Red' }
}

Write-Host ''
Say 'Listo. Resumilo con:' 'Gray'
Write-Host "  python `"$repo\.claude\skills\unreal-vr\scripts\resumen_modos.py`" `"$OutDir`""
