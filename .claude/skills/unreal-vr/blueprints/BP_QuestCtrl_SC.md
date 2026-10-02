# BP_QuestCtrl_SC — el mando de la obra (visual pasivo)

- **Ruta**: `/SC_Base/Blueprints/BP_QuestCtrl_SC` · **Estado**: 🟢 construido y verificado en el editor con capturas (2026-09-29, `Test_QuestCtrl`) · ⬜ visor.
- **Propósito**: el mando que ve el usuario. Pedido de Beltrán:
  - forma del Meta Quest sin botones, cuerpo negro y tapa gris-blanca;
  - solo el gatillo, que **se mueve y cambia de material al apretar**;
  - visible sin luz direccional.
- **Modelo y datos**: `blender-3d/assets/quest-controller.md`. Material: `M_QuestCtrl_SC` (`scripts/hlsl/QuestCtrlShadePS.hlsl`).

## Diseño mínimo (antes del primer nodo)

**Es un visual PASIVO.** No lee input ni conoce al pawn ([[arquitectura-manager-control]]): el rig que lo monta le pasa el valor del gatillo con `SetTrigger`. Así sirve a todos los rigs y al prototipo, y se prueba solo con `bDemo`.

| Componente | Qué es |
|---|---|
| `Root` (Scene) | Marco del Touch Plus oficial, el mismo de `/SC_Draw/Meshes/Controller`. |
| `Body` (StaticMesh) | `SM_QuestCtrl_Body_R_SC` / `_L_SC`; 2 instancias de material por mano: cuerpo y tapa en una sola, por UV1. |
| `Trigger` (StaticMesh, hijo de Root) | `SM_QuestCtrl_Trigger_R_SC` / `_L_SC`. Posición relativa = pivote de la bisagra. |

| Variable | Tipo | Por defecto | Para qué |
|---|---|---|---|
| `bLeft` | bool, editable | false | Mallas L, pivote con x negado, eje espejado y signo invertido. |
| `PressDegrees` | float, editable | 14 | Recorrido del gatillo apretado a fondo. |
| `FollowSpeed` | float, editable | 18 | Velocidad con que el gatillo sigue al valor (FInterpTo). |
| `PressedMaterial` | MaterialInterface, editable | vacío | Si se asigna, se usa en vez del parámetro `Pressed`, para cambiar el material entero al apretar (umbral 0,5). |
| `bDemo` | bool, editable | false | Aprieta y suelta solo, para probar sin rig. |
| `HingePivotR` | vector | (1.565, 2.432, −0.145) | Datos de la bisagra, derecho, en cm de Unreal. |
| `HingeAxisR` | vector | (0.976, −0.218, −0.008) | Eje de la bisagra, derecho, en Unreal. |
| `PressSign` | float | ±1 | **A verificar en el editor**: el signo que mete el gatillo hacia el cuerpo. |
| `Target`, `Value` | float | 0 | Estado del gatillo (runtime). |
| `TrigMID` | MaterialInstanceDynamic | — | Instancia dinámica del material del gatillo (runtime). |

- **Construction Script**: mallas según la mano → ubica `Trigger` en el pivote → crea `TrigMID` → `ApplyTrigger(0)`.
- **`SetTrigger(Amount)`** (pública, 0..1): fija `Target`. Atajos `Press` y `Release`.
- **Tick** (solo si `Value != Target` o `bDemo`): `Value = FInterpTo(Value, Target)`, luego `ApplyTrigger(Value)`.
- **`ApplyTrigger(V)`** hace dos cosas:
  - `Trigger.SetRelativeRotation(RotatorFromAxisAndAngle(Eje, Signo · V · PressDegrees))`
  - `TrigMID.SetScalar("Pressed", V)`, o el cambio de material entero si `PressedMaterial` está asignado.
- **Montaje en un rig**: `ChildActorComponent` colgado del **Grip**, con la transformada de `/SC_Draw/Meshes/Controller` en ese rig. Los rigs con `/SC_Base/Meshes/ControllerR|L` usan otro marco: medir la relación en el editor antes de cambiarlos. **No tocar rigs sin pedido de Beltrán.**

## Verificar al construir

1. Signo de apretar: con `Value` = 1, el gatillo entra hacia el cuerpo (holgura medida ≥ 0,75 mm en todo el recorrido).
2. La tapa se ve nítida (borde por `fwidth`) de cerca y de lejos.
3. Sin luz direccional: el cuerpo negro se lee por el sombreado y el borde de luz.
4. Contar triángulos en Unreal contra Blender (gotcha §19): 15.336 y 2.416.

## ✅ Construido (2026-09-29)

- **Assets** en `QuestController/`:
  - Mallas: `SM_QuestCtrl_{Body,Trigger}_{R,L}_SC`, con 15.336 y 2.416 tris (iguales a Blender), sin colisión.
  - Material: `M_QuestCtrl_SC`, con 19 entradas y parámetros agrupados por **Luz / Colores / Borde de luz / Gatillo**.
  - Instancias: `MI_QuestCtrl_Body_SC` y `MI_QuestCtrl_Trigger_SC` (`CapBias` −100, `BodyColor` gris-blanco).
  - Nivel de prueba: `Test_QuestCtrl`, copia de `Test_DrawPalette` (sin luces, `BP_XRGameMode`). Tiene 4 instancias: R/L, sueltos y apretados.
- **Gatillo con ORIGEN EN LA BISAGRA.** El importador de Unreal hornea la posición del objeto FBX en los vértices; por eso el gatillo se exporta en el origen, con la malla ya referida a la bisagra.
  - Posición del componente: R `(1.565, 2.432, −0.145)`. L: x negado.
- **Giro verificado con capturas** (en PIE todavía no):
  - `RotatorFromAxisAndAngle(Eje, PressSign · Value · 14)`, con **PressSign = −1**.
  - Eje R `(0.976, −0.2177, −0.0083)`. Eje L `(ax, −ay, −az)`, mismo signo.
  - Con +1 el gatillo se alejaba del mango.
- **Grafos:**
  - `ApplyTrigger`: posición, giro y `Pressed` por `SetScalarParameterValueonMaterials`, que crea la MID internamente.
  - `ApplyHand`: mallas R o L.
  - `SetTrigger(Amount)`.
  - Construction Script: `Target = Value`, luego `ApplyHand` y `ApplyTrigger`.
  - `EventTick`: modo demo por coseno, `FInterpTo` hacia `Target`, y `ApplyTrigger` solo si se mueve.
- ⚠ **Cambiar un valor por defecto en el CDO NO llega a las instancias ya colocadas.** Pasó con `PressSign`: hubo que corregir las 4 a mano ([[instance-editable-nace-en-cero]]).
- Pendiente:
  - visor;
  - color de `PressedColor` (Beltrán);
  - integración al dibujo (sesión Drawing);
  - rigs de respiración y latido: ahí lo reemplaza el sensor `SM_BioSensor_SC`.
