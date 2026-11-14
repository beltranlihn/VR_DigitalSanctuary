---
name: commit
description: Commitear y pushear el proyecto Soul Charger a GitHub. Usar cuando el usuario quiera guardar una versión / respaldar / commitear / pushear (p.ej. "/commit", "guardá una versión", "subí esto").
---

# Commit Soul Charger → GitHub (mínimo de tokens)

Repo privado `beltranlihn/VR_DigitalSanctuary` (`origin`), rama de trabajo **`core/esqueleto`** (la actual; no `main`).
Root: `C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal`.

**Ejecutá directo, sin explorar estado. No corras `git status`/`log`/`diff` salvo que algo falle.**

## Pasos
1. **Guardar en Unreal primero** (git ve el `.uasset` en disco, no lo sin-guardar):
   - Si el MCP `unreal` está conectado → `call_tool(editor_toolset.toolsets.asset.AssetTools, save_assets, {"asset_paths": []})`.
     ⚠ Re-guarda también BPs de plugin "sucios" solo por haberlos leído (quedan como M en git sin cambio real): es ruido, no rompe.
   - Si no está conectado → recordá en UNA línea: "hacé Save All en el editor (Ctrl+Shift+S)".
2. **Respaldar las fuentes de los BPs escritos por script** (viven en `VR_Test/Saved/ClaudeScripts`, que git ignora):
   `python tools/unreal/respaldar_fuentes_bp.py` → las espeja en `tools/bp_fuentes/`.
3. **Mensaje de commit:** usá el que dé el usuario; si no dio, inferí un hito corto de la sesión (no "cambios varios"). Si no hay contexto, preguntá en una línea.
4. **Un solo comando Bash** (add + commit + push a la rama actual):
   ```bash
   ROOT="C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal"
   python "$ROOT/tools/unreal/respaldar_fuentes_bp.py" && git -C "$ROOT" add -A && git -C "$ROOT" commit -q -m "MENSAJE" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && git -C "$ROOT" push -q 2>&1 | tail -5
   ```
   🔴 Lo pesado no va al repo: builds (`Packaging/`, `Recursos/Inner Canvas/APK…`) ya están en `.gitignore`. Si `git add` va a meter
   algo de más de 50 MB que no sea un asset de Content, parar y avisar.
5. Confirmá en 1-2 líneas (que commiteó y subió). Listo.

## Si falla (solo entonces investigá)
- **"nothing to commit, working tree clean"** → no había cambios guardados. ¿Hiciste Save All en Unreal?
- **push rejected / remote ahead** → `git -C "$ROOT" pull --rebase && git -C "$ROOT" push`.
- **pide login/credenciales** → las maneja el usuario (yo no ingreso contraseñas). Normalmente están cacheadas.

## Recordatorios
- `.uasset`/`.umap` son **binarios**: commitear **hitos** (mecánica lista, etapa terminada), no cada micro-cambio.
- Lo regenerable (Binaries/Intermediate/Saved/DDC/Build) ya está en `.gitignore` de la raíz — no tocar.
