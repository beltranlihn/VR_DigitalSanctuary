<#
    quest_perfmodes.ps1 - BANCO DE MEDICION del material de blobs (estacion Attracting).

    QUE RESUELVE. Medir dos builds en dos sesiones distintas NO sirve: el 2026-09-25 el
    MISMO build sin optimizar dio 21,65 y 24,85 ms (~15% de ruido). La causa es el
    protocolo: en una escena fill-rate bound manda cuanta pantalla cubren las gotas, o sea
    hacia donde mirabas. Aca las N fases corren en UNA sola sesion, alternando el modo del
    material por consola, asi que comparten escena, pose y estado termico. Gotcha 379.

    COMO FUNCIONA. El material M_SlotChain_SC lee PerfMode de la coleccion MPC_Perf_SC.
    BP_PerfSwitch_SC (actor PerfSwitch en TestMeshes) tiene los eventos Perf0..Perf3 que
    escriben esa coleccion. Se disparan por consola con "ke * PerfN" ("ke" = KismetEvent,
    vive en UEngine::Exec_Dev bajo #if !UE_BUILD_SHIPPING -> funciona en Development).

    LOS MODOS
      0  actual        el material tal como esta autorado. Es la referencia.
      1  steps/2       la mitad de pasos de raymarch.
      2  sdf lisa      sin wobble ni decoracion (raymarch mas barato).
      3  gratis        el material sale al instante sin dibujar. Es el PISO.
      4  solo cadena   las 20 esferas no dibujan (discrimina por WobbleAFS.x > 0).
      5  solo esferas  la cadena no dibuja.
      6  reloj half    +1024 s al reloj por el camino half (control invalido, ver gotcha 382).
      7  reloj fp32    +1024 s al reloj por el camino arreglado.
      8  sin poda      todo dibujado pero SIN la poda por gota de A4.

    EL A/B DE A4 (2026-09-25):  -Modos 0,8  mide cuanto rinde la poda por gota con la
    escena, la pose y el estado termico compartidos. El modo 8 es el 'antes' y el 0 el
    'despues', asi que ademas sirve de verificacion VISUAL: si en el visor los dos se
    ven iguales, la poda no cambio la imagen (que es todo su contrato).

    LA CUENTA QUE DECIDE:  (modo 0) - (modo 3) = lo que cuesta TODA la tecnica de blobs.
    Si ese numero es chico, el problema no son los blobs y hay que buscar en otro lado.
    Si es grande, dice exactamente cuanto presupuesto libera cambiar de tecnica.

    EL SPLIT (2026-09-25): -Modos 0,4,5,3 parte esos 12,28 ms entre cadena y esferas:
      esferas = (modo 5) - piso   |   cadena = (modo 4) - piso
      y como el modo 3 esta pegado al cap de 72 Hz (no se le ve el piso real),
      piso derivado = (modo 4) + (modo 5) - (modo 0), que el vsync no tapa.
    Decide cuanto rinde reemplazar SOLO las esferas por malla (enfoque C) y si la
    cadena necesita trabajo propio. resumen_modos.py imprime esta cuenta solo.

    LA MALLA DEL ENFOQUE C (2026-09-26). M_BlobMesh_SC (el tubo por vertices que
    reemplaza la cadena raymarch) lee el MISMO gate: en los modos 3 y 5 apaga la
    opacidad Y colapsa la geometria al origen del objeto (WPO = -LocalPos), asi que
    en esos modos NO rasteriza nada. Es el unico apagado valido para una malla
    translucida: con opacidad 0 el pixel shader igual corre y igual mezcla.
      -Modos 0,5,3   con la cadena raymarch FUERA de la escena:
          malla   = (modo 0) - (modo 5)     <- las esferas son identicas en los dos
          esferas = (modo 5) - (modo 3)
      OJO con el modo 3: suele quedar pegado al cap de 72 Hz y entonces el piso real
      no se ve. Si los tres dan parecido y clavados en ~13,9, la lectura correcta no
      es "cuesta 0" sino "entra en presupuesto"; para sacarle un numero hace falta el
      piso derivado, como en el split del 2026-09-25.
      Referencia contra la que se compara: cadena raymarch >= 8,93 ms, esferas 5,81 ms.

    Dos trampas de PowerShell 5.1 que este archivo esquiva (igual que sus hermanos):
      1. NADA de $ErrorActionPreference='Stop' con exes nativos: adb escribe cosas
         inocuas en stderr y PS 5.1 las convierte en error terminante.
      2. Archivo en ASCII puro: PS 5.1 lee los .ps1 como ANSI y un acento rompe el parser.

    Uso:  .\quest_perfmodes.ps1
          .\quest_perfmodes.ps1 -Seconds 20
          .\quest_perfmodes.ps1 -Modos 0,4,5,3     (el split cadena vs esferas)
#>
param(
    [string]$Package = 'com.almadigital.TESTMESHES',
    [string]$Project = 'VR_Test',
    [int]$Seconds = 20,
    [int]$Delay = 25,
    [string]$OutDir = '',
    # Como texto a proposito: 'powershell -File' y cmd parten '0,4,5,3' de formas
    # distintas (cmd usa la coma como separador de argumentos y PS puede leer '4,5,3'
    # como 453 con separador de miles). Aca se extraen los DIGITOS, venga como venga:
    # -Modos 0,4,5,3  |  -Modos '0 4 5 3'  |  -Modos 0453   -> todos dan 0,4,5,3.
    [string[]]$Modos = @('0', '1', '2', '3'),
    # ???? 2026-09-25: NO LANZAR LA APP POR INTENT. Arrancarla con 'am force-stop' + 'am start'
    # la deja sin una sesion de VR bien establecida y aparece el APP_CMD_LOST_FOCUS ->
    # APP_CMD_PAUSE -> deadlock del camino de suspension de UE en Android (imagen
    # congelada, sonido siguiendo, GPU en 0, proceso vivo). Beltran lo aislo abriendo la
    # app A MANO desde la biblioteca del visor: asi no se cuelga.
    # Por eso el default es ENGANCHARSE a la app que ya corre. -Lanzar la lanza igual.
    [switch]$Lanzar
)

$ModosNum = @()
foreach ($tok in $Modos) {
    foreach ($ch in ([string]$tok).ToCharArray()) {
        if ($ch -ge '0' -and $ch -le '9') { $ModosNum += [int][string]$ch }
    }
}
if ($ModosNum.Count -eq 0) { $ModosNum = @(0, 1, 2, 3) }

$ErrorActionPreference = 'Continue'

# .../.claude/skills/unreal-vr/scripts/x.ps1 -> 5 niveles hasta la raiz del repo.
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

# El CsvProfiler nombra los archivos Profile(2026...).csv y esos PARENTESIS rompen el pull.
function Renombrar-Ultimo([string]$destino) {
    $todos = @((Adb shell "ls -t $csvDir") -split "`n" | ForEach-Object { $_.Trim() } |
        Where-Object { $_ -match '\.csv$' -and $_ -notmatch '^modo' })
    if (-not $todos) { return $false }
    Adb shell "mv '$csvDir/$($todos[0])' '$csvDir/$destino'" | Out-Null
    return $true
}

# --- las fases. Se corren DOS VECES en orden inverso la segunda vuelta, para que una
#     deriva termica progresiva no se le cargue toda a la ultima fase. -----------------
$catalogo = @{
    0 = @{ n = 'modo0_actual';  ev = 'Perf0'; m = 0 }
    1 = @{ n = 'modo1_steps';   ev = 'Perf1'; m = 1 }
    2 = @{ n = 'modo2_lisa';    ev = 'Perf2'; m = 2 }
    3 = @{ n = 'modo3_gratis';  ev = 'Perf3'; m = 3 }
    4 = @{ n = 'modo4_cadena';  ev = 'Perf4'; m = 4 }
    5 = @{ n = 'modo5_esferas'; ev = 'Perf5'; m = 5 }
    6 = @{ n = 'modo6_relojhalf'; ev = 'Perf6'; m = 6 }
    7 = @{ n = 'modo7_relojfp32'; ev = 'Perf7'; m = 7 }
    8 = @{ n = 'modo8_sinpoda';  ev = 'Perf8'; m = 8 }
}
$lista = @()
foreach ($m in $ModosNum) {
    if (-not $catalogo.ContainsKey($m)) { Say "ERROR: modo $m no existe (0-8)." 'Red'; exit 1 }
    $lista += $catalogo[$m]
}
Say ("Modos pedidos: " + ($ModosNum -join ', ')) 'Gray'
$orden = @($lista) + @($lista[($lista.Count - 1)..0])

if ((Adb devices) -notmatch "`tdevice") { Say 'ERROR: no hay ninguna Quest conectada.' 'Red'; exit 1 }

# ???? EL CASCO VA PRIMERO, LA APP DESPUES (2026-09-25). Con el visor fuera de la cabeza la
# Quest manda la app a segundo plano en segundos, y el camino de suspension de UE en Android
# se DEADLOCKEA: el log queda en "SuspendApp_EventThread -> ERROR: backgrounding callback,
# not responded in timely manner" + "Blocking renderer on suspended window", y la app no
# vuelve nunca. Visto dos veces seguidas. Por eso ahora se lanza la app con el casco YA
# puesto, y no hay ninguna espera larga entre el arranque y las fases.
$total = ($Seconds * $orden.Count) + ($orden.Count * 6) + 40
Write-Host ''
Say "PONETE EL VISOR AHORA. La app arranca en $Delay segundos."
Say "Despues son unos $total segundos con el casco puesto, en $($orden.Count) fases de $Seconds s."
Say 'NO te saques el casco hasta el final: si la app pasa a segundo plano se cuelga.'
Say 'IMPORTANTE: juga PARECIDO todo el tiempo (agarra esferas, colocalas, mira la fila'
Say 'de gotas). Lo que se compara entre fases es el mismo tipo de vista.'
Say 'En algunas fases las gotas se van a ver distintas o directamente NO se van a ver:'
Say 'es a proposito, es la medicion.'
for ($t = $Delay; $t -gt 0; $t--) {
    if ($t -le 5 -or $t % 5 -eq 0) { Write-Host "   $t..." }
    Start-Sleep -Seconds 1
}
Write-Host ''
Adb shell "rm -rf $csvDir" | Out-Null
if ($Lanzar) {
    Say 'Lanzando la app por intent (OJO: es lo que colgaba, ver la cabecera)...' 'Gray'
    Adb shell "am force-stop $Package" | Out-Null
    Start-Sleep -Seconds 2
    Adb shell "am start -n $Package/com.epicgames.unreal.GameActivity" | Out-Null
} else {
    Say 'Esperando la app que ABRISTE VOS desde la biblioteca del visor...' 'Gray'
}
$vivo = $false
for ($i = 0; $i -lt 90; $i++) {
    if ((Adb shell "pidof $Package").Trim()) { $vivo = $true; break }
    Start-Sleep -Seconds 1
}
if (-not $vivo) {
    Say 'ERROR: la app no esta corriendo. Abrila desde la biblioteca del visor' 'Red'
    Say 'y volve a correr el script (o usa -Lanzar para que la lance el script).' 'Red'
    exit 1
}
Say "App viva. Dale unos segundos a la estacion si recien la abriste." 'Gray'
Start-Sleep -Seconds 5

# Control POSITIVO: si "ke" no llega al Blueprint, todo lo demas mide cualquier cosa.
# Se prueba CADA modo pedido, no uno solo: un APK viejo puede tener Perf0-3 pero no 4/5,
# y esas fases mediria(n) el modo anterior sin avisar.
Say 'Probando que CADA modo pedido conteste desde el Blueprint...' 'Gray'
$unicos = @{}
foreach ($f in $lista) { $unicos[$f.m] = $f.ev }
foreach ($m in ($unicos.Keys | Sort-Object)) {
    Adb logcat -c | Out-Null
    Send-Cmd "ke * $($unicos[$m])"
    Start-Sleep -Seconds 2
    $eco = (Adb logcat -d) -split "`n" | Select-String -Pattern "PERF: modo $m"
    if (-not $eco) {
        Say "ERROR: el modo $m NO contesto (no aparece 'PERF: modo $m' en el log)." 'Red'
        Say 'Si es el 4 o el 5: el APK instalado es viejo, hay que reempaquetar.' 'Red'
        Say 'Sin el eco esa fase mediria otra cosa sin avisar. Abortando.' 'Red'
        exit 1
    }
    Say "  modo $m responde." 'Gray'
}
Say '  OK: todos los modos contestan.' 'Green'
Send-Cmd 'ke * Perf0'

Send-Cmd 'r.GPUStatsEnabled 1'
Send-Cmd 'r.GPUCsvStatsEnabled 1'

# Guardia de FOCO: si la app ya se fue a segundo plano, medir es tirar el tiempo.
$pausa = (Adb logcat -d) -split "`n" | Select-String -Pattern 'APP_CMD_PAUSE|APP_CMD_LOST_FOCUS'
if ($pausa) {
    Say 'ERROR: la app perdio el foco (APP_CMD_PAUSE/LOST_FOCUS en el log).' 'Red'
    Say 'Pasa cuando el casco no esta puesto: la Quest la suspende y UE se traba ahi.' 'Red'
    Say 'Ponete el visor ANTES de correr el script y volve a intentar. Abortando.' 'Red'
    exit 1
}
Write-Host ''
Say 'Arrancando las fases. Segui mirando.' 'Green'

$k = 0
foreach ($f in $orden) {
    $k++
    $etiqueta = "$($f.n)_p$k"
    Send-Cmd "ke * $($f.ev)"
    Start-Sleep -Seconds 2
    Say ">>> fase $k/$($orden.Count): $($f.n) - $Seconds s" 'Green'
    Send-Cmd 'CsvProfile Start'
    Start-Sleep -Seconds $Seconds
    Send-Cmd 'CsvProfile Stop'
    Start-Sleep -Seconds 4
    if (-not (Renombrar-Ultimo "$etiqueta.csv")) { Say "  AVISO: la fase $k no dejo CSV." 'Red' }
}

Send-Cmd 'ke * Perf0'
Say 'LISTO. Sacate el visor. (El material vuelve al modo 0.)' 'Cyan'

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$k = 0
foreach ($f in $orden) {
    $k++
    $etiqueta = "$($f.n)_p$k"
    $destino = Join-Path $OutDir "$etiqueta.csv"
    if (Test-Path $destino) { Remove-Item $destino -Force }
    Adb pull "$csvDir/$etiqueta.csv" $destino | Out-Null
    if (Test-Path $destino) { Write-Host ("  $etiqueta.csv  (" + [int]((Get-Item $destino).Length / 1KB) + " KB)") }
    else { Say "  FALLO al traer $etiqueta.csv" 'Red' }
}

Write-Host ''
Say 'Listo. Resumilo con:' 'Gray'
Write-Host "  python `"$repo\.claude\skills\unreal-vr\scripts\resumen_modos.py`" `"$OutDir`""
