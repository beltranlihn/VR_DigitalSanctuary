<#
    quest_chladni_perf.ps1 - QUE PARTE DEL SALAR DE CHLADNI SE COME EL PRESUPUESTO, y cuanto rinde el
    gradiente analitico (APK de Test_Sequencer, paquete com.almadigital.sequencer,
    BP_ChladniFloor_SC + M_ChladniFloor_SC). Copia de quest_heart_perf.ps1 (probado en visor).

    QUE MIDE. 'App=' de la linea VrApi (tiempo de GPU de la app por cuadro; no queda clavado en
    13,9 ms por el vsync, asi que los modos se restan).

    LOS MODOS (PerfMode del material; eventos ChladniPerf0..6 del actor, 'ke * ChladniPerfN',
    solo Development; eco 'PERF: chladni modo N'). TODAS las fases fuerzan las 8 figuras del
    mandala (PerfForce 1): peor caso fijo, no depende de lo que haya en la mesa.
    Ronda 1 (medida el 29): 0 era el shader viejo (25,5 ms) y 1 el analitico (18,0 ms).
    Ronda 2: el 0 ES la obra optimizada; cada modo resta una capa para ver cuanto pesa:
      0  obra             1  sin arena (arena, granito, manchas)
      2  sin mandala PS   3  sin WPO          4  piso plano      5  cielo plano
      6  sin acabado      7  sin poligonos    8  sin agua        9  sin bruma
    Al final manda 'ke * ChladniPerfOff' (la obra, sin forzar) con el logcat ya cerrado.

    Tres reglas pagadas con sesiones perdidas (ver quest_heart_perf.ps1):
      1. La app NO se lanza por intent: se abre A MANO desde la biblioteca del visor, con el casco puesto.
      2. El casco NO se saca hasta que el script diga LISTO.
      3. Archivo en ASCII puro y sin $ErrorActionPreference='Stop' (PowerShell 5.1).

    Uso:  .\quest_chladni_perf.ps1                  (modos 0..9, ida y vuelta: unos 7 min con el casco)
          .\quest_chladni_perf.ps1 -Modos 0,4       (obra contra piso plano)
    Resumen: lo corre solo al final; a mano:  python resumen_chladni.py <carpeta de la sesion>
#>
param(
    [string]$Package = 'com.almadigital.sequencer',
    [int]$Seconds = 15,
    [int]$Settle = 3,
    [string[]]$Modos = @('0', '1', '2', '3', '4', '5', '6', '7', '8', '9'),
    [string]$OutDir = ''
)

$ModosNum = @()
foreach ($tok in $Modos) {
    foreach ($ch in ([string]$tok).ToCharArray()) {
        if ($ch -ge '0' -and $ch -le '9') { $ModosNum += [int][string]$ch }
    }
}
if ($ModosNum.Count -eq 0) { $ModosNum = @(0, 1, 2, 3, 4, 5, 6, 7, 8, 9) }

$ErrorActionPreference = 'Continue'

# .../.claude/skills/unreal-vr/scripts/x.ps1 -> 5 niveles hasta la raiz del repo.
$repo = $PSCommandPath
1..5 | ForEach-Object { $repo = Split-Path $repo -Parent }
if (-not $OutDir) { $OutDir = Join-Path $repo ('perf\chladni_' + (Get-Date -Format 'yyyyMMdd_HHmmss')) }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$logFile = Join-Path $OutDir 'sesion.log'

$adb = Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe'
if (-not (Test-Path $adb)) { Write-Host "ERROR: no encuentro adb en $adb" -ForegroundColor Red; exit 1 }

function Adb { & $adb @args 2>&1 | Out-String }
function Send-Cmd([string]$c) { Adb shell "am broadcast -a android.intent.action.RUN -e cmd '$c'" | Out-Null }
function Say([string]$t, [string]$c = 'Yellow') { Write-Host $t -ForegroundColor $c }
function Log-Text {
    try {
        $s = [IO.File]::Open($logFile, 'Open', 'Read', 'ReadWrite')
        $r = New-Object IO.StreamReader($s)
        $t = $r.ReadToEnd(); $r.Close()
        return $t
    } catch { return '' }
}
function Cuenta([string]$patron) { return ([regex]::Matches((Log-Text), $patron)).Count }
function Espera-Patron([string]$patron, [int]$antes, [int]$seg) {
    for ($i = 0; $i -lt ($seg * 2); $i++) {
        if ((Cuenta $patron) -gt $antes) { return $true }
        Start-Sleep -Milliseconds 500
    }
    return $false
}
$script:focoBase = 0
function Cuenta-Foco { return (Cuenta 'APP_CMD_PAUSE|APP_CMD_LOST_FOCUS') }
function Perdio-Foco { return ((Cuenta-Foco) -gt $script:focoBase) }

$desc = @{
    0 = 'OBRA optimizada (referencia)'
    1 = 'SIN ARENA (sin grano, granito ni manchas)'
    2 = 'SIN MANDALA en pixeles (desaparecen las crestas finas)'
    3 = 'SIN WPO (la ola/loma de geometria queda plana)'
    4 = 'PISO PLANO (piso de un solo color)'
    5 = 'CIELO PLANO (cielo de un solo color)'
    6 = 'SIN ACABADO (sin poligonos, arena, agua ni bruma)'
    7 = 'SIN POLIGONOS del salar'
    8 = 'SIN AGUA (sin reflejo del cielo)'
    9 = 'SIN BRUMA'
}

if ((Adb devices) -notmatch "`tdevice") { Say 'ERROR: no hay ninguna Quest conectada por USB.' 'Red'; exit 1 }
if ((Adb shell "pm list packages $Package") -notmatch [regex]::Escape($Package)) {
    Say "ERROR: la app $Package no esta instalada en la Quest." 'Red'; exit 1
}
if ((Adb shell "pidof $Package").Trim()) {
    Say 'La app ya estaba abierta: la cierro para empezar desde cero.' 'Gray'
    Adb shell "am force-stop $Package" | Out-Null
    Start-Sleep -Seconds 2
}

Adb logcat -c | Out-Null
$logcat = Start-Process -FilePath $adb -ArgumentList 'logcat', '-v', 'time' -RedirectStandardOutput $logFile -NoNewWindow -PassThru

try {
    Write-Host ''
    Say 'PONTE EL VISOR y abre "Soul Charger Sequencer" desde la biblioteca'
    Say '(Biblioteca > Aplicaciones > Origenes desconocidos). Te espero hasta 3 minutos.'
    Say 'NO te quites el casco hasta que el script diga LISTO.'
    $vivo = $false
    for ($i = 0; $i -lt 180; $i++) {
        if ((Adb shell "pidof $Package").Trim()) { $vivo = $true; break }
        Start-Sleep -Seconds 1
    }
    if (-not $vivo) { Say 'ERROR: la app no arranco en 3 minutos. Abortando.' 'Red'; exit 1 }
    Say 'App viva. Espero a que cargue el nivel...' 'Gray'
    if (-not (Espera-Patron 'LoadMap Load map complete /Game/Test_Sequencer' 0 60)) {
        Say 'AVISO: no vi la carga de /Game/Test_Sequencer en 60 s; sigo igual.' 'Red'
    }
    Start-Sleep -Seconds 6

    if ((Cuenta 'VrApi.*App=') -lt 3) {
        Say 'ERROR: logcat no trae la linea VrApi con "App=". Sin ella no hay nada que medir.' 'Red'
        exit 1
    }
    $script:focoBase = Cuenta-Foco

    # Control POSITIVO: el eco prueba que el evento LLEGO al Blueprint; el efecto lo ves tu
    # (cada modo saca una capa del piso: es la medicion).
    Say 'Pruebo cada modo (2 s cada uno). Mira que pase lo que digo:' 'Gray'
    $unicos = $ModosNum | Sort-Object -Unique
    foreach ($m in $unicos) {
        $antes = Cuenta "PERF: chladni modo $m"
        Send-Cmd "ke * ChladniPerf$m"
        if (-not (Espera-Patron "PERF: chladni modo $m" $antes 5)) {
            Say "ERROR: el modo $m NO contesto (no aparece 'PERF: chladni modo $m')." 'Red'
            Say 'O el APK es viejo (sin eventos Perf), o no es Development ("ke" no existe en Shipping).' 'Red'
            exit 1
        }
        Say ("  modo $m -> " + $desc[$m]) 'Gray'
        Start-Sleep -Seconds 2
    }
    Send-Cmd 'ke * ChladniPerf0'
    Say '  OK: todos los modos contestan.' 'Green'

    $orden = @($ModosNum) + @($ModosNum[($ModosNum.Count - 1)..0])
    $total = $orden.Count * ($Seconds + $Settle + 1)
    Write-Host ''
    Say "Arrancan $($orden.Count) fases de $Seconds s (unos $([int]($total / 60)) min $($total % 60) s)." 'Green'
    Say 'Mira SIEMPRE lo mismo: la mesa y el mandala del piso, desde tu lugar, sin girar la cabeza.'
    $k = 0
    foreach ($m in $orden) {
        $k++
        if (Perdio-Foco) { Say 'ERROR: la app perdio el foco a mitad de la medicion. Abortando.' 'Red'; exit 1 }
        Send-Cmd "ke * ChladniPerf$m"
        Say (">>> fase $k/$($orden.Count): modo $m - " + $desc[$m] + " - $Seconds s") 'Green'
        Start-Sleep -Seconds ($Seconds + $Settle)
    }
    Send-Cmd 'ke * ChladniPerf0'
}
finally {
    if ($logcat -and -not $logcat.HasExited) { Stop-Process -Id $logcat.Id -Force -ErrorAction SilentlyContinue }
}

Send-Cmd 'ke * ChladniPerfOff'
Say 'LISTO. Ya puedes quitarte el visor. (El piso vuelve a la obra, sin forzar.)' 'Cyan'
Write-Host ("  sesion: $logFile  (" + [int]((Get-Item $logFile).Length / 1KB) + " KB)")
Write-Host ''
$py = Join-Path $repo '.claude\skills\unreal-vr\scripts\resumen_chladni.py'
& python "$py" "$OutDir"
