<#
    quest_recorrido_perf.ps1 - FPS y tiempo de GPU POR ETAPA del APK de Test_Recorrido.

    QUE MIDE. Graba el logcat de la Quest mientras corre el recorrido (5 etapas de 1 minuto con
    sus transiciones) y al final lo parte por etapa usando las marcas "TOUR: ..." que imprime
    BP_StageTour_SC. Por etapa y por transicion da: FPS mediano y minimo, App= (ms de GPU de la
    app por cuadro; el presupuesto es 13,9 ms a 72 Hz), GPU% y CPU% del peor nucleo, y cuantos
    segundos estuvo por debajo del refresco.

    COMO SE USA (tres reglas pagadas con sesiones perdidas):
      1. Conectar la Quest por USB (adb) y correr este script ANTES de abrir la app.
      2. Abrir la app A MANO desde la biblioteca del visor ("Soul Charger Recorrido"), con el casco puesto.
         Lanzarla por intent colgaba UE.
      3. NO sacarse el casco hasta que el script diga que termino: si la app pasa a segundo plano, se cuelga.
    El script termina solo al ver "TOUR: fin" (el recorrido completo dura unos 7 minutos) o al
    llegar a -MaxMin.

    Uso:   .\quest_recorrido_perf.ps1
           .\quest_recorrido_perf.ps1 -MaxMin 15
    Resumen a mano:  python resumen_recorrido.py <carpeta de la sesion>
    (Archivo en ASCII puro y sin $ErrorActionPreference='Stop': PowerShell 5.1.)
#>
param(
    [string]$Package = 'com.almadigital.recorrido',
    [int]$MaxMin = 14,
    [string]$OutDir = ''
)
$ErrorActionPreference = 'Continue'

$aqui = Split-Path $PSCommandPath -Parent
if (-not $OutDir) { $OutDir = Join-Path (Get-Location) ('perf_recorrido_' + (Get-Date -Format 'yyyyMMdd_HHmmss')) }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$logFile = Join-Path $OutDir 'sesion.log'

$adb = Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe'
if (-not (Test-Path $adb)) { $adb = 'adb' }
function Say([string]$t, [string]$c = 'Yellow') { Write-Host $t -ForegroundColor $c }
function Log-Text {
    try {
        $s = [IO.File]::Open($logFile, 'Open', 'Read', 'ReadWrite')
        $r = New-Object IO.StreamReader($s); $t = $r.ReadToEnd(); $r.Close(); return $t
    } catch { return '' }
}

$dev = (& $adb devices 2>&1 | Out-String)
if ($dev -notmatch "`tdevice") { Say 'ERROR: no veo la Quest por adb. Conectala por USB y acepta la depuracion.' 'Red'; exit 1 }

& $adb logcat -c 2>&1 | Out-Null
$logcat = Start-Process -FilePath $adb -ArgumentList 'logcat', '-v', 'time' -RedirectStandardOutput $logFile -NoNewWindow -PassThru
Say "Grabando en $OutDir"
Say 'Ahora ponte el casco y abre "Soul Charger Recorrido" desde la biblioteca. No te saques el casco hasta el final.' 'Cyan'

$t0 = Get-Date
$ultimo = ''
while ($true) {
    Start-Sleep -Seconds 2
    $txt = Log-Text
    $m = [regex]::Matches($txt, 'TOUR: [^\r\n]*')
    if ($m.Count -gt 0) {
        $u = $m[$m.Count - 1].Value
        if ($u -ne $ultimo) { $ultimo = $u; Say ((Get-Date -Format 'HH:mm:ss') + '  ' + $u) 'Gray' }
        if ($u -match 'TOUR: fin') { Say 'Recorrido completo.' 'Green'; break }
    }
    if (((Get-Date) - $t0).TotalMinutes -gt $MaxMin) { Say "Tiempo maximo ($MaxMin min) alcanzado; corto la grabacion." 'Yellow'; break }
}
Start-Sleep -Seconds 2
if ($logcat -and -not $logcat.HasExited) { Stop-Process -Id $logcat.Id -Force -ErrorAction SilentlyContinue }

$py = Join-Path $aqui 'resumen_recorrido.py'
& python $py $OutDir
Say "Resumen en $OutDir\resumen.txt y tramos.csv" 'Green'
