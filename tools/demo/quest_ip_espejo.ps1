# quest_ip_espejo.ps1 - le dice a la demo del Quest a que IP mandar el espejo (el robot), sin recocinar el APK.
#
#   powershell -File tools/demo/quest_ip_espejo.ps1 -IP 192.168.1.50          # deja la IP fija en el visor (persiste)
#   powershell -File tools/demo/quest_ip_espejo.ps1 -IP 192.168.1.50 -Lanzar  # ademas abre la demo en el visor con esa IP
#   powershell -File tools/demo/quest_ip_espejo.ps1 -Borrar                   # vuelve a la IP que trae el APK
#   powershell -File tools/demo/quest_ip_espejo.ps1 -IP 192.168.0.190 -Extra "-DemoRenderPct=100"  # agrega parametros (21-10:
#       -DemoRenderPct=N pisa la resolucion del visor de los 4 niveles; sin -Extra cada nivel usa su RenderPct)
#
# Como funciona (LaunchAndroid.cpp, UE 5.8): en un build Development el juego lee
#   <GFilePathBase>/UnrealGame/VR_Test/UECommandLine.txt
# y REEMPLAZA su linea de comandos por la primera linea de ese archivo. Por eso el archivo lleva la linea normal del
# proyecto mas -MirrorIP=<IP>. BP_MirrorLink_SC lee -MirrorIP= en su Boot.
# GFilePathBase depende de la version de Android/almacenamiento: se escribe en las dos rutas posibles.
# Con -Lanzar usa ademas el extra 'cmdline' del intent (am start ... -e cmdline), que se AGREGA a la linea de comandos.
# ⬜ Sin verificar en el visor (2026-10-16): confirmar en logcat la linea "Override Commandline" o "MIRROR: emisor -> <IP>".
param([string]$IP = "", [switch]$Lanzar, [switch]$Borrar, [string]$Extra = "", [string]$Paquete = "com.almadigital.soulchargerdemo")
$pkg = $Paquete   # 24-10: -Paquete com.almadigital.soulchargerdemobi para la demo bilingue
$rutas = @("/sdcard/Android/data/$pkg/files/UnrealGame/VR_Test", "/sdcard/UnrealGame/VR_Test")
if (-not (adb devices | Select-String "device$")) { Write-Host "No hay visor conectado por adb."; exit 1 }
if ($Borrar) {
    foreach ($r in $rutas) { adb shell rm -f "$r/UECommandLine.txt" | Out-Null }
    Write-Host "Borrado: la demo usa la IP que trae el APK."; exit 0
}
if ($IP -notmatch '^\d{1,3}(\.\d{1,3}){3}$') { Write-Host "Pasar la IP del PC del robot: -IP 192.168.x.x"; exit 1 }
$linea = ("../../../VR_Test/VR_Test.uproject -MirrorIP=$IP " + $Extra).Trim()
$tmp = Join-Path $env:TEMP "UECommandLine.txt"
[IO.File]::WriteAllText($tmp, $linea + "`n")
foreach ($r in $rutas) {
    adb shell mkdir -p "$r" | Out-Null
    adb push $tmp "$r/UECommandLine.txt" | Out-Null
    Write-Host "escrito: $r/UECommandLine.txt -> $linea"
}
if ($Lanzar) {
    adb shell am force-stop $pkg | Out-Null
    $cl = ("-MirrorIP=$IP " + $Extra).Trim()
    adb shell "am start -n $pkg/com.epicgames.unreal.GameActivity -e cmdline '$cl'" | Out-Null
    Write-Host "demo abierta con $cl. Ver en logcat: adb logcat -s UE | Select-String MIRROR"
}
