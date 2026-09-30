// QuestCtrlShadePS v1 - M_QuestCtrl_SC, PIXEL SHADER (unlit, opaco). El mando de la obra (blender-3d/assets/quest-controller.md).
// Pedido de Beltran (2026-09-29): como el Meta Quest pero INVERTIDO (cuerpo negro, tapa gris-blanca), sin botones,
// solo el gatillo, que se mueve y cambia de material al apretar; tiene que leerse en niveles SIN luz direccional
// y con algo de sombra. Sombreado falso de la paleta (luz principal fija en el mundo con wrap, relleno desde la vista,
// hemisferio) + BORDE DE LUZ (fresnel) para que el cuerpo negro no se pierda contra el negro + RODILLA suave (sin
// blancos quemados en LDR, r.MobileHDR=False).
// Entradas: N (VertexNormalWS), V (CameraVector), Cap (TexCoord[1].x: mm sobre la linea de la tapa, > 0 tapa),
//           CapBias (el gatillo usa -100: todo "cuerpo" con BodyColor = su color), BodyColor, CapColor, LightDir,
//           Ambient, Diffuse, Wrap, Fill, SelfGlow, RimColor, Rim, RimPow, Pressed (0..1, lo maneja el BP),
//           PressedColor, PressedGlow, Knee.
float3 n = normalize(N);
float3 l = normalize(LightDir);
float key = saturate((dot(n, l) + Wrap) / (1.0 + Wrap));
float nv = saturate(dot(n, normalize(V)));
float hemi = 0.5 + 0.5 * n.z;
float shade = Ambient * hemi + Diffuse * key + Fill * nv + SelfGlow;
// tapa: borde de un pixel de ancho a cualquier distancia (sin serrucho ni borroneo)
float m = Cap + CapBias;
float w = max(fwidth(m) * 0.75, 0.02);
float cap = smoothstep(-w, w, m);
float p = saturate(Pressed);
float3 alb = lerp(lerp(BodyColor, CapColor, cap), PressedColor, p);
float3 c = alb * (shade + PressedGlow * p);
// borde de luz: separa el cuerpo negro del fondo oscuro
c += RimColor * (Rim * pow(max(1.0 - nv, 1.0e-4), RimPow));
// rodilla suave: por encima de Knee se comprime hacia 1 sin cortar (misma que el Hall)
float mx = max(max(c.r, c.g), c.b);
float kn = min(Knee, 0.99);
float mo = (mx < kn) ? mx : kn + (1.0 - kn) * (1.0 - exp(-(mx - kn) / (1.0 - kn)));
c *= mo / max(mx, 1.0e-4);
return c;
