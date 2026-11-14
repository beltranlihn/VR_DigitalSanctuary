# instalar_quest.ps1 - instala el ultimo APK de la Obra (+ OBB) en el Quest conectado por USB, lo lanza ~60 s
# para ver que llega al Hall sin errores, y lo deja CERRADO con el visor en estado normal.
#   powershell -File tools/unreal/instalar_quest.ps1              (paquete com.almadigital.soulcharger)
#   powershell -File tools/unreal/instalar_quest.ps1 -Variante v2 (paquete com.almadigital.soulchargerv2, convive con el otro)
#   powershell -File tools/unreal/instalar_quest.ps1 -Variante demo (paquete com.almadigital.soulchargerdemo, carpeta Android_Demo;
#       en vez del Hall espera que cargue L_Demo_Menu; -Marcador '<regex>' cambia esa senal, p. ej. un PrintString del menu)
#   -Variante demobi (24-10, feria): la demo bilingue (ENGLISH/ESPANOL), paquete com.almadigital.soulchargerdemobi, carpeta Android_DemoBi.
#   -Simular: solo muestra paquete, carpeta, APK, OBB y destino en el visor; no toca adb.
# Antes: python tools/unreal/empaquetar_obra.py [--variante v2|demo]. El visor tiene que estar conectado y con depuracion USB.
# Si el OBB no queda (secure_mkdirs): abre la app una vez para que el sistema cree la carpeta y repite el push.
#   -SinLanzar (22-10, feria): solo instala APK + OBB; no abre la app ni toca el sensor de proximidad ni el guardian (al final
#       el flujo normal hace automation_disable, que deshace el "pantalla siempre encendida" de prox_close).
param([ValidateSet("obra", "v2", "demo", "demobi")][string]$Variante = "obra", [string]$Marcador = "", [switch]$Simular, [switch]$SinLanzar)
$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
# $marca = linea de logcat que confirma que arranco; $resumen = lineas que se muestran al final; $meta = como se llama ese punto
$marca = "HALL: modo 1 paso 1\b"; $resumen = "OBRA CONFIG|partitura cargada|OBRA: aviso|OBRA: Hall - inicio|HALL: modo 1 paso 1\b"; $meta = "HALL"
if ($Variante -eq "v2") { $pkg = "com.almadigital.soulchargerv2"; $dir = Join-Path $root "VR_Test\Saved\Packaged\Android_ObraV2" }
elseif ($Variante -eq "demo" -or $Variante -eq "demobi") {
  $pkg = "com.almadigital.soulchargerdemo"; $dir = Join-Path $root "VR_Test\Saved\Packaged\Android_Demo"
  if ($Variante -eq "demobi") { $pkg = "com.almadigital.soulchargerdemobi"; $dir = Join-Path $root "VR_Test\Saved\Packaged\Android_DemoBi" }
  $marca = "seconds to LoadMap\(.*L_Demo_Menu"; $resumen = "DEMO:|seconds to LoadMap\(.*L_Demo_"; $meta = "MENU"
}
else { $pkg = "com.almadigital.soulcharger"; $dir = Join-Path $root "VR_Test\Saved\Packaged\Android_Obra" }
if ($Marcador) { $marca = $Marcador }
$out = Join-Path $root "VR_Test\Saved\Logs"
$apk = Get-ChildItem -Recurse $dir -Filter *.apk -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$obb = Get-ChildItem -Recurse $dir -Filter "main.*.obb" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($Simular) {
  "SIMULACION (no se toca el visor)"
  "variante $Variante  paquete $pkg"
  "carpeta  $dir"
  "APK      $(if ($apk) { $apk.FullName } else { '(todavia no hay: empaqueta primero)' })"
  "OBB      $(if ($obb) { $obb.FullName } else { '(todavia no hay: empaqueta primero)' }) -> /sdcard/Android/obb/$pkg/$(if ($obb) { $obb.Name } else { 'main.<n>.' + $pkg + '.obb' })"
  "llego al $meta si el logcat (UE) coincide con: $marca"
  "resumen final con: $resumen"
  exit 0
}
if (-not $apk -or -not $obb) { "No hay APK u OBB en $dir. Empaqueta primero: python tools/unreal/empaquetar_obra.py --variante $Variante"; exit 1 }
"APK $($apk.LastWriteTime)  OBB $($obb.Length)"
& $adb shell am force-stop $pkg
& $adb install -r "$($apk.FullName)" | Select-Object -Last 1
& $adb push "$($obb.FullName)" "/sdcard/Android/obb/$pkg/$($obb.Name)" | Select-Object -Last 1
$rs = (& $adb shell "stat -c %s /sdcard/Android/obb/$pkg/$($obb.Name) 2>/dev/null").Trim()
if ($rs -ne "$($obb.Length)") {
  "OBB no quedo ($rs): abro la app una vez para que el sistema cree la carpeta y repito"
  & $adb shell monkey -p $pkg -c android.intent.category.LAUNCHER 1 | Out-Null
  Start-Sleep -Seconds 4
  & $adb shell am force-stop $pkg
  & $adb push "$($obb.FullName)" "/sdcard/Android/obb/$pkg/$($obb.Name)" | Select-Object -Last 1
  $rs = (& $adb shell "stat -c %s /sdcard/Android/obb/$pkg/$($obb.Name) 2>/dev/null").Trim()
}
"OBB en el visor: $rs bytes (local $($obb.Length))"
if ($SinLanzar) { "instalado sin abrir (-SinLanzar): la app queda cerrada y el sensor de proximidad como estaba"; exit 0 }
& $adb shell am broadcast -a com.oculus.vrpowermanager.prox_close | Out-Null
& $adb shell setprop debug.oculus.guardian_pause 1
& $adb logcat -c
& $adb shell monkey -p $pkg -c android.intent.category.LAUNCHER 1 | Out-Null
"LAUNCH $(Get-Date -Format HH:mm:ss)"
$ok = $false
for ($i = 0; $i -lt 40; $i++) {
  Start-Sleep -Seconds 3
  if (& $adb logcat -d -v time -s UE:* | Select-String $marca) { $ok = $true; break }
}
Start-Sleep -Seconds 3
& $adb logcat -d -v time -s UE:* | Out-File -Encoding utf8 "$out\logcat_instalar.txt"
"LLEGO AL ${meta}: $ok"
Get-Content "$out\logcat_instalar.txt" | Select-String $resumen | ForEach-Object { $_.Line.Substring([Math]::Max(0, $_.Line.Length - 140)) }
$err = Get-Content "$out\logcat_instalar.txt" | Select-String "Accessed None|Runtime Error|Fatal error|Assertion failed|Infinite loop"
"ERRORES: $(@($err).Count)"
$err | Select-Object -First 5 | ForEach-Object { $_.Line.Substring(0, [Math]::Min(200, $_.Line.Length)) }
& $adb shell am force-stop $pkg
& $adb shell am broadcast -a com.oculus.vrpowermanager.automation_disable | Out-Null
& $adb shell setprop debug.oculus.guardian_pause 0
"FIN $(Get-Date -Format HH:mm:ss)  (logcat completo: $out\logcat_instalar.txt)"
