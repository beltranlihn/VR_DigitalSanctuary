# BP_DemoInstr_SC — el panel de instrucciones de cada experiencia de la demo

- **refPath**: `/Game/SoulCharger/Demo/Blueprints/BP_DemoInstr_SC` · parent Actor · creado 2026-10-16 (sesión Director).
- **Colocado en**: `L_Demo_Breath` (y `L_Demo_Draw`), con un `BP_ShareButton_SC` de tag `demo_instr` (el panel) y un `BP_SeqRig_SC` (el láser, `bShowControllers` false: en la mano ya está el sensor o el pincel).
- **Estado**: 🟡 compila; ⬜ PIE; ⬜ visor. Páginas provisorias (la máscara del cuadro) hasta que lleguen `T_Instr_*` de Blender.

## Qué hace
El panel es un `BP_ShareButton_SC` con **`bStay` = true** (nueva perilla de ese BP, 2026-10-16): después del clic se re-arma (`Rearm`) en vez de irse. Este director:
1. **St 0** — espera a que el ensayo (`BP_StageRunner_SC`) esté en `RPhase` 2 (Alma ya dio la bienvenida y fue al costado; `StageIntro` llamado) y `ShowDelay` s más → `ShowCard`: corrige la altura (`cam.z − (PlayerStart.z + EyeRef)`), pone la página 0 (`SetMaterial` slot 1 de `Plate`), `Appear`, `ResultsBeam(true)`.
2. **St 1** — `Pick`: hover por `Rig.BeamHitActor` + `AppearT ≥ 0,999`; clic = cambió `Rig.ResPressN` → `Press`.
3. **St 2** — a `PressWait` s (la luz dio la vuelta) → `Advance`: página siguiente, o en la última `Vanish` + `ResultsBeam(false)`.
4. **St 3** — 1 s después → `Runner.PT = Runner.InstrTime` → el ensayo llama `StageBegin` en su próximo tick.

🔴 Para que el ensayo **espere** al panel, `DA_Partitura_Demo.Instr_Dur` = 9999 en Breath (K 0) y Draw (K 4): el ensayo no avanza solo; lo empuja este BP.

## Variables
- **Instr** (por instancia): `Pages` (MaterialInterface[], una MI de `PlateTop` por página) · `ShowDelay` 1 · `PressWait` 0,5 · `EyeRef` 120.
- **Debug**: `AutoPress` (0 = apagado; N = clic simulado cada N s, para PIE sin visor). 🔴 0 en el APK.
- **Z-Estado**: `St`, `Page`, `T`, `LastPressN`, `Card`, `Rig`, `Runner`.


## 2026-10-19 — retirado de los niveles
Con el guion v2 lo reemplaza `BP_DemoFlow_SC` (páginas que avanzan solas, panel 16:9 curvo con imagen). El BP queda en la carpeta por si hace falta volver; los niveles ya no lo tienen.
