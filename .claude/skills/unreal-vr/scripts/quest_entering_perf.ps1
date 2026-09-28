<#
    quest_entering_perf.ps1 - CUANTO PESA EL METABALL en la etapa Entering (APK de Test_Entering).

    QUE MIDE. El tiempo de GPU de la app por cuadro ('App=' de la linea VrApi que la Quest
    escribe en logcat una vez por segundo), mas FPS, GPU% y el nivel de reloj de la GPU.
    'App' es trabajo real de GPU: NO queda clavado en 13,9 ms por el vsync como el
    FrameTime del CsvProfiler (gotcha del instrumento saturado, 2026-09-26). Por eso aca
    se puede restar un modo de otro aunque la escena corra a 72 fps.

    COMO SEPARA EL METABALL. BP_PerfEntering_SC (actor 'Perf_Entering' del nivel, carpeta
    Debug) apaga y prende por consola ('ke * PerfEN', solo en Development) la visibilidad
    del Volume del metaball y del Panel del pacer:
      modo 0  todo            la etapa tal como esta autorada (referencia)
      modo 1  sin metaball    el pacer sigue
      modo 2  sin pacer       el metaball sigue
      modo 3  nada            ni metaball ni pacer (queda el fondo liquido + mandos)
      modo 4  sin fondo       metaball y pacer visibles, el FONDO liquido oculto (2026-09-27)
    metaball = m0 - m1 (y m2 - m3 como segunda lectura) | pacer = m0 - m2 | fondo = m0 - m4
    | piso = m3 (con fondo). El fondo NO se apaga en los modos 0-3: esos miden lo mismo que
    antes, con el fondo encima.
    Todas las fases corren en UNA sesion, ida y vuelta (ABCD DCBA): comparten escena, pose
    y temperatura, y la separacion entre las dos pasadas de un modo es la resolucion real.

    LA ETAPA NO SE TERMINA EN MEDIO. Al engancharse, el script manda 'ke * PerfELoop' (el
    pacer pasa a ciclos infinitos). Al final manda 'ke * PerfEEnd': todo visible otra vez y
    el pacer vuelve a sus ciclos, asi que termina en el ciclo siguiente y la etapa cierra
    sola (pacer -> metaball -> fin). Esos ultimos segundos quedan grabados como linea de
    tiempo, incluido el nivel vacio del final.

    -SoloMirar: sin A/B. Graba la sesion entera tal cual la vive el usuario, hasta el fin
    de la etapa, y el resumen da el costo por tramo (antes del metaball, con metaball y
    pacer, despues del final).

    Tres reglas pagadas con sesiones perdidas (ver quest_perfmodes.ps1):
      1. La app NO se lanza por intent: se abre A MANO desde la biblioteca del visor, con
         el casco puesto (lanzarla por intent colgaba UE en el camino de suspension).
      2. El casco NO se saca hasta el final: si la app pasa a segundo plano, se cuelga.
      3. Archivo en ASCII puro y sin $ErrorActionPreference='Stop' (PowerShell 5.1).

    Uso:  .\quest_entering_perf.ps1                  (modos 0,1,2,3,4 - unos 5 min con el casco)
          .\quest_entering_perf.ps1 -Modos 0,4       (solo fondo si/no - unos 2 min)
          .\quest_entering_perf.ps1 -Modos 0,1       (solo metaball si/no - unos 2 min)
          .\quest_entering_perf.ps1 -SoloMirar       (la etapa tal cual, sin apagar nada)
          .\quest_entering_perf.ps1 -Modos 0,4,5,6   (la capa viva, 2026-09-28: FONDO = m0 - m4 = el valle
                                                   y AIRE = m5 - m6 = el aliento visible, en una sesion.
                                                   Necesita BP_BreathAir_SC en el nivel: sus PerfE0/5/6
                                                   ecoan 'PERF: entering modo N' y PerfE1-4 lo dejan normal.
                                                   OJO: BP_PerfEntering_SC NO tiene PerfE5/PerfE6, asi que en
                                                   las fases 5 y 6 el fondo queda como lo dejo el modo anterior:
                                                   en la ida y vuelta 0 4 5 6 6 5 4 0 el 5 y el 6 siempre vienen
                                                   despues del 4 -> el aire se mide con el VALLE OCULTO. La resta
                                                   m5 - m6 sigue valiendo (misma escena en las dos); con
                                                   -Modos 0,5,6 el valle queda VISIBLE: no mezclar sesiones.
                                                   El resumen agrega el CPU% del peor nucleo (VrApi 'CPU%=..(W..)'),
                                                   una senal gruesa del hilo de juego (el Blueprint del aire y
                                                   del valle), no un tiempo)
    Resumen: lo corre solo al final; a mano:
          python resumen_entering.py <carpeta de la sesion>
#>
param(
    [string]$Package = 'com.almadigital.entering',
    # 28 s = dos ciclos enteros del pacer 4-3-4-3: cada ventana promedia respiraciones
    # completas (el metaball cubre mas o menos pantalla segun la fase de la respiracion).
    [int]$Seconds = 28,
    [int]$Settle = 3,
    [string[]]$Modos = @('0', '1', '2', '3', '4'),
    [switch]$SoloMirar,
    [string]$OutDir = ''
)

$ModosNum = @()
foreach ($tok in $Modos) {
    foreach ($ch in ([string]$tok).ToCharArray()) {
        if ($ch -ge '0' -and $ch -le '6') { $ModosNum += [int][string]$ch }
    }
}
if ($ModosNum.Count -eq 0) { $ModosNum = @(0, 1, 2, 3, 4) }

$ErrorActionPreference = 'Continue'

# .../.claude/skills/unreal-vr/scripts/x.ps1 -> 5 niveles hasta la raiz del repo.
$repo = $PSCommandPath
1..5 | ForEach-Object { $repo = Split-Path $repo -Parent }
if (-not $OutDir) { $OutDir = Join-Path $repo ('perf\entering_' + (Get-Date -Format 'yyyyMMdd_HHmmss')) }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$logFile = Join-Path $OutDir 'sesion.log'

$adb = Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe'
if (-not (Test-Path $adb)) { Write-Host "ERROR: no encuentro adb en $adb" -ForegroundColor Red; exit 1 }

function Adb { & $adb @args 2>&1 | Out-String }
function Send-Cmd([string]$c) { Adb shell "am broadcast -a android.intent.action.RUN -e cmd '$c'" | Out-Null }
function Say([string]$t, [string]$c = 'Yellow') { Write-Host $t -ForegroundColor $c }
# Lectura COMPARTIDA: adb tiene el archivo abierto para escribir y ReadAllText/Get-Content
# fallan con "esta siendo utilizado en otro proceso" (probado 2026-09-27).
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
# El foco se compara contra una linea de BASE tomada con la app ya andando: un evento de
# foco durante el arranque (menu del sistema, limites) no es el cuelgue que se busca.
$script:focoBase = 0
function Cuenta-Foco { return (Cuenta 'APP_CMD_PAUSE|APP_CMD_LOST_FOCUS') }
function Perdio-Foco { return ((Cuenta-Foco) -gt $script:focoBase) }

$desc = @{
    0 = 'todo (metaball + pacer)'
    1 = 'SIN METABALL (el pacer sigue)'
    2 = 'SIN PACER (el metaball sigue)'
    3 = 'NADA (ni metaball ni pacer; queda el fondo)'
    4 = 'SIN FONDO (metaball y pacer siguen)'
    5 = 'AIRE LLENO (BP_BreathAir_SC: las dos corrientes llenas; el fondo como en el modo anterior)'
    6 = 'SIN AIRE (BP_BreathAir_SC oculto; el fondo como en el modo anterior)'
}

if ((Adb devices) -notmatch "`tdevice") { Say 'ERROR: no hay ninguna Quest conectada por USB.' 'Red'; exit 1 }
if ((Adb shell "pm list packages $Package") -notmatch [regex]::Escape($Package)) {
    Say "ERROR: la app $Package no esta instalada en la Quest." 'Red'; exit 1
}

# Sesion NUEVA siempre: si la app ya estaba abierta, la etapa puede haber terminado y el
# metaball ya no estar. Cerrarla es seguro (lo que colgaba era LANZARLA por intent).
if ((Adb shell "pidof $Package").Trim()) {
    Say 'La app ya estaba abierta: la cierro para empezar la etapa desde cero.' 'Gray'
    Adb shell "am force-stop $Package" | Out-Null
    Start-Sleep -Seconds 2
}

# La grabacion arranca ANTES de que se abra la app: asi queda la sesion entera, con sus
# marcas (BLOB: entra, pacer en marcha, ...) y la telemetria VrApi, en un solo archivo.
Adb logcat -c | Out-Null
$logcat = Start-Process -FilePath $adb -ArgumentList 'logcat', '-v', 'time' -RedirectStandardOutput $logFile -NoNewWindow -PassThru

try {
    Write-Host ''
    Say 'PONTE EL VISOR y abre "Soul Charger Entering" desde la biblioteca'
    Say '(Biblioteca > Aplicaciones > Origenes desconocidos). Te espero hasta 3 minutos.'
    Say 'NO te quites el casco hasta que el script diga LISTO: si la app pasa a segundo'
    Say 'plano, la Quest la suspende y Unreal se cuelga ahi.'
    $vivo = $false
    for ($i = 0; $i -lt 180; $i++) {
        if ((Adb shell "pidof $Package").Trim()) { $vivo = $true; break }
        Start-Sleep -Seconds 1
    }
    if (-not $vivo) { Say 'ERROR: la app no arranco en 3 minutos. Abortando.' 'Red'; exit 1 }
    Say 'App viva.' 'Gray'

    if ($SoloMirar) {
        Say 'Modo SOLO MIRAR: vive la etapa normal. Grabo hasta que termine.' 'Green'
        if (-not (Espera-Patron 'BREATHSTAGE: fin de la etapa' 0 400)) { Say 'AVISO: no vi el fin de la etapa en 400 s.' 'Red' }
        Say 'Fin de la etapa. Grabo 10 s mas del nivel vacio...' 'Gray'
        Start-Sleep -Seconds 10
    }
    else {
        # 1) El pacer pasa a infinito ANTES de que termine la etapa (la etapa entera dura
        #    ~80 s con 5 ciclos; el A/B completo, unos 4 min). Se espera el BeginPlay del
        #    actor de medicion: antes de eso el nivel no esta cargado y el comando se pierde.
        if (-not (Espera-Patron 'PERF: entering listo' 0 90)) {
            Say 'ERROR: no aparece "PERF: entering listo" en 90 s. El APK no trae BP_PerfEntering_SC' 'Red'
            Say 'o la app no llego a cargar el nivel. Abortando.' 'Red'
            exit 1
        }
        Start-Sleep -Seconds 1
        $n0 = Cuenta 'PERF: entering bucle'
        Send-Cmd 'ke * PerfELoop'
        if (-not (Espera-Patron 'PERF: entering bucle' $n0 6)) {
            Send-Cmd 'ke * PerfELoop'
            if (-not (Espera-Patron 'PERF: entering bucle' $n0 6)) {
                Say 'ERROR: el APK no contesta a "ke * PerfELoop" (no aparece el eco en el log).' 'Red'
                Say 'O es un APK sin BP_PerfEntering_SC, o no es Development (en Shipping "ke" no existe).' 'Red'
                exit 1
            }
        }
        if ((Cuenta 'BREATHSTAGE: fin de la etapa') -gt 0) {
            Say 'ERROR: la etapa ya habia terminado antes del bucle. Vuelve a correr el script.' 'Red'; exit 1
        }
        Say '  pacer en bucle: la etapa no termina hasta el final de la medicion.' 'Gray'

        # 2) Esperar a que el pacer este de verdad animando (entra + 3 s de pausa de entrada).
        if (-not (Espera-Patron 'BREATHSTAGE: pacer en marcha' 0 40)) { Say 'AVISO: no vi "pacer en marcha"; sigo igual.' 'Red' }
        Start-Sleep -Seconds 5

        # 3) Telemetria: sin lineas VrApi con App= no hay nada que medir.
        if ((Cuenta 'VrApi.*App=') -lt 3) {
            Say 'ERROR: logcat no trae la linea VrApi con "App=" (la telemetria de la Quest).' 'Red'
            Say 'Sin ella no hay tiempo de GPU que medir. Abortando.' 'Red'
            exit 1
        }
        $script:focoBase = Cuenta-Foco
        if ($script:focoBase -gt 0) {
            Say "AVISO: hubo $($script:focoBase) evento(s) de perdida de foco al arrancar. Si la imagen" 'Red'
            Say 'esta congelada, corta con Ctrl+C, cierra la app y vuelve a empezar con el casco puesto.' 'Red'
        }

        # 4) Control POSITIVO de cada modo: el eco prueba que el evento LLEGO; el efecto lo
        #    confirmas tu mirando (el metaball / el pacer tienen que desaparecer de verdad).
        Say 'Pruebo cada modo (2 s cada uno). Mira que pase lo que digo:' 'Gray'
        $unicos = $ModosNum | Sort-Object -Unique
        foreach ($m in $unicos) {
            $antes = Cuenta "PERF: entering modo $m"
            Send-Cmd "ke * PerfE$m"
            if (-not (Espera-Patron "PERF: entering modo $m" $antes 5)) {
                Say "ERROR: el modo $m NO contesto (no aparece 'PERF: entering modo $m'). Abortando." 'Red'; exit 1
            }
            Say ("  modo $m -> " + $desc[$m]) 'Gray'
            Start-Sleep -Seconds 2
        }
        Send-Cmd 'ke * PerfE0'
        Say '  OK: todos los modos contestan.' 'Green'

        # 5) Las fases: ida y vuelta.
        $orden = @($ModosNum) + @($ModosNum[($ModosNum.Count - 1)..0])
        $total = $orden.Count * ($Seconds + $Settle + 1)
        Write-Host ''
        Say "Arrancan $($orden.Count) fases de $Seconds s (unos $([int]($total / 60)) min $($total % 60) s)." 'Green'
        Say 'Haz lo MISMO todo el tiempo: mira el metaball como en la experiencia y respira'
        Say 'normal con el sensor en la panza. Lo que se compara entre fases es la misma vista.'
        $k = 0
        foreach ($m in $orden) {
            $k++
            if (Perdio-Foco) { Say 'ERROR: la app perdio el foco a mitad de la medicion. Abortando.' 'Red'; exit 1 }
            Send-Cmd "ke * PerfE$m"
            Say (">>> fase $k/$($orden.Count): modo $m - " + $desc[$m] + " - $Seconds s") 'Green'
            Start-Sleep -Seconds ($Seconds + $Settle)
        }

        # 6) Cierre natural de la etapa, grabado.
        $nf = Cuenta 'BREATHSTAGE: fin de la etapa'
        Send-Cmd 'ke * PerfEEnd'
        Say 'Medicion hecha. Todo visible otra vez; la etapa cierra en el proximo ciclo...' 'Cyan'
        if (-not (Espera-Patron 'BREATHSTAGE: fin de la etapa' $nf 60)) { Say 'AVISO: la etapa no cerro en 60 s.' 'Red' }
        Start-Sleep -Seconds 10
    }
}
finally {
    if ($logcat -and -not $logcat.HasExited) { Stop-Process -Id $logcat.Id -Force -ErrorAction SilentlyContinue }
}

Say 'LISTO. Ya puedes quitarte el visor.' 'Cyan'
Write-Host ("  sesion: $logFile  (" + [int]((Get-Item $logFile).Length / 1KB) + " KB)")
Write-Host ''

$py = Join-Path $repo '.claude\skills\unreal-vr\scripts\resumen_entering.py'
# resumen_entering.py escribe resumen.txt el mismo (UTF-8); Tee-Object de PS 5.1 lo
# dejaba en UTF-16.
& python "$py" "$OutDir"
Write-Host ''
Say ("Resumen guardado en " + (Join-Path $OutDir 'resumen.txt')) 'Gray'
