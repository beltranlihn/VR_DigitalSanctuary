;; draw_sea.dsl - los grafos de BP_DrawSea_SC (el OCEANO de la etapa de dibujo). 2026-09-29.
;; Plan: docs/PLAN-OCEANO-DIBUJO-2026-09-28.md (seccion 3 y la receta del editor, seccion 7).
;; scripts/draw_sea_sim.py EJECUTA este archivo (semantica de dsl_sim.py: un bind puro se re-evalua en cada uso) y lo
;; compara con draw_sea_model.wave_constants:    python draw_sea_sim.py   -> tiene que decir TODO OK antes de pegar.
;;
;; COMO SE PEGA: un write_graph_dsl POR GRAFO, en el orden de las secciones. Cada bloque va entre las lineas
;; ";; ===== GRAFO: <nombre>" y se copia SIN los comentarios de cabecera. BP NUEVO: todos los grafos son nuevos o
;; vacios (regla de oro 2). Antes de escribir:
;;   - variables creadas con su categoria y el BP compilado (tabla VARS de draw_sea_sim.py = la unica fuente);
;;   - funciones creadas con add_function_graph + add_function_param: Wave (I float, Off float),
;;     LookSea (C MeshComponent, gotcha 460); las demas sin parametros;
;;   - los type_id marcados VERIFICAR confirmados con find_node_types.
;; Categorias SIN espacios (gotcha 466). Bools: getter SIN la b (bShowDust -> GetShowDust; gotcha 475).
;; Llamadas propias por KEYWORD (gotchas 461, 654). Material sobre componente: "on" MINUSCULA (gotcha 2258).
;; Verificados con find_node_types (2026-09-29): Math|Float|Power, Math|Float|%(Float), Rendering|Material|SetMaterial.

;; ===== GRAFO: Wave  (funcion nueva; parametros de entrada I float, Off float)
;; Constantes del oleaje I (0..5): lo mismo que draw_sea_model.wave_constants y waveConstants() del prototipo.
;; Deja el resultado en Wc / Vc / Ec (LinearColor, Z-Interno); WaveConstants los escribe en el mar con su nombre.
;; hash(n) = frac(sin(n * 127.1) * 43758.5453) con el frac de GLSL (x - floor x). El Fraction de Unreal es x - trunc x
;; (conserva el signo): se le suma 1 si el argumento es negativo.
(fn Wave (I Off)
  (bind _lmax (Math|Float|Max(Float) (Variables|1-Oleaje|GetSwellLenMax) 10.0))
  (bind _lmin (Math|Float|Min(Float) (Variables|1-Oleaje|GetSwellLenMin) (- _lmax 1.0)))
  (bind _lam (* _lmax (Math|Float|Power (/ _lmin _lmax) (/ I 5.0))))
  (bind _k (/ 6.283185307179586 _lam))
  (bind _ang (Math|Trig|DegreesToRadians (+ (Variables|1-Oleaje|GetSwellDir) (* (Variables|1-Oleaje|GetSwellSpread) Off))))
  (bind _om (* (Math|Float|Sqrt (* 981.0 _k)) (Variables|1-Oleaje|GetTempo)))
  (bind _ea (+ _ang (select (> (Math|Float|%(Float) I 2.0) 0.5) 0.5 -0.5)))
  (bind _dx (Math|Trig|Cos(Radians) _ang))
  (bind _dy (Math|Trig|Sin(Radians) _ang))
  (bind _mx (Math|Trig|Cos(Radians) _ea))
  (bind _my (Math|Trig|Sin(Radians) _ea))
  (bind _h1 (* (Math|Trig|Sin(Radians) (* (+ I 1.0) 127.1)) 43758.5453))
  (bind _h3 (* (Math|Trig|Sin(Radians) (* (+ I 3.0) 127.1)) 43758.5453))
  (bind _f1 (+ (Math|Float|Fraction _h1) (select (< _h1 0.0) 1.0 0.0)))
  (bind _f3 (+ (Math|Float|Fraction _h3) (select (< _h3 0.0) 1.0 0.0)))
  (Variables|Z-Interno|SetWc (Math|Color|MakeColor _dx _dy _k _om))
  (Variables|Z-Interno|SetVc (Math|Color|MakeColor (* (Variables|1-Oleaje|GetSwellAmp) (Math|Float|Power (/ _lam _lmax) 0.6)) (* 6.283185307179586 _f1) (* (* 0.5 (/ _om _k)) (+ (* _mx _dx) (* _my _dy))) (* 6.283185307179586 _f3)))
  (Variables|Z-Interno|SetEc (Math|Color|MakeColor _mx _my (* _lam (Variables|4-CercaLejos|GetLodNear)) (* _lam (Math|Float|Max(Float) (Variables|4-CercaLejos|GetLodFar) (+ (Variables|4-CercaLejos|GetLodNear) 1.0))))))

;; ===== GRAFO: WaveConstants  (funcion nueva, sin parametros)
;; Los 6 oleajes con los OFFS del prototipo [0, 0.85, -0.7, 0.35, -1.0, 0.55], escritos con su nombre en el mar
;; (vectores con nombre, sin arreglos en el shader: gotcha 399). El cielo no los usa (Part 1 no se desplaza).
(fn WaveConstants ()
  (bind _s (Variables|Default|GetSea))
  (CallFunction|Wave :I 0.0 :Off 0.0)
  (Rendering|Material|SetColorParameterValueonMaterials _s "W0" (Variables|Z-Interno|GetWc))
  (Rendering|Material|SetColorParameterValueonMaterials _s "V0" (Variables|Z-Interno|GetVc))
  (Rendering|Material|SetColorParameterValueonMaterials _s "E0" (Variables|Z-Interno|GetEc))
  (CallFunction|Wave :I 1.0 :Off 0.85)
  (Rendering|Material|SetColorParameterValueonMaterials _s "W1" (Variables|Z-Interno|GetWc))
  (Rendering|Material|SetColorParameterValueonMaterials _s "V1" (Variables|Z-Interno|GetVc))
  (Rendering|Material|SetColorParameterValueonMaterials _s "E1" (Variables|Z-Interno|GetEc))
  (CallFunction|Wave :I 2.0 :Off -0.7)
  (Rendering|Material|SetColorParameterValueonMaterials _s "W2" (Variables|Z-Interno|GetWc))
  (Rendering|Material|SetColorParameterValueonMaterials _s "V2" (Variables|Z-Interno|GetVc))
  (Rendering|Material|SetColorParameterValueonMaterials _s "E2" (Variables|Z-Interno|GetEc))
  (CallFunction|Wave :I 3.0 :Off 0.35)
  (Rendering|Material|SetColorParameterValueonMaterials _s "W3" (Variables|Z-Interno|GetWc))
  (Rendering|Material|SetColorParameterValueonMaterials _s "V3" (Variables|Z-Interno|GetVc))
  (Rendering|Material|SetColorParameterValueonMaterials _s "E3" (Variables|Z-Interno|GetEc))
  (CallFunction|Wave :I 4.0 :Off -1.0)
  (Rendering|Material|SetColorParameterValueonMaterials _s "W4" (Variables|Z-Interno|GetWc))
  (Rendering|Material|SetColorParameterValueonMaterials _s "V4" (Variables|Z-Interno|GetVc))
  (Rendering|Material|SetColorParameterValueonMaterials _s "E4" (Variables|Z-Interno|GetEc))
  (CallFunction|Wave :I 5.0 :Off 0.55)
  (Rendering|Material|SetColorParameterValueonMaterials _s "W5" (Variables|Z-Interno|GetWc))
  (Rendering|Material|SetColorParameterValueonMaterials _s "V5" (Variables|Z-Interno|GetVc))
  (Rendering|Material|SetColorParameterValueonMaterials _s "E5" (Variables|Z-Interno|GetEc)))

;; ===== GRAFO: LookSea  (funcion nueva; parametro de entrada C MeshComponent)
;; Las perillas del actor que usa M_DrawSea_SC. Se llama para el mar y para el cielo (mismo material, Part 0 / 1).
(fn LookSea (C)
  (Rendering|Material|SetScalarParameterValueonMaterials C "SwellAmp" (Variables|1-Oleaje|GetSwellAmp))
  (Rendering|Material|SetScalarParameterValueonMaterials C "GroupAmt" (Variables|2-Grupos|GetGroupAmt))
  (Rendering|Material|SetScalarParameterValueonMaterials C "GroupLen" (Variables|2-Grupos|GetGroupLen))
  (Rendering|Material|SetScalarParameterValueonMaterials C "Warp" (Variables|2-Grupos|GetWarp))
  (Rendering|Material|SetScalarParameterValueonMaterials C "WarpScale" (Variables|2-Grupos|GetWarpScale))
  (Rendering|Material|SetScalarParameterValueonMaterials C "Advance" (Variables|3-Avance|GetAdvance))
  (Rendering|Material|SetScalarParameterValueonMaterials C "CalmR" (Variables|4-CercaLejos|GetCalmR))
  (Rendering|Material|SetScalarParameterValueonMaterials C "CalmMin" (Variables|4-CercaLejos|GetCalmMin))
  (Rendering|Material|SetColorParameterValueonMaterials C "DeepColor" (Variables|5-Superficie|GetDeepColor))
  (Rendering|Material|SetColorParameterValueonMaterials C "SurfColor" (Variables|5-Superficie|GetSurfColor))
  (Rendering|Material|SetColorParameterValueonMaterials C "CrestColor" (Variables|5-Superficie|GetCrestColor))
  (Rendering|Material|SetScalarParameterValueonMaterials C "CrestAmt" (Variables|5-Superficie|GetCrestAmt))
  (Rendering|Material|SetScalarParameterValueonMaterials C "LightAz" (Variables|5-Superficie|GetLightAz))
  (Rendering|Material|SetScalarParameterValueonMaterials C "LightEl" (Variables|5-Superficie|GetLightEl))
  (Rendering|Material|SetScalarParameterValueonMaterials C "WrapPow" (Variables|5-Superficie|GetWrapPow))
  (Rendering|Material|SetColorParameterValueonMaterials C "ZenithColor" (Variables|6-CieloNiebla|GetZenithColor))
  (Rendering|Material|SetColorParameterValueonMaterials C "HorizonColor" (Variables|6-CieloNiebla|GetHorizonColor))
  (Rendering|Material|SetScalarParameterValueonMaterials C "SkyPow" (Variables|6-CieloNiebla|GetSkyPow))
  (Rendering|Material|SetColorParameterValueonMaterials C "GlowColor" (Variables|6-CieloNiebla|GetGlowColor))
  (Rendering|Material|SetScalarParameterValueonMaterials C "GlowAmt" (Variables|6-CieloNiebla|GetGlowAmt))
  (Rendering|Material|SetScalarParameterValueonMaterials C "GlowPow" (Variables|6-CieloNiebla|GetGlowPow))
  (Rendering|Material|SetScalarParameterValueonMaterials C "FogStart" (Variables|6-CieloNiebla|GetFogStart))
  (Rendering|Material|SetScalarParameterValueonMaterials C "FogDensity" (Variables|6-CieloNiebla|GetFogDensity))
  (Rendering|Material|SetScalarParameterValueonMaterials C "Dither" (Variables|6-CieloNiebla|GetDither))
  (Rendering|Material|SetScalarParameterValueonMaterials C "PerfMode" (Variables|Z-Interno|GetPerfMode)))

;; ===== GRAFO: LookDust  (funcion nueva, sin parametros)
;; Las perillas que usa M_DrawDust_SC. SeaZ = Z del actor (el disco del mar esta en el origen del actor): el polvo no
;; baja del agua. La visibilidad junta la perilla y el banco (PerfDS4 = sin polvo).
(fn LookDust ()
  (bind _d (Variables|Default|GetDust))
  (Rendering|Material|SetScalarParameterValueonMaterials _d "Advance" (Variables|3-Avance|GetAdvance))
  (Rendering|Material|SetScalarParameterValueonMaterials _d "DustFollow" (Variables|7-Polvo|GetDustFollow))
  (Rendering|Material|SetScalarParameterValueonMaterials _d "DustRise" (Variables|7-Polvo|GetDustRise))
  (Rendering|Material|SetScalarParameterValueonMaterials _d "DustWobble" (Variables|7-Polvo|GetDustWobble))
  (Rendering|Material|SetScalarParameterValueonMaterials _d "DustBox" (Variables|7-Polvo|GetDustBox))
  (Rendering|Material|SetScalarParameterValueonMaterials _d "DustSize" (Variables|7-Polvo|GetDustSize))
  (Rendering|Material|SetScalarParameterValueonMaterials _d "DustNear" (Variables|7-Polvo|GetDustNear))
  (Rendering|Material|SetScalarParameterValueonMaterials _d "FogStart" (Variables|6-CieloNiebla|GetFogStart))
  (Rendering|Material|SetScalarParameterValueonMaterials _d "FogDensity" (Variables|6-CieloNiebla|GetFogDensity))
  (Rendering|Material|SetScalarParameterValueonMaterials _d "SeaZ" (.z (Transformation|GetActorLocation)))
  (Rendering|Material|SetColorParameterValueonMaterials _d "DustColor" (Variables|7-Polvo|GetDustColor))
  (Rendering|Material|SetScalarParameterValueonMaterials _d "DustAmt" (Variables|7-Polvo|GetDustAmt))
  (Rendering|Material|SetColorParameterValueonMaterials _d "DustBG" (Variables|7-Polvo|GetDustBG))
  (Rendering|SetVisibility _d (and (Variables|7-Polvo|GetShowDust) (not (Variables|Z-Interno|GetPerfNoDust))) false))

;; ===== GRAFO: ApplyLook  (funcion nueva, sin parametros)
;; Perillas del actor -> los tres materiales. Desde el Construction Script (se ve al instante en el viewport) y desde
;; BeginPlay (en el juego cocinado no se depende de los MIDs del Construction Script).
(fn ApplyLook ()
  (CallFunction|LookSea :C (Variables|Default|GetSea))
  (CallFunction|LookSea :C (Variables|Default|GetSky))
  (Rendering|Material|SetScalarParameterValueonMaterials (Variables|Default|GetSea) "Part" 0.0)
  (Rendering|Material|SetScalarParameterValueonMaterials (Variables|Default|GetSky) "Part" 1.0)
  (CallFunction|WaveConstants)
  (CallFunction|LookDust))

;; ===== GRAFO: ApplyPerf  (funcion nueva, sin parametros)
(fn ApplyPerf ()
  (Rendering|Material|SetScalarParameterValueonMaterials (Variables|Default|GetSea) "PerfMode" (Variables|Z-Interno|GetPerfMode))
  (Rendering|Material|SetScalarParameterValueonMaterials (Variables|Default|GetSky) "PerfMode" (Variables|Z-Interno|GetPerfMode))
  (Rendering|SetVisibility (Variables|Default|GetDust) (and (Variables|7-Polvo|GetShowDust) (not (Variables|Z-Interno|GetPerfNoDust))) false))

;; ===== GRAFO: ConstructionScript  (el Construction Script del BP nuevo esta vacio: se escribe con fn ConstructionScript)
;; La MI de cada componente sale de la perilla (8-Material); sin colision (el dibujo no choca con el mar).
(fn ConstructionScript ()
  (Rendering|Material|SetMaterial (Variables|Default|GetSea) 0 (Variables|8-Material|GetSeaMI))
  (Rendering|Material|SetMaterial (Variables|Default|GetSky) 0 (Variables|8-Material|GetSeaMI))
  (Rendering|Material|SetMaterial (Variables|Default|GetDust) 0 (Variables|8-Material|GetDustMI))
  (Collision|SetCollisionEnabled (Variables|Default|GetSea) "NoCollision")
  (Collision|SetCollisionEnabled (Variables|Default|GetSky) "NoCollision")
  (Collision|SetCollisionEnabled (Variables|Default|GetDust) "NoCollision")
  (CallFunction|ApplyLook))

;; ===== GRAFO: EventGraph  (BP nuevo: borrar ANTES los 3 eventos fantasma que trae el EventGraph; los Custom primero)
;; Banco (plan seccion 5): 'ke * PerfDS<N>' en la consola del visor. Nombres PROPIOS (PerfDS*) para no chocar con los
;; Perf0..3 del latido si los dos entornos estan en el mismo nivel (Test_Recorrido).
;;   0 todo · 1 vertices baratos (sin oleaje) · 2 pixeles baratos (color plano) · 3 los dos · 4 sin polvo
(event Custom|PerfDS0 ()
  (Variables|Z-Interno|SetPerfMode 0.0)
  (Variables|Z-Interno|SetPerfNoDust false)
  (CallFunction|ApplyPerf)
  (Development|PrintString "PERF: drawsea modo 0 (todo)"))
(event Custom|PerfDS1 ()
  (Variables|Z-Interno|SetPerfMode 1.0)
  (Variables|Z-Interno|SetPerfNoDust false)
  (CallFunction|ApplyPerf)
  (Development|PrintString "PERF: drawsea modo 1 (vertices baratos)"))
(event Custom|PerfDS2 ()
  (Variables|Z-Interno|SetPerfMode 2.0)
  (Variables|Z-Interno|SetPerfNoDust false)
  (CallFunction|ApplyPerf)
  (Development|PrintString "PERF: drawsea modo 2 (pixeles baratos)"))
(event Custom|PerfDS3 ()
  (Variables|Z-Interno|SetPerfMode 3.0)
  (Variables|Z-Interno|SetPerfNoDust false)
  (CallFunction|ApplyPerf)
  (Development|PrintString "PERF: drawsea modo 3 (vertices y pixeles baratos)"))
(event Custom|PerfDS4 ()
  (Variables|Z-Interno|SetPerfMode 0.0)
  (Variables|Z-Interno|SetPerfNoDust true)
  (CallFunction|ApplyPerf)
  (Development|PrintString "PERF: drawsea modo 4 (sin polvo)"))
(event EventBeginPlay
  (CallFunction|ApplyLook))
