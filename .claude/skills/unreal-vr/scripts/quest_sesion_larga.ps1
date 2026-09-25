<#
    quest_sesion_larga.ps1 - El test DECISIVO del "trabado progresivo" del material.

    QUE DECIDE. Beltran reporta que las animaciones DEL MATERIAL (wobble de esferas,
    deformacion del metaball) se van trabando a medida que avanza la sesion, mientras
    manos y mundo siguen fluidos. Hay DOS hipotesis que producen EXACTAMENTE ese sintoma:

      H1 - reloj en fp16: Time acumula y a T~1000 s su ulp en half es ~1 s, asi que los
           senos del material avanzan a saltos. El framerate se mantiene en 72.
      H2 - throttling termico + reproyeccion: la GPU se calienta, baja de clock, no llega
           a 72, y el runtime reproyecta. Cabeza y manos se ven suaves porque SE
           REPROYECTAN; lo unico que se ve a saltos es el contenido animado por shader.
           El framerate CAE con los minutos.

    Las dos se ven igual con el visor puesto. Se separan con UN dato: que le pasa al
    frame time A LO LARGO de la sesion. De ahi este script.

    COMO. Una sola sesion de ~$Minutos minutos en el modo 0 (la obra tal como esta),
    partida en tramos de $Tramo segundos. Cada tramo deja su propio CSV del CsvProfiler,
    asi que el promedio por tramo ES la serie de tiempo. En paralelo poletea la
    temperatura de la placa por dumpsys thermalservice y guarda el logcat completo
    (donde el runtime de Meta deja su telemetria por segundo, si la deja).

    LECTURA DEL RESULTADO
      frame time PLANO en ~13,9 y el trabado aparece igual  -> H1, es el reloj.
      frame time que CRECE con los minutos (y temp subiendo) -> H2, es termico, y el fix
                                                                del reloj es irrelevante.
      ninguna de las dos y no hay trabado                    -> el fix del reloj sirvio
                                                                (o el tubo lo tapo).

    Este build lleva ademas el FFR en 0 (bordes nitidos, mas carga de fill). Si el
    trabado vuelve SOLO con FFR apagado, eso tambien apunta a H2.

    Dos trampas de PowerShell 5.1 que este archivo esquiva (igual que sus hermanos):
      1. NADA de $ErrorActionPreference='Stop' con exes nativos: adb escribe cosas
         inocuas en stderr y PS 5.1 las convierte en error terminante.
      2. Archivo en ASCII puro: PS 5.1 lee los .ps1 como ANSI y un acento rompe el parser.

    Uso:  .\quest_sesion_larga.ps1
          .\quest_sesion_larga.ps1 -Minutos 20 -Tramo 60
#>
param(
    [string]$Package = 'com.almadigital.TESTMESHES',
    [string]$Project = 'VR_Test',
    [int]$Minutos = 18,
    [int]$Tramo = 60,
    [int]$Delay = 25,
    [string]$OutDir = ''
)

$ErrorActionPreference = 'Continue'

# .../.claude/skills/unreal-vr/scripts/x.ps1 -> 5 niveles hasta la raiz del repo.
$repo = $PSCommandPath
1..5 | ForEach-Object { $repo = Split-Path $repo -Parent }
if (-not $OutDir) { $OutDir = Join-Path $repo ('perf\sesion-larga-' + (Get-Date -Format 'yyyy-MM-dd-HHmm')) }

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
        Where-Object { $_ -match '\.csv$' -and $_ -notmatch '^tramo' })
    if (-not $todos) { return $false }
    Adb shell "mv '$csvDir/$($todos[0])' '$csvDir/$destino'" | Out-Null
    return $true
}

# Temperatura de la placa. En la Quest el thermalservice expone varias zonas; se guardan
# todas crudas y despues se elige. Si el comando no existe, no pasa nada: queda vacio.
function Temperatura {
    $d = Adb shell 'dumpsys thermalservice'
    $m = [regex]::Matches($d, 'mValue=([0-9.]+).*?mName=([A-Za-z0-9_-]+)')
    $p = @()
    foreach ($x in $m) { $p += ($x.Groups[2].Value + '=' + $x.Groups[1].Value) }
    return ($p -join ' ')
}

$tramos = [math]::Max(1, [int][math]::Floor(($Minutos * 60) / $Tramo))

if ((Adb devices) -notmatch "`tdevice") { Say 'ERROR: no hay ninguna Quest conectada.' 'Red'; exit 1 }

# 🔴 EL CASCO VA PRIMERO, LA APP DESPUES (2026-09-25). Con el visor fuera de la cabeza la
# Quest manda la app a segundo plano en segundos y el camino de suspension de UE en Android
# se DEADLOCKEA ("SuspendApp_EventThread -> ERROR: backgrounding callback, not responded in
# timely manner" + "Blocking renderer on suspended window"): la app no vuelve nunca.
Write-Host ''
Say "PONETE EL VISOR AHORA. La app arranca en $Delay segundos."
Say "Despues son $Minutos minutos con el casco puesto, en $tramos tramos de $Tramo s, todo en modo 0."
Say 'NO te saques el casco hasta el final: si la app pasa a segundo plano se cuelga.'
Write-Host ''
Say 'QUE TENES QUE HACER:' 'Cyan'
Say '  - Jugar normal y PARECIDO todo el tiempo (agarrar esferas, colocarlas, mirar la'
Say '    fila de gotas). No hace falta hacer nada especial: la idea es que pase el tiempo.'
Say '  - MIRAR el material (wobble de las esferas y la deformacion del metaball).'
Say '  - Cuando empiece a trabarse, DECILO EN VOZ ALTA con el minuto aproximado'
Say '    ("se traba, van como 9 minutos"). Ese minuto es el dato que cruzo con el CSV.'
Say '  - Si NO se traba en todo el rato, decilo tambien: eso es el resultado bueno.'
Write-Host ''
for ($t = $Delay; $t -gt 0; $t--) {
    if ($t -le 5 -or $t % 5 -eq 0) { Write-Host "   $t..." }
    Start-Sleep -Seconds 1
}
Write-Host ''
Say 'Reiniciando la app para partir limpio (el reloj del shader arranca en 0)...' 'Gray'
Adb shell "am force-stop $Package" | Out-Null
Adb shell "rm -rf $csvDir" | Out-Null
Adb logcat -c | Out-Null
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

# Control POSITIVO del instrumento: si "ke" no llega al Blueprint, el modo no es el que
# creemos y todo lo demas mide cualquier cosa. Es la leccion de gotcha 382.
Say 'Probando que el Blueprint conteste (control positivo)...' 'Gray'
Adb logcat -c | Out-Null
Send-Cmd 'ke * Perf0'
Start-Sleep -Seconds 2
if (-not ((Adb logcat -d) -split "`n" | Select-String -Pattern 'PERF: modo 0')) {
    Say 'ERROR: el modo 0 no contesto. O la app se cerro o el APK es viejo. Abortando.' 'Red'
    exit 1
}
Say '  OK: contesta.' 'Green'

Send-Cmd 'r.GPUStatsEnabled 1'
Send-Cmd 'r.GPUCsvStatsEnabled 1'

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$logTemp = Join-Path $OutDir 'temperatura.csv'
'segundo,tramo,zonas' | Out-File -FilePath $logTemp -Encoding utf8

# El logcat completo de la sesion, en paralelo. Ahi cae la telemetria por segundo del
# runtime de Meta (FPS/Stale/clock levels/Temp) si este runtime la emite.
$logcatFile = Join-Path $OutDir 'logcat.txt'
Adb logcat -c | Out-Null
$logcatJob = Start-Process -FilePath $adb -ArgumentList @('logcat', '-v', 'time') `
    -RedirectStandardOutput $logcatFile -NoNewWindow -PassThru

# Guardia de FOCO: si la app ya se fue a segundo plano, la sesion no mide nada.
$pausa = (Adb logcat -d) -split "`n" | Select-String -Pattern 'APP_CMD_PAUSE|APP_CMD_LOST_FOCUS'
if ($pausa) {
    Say 'ERROR: la app perdio el foco (APP_CMD_PAUSE/LOST_FOCUS en el log).' 'Red'
    Say 'Pasa cuando el casco no esta puesto: la Quest la suspende y UE se traba ahi.' 'Red'
    Say 'Ponete el visor ANTES de correr el script y volve a intentar. Abortando.' 'Red'
    if ($logcatJob -and -not $logcatJob.HasExited) { Stop-Process -Id $logcatJob.Id -Force }
    exit 1
}
Write-Host ''
Say 'Arrancando los tramos. Segui mirando.' 'Green'

$t0 = Get-Date
for ($k = 1; $k -le $tramos; $k++) {
    $etiqueta = ('tramo{0:d2}' -f $k)
    $seg = [int]((Get-Date) - $t0).TotalSeconds
    ('{0},{1},{2}' -f $seg, $k, (Temperatura)) | Out-File -FilePath $logTemp -Encoding utf8 -Append
    $min = [math]::Round($seg / 60.0, 1)
    Say (">>> tramo $k/$tramos  (minuto $min de la sesion)") 'Green'
    Send-Cmd 'CsvProfile Start'
    Start-Sleep -Seconds $Tramo
    Send-Cmd 'CsvProfile Stop'
    Start-Sleep -Seconds 3
    if (-not (Renombrar-Ultimo "$etiqueta.csv")) { Say "  AVISO: el tramo $k no dejo CSV." 'Red' }
}

$seg = [int]((Get-Date) - $t0).TotalSeconds
('{0},fin,{1}' -f $seg, (Temperatura)) | Out-File -FilePath $logTemp -Encoding utf8 -Append

Say 'LISTO. Sacate el visor.' 'Cyan'
if ($logcatJob -and -not $logcatJob.HasExited) { Stop-Process -Id $logcatJob.Id -Force }

for ($k = 1; $k -le $tramos; $k++) {
    $etiqueta = ('tramo{0:d2}' -f $k)
    $destino = Join-Path $OutDir "$etiqueta.csv"
    if (Test-Path $destino) { Remove-Item $destino -Force }
    Adb pull "$csvDir/$etiqueta.csv" $destino | Out-Null
    if (Test-Path $destino) { Write-Host ("  $etiqueta.csv  (" + [int]((Get-Item $destino).Length / 1KB) + " KB)") }
    else { Say "  FALLO al traer $etiqueta.csv" 'Red' }
}

Write-Host ''
Say "Carpeta: $OutDir" 'Gray'
Say 'Resumilo con:' 'Gray'
Write-Host "  python `"$repo\.claude\skills\unreal-vr\scripts\resumen_sesion_larga.py`" `"$OutDir`""
