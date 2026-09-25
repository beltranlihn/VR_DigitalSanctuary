<#
    quest_phases.ps1 - graba N fases seguidas en UNA sola sesion con el visor puesto,
    aplicando cvars distintas en cada una. Sirve para comparar palancas de
    performance sin reempaquetar y sin pedir varias pasadas.

    Mismas dos trampas esquivadas que en quest_ab.ps1:
      - NADA de $ErrorActionPreference='Stop' con exes nativos (adb escribe en
        stderr cosas inocuas y PS 5.1 las vuelve error terminante).
      - Archivo en ASCII puro (PS 5.1 lee los .ps1 como ANSI).
    Y una tercera, que costo una corrida: el CsvProfiler nombra los archivos
    Profile(2026...).csv y esos PARENTESIS rompen el pull -> se renombran en el
    device antes de traerlos.

    Uso:  .\quest_phases.ps1
          .\quest_phases.ps1 -Seconds 20
#>
param(
    [string]$Package = 'com.almadigital.TESTMESHES',
    [string]$Project = 'VR_Test',
    [int]$Seconds = 15,
    [int]$Delay = 20,
    [string]$OutDir = ''
)

$ErrorActionPreference = 'Continue'

# .../.claude/skills/unreal-vr/scripts/quest_phases.ps1 -> 5 niveles hasta la raiz.
# (La version anterior contaba 4 y dejaba los CSV en .claude\perf.)
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

# --- las fases -------------------------------------------------------------
# etiqueta -> cvars que la definen. La primera es la linea de base.
$fases = @(
    @{ n = 'base';      cmds = @('xr.VRS.FoveationLevel 0', 'xr.SecondaryScreenPercentage.HMDRenderTarget 100') },
    @{ n = 'vrs3';      cmds = @('xr.VRS.FoveationLevel 3', 'xr.SecondaryScreenPercentage.HMDRenderTarget 100') },
    @{ n = 'res85';     cmds = @('xr.VRS.FoveationLevel 0', 'xr.SecondaryScreenPercentage.HMDRenderTarget 85') },
    @{ n = 'vrs3res85'; cmds = @('xr.VRS.FoveationLevel 3', 'xr.SecondaryScreenPercentage.HMDRenderTarget 85') }
)

if ((Adb devices) -notmatch "`tdevice") { Say 'ERROR: no hay Quest conectada.' 'Red'; exit 1 }

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
if (-not $vivo) { Say 'ERROR: la app no arranco.' 'Red'; exit 1 }
Start-Sleep -Seconds 8
Send-Cmd 'r.GPUStatsEnabled 1'
Send-Cmd 'r.GPUCsvStatsEnabled 1'

$totalSeg = $Delay + ($fases.Count * ($Seconds + 6))
Write-Host ''
Say "PONETE EL VISOR AHORA. Arranco en $Delay segundos."
Say "Son unos $totalSeg segundos con el casco puesto, en $($fases.Count) tandas."
Say 'Juga normal todo el rato. Algunas tandas se van a ver distinto: es a proposito.'
Say 'Cuando termine la ultima vuelve todo a normal; ahi sacatelo.'
Start-Sleep -Seconds $Delay

foreach ($f in $fases) {
    foreach ($c in $f.cmds) { Send-Cmd $c }
    Start-Sleep -Seconds 2
    Say (">>> " + $f.n + " - " + $Seconds + " s") 'Green'
    Send-Cmd 'CsvProfile Start'
    Start-Sleep -Seconds $Seconds
    Send-Cmd 'CsvProfile Stop'
    Start-Sleep -Seconds 4
    # renombrar en el device: los parentesis del nombre original rompen el pull
    $sueltos = @((Adb shell "ls -t $csvDir") -split "`n" | ForEach-Object { $_.Trim() } |
        Where-Object { $_ -match '^Profile.*\.csv$' })
    if ($sueltos) { Adb shell "mv '$csvDir/$($sueltos[0])' '$csvDir/$($f.n).csv'" | Out-Null }
    else { Say ("  OJO: la fase " + $f.n + " no dejo captura") 'Red' }
}

Send-Cmd 'xr.VRS.FoveationLevel 0'
Send-Cmd 'xr.SecondaryScreenPercentage.HMDRenderTarget 100'
Say 'LISTO. Sacate el visor.' 'Cyan'

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
foreach ($f in $fases) {
    $destino = Join-Path $OutDir ($f.n + '.csv')
    if (Test-Path $destino) { Remove-Item $destino -Force }
    Adb pull "$csvDir/$($f.n).csv" $destino | Out-Null
    if (Test-Path $destino) { Write-Host ("  " + $f.n + ".csv  (" + [int]((Get-Item $destino).Length / 1KB) + " KB)") }
    else { Say ("  FALTA " + $f.n + ".csv") 'Red' }
}
Write-Host ''
Say ("capturas en: " + $OutDir) 'Gray'
