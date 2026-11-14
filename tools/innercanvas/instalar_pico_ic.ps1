# instalar_pico_ic.ps1 - instala Inner Canvas en uno o varios visores PICO y le dice a cada uno su numero (1..8) y la IP del PC.
#
#   powershell -File tools/innercanvas/instalar_pico_ic.ps1 -Listar                     # visores conectados por adb (serie)
#   powershell -File tools/innercanvas/instalar_pico_ic.ps1 -Slot 3 -Wall 192.168.1.10  # el unico visor conectado = visor 3
#   powershell -File tools/innercanvas/instalar_pico_ic.ps1 -Serial PA9X... -Slot 3 -Wall 192.168.1.10
#   powershell -File tools/innercanvas/instalar_pico_ic.ps1 -Todos -Wall 192.168.1.10   # cada visor conectado con su numero de
#                                                                                       #   tools/innercanvas/visores_ic.json
#   -SoloLinea: no reinstala; solo cambia el numero y la IP (UECommandLine.txt). -Lanzar: abre la app y espera "IC: arranca".
#   -Simular: muestra que haria. -Extra "<args>": parametros extra para la linea de comandos (p. ej. -PicoAimPitch=-8).
#   Correccion de poses del PICO (BP_ICFlow_IC, PLAN-INNER-CANVAS §5): -PicoAimPitch= (grados, negativo = el laser baja; -15 por
#   defecto) -PicoAimFwd= (cm que la punta y el laser salen hacia adelante; 5) -PicoGripUp= (cm que suben mando y paleta; 2)
#   -PicoFix=0 la apaga. Medir: -Extra "-PoseDump" y  adb logcat -s UE | findstr SCPOSE  (aim respecto del grip, cada 1 s).
#   Ajustar sin reinstalar: -SoloLinea -Extra "-PicoAimPitch=-10 -PicoGripUp=1.5"
#
# El numero y la IP van en UECommandLine.txt (LaunchAndroid.cpp: un build Development reemplaza su linea de comandos por la del
# archivo; ver tools/demo/quest_ip_espejo.ps1). BP_ICLink_IC lee -ICSlot=, -ICWall= y -ICPort=.
# Antes: python tools/unreal/empaquetar_obra.py --variante innercanvas
#   -Variante quest (2026-11-13): el build de Meta Quest (Quest 2/3), app aparte com.almadigital.innercanvasquest, carpeta
#   Android_InnerCanvasQuest. Antes: python tools/unreal/empaquetar_obra.py --variante innercanvasquest
param([int]$Slot = 0, [string]$Wall = "", [string]$Serial = "", [switch]$Todos, [switch]$Listar, [switch]$SoloLinea,
      [switch]$Lanzar, [switch]$Simular, [string]$Extra = "", [int]$Port = 9300, [ValidateSet("pico", "quest")][string]$Variante = "pico")
$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$pkg = "com.almadigital.innercanvas"
$dir = Join-Path $root "VR_Test\Saved\Packaged\Android_InnerCanvas"
if ($Variante -eq "quest") { $pkg = "com.almadigital.innercanvasquest"; $dir = Join-Path $root "VR_Test\Saved\Packaged\Android_InnerCanvasQuest" }
$mapa = Join-Path $PSScriptRoot "visores_ic.json"
$serials = @(& $adb devices | Select-String "\tdevice$" | ForEach-Object { ($_.Line -split "\t")[0] })
if ($Listar) {
  "visores conectados: $($serials.Count)"
  foreach ($s in $serials) { "  $s  modelo: $((& $adb -s $s shell getprop ro.product.model).Trim())  sistema: $((& $adb -s $s shell getprop ro.build.display.id).Trim())" }
  if (Test-Path $mapa) { "numeros (visores_ic.json):"; Get-Content $mapa }
  exit 0
}
if ($Wall -notmatch '^\d{1,3}(\.\d{1,3}){3}$') { "Pasar la IP del PC de la pantalla: -Wall 192.168.x.x"; exit 1 }
$plan = @()
if ($Todos) {
  if (-not (Test-Path $mapa)) { "Falta $mapa con {`"<serie>`": <numero>, ...} (ver -Listar)"; exit 1 }
  $m = Get-Content $mapa -Raw | ConvertFrom-Json
  foreach ($s in $serials) { if ($m.$s) { $plan += ,@($s, [int]$m.$s) } else { "aviso: $s no esta en visores_ic.json, lo salteo" } }
} else {
  if ($Slot -lt 1 -or $Slot -gt 8) { "Pasar -Slot 1..8 (o -Todos con visores_ic.json)"; exit 1 }
  if (-not $Serial) {
    if ($serials.Count -ne 1) { "Hay $($serials.Count) visores conectados: pasar -Serial (ver -Listar)"; exit 1 }
    $Serial = $serials[0]
  }
  $plan += ,@($Serial, $Slot)
}
$apk = Get-ChildItem -Recurse $dir -Filter *.apk -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$obb = Get-ChildItem -Recurse $dir -Filter "main.*.obb" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $SoloLinea -and -not $apk) { "No hay APK en $dir. Empaquetar primero: python tools/unreal/empaquetar_obra.py --variante innercanvas"; exit 1 }
foreach ($p in $plan) {
  $s = $p[0]; $n = $p[1]
  $linea = ("../../../VR_Test/VR_Test.uproject -ICSlot=$n -ICWall=$Wall -ICPort=$Port " + $Extra).Trim()
  "== visor $n ($s): $linea"
  if ($Simular) { "   APK $($apk.FullName)  OBB $(if ($obb) { $obb.Name } else { '(sin OBB)' })"; continue }
  & $adb -s $s shell am force-stop $pkg
  if (-not $SoloLinea) {
    & $adb -s $s install -r "$($apk.FullName)" | Select-Object -Last 1
    if ($obb) {
      & $adb -s $s push "$($obb.FullName)" "/sdcard/Android/obb/$pkg/$($obb.Name)" | Select-Object -Last 1
      $rs = "$(& $adb -s $s shell "stat -c %s /sdcard/Android/obb/$pkg/$($obb.Name) 2>/dev/null")".Trim()
      if ($rs -ne "$($obb.Length)") {
        "   OBB no quedo ($rs): abro la app una vez y repito"
        & $adb -s $s shell monkey -p $pkg -c android.intent.category.LAUNCHER 1 | Out-Null
        Start-Sleep -Seconds 4
        # 2026-11-13 (gafa 7): esperar a que la app cree SU carpeta UnrealGame/VR_Test antes de cerrarla; si la crea el mkdir de
        # adb mas abajo (duenio shell), Unreal no puede escribir Saved/ ni su log
        for ($w = 0; $w -lt 20; $w++) { if ("$(& $adb -s $s shell "ls -d /sdcard/Android/data/$pkg/files/UnrealGame/VR_Test 2>/dev/null")".Trim()) { break }; Start-Sleep -Seconds 2 }
        & $adb -s $s shell am force-stop $pkg
        & $adb -s $s push "$($obb.FullName)" "/sdcard/Android/obb/$pkg/$($obb.Name)" | Select-Object -Last 1
      }
    }
  }
  # la carpeta de la app tiene que existir (creada por la app) antes de escribir la linea; si no, se abre una vez y se espera
  if (-not "$(& $adb -s $s shell "ls -d /sdcard/Android/data/$pkg/files/UnrealGame/VR_Test 2>/dev/null")".Trim()) {
    "   la app todavia no creo su carpeta: la abro y espero"
    & $adb -s $s shell monkey -p $pkg -c android.intent.category.LAUNCHER 1 | Out-Null
    for ($w = 0; $w -lt 30; $w++) { Start-Sleep -Seconds 2; if ("$(& $adb -s $s shell "ls -d /sdcard/Android/data/$pkg/files/UnrealGame/VR_Test 2>/dev/null")".Trim()) { break } }
    & $adb -s $s shell am force-stop $pkg
  }
  $tmp = Join-Path $env:TEMP "UECommandLine_ic.txt"
  [IO.File]::WriteAllText($tmp, $linea + "`n")
  foreach ($r in @("/sdcard/Android/data/$pkg/files/UnrealGame/VR_Test", "/sdcard/UnrealGame/VR_Test")) {
    & $adb -s $s shell mkdir -p "$r" | Out-Null
    & $adb -s $s push $tmp "$r/UECommandLine.txt" | Out-Null
  }
  "   linea de comandos escrita"
  if ($Lanzar) {
    # 2026-11-13: se lee el log que la app escribe EN el visor, no logcat: el runtime PICO llena logcat con un aviso del eye tracking
    # (XR_ERROR_EYEGAZY_PERMISION_NOT_ENABLE_BD, ~70 lineas/s) y las lineas UE se pierden del buffer -> daba "arranco: False" en falso.
    $ulog = "/sdcard/Android/data/$pkg/files/UnrealGame/VR_Test/VR_Test/Saved/Logs/VR_Test.log"
    & $adb -s $s shell rm -f $ulog
    & $adb -s $s shell monkey -p $pkg -c android.intent.category.LAUNCHER 1 | Out-Null
    $ok = $false
    for ($i = 0; $i -lt 30; $i++) {
      Start-Sleep -Seconds 2
      $l = & $adb -s $s shell "grep -E 'IC: arranca Inner Canvas|LINK: visor|IC: correccion PICO|Accessed None|Fatal error' $ulog 2>/dev/null"
      if ($l | Select-String "IC: arranca Inner Canvas") { $ok = $true; break }
    }
    "   arranco: $ok"
    $l | Select-Object -First 8 | ForEach-Object { "   " + $_.Substring([Math]::Max(0, $_.Length - 150)) }
  }
}
"FIN"
