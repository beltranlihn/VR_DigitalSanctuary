# UMGToolSet — firmas destiladas (usar en vez de `describe_toolset`, que pesa 62 KB)

Destilado de `describe_toolset` en vivo el 2026-10-01 (UE 5.8). **23 tools.**

- **`toolset_name` = `UMGToolSet.UMGToolSet`** (NO sigue el patrón `editor_toolset.toolsets.X`).
- `tool_name` corto (p. ej. `AddWidget`). Llamada: `mcp__unreal__call_tool {toolset_name, tool_name, arguments}`.
- Refs: `{"refPath": "..."}`. `widgetBlueprint` = el asset WBP **sin `_C`** (ej. `/Game/UI/WBP_X`; si lo rechaza, probá `Paquete.Objeto` → `/Game/UI/WBP_X.WBP_X`, ver `toolsets.md`). Clases: `{"refPath": "/Script/UMG.CanvasPanel"}`, `/Script/UMG.TextBlock`, etc.
- Widgets/slots devueltos son refs a instancias del árbol: pasarlos tal cual a esta toolset o a `ObjectTools`.
- 🔴 **Flujo obligatorio** (lo dice el toolset): por cada widget/slot devuelto → `ObjectTools.list_properties` → `get_properties` → `set_properties` con los nombres EXACTOS. Los nombres no se adivinan; sin `list_properties`, `set_properties` falla en silencio.
- **Enums: ninguno.** El schema no declara valores enum (ni clases de widget, ni alineación, ni anchors). Las clases salen de `ListWidgetClasses`; alineación/anchors/padding son propiedades del **slot** vía `ObjectTools`.
- **Guardar**: esta toolset NO guarda. `CompileWidgetBlueprint` y después guardar con `AssetTools` (la descripción dice `save_asset`; en `toolsets.md` figura `save_assets`).

## Tools por tarea

| Tarea | Tool |
|---|---|
| Crear un **asset** Widget Blueprint nuevo | `CreateWidgetBlueprint` |
| Agregar un hijo bajo un padre (o crear el root) | `AddWidget` |
| Marcar/desmarcar como variable | `ToggleWidgetAsVariable` |
| Compilar | `CompileWidgetBlueprint` (guardar aparte con `AssetTools`) |
| **Root**: no hay `SetRootWidget` | `AddWidget` con `parentWidget` nulo **en árbol vacío** = root. Para cambiar el root existente: `WrapWidgets` (envolverlo en un panel), `ReplaceWidgetWithTemplate` (cambiarle la clase), `ReplaceWidgetWithChild` (subir su único hijo). Leer `GetWidgets.info.rootWidgetClass` |

## Firmas (R = requerido, o = opcional)

### Asset / consulta
- **`CreateWidgetBlueprint`**(`folderPath`: string R — ej. `/Game/UI/Widgets`; `assetName`: string R; `parentClass`: ref Class@`/Script/UMG.UserWidget` R — sacarlo de `GetWidgets.info.parentClass` o `/Script/UMG.UserWidget`) → ref `WidgetBlueprint` (nulo si falla). Crea el asset.
- **`ListWidgetBlueprints`**(`folderPath`: string R, recursivo) → array de refs.
- **`ListWidgetClasses`**(`filter`: string R — `""` = todas) → array `{widgetClass, bIsPanel, category, description}`.
- **`GetWidgetClassInfo`**(`widgetClass`: ref Class@`/Script/UMG.Widget` R) → `{widgetClass, bIsPanel, category, description}`.
- **`GetWidgets`**(`widgetBlueprint`: ref WidgetBlueprint R) → `{info:{parentClass, rootWidgetClass, widgetCount, inheritedWidgetCount, namedSlotCount}, widgets:[UMGWidgetInfo]}` en orden depth-first (orden del designer).
- **`GetWidgetDescription`**(`widgetBlueprint` R; `startWidget`: ref Widget o — nulo = desde root; `maxDepth`: int o, default -1 = sin límite, 0 = solo startWidget) → `{description: texto "[N] Tipo Nombre Prop:Valor … slot:(…)", widgets:[UMGWidgetInfo]}`. Volcado completo de propiedades: **puede ser grande, filtrar con `startWidget`/`maxDepth`.**
- **`GetWidgetTreeDepth`**(`widgetBlueprint` R; `startWidget` o) → int (-1 error).
- **`GetNamedSlots`**(`widgetBlueprint` R) → array `{slotName, hostWidget, contentWidget}`.

### Edición del árbol
- **`AddWidget`**(`widgetBlueprint` R; `widgetClass`: ref Class@`/Script/UMG.Widget` R; `widgetDisplayName`: string R; `parentWidget`: ref Widget o — nulo = agregar al root, o pasa a SER el root si el árbol está vacío; `childIndex`: int o, default -1 = al final) → `UMGWidgetInfo`.
- **`RemoveWidget`**(`widgetBlueprint` R; `widget` R) → bool. Borra también los hijos.
- **`MoveWidget`**(`widgetBlueprint` R; `widget` R; `newParent`: ref PanelWidget R; `childIndex`: int o, default -1) → `UMGWidgetInfo` (slot nuevo).
- **`RenameWidget`**(`widgetBlueprint` R; `widget` R; `newDisplayName`: string R) → `UMGWidgetInfo` (vacío si falla).
- **`WrapWidgets`**(`widgetBlueprint` R; `widgets`: array ref Widget R; `wrapperClass`: ref Class@`/Script/UMG.PanelWidget` R) → array `UMGWidgetInfo` de los wrappers. Solo envuelve los más altos de la selección.
- **`ReplaceWidgetWithChild`**(`widgetBlueprint` R; `widgetToReplace`: panel con UN solo hijo R) → bool.
- **`ReplaceWidgetWithTemplate`**(`widgetBlueprint` R; `widgetToReplace` R; `templateClass`: ref Class@Widget R) → `{bSuccess, missingReferencesWarning, unmatchedProperties[], unmatchedReferencedProperties[], unmatchedFunctions[], unmatchedReferencedFunctions[]}` (cada uno `{name, reason}`). Conserva bindings/refs compatibles; lo incompatible queda huérfano.
- **`ReplaceWidgetWithNamedSlot`**(`widgetBlueprint` R; `widgetToReplace`: host con INamedSlotInterface R; `namedSlot`: string R) → bool.
- **`SetNamedSlotContent`**(`widgetBlueprint` R; `hostWidget`: ref Widget R — nulo = WidgetTree root; `slotName`: string R; `widgetClass`: ref Class@Widget R; `widgetName`: string R) → `UMGWidgetInfo`.
- **`ToggleWidgetAsVariable`**(`widgetBlueprint` R; `widget`: ref Widget R; `bIsVariable`: bool R) → (sin returnValue). Setea `bIsVariable`.

### UI Components
- **`AddUIComponent`**(`widgetBlueprint` R; `widgetName`: string R; `componentClass`: ref Class@`/Script/UMG.UIComponent` R) → `UMGWidgetInfo` con `uIComponents` poblado.
- **`RemoveUIComponent`**(`widgetBlueprint` R; `widgetName`: string R; `componentClass` R) → bool.
- **`MoveUIComponent`**(`widgetBlueprint` R; `widgetName`: string R; `componentClassToMove` R; `relativeToComponentClass` R; `bMoveAfter`: bool R) → bool.

### Eventos y compilación
- **`BindToEventProperty`**(`widgetBlueprint` R; `eventName`: string R — ej. `OnClicked`; `propertyName`: string R — la variable del widget (tiene que ser variable); `propertyClass`: ref Class@`/Script/CoreUObject.Object` R — ej. `/Script/UMG.Button`) → bool. Crea el nodo de evento en el grafo.
- **`CompileWidgetBlueprint`**(`widgetBlueprint` R) → bool (false con detalle de errores: BindWidget faltante, tipos, grafo). Llamar al final; **no guarda**.

## `UMGWidgetInfo` (lo que devuelven Add/Move/Rename/Wrap/SetNamedSlotContent/GetWidgets)
`widget` (ref Widget) · `parent` (ref PanelWidget; nulo si es root o vive en named slot) · `slot` (ref PanelSlot: padding/alignment/anchors via `ObjectTools`; nulo en el root) · `namedSlotHost` · `widgetClassPath` · `widgetName` · `bIsVariable` · `bInherited` · `uIComponents[] {component, componentClassPath}`.
