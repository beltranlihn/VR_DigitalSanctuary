<#
    quest_borde.ps1 - alterna EN VIVO el suavizado del borde del metaball (Test_Entering).

    Manda 'ke * PerfEdgeN' a la app que esta corriendo en la Quest (BP_PerfEntering_SC,
    solo builds Development) y confirma el eco en logcat.
      0  sin suavizado (EdgeAA 0.01)  CONTROL NEGATIVO: tiene que verse el borde escalonado de antes
      1  suavizado 1.5 (el default)   EL ARREGLO
      2  suavizado 5                  CONTROL POSITIVO: el borde tiene que verse claramente difuso.
                                      Si 2 se ve igual que 0, el parametro no llega y la prueba no vale.
    Mirar el borde del metaball contra el negro, no la escena entera.

    Uso:  .\quest_borde.ps1 0      .\quest_borde.ps1 1      .\quest_borde.ps1 2
          .\quest_borde.ps1 -Ciclo      (0 -> 1 -> 2 -> 1, 8 s cada uno)
    Archivo en ASCII puro (PowerShell 5.1).
#>
param(
    [int]$Modo = 1,
    [switch]$Ciclo,
    [int]$Segundos = 8,
    [string]$Package = 'com.almadigital.entering'
)
$ErrorActionPreference = 'Continue'
$adb = Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe'
if (-not (Test-Path $adb)) { Write-Host "ERROR: no encuentro adb en $adb" -ForegroundColor Red; exit 1 }
if (-not ((& $adb shell "pidof $Package" 2>&1 | Out-String).Trim())) {
    Write-Host 'ERROR: la app no esta corriendo. Abrela desde la biblioteca del visor.' -ForegroundColor Red; exit 1
}
$desc = @{ 0 = 'SIN suavizado (control negativo)'; 1 = 'suavizado 1.5 (el arreglo)'; 2 = 'suavizado 5 (control positivo, difuso)' }

function Poner([int]$m) {
    & $adb logcat -c 2>&1 | Out-Null
    & $adb shell "am broadcast -a android.intent.action.RUN -e cmd 'ke * PerfEdge$m'" 2>&1 | Out-Null
    for ($i = 0; $i -lt 10; $i++) {
        Start-Sleep -Milliseconds 300
        if ((& $adb logcat -d 2>&1 | Out-String) -match "PERF: borde $m") {
            Write-Host ("  borde " + $m + ": " + $desc[$m]) -ForegroundColor Green
            return $true
        }
    }
    Write-Host "  AVISO: el modo $m no confirmo (sin eco 'PERF: borde $m'). APK sin los eventos o no Development." -ForegroundColor Red
    return $false
}

if ($Ciclo) {
    foreach ($m in @(0, 1, 2, 1)) {
        [void](Poner $m)
        Start-Sleep -Seconds $Segundos
    }
} else {
    if ($Modo -lt 0 -or $Modo -gt 2) { Write-Host 'Modo 0, 1 o 2.' -ForegroundColor Red; exit 1 }
    [void](Poner $Modo)
}
