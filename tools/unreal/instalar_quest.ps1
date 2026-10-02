# instalar_quest.ps1 - instala el ultimo APK de la Obra (+ OBB) en el Quest conectado por USB, lo lanza ~60 s
# para ver que llega al Hall sin errores, y lo deja CERRADO con el visor en estado normal.
#   powershell -File tools/unreal/instalar_quest.ps1              (paquete com.almadigital.soulcharger)
#   powershell -File tools/unreal/instalar_quest.ps1 -Variante v2 (paquete com.almadigital.soulchargerv2, convive con el otro)
# Antes: python tools/unreal/empaquetar_obra.py [--variante v2]. El visor tiene que estar conectado y con depuracion USB.
# Si el OBB no queda (secure_mkdirs): abre la app una vez para que el sistema cree la carpeta y repite el push.
param([string]$Variante = "obra")
$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
if ($Variante -eq "v2") { $pkg = "com.almadigital.soulchargerv2"; $dir = Join-Path $root "VR_Test\Saved\Packaged\Android_ObraV2" }
else { $pkg = "com.almadigital.soulcharger"; $dir = Join-Path $root "VR_Test\Saved\Packaged\Android_Obra" }
$out = Join-Path $root "VR_Test\Saved\Logs"
$apk = Get-ChildItem -Recurse $dir -Filter *.apk | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$obb = Get-ChildItem -Recurse $dir -Filter "main.*.obb" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
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
& $adb shell am broadcast -a com.oculus.vrpowermanager.prox_close | Out-Null
& $adb shell setprop debug.oculus.guardian_pause 1
& $adb logcat -c
& $adb shell monkey -p $pkg -c android.intent.category.LAUNCHER 1 | Out-Null
"LAUNCH $(Get-Date -Format HH:mm:ss)"
$ok = $false
for ($i = 0; $i -lt 40; $i++) {
  Start-Sleep -Seconds 3
  if (& $adb logcat -d -v time -s UE:* | Select-String "HALL: modo 1 paso 1\b") { $ok = $true; break }
}
Start-Sleep -Seconds 3
& $adb logcat -d -v time -s UE:* | Out-File -Encoding utf8 "$out\logcat_instalar.txt"
"LLEGO AL HALL: $ok"
Get-Content "$out\logcat_instalar.txt" | Select-String "OBRA CONFIG|partitura cargada|OBRA: aviso|OBRA: Hall - inicio|HALL: modo 1 paso 1\b" | ForEach-Object { $_.Line.Substring([Math]::Max(0, $_.Line.Length - 140)) }
$err = Get-Content "$out\logcat_instalar.txt" | Select-String "Accessed None|Runtime Error|Fatal error|Assertion failed|Infinite loop"
"ERRORES: $(@($err).Count)"
$err | Select-Object -First 5 | ForEach-Object { $_.Line.Substring(0, [Math]::Min(200, $_.Line.Length)) }
& $adb shell am force-stop $pkg
& $adb shell am broadcast -a com.oculus.vrpowermanager.automation_disable | Out-Null
& $adb shell setprop debug.oculus.guardian_pause 0
"FIN $(Get-Date -Format HH:mm:ss)  (logcat completo: $out\logcat_instalar.txt)"
