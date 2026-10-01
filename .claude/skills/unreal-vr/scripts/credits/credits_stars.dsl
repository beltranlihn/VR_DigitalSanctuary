;; credits_stars.dsl - BP_Credits_SC: las 30 estrellas de la constelacion CRECEN en vez de aparecer de golpe (2026-10-01,
;; pedido de Beltran via Narrativa). NO toca CreditsStep (que sigue des-ocultando la estrella i a los i*0,18 s) ni BP_Obra_SC:
;; EventTick llama StarsGrow DESPUES de CreditsStep, en el mismo cuadro -> la estrella que se des-oculta ya tiene escala ~0.
;; Cada estrella crece de 0 a SU escala del nivel (la que se autora en el viewport) en GrowTime, con salida suave
;; (1 - (1-t)^3), empezando en el mismo instante que hoy (i * StarStep). StarStep tiene que ser el 0,18 de CreditsStep.
;; Vars nuevas: Stars (GrowTime 1,2 · StarStep 0,18; perillas del BLUEPRINT, no de la instancia) y Z-Stars (StarsCached,
;; StarsDone, StarActors, StarScale). Gotcha 558b: la instancia colocada en la Obra nace con las variables nuevas en 0 y la
;; Obra NO se puede guardar ahora (cambios de Beltran) -> si una perilla vale 0 se usa su valor de diseno (1,2 / 0,18).

;; ===== GRAFO: StarsGrow
(fn StarsGrow ()
  (bind _self self)
  (if (and (Variables|Default|GetRun) (not (Variables|Z-Stars|GetStarsDone)))
    (CallFunction|StarsCache _self)
    (CallFunction|StarsAll _self)))

;; ===== GRAFO: StarsCache
;; Una sola vez (el primer cuadro con Run): las estrellas y su escala del nivel, antes de tocarlas.
(fn StarsCache ()
  (if (not (Variables|Z-Stars|GetStarsCached))
    (CallFunction|StarsCacheGo self)))

;; ===== GRAFO: StarsCacheGo
(fn StarsCacheGo ()
  (bind _arr (Actor|GetAllActorswithTag "CreditStar"))
  (Variables|Z-Stars|SetStarsCached true)
  (Variables|Z-Stars|SetStarActors _arr)
  (Utilities|Array|Clear (Variables|Z-Stars|GetStarScale))
  (for _a _arr
    (Utilities|Array|Add (Variables|Z-Stars|GetStarScale) (Transformation|GetActorScale3D _a))))

;; ===== GRAFO: StarsAll
;; Termina cuando la ultima estrella llego a su escala (ese ultimo cuadro todavia las escribe, ya en 1).
(fn StarsAll ()
  (bind _n (Utilities|Array|Length (Variables|Z-Stars|GetStarActors)))
  (bind _ss (select (> (Variables|Stars|GetStarStep) 0.0) (Variables|Stars|GetStarStep) 0.18))
  (bind _gt (select (> (Variables|Stars|GetGrowTime) 0.0) (Variables|Stars|GetGrowTime) 1.2))
  (Variables|Z-Stars|SetStarsDone (>= (Variables|Default|GetCT) (+ (* (Math|Conversions|ToFloat(Integer) _n) _ss) _gt)))
  (for _i (range _n)
    (CallFunction|StarOne self _i)))

;; ===== GRAFO: StarOne
(fn StarOne (I)
  (bind _ss (select (> (Variables|Stars|GetStarStep) 0.0) (Variables|Stars|GetStarStep) 0.18))
  (bind _gt (select (> (Variables|Stars|GetGrowTime) 0.0) (Variables|Stars|GetGrowTime) 1.2))
  (bind _t (Math|Float|Clamp(Float) (/ (- (Variables|Default|GetCT) (* (Math|Conversions|ToFloat(Integer) I) _ss)) _gt)))
  (bind _e (- 1.0 (* (- 1.0 _t) (* (- 1.0 _t) (- 1.0 _t)))))
  (Transformation|SetActorScale3D :self (Utilities|Array|Get(acopy) (Variables|Z-Stars|GetStarActors) I) :NewScale3D (* (Utilities|Array|Get(acopy) (Variables|Z-Stars|GetStarScale) I) (Math|Float|Max(Float) 0.001 _e))))
