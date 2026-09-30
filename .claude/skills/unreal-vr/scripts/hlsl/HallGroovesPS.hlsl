// HallGroovesPS v6 - M_Hall_Interior_SC, segundo Custom node (salida float3). Las HENDIDURAS ILUMINADAS
// que dividen el hall en placas (pedido de Beltran 2026-09-29, croquis en planta + frente):
//   anillos: borde de la alfombra (piso), borde del piso junto al muro, remate del muro (arranque de la boveda),
//            contorno del oculo (boveda), contorno de las dos puertas (circulo en elevacion sobre el muro)
//   5 meridianos: del anillo de la alfombra, por el piso, el muro y la boveda, hasta el anillo del oculo;
//            se cortan en el anillo de cada puerta (SDF: max con la distancia al interior del disco)
// Todas las distancias son CONTINUAS en 3D (sin mascaras por zona) -> fwidth limpio, sin pixeles sueltos.
// Salida: x = nucleo emisivo (ya por GrooveCore), y = halo que lava la superficie (ya por GrooveGlow),
//         z = multiplicador del labio oscuro (1 - LipDark en el borde de la ranura).
// Entradas: P (LocalPosition, cm), GrooveWidth, GlowWidth, LipWidth (cm), GrooveCore, GrooveGlow, LipDark,
//           CarpetRingR, FloorRingR, TopRingZ, OculusRingR, DoorRingR (cm), MeridianPhase (grados).
// Geometria fija (gen_hall_portal.py): piso z 30, muro r 700, centro de puerta z 245,
//           esfera interior de la boveda centro z -2355.6, radio 2975.6.
float r = length(P.xy);
float z = P.z;
float dCarpet = length(float2(r - CarpetRingR, z - 30.0));
float dFloor = length(float2(r - FloorRingR, z - 30.0));
// remate: sobre el muro (z <= 456.7) o sobre el cove de la boveda (centro r 600 / z 456.7, radio 100).
// v2: default 525 (en el cove) -> no toca el tope del anillo de la puerta (245 + DoorRingR); a 440 lo cruzaba.
float tz = TopRingZ - 456.7;
float rTop = (tz <= 0.0) ? 700.0 : 600.0 + sqrt(max(10000.0 - tz * tz, 0.0));
float dTop = length(float2(r - rTop, z - TopRingZ));
float zOc = -2355.6 + sqrt(max(2975.6 * 2975.6 - OculusRingR * OculusRingR, 0.0));
float dOc = length(float2(r - OculusRingR, z - zOc));
float eD = length(float2(P.y, z - 245.0));
// v3: el anillo sigue la SUPERFICIE (su borde inferior cae en el cove del piso, r < 700): distancia en elevacion,
// limitada a la zona de las puertas con una penalizacion continua (|x| < 600 = lejos de las puertas).
// Con (r - 700) como antes, el tramo de abajo se desvanecia (visto por Beltran).
float dDoor = length(float2(eD - DoorRingR, max(600.0 - abs(P.x), 0.0)));
float d = min(min(dCarpet, dFloor), min(min(dTop, dOc), dDoor));
float start = (z < 300.0) ? CarpetRingR : OculusRingR;
float cut = (abs(P.x) > 500.0) ? (DoorRingR - eD) : -1.0e4;
for (int k = 0; k < 5; k++)
{
    float a = radians(MeridianPhase + 72.0 * k);
    float2 dir = float2(cos(a), sin(a));
    float along = dot(P.xy, dir);
    float dm = (along >= start) ? abs(P.x * dir.y - P.y * dir.x) : length(P.xy - dir * start);
    d = min(d, max(dm, cut));
}
// v5: JUNTA de las baldosas (SM_HallTiles_SC) con la DISTANCIA EXACTA a su forma. 🔴 Constantes compartidas con
// gen_bake_hall_tiles.py: TILE_R1 100, TILE_R2 250, TILE_GAP 22, TILE_FIL 20 cm; baldosas centradas en 36 + 72k
// (MeridianPhase 0: si se gira la fase, las baldosas NO giran).
// La baldosa = S' (sector de anillo con esquinas VIVAS: R1+fil, R2-fil, junta+2 fil) engordado fil -> distancia
// exacta = dist(p, S') - fil. v4 usaba la interseccion redondeada de dos SDF, que solo es exacta a 90 grados:
// en las esquinas la junta se afinaba y desaparecia bajo la baldosa (visto por Beltran).
// Distancia a S' en el marco local de cada baldosa, doblado por simetria: arco exterior, arco interior, el tramo recto
// sobre el meridiano de +36 grados y sus dos esquinas.
float dt = 1.0e4;
{
    const float h = 31.0;                                  // media junta + filete
    const float2 mm = float2(0.809017, 0.587785);          // meridiano a +36 (marco local)
    const float2 nn = float2(0.587785, -0.809017);         // normal hacia la baldosa
    float to = sqrt(230.0 * 230.0 - h * h);
    float ti = sqrt(120.0 * 120.0 - h * h);
    float2 Co = to * mm + h * nn;
    float2 Ci = ti * mm + h * nn;
    float ao = atan2(Co.y, Co.x);
    float ai = atan2(Ci.y, Ci.x);
    for (int j = 0; j < 5; j++)
    {
        float c = radians(36.0 + 72.0 * j);
        float2 u = float2(cos(c), sin(c));
        float2 pl = float2(dot(P.xy, u), abs(P.x * -u.y + P.y * u.x));
        float rl = length(pl);
        float al = atan2(pl.y, pl.x);
        float sn = dot(pl, nn) - h;
        float tp = dot(pl, mm);
        float cand = min(length(pl - Co), length(pl - Ci));
        if (al <= ao) cand = min(cand, abs(rl - 230.0));
        if (al <= ai) cand = min(cand, abs(rl - 120.0));
        if (tp >= ti && tp <= to) cand = min(cand, abs(sn));
        bool inS = (rl >= 120.0 && rl <= 230.0 && sn >= 0.0);
        dt = min(dt, inS ? -cand - 20.0 : cand - 20.0);
    }
}
// v6 (2026-09-30, baldosas biseladas v3 de Mesh 3D: bisel 3,5 cm): en reposo (asoman 5 mm) el canto corta el piso
// 1,7 cm ADENTRO del contorno -> la junta arranca en -1,7 cm (antes -0,4 con el bisel de 1,5).
float onFloor = 1.0 - smoothstep(31.0, 34.0, z);
float taa = clamp(fwidth(dt), 0.01, 5.0);
float band = smoothstep(-1.9 - taa, -1.7 + taa, dt) * (1.0 - smoothstep(1.4 - taa, 1.4 + taa, dt));
float reveal = onFloor * saturate(0.45 * band + 0.15 * exp(-max(dt - 1.4, 0.0) / 5.0) * step(-1.7, dt));
float aa = clamp(fwidth(d), 0.01, 5.0);
float hw = 0.5 * GrooveWidth;
float inner = smoothstep(hw - aa, hw + aa, d);
float core = (1.0 - inner) * saturate(GrooveWidth / (2.0 * aa));
float glow = exp(-max(d - hw, 0.0) / max(GlowWidth, 0.1));
float lip = inner * (1.0 - smoothstep(hw + LipWidth - aa, hw + LipWidth + aa, d));
return float3(core * GrooveCore, glow * GrooveGlow, (1.0 - lip * LipDark) * (1.0 - reveal));
