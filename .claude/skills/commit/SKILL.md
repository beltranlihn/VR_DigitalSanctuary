---
name: commit
description: Commitear y pushear el proyecto Soul Charger a GitHub. Usar cuando el usuario quiera guardar una versión / respaldar / commitear / pushear (p.ej. "/commit", "guardá una versión", "subí esto").
---

# Commit Soul Charger → GitHub (mínimo de tokens)

Repo privado `beltranlihn/VR_Digital`, rama `main`. Root: `C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal`.

**Ejecutá directo, sin explorar estado. No corras `git status`/`log`/`diff` salvo que algo falle.**

## Pasos
1. **Guardar en Unreal primero** (git ve el `.uasset` en disco, no lo sin-guardar):
   - Si el MCP `unreal` está conectado → `call_tool(editor_toolset.toolsets.asset.AssetTools, save_assets, {"asset_paths": []})`.
   - Si no está conectado → recordá en UNA línea: "hacé Save All en el editor (Ctrl+Shift+S)".
2. **Mensaje de commit:** usá el que dé el usuario; si no dio, inferí un hito corto de la sesión (no "cambios varios"). Si no hay contexto, preguntá en una línea.
3. **Un solo comando Bash** (add + commit + push):
   ```bash
   ROOT="C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal"
   git -C "$ROOT" add -A && git -C "$ROOT" commit -q -m "MENSAJE" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>" && git -C "$ROOT" push -q 2>&1 | tail -5
   ```
4. Confirmá en 1-2 líneas (que commiteó y subió). Listo.

## Si falla (solo entonces investigá)
- **"nothing to commit, working tree clean"** → no había cambios guardados. ¿Hiciste Save All en Unreal?
- **push rejected / remote ahead** → `git -C "$ROOT" pull --rebase && git -C "$ROOT" push`.
- **pide login/credenciales** → las maneja el usuario (yo no ingreso contraseñas). Normalmente están cacheadas.

## Recordatorios
- `.uasset`/`.umap` son **binarios**: commitear **hitos** (mecánica lista, etapa terminada), no cada micro-cambio.
- Lo regenerable (Binaries/Intermediate/Saved/DDC/Build) ya está en `.gitignore` de la raíz — no tocar.
