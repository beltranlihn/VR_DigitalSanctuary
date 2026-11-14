# Recursos/ — material de trabajo (ordenado el 2026-11-14)

Lo que sirve para hacer la obra pero no es parte del proyecto Unreal. Lo pesado no va a git (ver `.gitignore`).

| Carpeta | Qué hay | En git |
|---|---|---|
| `Audio/` | sonidos sueltos de las mecánicas (`Breath/`, `Heart/`…), `Calibration/` (voces de la calibración), `Sonidos/` (proyecto Ableton chico), `VoiceOvers/` (las primeras voces, julio) | sí |
| `Music/` | **Soul Charger Music Project** (Ableton) y sus exportaciones (`Export/FX` lo usa el editor web) | sí |
| `Marca e interfaz/` | logos e íconos (`1x/`, `Asset/`, `SVG/`), el QR de Alma Digital Studio y los originales de Photoshop/Illustrator | sí |
| `3D/` | fbx y blend sueltos (puertas, piso, `VR3D.blend`) y `Blender/` (el mando `Controllers.blend`, el anillo de prueba) | sí |
| `Referencias/` | capturas de otras experiencias VR | sí |
| `Soul Charger - Instalacion Feria/` | el medio domo de la feria: Blender, planos, renders (ver `docs/instalacion-feria/`) | sí |
| `Soul Charger - Escritorio 2026-10/` | lo que vino del escritorio en octubre: `Audio/` (lo lee el editor web), `Videos y grabaciones/` (12,6 GB, grabaciones de la obra), planos del Hall, logos del título y `APK/` (la última copia de cada app) | **no** |
| `Inner Canvas/` | `Renders/` (en git) y la última copia de cada build: `APK/` (PICO), `APK Quest/`, `Pantalla/` (Windows) | solo `Renders/` |

- **Copias de builds:** cada empaquetado deja la suya en `Soul Charger - Escritorio 2026-10/APK` o en `Inner Canvas/` (lo hacen
  `empaquetar_obra.py` y `empaquetar_pantalla.py`).
- **Limpieza (11-14):** se borraron las intermedias y queda solo la última de cada app.
- **Versiones entregadas:** van a `Projects/Packagings/<Nombre vX.Y>/`, fuera de esta carpeta.
- **Copias de Fab sacadas el 2026-11-14:** `DrawingToolkit`, `GDXR` y `Test_3DDraw` (proyectos de dibujo de julio). Quedan en el
  historial de git y en el tag `respaldo-pre-orden-2026-11-14`.
