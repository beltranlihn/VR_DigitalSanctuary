<#
    quest_ab.ps1 - test oficial de Meta: el cuello son los PIXELES o la CPU?
    Graba dos capturas seguidas con el visor puesto:
        A  resolucion normal
        B  resolucion baja  (xr.SecondaryScreenPercentage.HMDRenderTarget)
    Si B mejora fuerte -> fill-rate bound. Si no cambia -> CPU bound.
    Fuente: references/profiling-quest.md seccion 2-3 (doc de Meta).

    DOS TRAMPAS DE POWERSHELL 5.1 QUE ESTE SCRIPT ESQUIVA A PROPOSITO:
    1. NADA de $ErrorActionPreference='Stop' con exes nativos: adb escribe cosas
       inocuas en stderr y PS 5.1 las convierte en error TERMINANTE. Mato la
       primera version del script en el segundo comando, sin dejar rastro.
    2. Archivo en ASCII puro: PS 5.1 lee los .ps1 como ANSI y un acento o una raya
       larga le rompe el parser.

    Cada paso se VERIFICA en vez de asumirse, y si algo falla lo dice y corta.

    Uso:  .\quest_ab.ps1
          .\quest_ab.ps1 -Seconds 45
#>
param(
    [string]$Package = 'com.almadigital.TESTMESHES',
    [string]$Project = 'VR_Test',
    [int]$Seconds = 20,
    [int]$Delay = 20,
    [int]$LowRes = 30,
    [string]$OutDir = ''
)

# Ver trampa 1 del encabezado. Los errores se manejan a mano, abajo.
$ErrorActionPreference = 'Continue'

# .../.claude/skills/unreal-vr/scripts/quest_ab.ps1 -> son 5 niveles hasta la raiz.
# Conte 4 y los CSV terminaron en .claude\perf: la corrida parecia fallada y no lo estaba.
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
function Contar-CSV { @((Adb shell "ls $csvDir" ) -split "`n" | Where-Object { $_ -match '\.csv' }).Count }

# El CsvProfiler nombra los archivos Profile(2026...).csv y esos PARENTESIS rompen
# el pull. Se renombra en el device a un nombre simple apenas cierra cada fase.
function Renombrar-Ultimo([string]$destino) {
    $todos = @((Adb shell "ls -t $csvDir") -split "`n" | ForEach-Object { $_.Trim() } |
        Where-Object { $_ -match '\.csv$' -and $_ -notmatch '^[AB]\.csv$' })
    if (-not $todos) { return $false }
    Adb shell "mv '$csvDir/$($todos[0])' '$csvDir/$destino'" | Out-Null
    return $true
}

# --- 0. hay visor? ---------------------------------------------------------
if ((Adb devices) -notmatch "`tdevice") {
    Say 'ERROR: no hay ninguna Quest conectada (adb devices vacio).' 'Red'; exit 1
}

# --- 1. arranque limpio ----------------------------------------------------
Say 'Reiniciando la app para partir de cvars limpias...' 'Gray'
Adb shell "am force-stop $Package" | Out-Null
Adb shell "rm -rf $csvDir" | Out-Null
Start-Sleep -Seconds 2
Adb shell "am start -n $Package/com.epicgames.unreal.GameActivity" | Out-Null

# verificar que ARRANCO de verdad, en vez de dormir a ciegas
$vivo = $false
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Seconds 1
    if ((Adb shell "pidof $Package").Trim()) { $vivo = $true; break }
}
if (-not $vivo) { Say 'ERROR: la app no arranco. Abrila a mano desde la biblioteca del visor.' 'Red'; exit 1 }
Say "App viva (tardo $i s). Esperando que cargue el nivel..." 'Gray'
Start-Sleep -Seconds 8

Send-Cmd 'r.GPUStatsEnabled 1'
Send-Cmd 'r.GPUCsvStatsEnabled 1'

$total = $Delay + ($Seconds * 2) + 10
Write-Host ''
Say "PONETE EL VISOR AHORA. Arranco en $Delay segundos."
Say "Son $total segundos en total con el casco puesto. Juga normal:"
Say 'agarra esferas, colocalas, movete. La senal de que terminaste es que'
Say 'la imagen se pone BORROSA y despues vuelve a NITIDA. Ahi sacatelo.'
for ($t = $Delay; $t -gt 0; $t--) {
    if ($t -le 5 -or $t % 5 -eq 0) { Write-Host "   $t..." -NoNewline; Write-Host '' }
    Start-Sleep -Seconds 1
}

# --- 2. fase A: resolucion normal -----------------------------------------
Say ">>> FASE A - resolucion normal - $Seconds segundos. Juga." 'Green'
Send-Cmd 'CsvProfile Start'
Start-Sleep -Seconds $Seconds
Send-Cmd 'CsvProfile Stop'
Start-Sleep -Seconds 4
if ((Contar-CSV) -lt 1) { Say 'ERROR: la fase A no dejo ningun CSV. Abortando.' 'Red'; exit 1 }
if (-not (Renombrar-Ultimo 'A.csv')) { Say 'ERROR: no pude renombrar la captura A.' 'Red'; exit 1 }

# --- 3. fase B: resolucion baja -------------------------------------------
Send-Cmd "xr.SecondaryScreenPercentage.HMDRenderTarget $LowRes"
Start-Sleep -Seconds 2
Say ">>> FASE B - se va a ver BORROSO, es a proposito - $Seconds segundos. Segui jugando igual." 'Green'
Send-Cmd 'CsvProfile Start'
Start-Sleep -Seconds $Seconds
Send-Cmd 'CsvProfile Stop'
Start-Sleep -Seconds 4
$okB = Renombrar-Ultimo 'B.csv'
Send-Cmd 'xr.SecondaryScreenPercentage.HMDRenderTarget 100'
Say 'LISTO. Sacate el visor.' 'Cyan'
if (-not $okB) { Say 'ERROR: la fase B no dejo captura.' 'Red'; exit 1 }

# --- 4. traer los dos CSV --------------------------------------------------
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$faltan = $false
foreach ($par in @(@('A.csv', 'A_normal.csv'), @('B.csv', 'B_baja.csv'))) {
    $destino = Join-Path $OutDir $par[1]
    if (Test-Path $destino) { Remove-Item $destino -Force }
    Adb pull "$csvDir/$($par[0])" $destino | Out-Null
    if (Test-Path $destino) {
        Write-Host ("  " + $par[1] + "  (" + [int]((Get-Item $destino).Length / 1KB) + " KB)")
    }
    else { Say ("  FALLO al traer " + $par[0]) 'Red'; $faltan = $true }
}
if ($faltan) { exit 1 }

Write-Host ''
Say 'Listo. Analizalo con:' 'Gray'
Write-Host "  python `"$repo\.claude\skills\unreal-vr\scripts\read_csv_perf.py`" `"$OutDir\A_normal.csv`" `"$OutDir\B_baja.csv`""
