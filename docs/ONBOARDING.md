# Onboarding — primera vez con Soul Charger + Claude Code + MCP

Guía paso a paso para un dev nuevo que **nunca usó Claude Code ni el MCP de Unreal**. Al terminar vas a poder pedirle a Claude que edite Blueprints, arme niveles y toque el editor directamente.

---

## 0. Concepto: cómo trabajamos
En este proyecto **Claude Code maneja Unreal por vos** a través de un **MCP** (Model Context Protocol): un "puente" que expone las herramientas del editor (crear/editar Blueprints, colocar actores, compilar, etc.) para que Claude las llame. Vos guiás, revisás y probás en el visor; Claude construye. Casi no se toca el editor a mano salvo lo que Claude no puede hacer (structs, enums, project settings, algunos widgets).

## 1. Requisitos
- **Unreal Engine 5.8** instalado (la versión exacta importa; el proyecto es 5.8).
- **Meta Quest 3** + Meta Quest Link (para probar por PC VR) y/o cable USB (para build APK).
- **Claude Code** instalado y logueado.
- **Git** con acceso al repo `github.com/beltranlihn/VR_DigitalSanctuary` (pedir acceso a Beltrán).

## 2. Clonar y abrir
1. `git clone https://github.com/beltranlihn/VR_DigitalSanctuary.git`
2. Abrí `VR_Test/VR_Test.uproject` en Unreal 5.8. Si pide recompilar/derivar shaders, dejalo terminar (la primera vez tarda).
3. **Dejá Unreal abierto toda la sesión.**

## 3. El MCP de Unreal (el puente)
El proyecto ya trae habilitado el plugin **ModelContextProtocol** de UE 5.8. Al abrir el proyecto, arranca un server HTTP en **`localhost:8000/mcp`**.
- Verificá que esté encendido: en Project Settings buscá *Model Context Protocol* y confirmá que el server está activo (o corré en la consola del editor: `ModelContextProtocol.StartServer 8000`).
- **Orden que importa:** Unreal (con el server) tiene que estar corriendo **ANTES** de abrir Claude Code. El MCP se engancha cuando Claude arranca. Si abrís Claude sin Unreal, las herramientas `unreal` no existen y hay que reiniciar Claude.

## 4. Conectar Claude Code al MCP
1. Abrí una terminal en la **raíz del repo** (la carpeta `VR Unreal/`, la que tiene `CLAUDE.md`).
2. Arrancá Claude Code ahí (`claude`). Al iniciar, carga automáticamente:
   - **`CLAUDE.md`** (el contexto del proyecto).
   - La **skill `unreal-vr`** (la biblia técnica).
   - El **MCP `unreal`** si Unreal está corriendo.
3. Si Claude no ve el MCP, revisá que el server 8000 esté vivo y **reiniciá Claude con Unreal abierto**.

> El MCP ya viene **versionado en el repo** (`.mcp.json` en la raíz apunta a `http://localhost:8000/mcp`). La **primera vez**, Claude Code te va a pedir **aprobar el server MCP del proyecto** — aceptalo. Si aun así no aparece, confirmá que el server 8000 esté vivo en Unreal (§3) y reiniciá Claude con el editor abierto.

## 5. Verificar que todo anda
Pedile a Claude algo mínimo, por ejemplo: **"¿qué nivel está cargado en Unreal?"**. Internamente Claude llama `SceneTools.get_current_level`. Si responde con un nivel, el puente funciona. 🎉

## 6. El ritmo de trabajo (para gastar menos y rendir más)
Leé [`../GUIA-RAPIDA.md`](../GUIA-RAPIDA.md). Lo clave:
- **Unreal abierto antes que Claude**, toda la sesión.
- **`/clear` al cambiar de tema** (otro BP, otro subsistema). No arrastres una sesión eterna.
- **Elegí modelo/effort al inicio** y no los cambies a mitad (reprocesa todo el contexto).
- **Save All en Unreal antes de `/commit`.**
- **Prompts específicos** ("agregá un branch en la función X del BP Y") rinden mucho más que "mejorá esto".
- **Plan mode (Shift+Tab)** antes de una tarea grande.

## 7. Antes de tu primer cambio
1. Leé [`../CLAUDE.md`](../CLAUDE.md) entero (5 min).
2. Leé [`WORKFLOW-EQUIPO.md`](WORKFLOW-EQUIPO.md) — cómo trabajamos en paralelo sin pisarnos.
3. Mirá [`ESTADO-STAGES.md`](ESTADO-STAGES.md) para saber qué stage te toca y qué existe.
4. Creá tu rama de stage: `git checkout -b stage/<tu-stage>`.
5. Antes de tocar cualquier Blueprint, pedile a Claude que **lea su tracker** en `.claude/skills/unreal-vr/blueprints/`.

## 8. Cosas que Claude NO puede crear (pedilas a mano o por lote)
Structs, enums, plugins, algunos project settings y ciertas cosas de widgets. Cuando aparezca, definí nombres/campos y hacelo de una sola vez en el editor (o pedile a Claude la lista exacta y creála vos).

## 9. Si algo se rompe
- **Las tools `unreal` desaparecieron** → el editor se cerró o el server cayó; reiniciá Claude con Unreal abierto.
- **Claude "editó" pero no se ve** → ¿compiló el Blueprint? ¿hiciste Save All? El MCP toca el asset en memoria; guardá.
- **Push rechazado / repo movido** → ver [`WORKFLOW-EQUIPO.md`](WORKFLOW-EQUIPO.md).
