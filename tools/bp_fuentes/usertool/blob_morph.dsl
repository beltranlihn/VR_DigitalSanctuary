;; blob_morph.dsl - la entrada y la salida del metaball por MORFEO (pedido de Beltran, audio 04:30 del 2026-09-30:
;; "no de escala 0 a 1 con la misma forma: los blobs crecen y se mezclan").
;; SIN tocar el shader del raymarch: BlobMorph empuja al MID del Volume las perillas de forma multiplicadas por una curva
;; de EnvT (quintica q). En q = 1 todo vale EXACTAMENTE la perilla autorada (el look aprobado queda intacto).
;;   radio × lerp(MorphRadius, 1, q)       gotas que nacen de puntos (el shader tiene piso de 0,5 u)
;;   SizeVariation lerp(MorphSizeVar, SV, q) con 1,6 las gotas de SF negativo quedan en el piso mientras las otras crecen:
;;                                          nacen ESCALONADAS, sin tocar el shader
;;   Spread × lerp(MorphSpread | MorphSpreadOut, 1, q)   entran de afuera y se juntan; al salir se DISPERSAN mas
;;   Smoothness × lerp(MorphSmooth, 1, q)  esferas sueltas que se funden en la masa
;;   Brightness × lerp(MorphBright, 1, q)  nacen un poco mas luminosas (familia "luz primero")
;;   CurlAmount × lerp(MorphCurl, 1, q)    mas remolino mientras se arman
;; La escala del actor ya no va de 0 a 1: lerp(MorphScale, 1, q) (la sombra del valle la sigue igual, crece con el metaball).
;; Entrada vs salida: bShown (true = entrando). __PARAM_*__ = nombres reales de los parametros del material (recon).
;; Variables en Default al escribir; las de categoria con espacios se pasan a Default antes y se devuelven despues.

;; ===== GRAFO: BlobMorph
(fn BlobMorph ()
  (bind _e (Math|Float|Clamp(Float) (Variables|Default|GetEnvT)))
  (bind _q (* (* (* _e _e) _e) (+ (* _e (- (* _e 6.0) 15.0)) 10.0)))
  (bind _vol (Variables|Default|GetVolume))
  (Rendering|Material|SetScalarParameterValueonMaterials _vol "BlobRadius" (* (Variables|Default|GetBlobRadius) (Math|Float|Lerp (Variables|Default|GetMorphRadius) 1.0 _q)))
  (Rendering|Material|SetScalarParameterValueonMaterials _vol "SizeVariation" (Math|Float|Lerp (Variables|Default|GetMorphSizeVar) (Variables|Default|GetSizeVariation) _q))
  (Rendering|Material|SetScalarParameterValueonMaterials _vol "Spread" (* (Variables|Default|GetSpread) (Math|Float|Lerp (select (Variables|Default|GetShown) (Variables|Default|GetMorphSpread) (Variables|Default|GetMorphSpreadOut)) 1.0 _q)))
  (Rendering|Material|SetScalarParameterValueonMaterials _vol "Smoothness" (* (Variables|Default|GetSmoothness) (Math|Float|Lerp (Variables|Default|GetMorphSmooth) 1.0 _q)))
  (Rendering|Material|SetScalarParameterValueonMaterials _vol "Brightness" (* (Variables|Default|GetBrightness) (Math|Float|Lerp (Variables|Default|GetMorphBright) 1.0 _q)))
  (Rendering|Material|SetScalarParameterValueonMaterials _vol "CurlAmount" (* (Variables|Default|GetCurlAmount) (Math|Float|Lerp (Variables|Default|GetMorphCurl) 1.0 _q))))

;; ===== GRAFO: BlobApplyEnv
;; misma logica que la anterior (escala del actor + oculto en 0) con dos cambios: la escala sale de MorphScale (no de 0)
;; con un arranque smoothstep en el primer 20 % (nace de tamano cero, sin puntos que salten el primer cuadro), y al
;; final BlobMorph empuja la forma.
(fn BlobApplyEnv ()
  (bind _self self)
  (bind _e (Math|Float|Clamp(Float) (Variables|Default|GetEnvT)))
  (bind _q (* (* (* _e _e) _e) (+ (* _e (- (* _e 6.0) 15.0)) 10.0)))
  (bind _r (Math|Float|Clamp(Float) (* _e 5.0)))
  (bind _s (Math|Float|Max(Float) (* (* (* _r _r) (- 3.0 (* 2.0 _r))) (Math|Float|Lerp (Variables|Default|GetMorphScale) 1.0 _q)) 0.001))
  (Transformation|SetActorScale3D _self (Math|Vector|MakeVector _s _s _s))
  (Rendering|SetActorHiddenInGame _self (<= _e 0.0))
  (CallFunction|BlobMorph))
