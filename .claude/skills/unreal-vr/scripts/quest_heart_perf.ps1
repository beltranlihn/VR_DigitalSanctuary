<#
    quest_heart_perf.ps1 - CUANTO PESAN LOS VERTICES Y LOS PIXELES de la membrana del latido
    (APK de Test_Heart, paquete com.almadigital.heart, BP_HeartScape_SC + M_HeartScape_SC).

    QUE MIDE. El tiempo de GPU de la app por cuadro ('App=' de la linea VrApi que la Quest
    escribe en logcat una vez por segundo). 'App' es trabajo real de GPU y no queda clavado
    en 13,9 ms por el vsync, asi que se puede restar un modo de otro (gotcha 440).

    LOS MODOS (PerfMode del material; eventos Perf0..Perf3 del actor, 'ke * PerfN',
    solo en Development). Cada evento escribe en logcat 'PERF: heart modo N':
      0  todo              la escena tal como esta autorada (referencia)
      1  vertices baratos  sin ondas: WPO, gradiente y crestas en cero
      2  pixeles baratos   membrana y esfera de un color plano
      3  ambos baratos     el piso
    vertices = m0 - m1 | pixeles = m0 - m2 | piso = m3.
    Las fases corren en UNA sesion, ida y vuelta (0123 3210): comparten escena, pose y
    temperatura; la separacion entre las dos pasadas de un modo es la resolucion real.

    Tres reglas pagadas con sesiones perdidas (ver quest_perfmodes.ps1 y quest_entering_perf.ps1):
      1. La app NO se lanza por intent: se abre A MANO desde la biblioteca del visor, con el
         casco puesto (lanzarla por intent colgaba UE en el camino de suspension).
      2. El casco NO se saca hasta que el script diga LISTO.
      3. Archivo en ASCII puro y sin $ErrorActionPreference='Stop' (PowerShell 5.1).

    Uso:  .\quest_heart_perf.ps1                 (modos 0,1,2,3 - unos 3 min con el casco)
          .\quest_heart_perf.ps1 -Modos 0,2      (solo pixeles si/no)
    Resumen: lo corre solo al final; a mano:  python resumen_heart.py <carpeta de la sesion>
#>
param(
    [string]$Package = 'com.almadigital.heart',
    [int]$Seconds = 20,
    [int]$Settle = 3,
    [string[]]$Modos = @('0', '1', '2', '3'),
    [string]$OutDir = ''
)

$ModosNum = @()
foreach ($tok in $Modos) {
    foreach ($ch in ([string]$tok).ToCharArray()) {
        if ($ch -ge '0' -and $ch -le '3') { $ModosNum += [int][string]$ch }
    }
}
if ($ModosNum.Count -eq 0) { $ModosNum = @(0, 1, 2, 3) }

$ErrorActionPreference = 'Continue'

# .../.claude/skills/unreal-vr/scripts/x.ps1 -> 5 niveles hasta la raiz del repo.
$repo = $PSCommandPath
1..5 | ForEach-Object { $repo = Split-Path $repo -Parent }
if (-not $OutDir) { $OutDir = Join-Path $repo ('perf\heart_' + (Get-Date -Format 'yyyyMMdd_HHmmss')) }
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
    0 = 'todo'
    1 = 'VERTICES BARATOS (la membrana queda plana)'
    2 = 'PIXELES BARATOS (membrana y esfera de color plano)'
    3 = 'AMBOS BARATOS (el piso)'
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
    Say 'PONTE EL VISOR y abre "Soul Charger Heart" desde la biblioteca'
    Say '(Biblioteca > Aplicaciones > Origenes desconocidos). Te espero hasta 3 minutos.'
    Say 'NO te quites el casco hasta que el script diga LISTO.'
    $vivo = $false
    for ($i = 0; $i -lt 180; $i++) {
        if ((Adb shell "pidof $Package").Trim()) { $vivo = $true; break }
        Start-Sleep -Seconds 1
    }
    if (-not $vivo) { Say 'ERROR: la app no arranco en 3 minutos. Abortando.' 'Red'; exit 1 }
    Say 'App viva. Espero a que cargue el nivel...' 'Gray'
    if (-not (Espera-Patron 'LoadMap Load map complete /Game/Test_Heart' 0 60)) {
        Say 'AVISO: no vi la carga de /Game/Test_Heart en 60 s; sigo igual.' 'Red'
    }
    Start-Sleep -Seconds 6

    if ((Cuenta 'VrApi.*App=') -lt 3) {
        Say 'ERROR: logcat no trae la linea VrApi con "App=". Sin ella no hay nada que medir.' 'Red'
        exit 1
    }
    $script:focoBase = Cuenta-Foco

    # Control POSITIVO: el eco prueba que el evento LLEGO al Blueprint; el efecto lo ves tu
    # (en el modo 1 la membrana queda plana; en el 2, de un color plano).
    Say 'Pruebo cada modo (2 s cada uno). Mira que pase lo que digo:' 'Gray'
    $unicos = $ModosNum | Sort-Object -Unique
    foreach ($m in $unicos) {
        $antes = Cuenta "PERF: heart modo $m"
        Send-Cmd "ke * Perf$m"
        if (-not (Espera-Patron "PERF: heart modo $m" $antes 5)) {
            Say "ERROR: el modo $m NO contesto (no aparece 'PERF: heart modo $m')." 'Red'
            Say 'O el APK es viejo (sin eventos Perf), o no es Development ("ke" no existe en Shipping).' 'Red'
            exit 1
        }
        Say ("  modo $m -> " + $desc[$m]) 'Gray'
        Start-Sleep -Seconds 2
    }
    Send-Cmd 'ke * Perf0'
    Say '  OK: todos los modos contestan.' 'Green'

    $orden = @($ModosNum) + @($ModosNum[($ModosNum.Count - 1)..0])
    $total = $orden.Count * ($Seconds + $Settle + 1)
    Write-Host ''
    Say "Arrancan $($orden.Count) fases de $Seconds s (unos $([int]($total / 60)) min $($total % 60) s)." 'Green'
    Say 'Mira SIEMPRE lo mismo: la esfera y las ondas, desde tu lugar, sin girar la cabeza.'
    $k = 0
    foreach ($m in $orden) {
        $k++
        if (Perdio-Foco) { Say 'ERROR: la app perdio el foco a mitad de la medicion. Abortando.' 'Red'; exit 1 }
        Send-Cmd "ke * Perf$m"
        Say (">>> fase $k/$($orden.Count): modo $m - " + $desc[$m] + " - $Seconds s") 'Green'
        Start-Sleep -Seconds ($Seconds + $Settle)
    }
    Send-Cmd 'ke * Perf0'
}
finally {
    if ($logcat -and -not $logcat.HasExited) { Stop-Process -Id $logcat.Id -Force -ErrorAction SilentlyContinue }
}

Say 'LISTO. Ya puedes quitarte el visor. (El material vuelve al modo 0.)' 'Cyan'
Write-Host ("  sesion: $logFile  (" + [int]((Get-Item $logFile).Length / 1KB) + " KB)")
Write-Host ''
$py = Join-Path $repo '.claude\skills\unreal-vr\scripts\resumen_heart.py'
& python "$py" "$OutDir"
