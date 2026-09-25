<#
    quest_modo.ps1 - dispara un modo del banco PerfMode en la Quest, muestra el eco y
    VERIFICA QUE LA APP SIGA VIVA despues.
    Uso:  .\quest_modo.ps1 6      (modos 0-8; ver PLAN-PERF-ATTRACTING.md)
          .\quest_modo.ps1 1 -Delay 10    (para tenerlo puesto el visor antes)

    🔴 2026-09-25: la prueba de vida no es un adorno. El modo 8 CUELGA la app (game thread
    bloqueado, imagen congelada, sonido siguiendo), y sin este chequeo el script decia
    "modo 8 responde" y seguia adelante midiendo una app muerta. El eco del PrintString
    prueba que el evento LLEGO; la cvar prueba que el motor SIGUE ATENDIENDO despues.
    Son dos cosas distintas y hacen falta las dos.

    ASCII puro a proposito (PS 5.1 lee los .ps1 como ANSI).
#>
param(
    [string]$Modo = '0',
    [int]$Delay = 0,
    [int]$Espera = 8
)

$ErrorActionPreference = 'Continue'
$adb = Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe'
if (-not (Test-Path $adb)) { Write-Host "ERROR: no encuentro adb en $adb" -ForegroundColor Red; exit 1 }

if ($Delay -gt 0) {
    Write-Host "PONETE EL VISOR. Disparo el modo $Modo en $Delay segundos." -ForegroundColor Yellow
    for ($t = $Delay; $t -gt 0; $t--) { if ($t -le 5 -or $t % 5 -eq 0) { Write-Host "   $t..." }; Start-Sleep -Seconds 1 }
}

& $adb logcat -c 2>&1 | Out-Null
& $adb shell "am broadcast -a android.intent.action.RUN -e cmd 'ke * Perf$Modo'" 2>&1 | Out-Null
Start-Sleep -Seconds 2
$eco = (& $adb logcat -d 2>&1 | Out-String) -split "`n" | Select-String -Pattern 'PERF: modo'
if ($eco) {
    $linea = $eco[-1].ToString()
    $i = $linea.IndexOf('PERF')
    Write-Host ('  ' + $linea.Substring($i)) -ForegroundColor Green
} else {
    Write-Host '  Sin eco en logcat: o la app no corre, o el APK no tiene ese modo.' -ForegroundColor Red
}

# --- PRUEBA DE VIDA: el motor tiene que seguir contestando DESPUES del cambio de modo ---
Start-Sleep -Seconds $Espera
& $adb logcat -c 2>&1 | Out-Null
& $adb shell "am broadcast -a android.intent.action.RUN -e cmd 'xr.OpenXRFBFoveationLevel'" 2>&1 | Out-Null
Start-Sleep -Seconds 3
$vida = (& $adb logcat -d 2>&1 | Out-String) -split "`n" | Select-String -Pattern 'OpenXRFBFoveationLevel = '
if ($vida) {
    Write-Host "  VIVA: el motor sigue contestando $Espera s despues del modo $Modo." -ForegroundColor Green
} else {
    Write-Host "  COLGADA: el motor dejo de contestar tras el modo $Modo." -ForegroundColor Red
    Write-Host '  (game thread bloqueado; hay que cerrar la app con am force-stop)' -ForegroundColor Red
}
