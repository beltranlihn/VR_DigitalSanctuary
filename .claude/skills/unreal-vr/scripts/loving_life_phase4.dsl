;; BP_LovingCell_SC — fase 4 (V4, 2026-09-28): la ENVOLTURA EXTERIOR translucida que encierra toda la celula
;; (pedido de Beltran: "envuelve toda la celula en una ameba translucida tambien, con deformacion. Bastante
;; opacidad" + "siempre pensando que corra en un APK"). Funcion NUEVA PushOuter (grafo nuevo, write_graph_dsl
;; entero). Empalme por cirugia: PushMore -> al FINAL, despues de SetVisibility(Dust) -> CallFunction PushOuter.
;; Componente nuevo OuterShell (SM_LovingIco_SC + M_LovingOuter_SC, sort 40, bounds x5, sin sombra, NoCollision).
;; Variables nuevas, categoria 6-Envoltura (instance editable): OuterOpacity 0,5 · OuterMargin 3 · OuterBody 8 ·
;; OuterSoftness 0,8 (p = lerp(8, 3, x) -> p 4; revision 2026-09-28: con 0,65 y p 16 -> 4 era una estrella con muescas en V)
;; · OuterWobble 1 · OuterColor (0,62 0,52 0,86 1).
;; Otra cirugia de esta fase (ameba del nucleo con pseudopodos, CoreWob V4): LifeStep -> SetRMin, literal
;; 0.0675 -> 0.26 (el que multiplica GetNoiseAmount) y 0.4 -> 0.5 SOLO el de (1 - 0.4*Coh); ya reflejado en
;; loving_life_phase1.dsl linea 55. El shader y este cambio van JUNTOS (sin el, en calma los grupos pueden
;; tocar los pseudopodos).

;; PushOuter (): la ENVOLTURA EXTERIOR (componente OuterShell, M_LovingOuter_SC). Va al FINAL de PushMore
;; (despues de SetVisibility(Dust)) por cirugia. Empuja LV0..LV5 (PushGlobals), los 10 centroides con presencia
;; (M0..M9, la misma receta que el nucleo y las particulas), OuterK y OuterCol.
;; OuterK.x = margen EFECTIVO = OuterMargin + holgura de la nube de particulas (DustOffset + 1,8 DustDrift +
;;   2 DustSize: la deriva son 3 senos, <= sqrt3 DustDrift, y la esquina del sprite llega a 1,4 sqrt2 DustSize):
;;   asi la nube tambien queda ADENTRO. OuterK.yzw = OuterBody, OuterSoftness, OuterWobble.
;; OuterCol = OuterColor con alfa = OuterOpacity (NewOpacity, un nodo). Con OuterOpacity 0 el componente se
;;   oculta y no se empuja nada: costo CERO en GPU (A/B exacto para medir en el visor).
;; Un solo Get(acopy) por centroide alimenta .x .y .z (bind: nodo puro, un nodo en vez de tres).
;; 🔴 El multi-exec (if) va AL FINAL: nada despues (trampa 1 del parser).
(fn PushOuter ()
  (bind _n (Math|Integer|Clamp(Integer) (Variables|2-Forma|GetGroupCount) 1 10))
  (bind _on (> (Variables|6-Envoltura|GetOuterOpacity) 0.001))
  (bind _pos (Variables|Z-Interno|GetPos))
  (bind _p0 (Utilities|Array|Get(acopy) _pos 0))
  (bind _p1 (Utilities|Array|Get(acopy) _pos 1))
  (bind _p2 (Utilities|Array|Get(acopy) _pos 2))
  (bind _p3 (Utilities|Array|Get(acopy) _pos 3))
  (bind _p4 (Utilities|Array|Get(acopy) _pos 4))
  (bind _p5 (Utilities|Array|Get(acopy) _pos 5))
  (bind _p6 (Utilities|Array|Get(acopy) _pos 6))
  (bind _p7 (Utilities|Array|Get(acopy) _pos 7))
  (bind _p8 (Utilities|Array|Get(acopy) _pos 8))
  (bind _p9 (Utilities|Array|Get(acopy) _pos 9))
  (Rendering|SetVisibility (Variables|Default|GetOuterShell) _on)
  (if _on
    (CallFunction|PushGlobals :Comp (Variables|Default|GetOuterShell))
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetOuterShell) "M0" (Math|Color|MakeColor (.x _p0) (.y _p0) (.z _p0) (select (> _n 0) 1.0 0.0)))
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetOuterShell) "M1" (Math|Color|MakeColor (.x _p1) (.y _p1) (.z _p1) (select (> _n 1) 1.0 0.0)))
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetOuterShell) "M2" (Math|Color|MakeColor (.x _p2) (.y _p2) (.z _p2) (select (> _n 2) 1.0 0.0)))
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetOuterShell) "M3" (Math|Color|MakeColor (.x _p3) (.y _p3) (.z _p3) (select (> _n 3) 1.0 0.0)))
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetOuterShell) "M4" (Math|Color|MakeColor (.x _p4) (.y _p4) (.z _p4) (select (> _n 4) 1.0 0.0)))
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetOuterShell) "M5" (Math|Color|MakeColor (.x _p5) (.y _p5) (.z _p5) (select (> _n 5) 1.0 0.0)))
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetOuterShell) "M6" (Math|Color|MakeColor (.x _p6) (.y _p6) (.z _p6) (select (> _n 6) 1.0 0.0)))
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetOuterShell) "M7" (Math|Color|MakeColor (.x _p7) (.y _p7) (.z _p7) (select (> _n 7) 1.0 0.0)))
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetOuterShell) "M8" (Math|Color|MakeColor (.x _p8) (.y _p8) (.z _p8) (select (> _n 8) 1.0 0.0)))
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetOuterShell) "M9" (Math|Color|MakeColor (.x _p9) (.y _p9) (.z _p9) (select (> _n 9) 1.0 0.0)))
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetOuterShell) "OuterK" (Math|Color|MakeColor (+ (Math|Float|Max(Float) (Variables|6-Envoltura|GetOuterMargin) 0.0) (+ (Math|Float|Max(Float) (Variables|5-Particulas|GetDustOffset) 0.0) (+ (* 1.8 (Math|Float|Max(Float) (Variables|5-Particulas|GetDustDrift) 0.0)) (* 2.0 (Math|Float|Max(Float) (Variables|5-Particulas|GetDustSize) 0.0))))) (Variables|6-Envoltura|GetOuterBody) (Variables|6-Envoltura|GetOuterSoftness) (Variables|6-Envoltura|GetOuterWobble)))
    (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetOuterShell) "OuterCol" (Math|Color|NewOpacity(LinearColor) (Variables|6-Envoltura|GetOuterColor) (Variables|6-Envoltura|GetOuterOpacity)))))

;; PushLook (): los COLORES de la celula (perillas 7-Color, pedido de Beltran 2026-09-28: "color 1 y 2 de ameba,
;; color de malla, color de particulas"). Corre en el Construction Script y en BeginPlay (no en Tick): los
;; colores se autoran en el editor (cambiar una perilla re-corre el CS). DustColor y OuterColor ya los empuja
;; PushMore/PushOuter cada cuadro.
;;   AmoebaColor1 -> ShadeHigh (luz; alfa = brillo, rgb x alfa <= 1) · AmoebaColor2 -> ShadeLow (sombra; alfa = contraste:
;;   CoreContrast en el nucleo, BallContrast en las bolas) · ShadowColor -> ShadowFill (relleno de sombra; alfa = tinte)
;;   MembraneColor -> FilmCol (alfa = densidad) · MembraneRim -> FilmRim, en la membrana del nucleo, brazos y puentes.
(fn PushLook ()
  (bind _hi (Variables|7-Color|GetAmoebaColor1))
  (bind _lc (Math|Color|NewOpacity(LinearColor) (Variables|7-Color|GetAmoebaColor2) (Variables|7-Color|GetCoreContrast)))
  (bind _lb (Math|Color|NewOpacity(LinearColor) (Variables|7-Color|GetAmoebaColor2) (Variables|7-Color|GetBallContrast)))
  (bind _sh (Variables|7-Color|GetShadowColor))
  (bind _mc (Variables|7-Color|GetMembraneColor))
  (bind _mr (Variables|7-Color|GetMembraneRim))
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentre) "ShadeHigh" _hi)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentre) "ShadeLow" _lc)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentre) "ShadowFill" _sh)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster0) "ShadeHigh" _hi)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster0) "ShadeLow" _lb)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster0) "ShadowFill" _sh)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster1) "ShadeHigh" _hi)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster1) "ShadeLow" _lb)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster1) "ShadowFill" _sh)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster2) "ShadeHigh" _hi)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster2) "ShadeLow" _lb)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster2) "ShadowFill" _sh)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster3) "ShadeHigh" _hi)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster3) "ShadeLow" _lb)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster3) "ShadowFill" _sh)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster4) "ShadeHigh" _hi)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster4) "ShadeLow" _lb)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster4) "ShadowFill" _sh)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster5) "ShadeHigh" _hi)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster5) "ShadeLow" _lb)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster5) "ShadowFill" _sh)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster6) "ShadeHigh" _hi)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster6) "ShadeLow" _lb)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster6) "ShadowFill" _sh)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster7) "ShadeHigh" _hi)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster7) "ShadeLow" _lb)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster7) "ShadowFill" _sh)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster8) "ShadeHigh" _hi)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster8) "ShadeLow" _lb)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster8) "ShadowFill" _sh)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster9) "ShadeHigh" _hi)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster9) "ShadeLow" _lb)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCluster9) "ShadowFill" _sh)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentreFilm) "FilmCol" _mc)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetCentreFilm) "FilmRim" _mr)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetArm0) "FilmCol" _mc)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetArm0) "FilmRim" _mr)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetArm1) "FilmCol" _mc)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetArm1) "FilmRim" _mr)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetArm2) "FilmCol" _mc)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetArm2) "FilmRim" _mr)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetArm3) "FilmCol" _mc)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetArm3) "FilmRim" _mr)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetArm4) "FilmCol" _mc)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetArm4) "FilmRim" _mr)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetArm5) "FilmCol" _mc)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetArm5) "FilmRim" _mr)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetArm6) "FilmCol" _mc)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetArm6) "FilmRim" _mr)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetArm7) "FilmCol" _mc)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetArm7) "FilmRim" _mr)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetArm8) "FilmCol" _mc)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetArm8) "FilmRim" _mr)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetArm9) "FilmCol" _mc)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetArm9) "FilmRim" _mr)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetBridge0) "FilmCol" _mc)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetBridge0) "FilmRim" _mr)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetBridge1) "FilmCol" _mc)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetBridge1) "FilmRim" _mr)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetBridge2) "FilmCol" _mc)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetBridge2) "FilmRim" _mr)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetBridge3) "FilmCol" _mc)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetBridge3) "FilmRim" _mr)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetBridge4) "FilmCol" _mc)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetBridge4) "FilmRim" _mr)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetBridge5) "FilmCol" _mc)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetBridge5) "FilmRim" _mr)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetBridge6) "FilmCol" _mc)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetBridge6) "FilmRim" _mr)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetBridge7) "FilmCol" _mc)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetBridge7) "FilmRim" _mr)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetBridge8) "FilmCol" _mc)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetBridge8) "FilmRim" _mr)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetBridge9) "FilmCol" _mc)
  (Rendering|Material|SetColorParameterValueOnMaterials (Variables|Default|GetBridge9) "FilmRim" _mr))
