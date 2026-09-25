<#
    quest_perf.ps1 — medir performance de un APK de Soul Charger ya instalado en la Quest.

    Requiere: la Quest conectada por USB con depuracion activada, y un build DEVELOPMENT
    (en Shipping no hay garantia de que las cvars respondan).

    El mecanismo es el broadcast intent de Unreal, confirmado en el codigo de UE 5.8
    (Engine\Build\Android\Java\src\com\epicgames\unreal\ConsoleCmdReceiver.java):
        adb shell "am broadcast -a android.intent.action.RUN -e cmd 'stat unit'"
    Ver references/profiling-quest.md §3 y §6.

    Uso tipico:
        .\quest_perf.ps1 stats          # numeros en pantalla dentro del visor
        .\quest_perf.ps1 start          # empieza a grabar el CSV por frame
        ... jugar la estacion 30-60 s ...
        .\quest_perf.ps1 stop
        .\quest_perf.ps1 pull           # trae CSV + log a .\perf\
        .\quest_perf.ps1 off            # apaga los stats de pantalla
#>
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('stats', 'off', 'start', 'stop', 'pull', 'cmd', 'launch', 'measure')]
    [string]$Action,

    [string]$Package = 'com.almadigital.TESTMESHES',
    [string]$Project = 'VR_Test',
    [string]$OutDir = (Join-Path (Get-Location) 'perf'),
    [string]$Command = '',
    [int]$Seconds = 60,
    [int]$Delay = 20
)

$ErrorActionPreference = 'Stop'

$adb = Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe'
if (-not (Test-Path $adb)) { throw "No encuentro adb en $adb" }

$devices = & $adb devices | Select-String -Pattern '\sdevice$'
if (-not $devices) { throw 'No hay ningun dispositivo conectado (adb devices vacio).' }

# La carpeta Saved del juego dentro del almacenamiento externo de la app.
$savedDir = "/sdcard/Android/data/$Package/files/UnrealGame/$Project/$Project/Saved"

function Send-Cmd([string]$c) {
    Write-Host "  -> $c"
    & $adb shell "am broadcast -a android.intent.action.RUN -e cmd '$c'" | Out-Null
}

switch ($Action) {

    'launch' {
        # El nombre de la activity de Unreal es constante entre proyectos.
        & $adb shell "am start -n $Package/com.epicgames.unreal.GameActivity"
        Write-Host 'App lanzada. Ponete el visor.'
    }

    'stats' {
        # unit  = Frame / Game / Draw / GPU en ms — el cuadro de mando.
        # gpu   = desglose del tiempo de GPU por pase; es lo que importa en Quest,
        #         que es fill-rate bound.
        Send-Cmd 'stat unit'
        Send-Cmd 'stat gpu'
        Write-Host 'Stats encendidos. Si el frame se acerca a 13,9 ms, no llega a 72 Hz.'
    }

    'off' {
        Send-Cmd 'stat none'
        Write-Host 'Stats apagados.'
    }

    'measure' {
        # Para medir solo: corré esto, dejá el teclado y ponete el visor.
        # 🔴 Una captura con el visor EN LA MESA no mide nada: al soltar el sensor de
        # proximidad la Quest baja los clocks y capa a 30 fps. Se nota en la columna
        # MaxFrameTime del CSV (33,33 ms = no lo tenías puesto · 13,89 ms = sí).
        Send-Cmd 'r.GPUStatsEnabled 1'
        Send-Cmd 'r.GPUCsvStatsEnabled 1'
        Write-Host ''
        Write-Host "Ponete el visor YA. Empiezo a grabar en $Delay segundos." -ForegroundColor Yellow
        Start-Sleep -Seconds $Delay
        Send-Cmd 'CsvProfile Start'
        Write-Host "Grabando $Seconds s. Jugá la estación normal: agarrá esferas, colocalas, movete." -ForegroundColor Yellow
        Start-Sleep -Seconds $Seconds
        Send-Cmd 'CsvProfile Stop'
        Start-Sleep -Seconds 3
        Write-Host 'Listo, sacate el visor.' -ForegroundColor Yellow
        & $PSCommandPath -Action pull -Package $Package -Project $Project -OutDir $OutDir
    }

    'start' {
        Send-Cmd 'CsvProfile Start'
        Write-Host 'Grabando CSV por frame. Jugá la estación y despues corré: .\quest_perf.ps1 stop'
    }

    'stop' {
        Send-Cmd 'CsvProfile Stop'
        Start-Sleep -Seconds 3   # el profiler escribe el archivo al cerrar
        Write-Host 'CSV cerrado. Traelo con: .\quest_perf.ps1 pull'
    }

    'cmd' {
        if (-not $Command) { throw 'Falta -Command "lo que sea"' }
        Send-Cmd $Command
    }

    'pull' {
        New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

        $csvDir = "$savedDir/Profiling/CSV"
        $listing = & $adb shell "ls $csvDir" 2>$null
        if ($LASTEXITCODE -eq 0 -and $listing) {
            foreach ($f in $listing) {
                $name = $f.Trim()
                if (-not $name) { continue }
                Write-Host "CSV: $name"
                & $adb pull "$csvDir/$name" (Join-Path $OutDir $name) | Out-Null
            }
        } else {
            Write-Warning "No hay CSVs en $csvDir (¿corriste 'start' y 'stop' con la app abierta?)"
        }

        # Ojo: NADA de `2>$null` sobre un exe nativo — PowerShell envuelve cada linea
        # de stderr en un ErrorRecord y el script sale con 1 aunque adb devuelva 0.
        $log = "$savedDir/Logs/$Project.log"
        & $adb pull $log (Join-Path $OutDir "$Project.log") | Out-Null
        if ($LASTEXITCODE -eq 0) { Write-Host "Log: $Project.log" }

        Write-Host ''
        Write-Host "Todo en: $OutDir"
    }
}
