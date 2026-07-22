# Workflow de equipo — trabajar en paralelo sin pisarnos

Dos (o más) devs trabajando el mismo proyecto Unreal, cada uno en **su stage**. El enemigo #1 son los **`.uasset`/`.umap` binarios**: git **no los puede mergear**. Si dos personas editan el mismo asset, uno de los dos pierde su trabajo. Todo lo de acá existe para que eso no pase.

---

## 0. El modelo mental: git sube CAMBIOS, no tu carpeta (leer esto primero)
La duda más común al empezar en equipo: *"si yo subo Breath actualizado y Nico sube Touch desde una copia con Breath viejo, ¿me pisa el Breath?"* **No.** Y entender por qué evita el 90% de los problemas.

**Git no sube "tu carpeta entera". Sube los cambios específicos que hiciste** (qué archivos tocaste y qué parte cambió). Un commit es una lista de *diferencias*, no una foto completa que reemplaza lo del otro.

Ejemplo concreto:
- Vos tocás archivos de **Breath** → tu commit dice "cambié estos archivos de Breath".
- Nico toca archivos de **Touch** → su commit dice "cambié estos de Touch".
- Aunque Nico tenga en su copia un Breath **viejo**, su commit **no incluye ningún cambio de Breath** (no los tocó) → al subir **no puede pisar tu Breath**.

**El paso que lo hace seguro: `pull` antes de `push`.** Paso a paso:
1. Vos avanzás Breath → `push`. `main` ya tiene tu Breath nuevo.
2. Nico trabaja Touch en su copia (con el Breath viejo).
3. Nico intenta `push` → **git se lo RECHAZA** ("estás atrasado, traé los cambios primero"). Git no te deja pisar lo del otro por accidente.
4. Nico hace `pull` → git **fusiona** tu Breath nuevo en su copia. Como él no tocó Breath, **entra sin conflicto**; su Touch queda intacto.
5. Ahora su copia tiene **tu Breath + su Touch** → `push` → `main` queda con las dos cosas. Nadie perdió nada. ✅

**En una línea:** GitHub *integra* el trabajo de los dos, no lo reemplaza; cada push sube solo tus cambios; y git te obliga a traer lo del otro antes de subir. Lo tuyo nunca se pierde… **salvo que ambos editen el mismo `.uasset`** (binario, no se fusiona) — que es justo lo que evita la regla de "un stage cada uno" (§1).

**Rutina diaria mínima:** al empezar → `git pull` (o `git pull --rebase`). Al terminar un hito → `commit` + `push`. Si el push se rechaza → `pull` y volvé a `push`.

## 1. Regla de oro
> **Un dev = un stage = una rama. Nunca dos personas editan el mismo `.uasset` a la vez.**

Como cada stage vive en su propia carpeta (`Content/SoulCharger/Stages/<Stage>/`), si cada uno se queda en la suya no hay colisión. Los choques solo pasan en lo **compartido** (ver §4).

## 2. Ramas
- Rama base: **`main`** (siempre estable, empaquetable).
- Cada stage en su rama: **`stage/heart`**, **`stage/movement`**, etc. Una herramienta/experimento: `tool/<nombre>`.
- Trabajás y commiteás en tu rama. Cuando cerrás un **hito** (una mecánica anda en el visor), abrís un **Pull Request a `main`**.
- Antes de empezar el día: `git checkout tu-rama && git pull origin main --rebase` (traés lo último de main sin romper lo tuyo). Si el rebase toca un `.uasset` que ambos cambiaron → ver §5.

## 3. Commits y push
- **Save All en Unreal ANTES de commitear** (git ve el archivo en disco, no lo que está sin guardar en el editor). Mini-skill `/commit` lo recuerda.
- **Commiteá HITOS, no micro-cambios.** Los `.uasset` son binarios y pesan; un commit por cada nodo llena el repo. Un commit = "la mecánica X quedó armada y compila".
- Mensajes claros en presente ("Heart: sensor de latido lee OSC y pulsa la esfera"). No "cambios varios".
- Push a tu rama seguido (respaldo). Merge a `main` solo por PR de hitos.

## 4. Assets compartidos — coordinar SIEMPRE
Estos los tocan todos, así que **avisá al otro antes** y serializá (uno a la vez):
- `Content/SoulCharger/Core/` — el **pawn VR**, fades, UI compartida.
- `VR_Test/Config/` — `DefaultEngine.ini`, `DefaultGame.ini`, `DefaultInput.ini` (project settings, mapas a cocinar, packaging).
- El **hub / FlowDirector** cuando exista (el que encadena los stages).
- `MapsToCook` y ajustes de packaging.

Regla: si tu cambio toca algo de acá, decilo por el canal del equipo, hacelo rápido, commiteá y avisá que quedó libre. **No metas lógica de tu stage en el pawn** — cada mecánica en su propio BP (el pawn liviano es regla del proyecto).

## 5. Si igual hay conflicto en un `.uasset`
Git no lo mergea. Opciones:
1. **Prevención:** no debería pasar si respetaste §1/§4.
2. Si pasó: **decidan quién gana** ese asset. El que pierde hace `git checkout --theirs <asset>` (o `--ours`) para quedarse con una versión, y **re-aplica sus cambios a mano** en el editor. No hay merge automático posible.
3. Para reducir riesgo: hitos chicos y frecuentes a `main` → menos ventana de divergencia.

## 6. Deploy (empaquetar APK)
- **Cuándo:** cuando una mecánica está lista para probar en el device real (no en cada cambio).
- **Cómo:** empaquetar en **Development** (no Shipping) para trabajo y captura de datos — Shipping recorta logs y cambia rutas de guardado. Ver `skills/unreal-vr/references/packaging-pso.md` y las memorias de packaging.
- Antes de empaquetar: que el stage compile limpio y que el nivel esté en `MapsToCook` (`DefaultGame.ini`).
- El build final de la obra (Shipping) es un paso aparte, coordinado.

## 7. Conocimiento compartido — que no se pierda
El aprendizaje del equipo vive en el **repo**, no en la cabeza ni en la memoria local de Claude de cada uno:
- **Técnica reusable** (un gotcha, un patrón de nodos, cómo se hace X en Quest) → PR a `.claude/skills/unreal-vr/` (a `references/` o `gotchas.md`).
- **Estructura de un Blueprint** (qué hace cada variable, orden del grafo, qué palanca ajusta qué) → su tracker en `skills/unreal-vr/blueprints/<BP>.md`. 🔴 **Leelo antes de tocar el BP; actualizalo después.** Y actualizá su fila en el **índice maestro** `skills/unreal-vr/blueprints/_INDEX.md` (el mapa de todos los BPs: qué es, dónde, estado).
- **Narrativa / diseño / concepto de un stage** → 🔴 **`Soul-Charger-Design.md` es la BIBLIA DE NARRATIVA** (documento vivo). Si cambia la idea/mecánica de cualquier etapa, **se actualiza ahí primero** (marcando el cambio, como la §4.4 de Touch). Los planes de construcción por stage van en `docs/stages/`.
- **Estado de un stage** → [`ESTADO-STAGES.md`](ESTADO-STAGES.md).
- **Memoria local de Claude Code** (`~/.claude/...`) = tus notas personales de sesión. NO es conocimiento de equipo (el otro no la ve). Si algo sirve al equipo, subilo al repo.

## 8. Checklist de fin de sesión
1. Save All en Unreal.
2. Actualizaste el/los tracker(s) de los BPs que tocaste.
3. Si cambió el estado del stage → actualizaste `ESTADO-STAGES.md`.
4. `/commit` (o commit + push manual a tu rama).
5. ¿Hito cerrado? Abrí/actualizá el PR a `main`.

## 9. Nota sobre el repo
- URL: `github.com/beltranlihn/VR_DigitalSanctuary` (fue renombrado desde `VR_Digital`; si tenés un clon viejo: `git remote set-url origin https://github.com/beltranlihn/VR_DigitalSanctuary.git`).
- `.gitignore` (raíz) ignora lo regenerable: `Binaries/`, `Intermediate/`, `Saved/`, DDC, `Build/`. No los versiones.
- Sin Git LFS por ahora (ningún asset >50 MB). Si algún día metés un asset pesado, avisá para evaluar LFS.
