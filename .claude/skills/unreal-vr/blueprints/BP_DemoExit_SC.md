# BP_DemoExit_SC — salida del operador de la demo

`/Game/SoulCharger/Demo/Blueprints/BP_DemoExit_SC` · colocado en los 3 niveles de la demo · vars `HoldTime` 2, `MenuLevel` "L_Demo_Menu", `Hold`, `bDone`, `MenuN`, `MenuLastT`.

- **Visor**: **cinco** toques del botón Menú **o Y** izquierdo (cada uno a menos de 0,7 s del anterior; `IMC_Default` mapea los dos a `IA_Menu_Toggle_Left`) → `OpenLevel(MenuLevel)`. Cinco para que un visitante que toca Y no lo dispare. Evento `IA_Menu_Toggle_Left` (de `IMC_Default`, que agrega el pawn; trigger Pressed = un evento por toque) creado por cirugía → `MenuPress`. CDO `AutoReceiveInput` = Player0. ⬜ verificar en visor.
- **Escritorio**: mantener **M** `HoldTime` s (Tick con `IsInputKeyDown`; en el visor ese camino no funciona para teclas XR). 19-10: las dos teclas estaban en `(` (camino muerto); ahora `M` en los dos nodos.
- 2026-10-19: era "mantener Menú 2 s" por `IsInputKeyDown`, que en el visor nunca llega. El botón Menú del framework dispara una vez por toque (no sirve para "mantener"), de ahí los toques (3 primero, 5 después de ver que Y comparte la acción).
