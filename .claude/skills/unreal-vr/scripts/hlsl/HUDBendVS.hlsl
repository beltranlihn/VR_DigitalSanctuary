// HUDBendVS v3 - WPO de CURVATURA del HUD 3D (M_SCObjectTrans_SC y M_SCGlass_SC, solo HUD). Perilla: MPC_HUD_SC.CurveR
// (cm LOCALES, con signo: |R| < 1 plano; R > 0 extremos hacia +Z; R < 0 hacia -Z). Doblez exacto alrededor del Y local:
// th = x/R, x' = R*sin(th), z' = R*(1 - cos(th)).
// v3 (bug de Beltran en el visor: "al girar la cabeza se enrolla como un tubo y se separa del anillo"): la v1-v2 armaba la
// posicion con WorldPosition - ActorPositionWS; ActorPositionWS no tiene version del cuadro previo y puede llegar
// desfasado respecto de la transformada del primitivo (hijo de un ChildActor pegado a la cabeza). Ahora NO depende del
// actor: P = LocalPosition (sin offsets) y OffX = CustomPrimitiveData[0] = corrimiento X de la pieza respecto del centro de
// la pildora, en cm locales (0 en borde/marco/lamina; +-10,11 en los nidos, seteado en BP_HUDArt_SC).
// Entradas: P (LocalPosition), OffX (CustomPrimitiveData 0), R (CurveR). Devuelve el offset LOCAL.
if (abs(R) < 1.0) return float3(0.0, 0.0, 0.0);
float px = P.x + OffX;
float ar = abs(R);
float x = clamp(px, -ar * 1.5, ar * 1.5);
float th = x / R;
return float3(R * sin(th) - px, 0.0, R * (1.0 - cos(th)));
