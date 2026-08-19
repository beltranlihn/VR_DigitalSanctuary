# Recursos compartidos — quién comanda qué

**Para qué existe este archivo.** Cuando el síntoma es global —"la pantalla se fue a negro", "bajó la luz", "se cortó el audio", "vibró el mando"— la pregunta correcta **no** es *"¿en qué parte del flujo pasa?"* sino **"¿quién puede provocar esto?"**. Este archivo responde la segunda en un vistazo.

Nace de un caso real (2026-08-16): un negro de 0,58 s en Attracting costó una tarde. Se buscó en `BP_StageDirector` y `BP_Stage_Attracting` —los dos Blueprints donde *se suponía* que estaba el momento— y se concluyó, mal, que "no hay ningún fundido en el recorrido". El `StartFade` culpable estaba en un tercero, `BP_TouchInstrPanel`. Encontrarlo por síntoma habría costado **dos segundos**.

## 🔴 El comando que había que correr primero

```bash
cd "VR_Test/Content/SoulCharger" && grep -rl "StartFade" --include="*.uasset" . | sed 's|.*/||'
```

Los `.uasset` son binarios, pero **los nombres de funciones y de nodos quedan como texto plano adentro**, así que `grep -rl` sobre el Content responde "quién referencia X" de forma fiable y casi gratis. Son 77 Blueprints: barrerlos todos cuesta menos que abrir dos.

⚠ Da **referencias**, no llamadas: incluye al dueño del recurso y puede incluir a quien solo guarda una variable de ese tipo. Sirve para **acotar de 77 a 5**, no para señalar al culpable. El paso siguiente es `read_graph_dsl` sobre esos pocos.

## Mapa (regenerado 2026-08-16)

| Recurso | Dueño | Quién lo comanda | Riesgo |
|---|---|---|---|
| **Fundido a negro** | `BP_FadeSphere` | `BP_StageDirector` · `BP_FlowDirector` · `BP_CalibDirector` · `BP_Finale` · `BP_BreathStageManager` · `BP_HeartStageManager` · **`BP_TouchInstrPanel`** | 🔴 **7 comandantes.** Es el que ya mordió. |
| **Luz de la sala** | `BP_Room` (`SetLight`/`RampLight`) | `BP_StageDirector` | 🟢 un solo comandante externo |
| **Loops de audio** | `BP_AudioHub` (`LoopPlay`/`LoopStop`) | `BP_StageDirector` · `BP_SoulChoice` · `BP_Stage_Loving` · `BP_MenuButton` · `BP_BreathPacer` · `BP_DrawCanvas` · `BP_AttractDirector` | 🟡 7, pero cada uno con su nombre de loop |
| **SFX** | `BP_AudioHub` (`PlaySfx`) | `BP_StageDirector` · `BP_SoulChoice` · `BP_Ceremony` · `BP_Finale` · `BP_Stage_Loving` · `BP_Stage_Recognizing` · `BP_MenuButton` | 🟡 |
| **Ambiente** | `BP_AudioHub` (`PlayAmbient`/`SwapAmbient`) | `BP_StageDirector` · `BP_Finale` | 🟢 |
| **Cambio de nivel** | motor (`OpenLevel`) | `BP_CalibDirector` · `BP_Finale` · `BP_BreathStageManager` · `BP_HeartStageManager` | 🟡 ninguno en el recorrido normal |

Para regenerarlo:
```bash
cd "VR_Test/Content/SoulCharger" && for k in StartFade RampLight LoopPlay PlaySfx PlayAmbient SetLight OpenLevel; do printf "%-14s " "$k"; grep -rl "$k" --include="*.uasset" . | sed 's|.*/||;s|\.uasset||' | tr '\n' ' '; echo; done
```

## 🔴 Regla: un recurso compartido dice en el log QUÉ le pidieron

El log viejo de la esfera decía `FS 5: StartFade ejecutando` — no dice quién, ni a cuánto, ni en cuánto tiempo. **Inútil para diagnosticar.** Ahora dice:

```
FADE -> alpha 1.000000
```

Con eso, el log que ya existía habría gritado la respuesta: *alguien pidió negro pleno*, y la línea del mismo milisegundo (`TCH|Panel con input propio`) identifica al que lo pidió. **Una línea de log en el dueño reemplaza una tarde de búsqueda.**

Aplicar lo mismo cuando toque: `BP_Room.SetLight` debería loguear el alpha, y `BP_AudioHub.LoopPlay` el nombre y el fundido.

## Cómo no acumular comandantes nuevos

Antes de que un Blueprint nuevo comande un recurso de esta tabla, preguntarse si no debería **pedírselo a su director**. Un solo comandante es la razón por la que la luz de la sala se leyó en dos minutos y el fundido costó una tarde. No hace falta refactorizar lo que ya anda — sí no agregar el octavo.

## Relacionados
[[_INDEX]] · `references/workflow.md` (método y tokens) · `references/assets-existentes.md` (qué existe y es reusable)
