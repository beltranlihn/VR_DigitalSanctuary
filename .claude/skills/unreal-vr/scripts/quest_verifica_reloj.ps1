<#
    quest_verifica_reloj.ps1 - Verificacion GUIADA del fix del reloj fp16 (gotcha 382).

    Corre solo: arranca la app, te avisa cuando ponerte el visor, y alterna los modos
    6 -> 7 -> 6 -> 7 -> 0 cantando que MIRAR en cada fase:
      modo 6 = reloj +1024 s por el camino HALF  -> los blobs deberian TRABARSE al instante
      modo 7 = mismo reloj inflado por fp32      -> deberian quedar FLUIDOS
      modo 0 = la obra normal                    -> quedate y proba la FUSION esfera-slot
    Cada cambio de modo se confirma por el eco en logcat; si no llega, aborta.

    Uso:  .\quest_verifica_reloj.ps1
          .\quest_verifica_reloj.ps1 -Seconds 15
    ASCII puro a proposito (PS 5.1 lee los .ps1 como ANSI).
#>
param(
    [string]$Package = 'com.almadigital.TESTMESHES',
    [int]$Seconds = 20,
    [int]$Delay = 20
)

$ErrorActionPreference = 'Continue'

$adb = Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe'
if (-not (Test-Path $adb)) { Write-Host "ERROR: no encuentro adb en $adb" -ForegroundColor Red; exit 1 }

function Adb { & $adb @args 2>&1 | Out-String }
function Say([string]$t, [string]$c = 'Yellow') { Write-Host $t -ForegroundColor $c }

function Modo([int]$n) {
    Adb logcat -c | Out-Null
    Adb shell "am broadcast -a android.intent.action.RUN -e cmd 'ke * Perf$n'" | Out-Null
    Start-Sleep -Seconds 2
    $eco = (Adb logcat -d) -split "`n" | Select-String -Pattern "PERF: modo $n"
    if (-not $eco) {
        Say "ERROR: el modo $n NO contesto. O la app se cerro o el APK es viejo. Abortando." 'Red'
        exit 1
    }
}

if ((Adb devices) -notmatch "`tdevice") { Say 'ERROR: no hay ninguna Quest conectada.' 'Red'; exit 1 }

Say 'Reiniciando la app para partir limpio...' 'Gray'
Adb shell "am force-stop $Package" | Out-Null
Start-Sleep -Seconds 2
Adb shell "am start -n $Package/com.epicgames.unreal.GameActivity" | Out-Null
$vivo = $false
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Seconds 1
    if ((Adb shell "pidof $Package").Trim()) { $vivo = $true; break }
}
if (-not $vivo) { Say 'ERROR: la app no arranco.' 'Red'; exit 1 }
Say "App viva. Esperando que cargue la estacion..." 'Gray'
Start-Sleep -Seconds 10

Write-Host ''
Say "PONETE EL VISOR. Arranco en $Delay segundos."
Say 'Vas a mirar los BLOBS (las esferas y el metaball del secuenciador) todo el tiempo.'
for ($t = $Delay; $t -gt 0; $t--) {
    if ($t -le 5 -or $t % 5 -eq 0) { Write-Host "   $t..." }
    Start-Sleep -Seconds 1
}

$fases = @(
    @{ n = 6; msg = 'FASE 1/4 - modo 6 (camino VIEJO, reloj a los "17 min"): los blobs deberian TRABARSE YA' },
    @{ n = 7; msg = 'FASE 2/4 - modo 7 (camino NUEVO, mismo reloj): deberian quedar FLUIDOS' },
    @{ n = 6; msg = 'FASE 3/4 - modo 6 de nuevo: TRABADO otra vez (para confirmar el contraste)' },
    @{ n = 7; msg = 'FASE 4/4 - modo 7 de nuevo: FLUIDO otra vez' }
)
foreach ($f in $fases) {
    Modo $f.n
    Say (">>> " + $f.msg) 'Green'
    Start-Sleep -Seconds $Seconds
}

Modo 0
Write-Host ''
Say 'LISTO: la obra quedo en modo 0 (normal) y la app sigue corriendo.' 'Cyan'
Say 'Aprovecha AHORA para la FUSION: agarra una esfera y acercala DESPACIO a un slot.' 'Cyan'
Say 'Mira que el estiron de la cadena hacia la esfera no se corte seco en el aire.' 'Cyan'
Write-Host ''
Say 'Para reportar: 1) el 6 se trababa? 2) el 7 quedo fluido? 3) la fusion se corta?' 'Yellow'
