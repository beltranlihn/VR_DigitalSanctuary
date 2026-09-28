# gen_draw_sea_hlsl.py - genera los Custom HLSL del oceano del dibujo (M_DrawSea_SC / M_DrawDust_SC).
# Plan: docs/PLAN-OCEANO-DIBUJO-2026-09-28.md (seccion 2). Prototipo aprobado: docs/prototipos/oceano-dibujo.html.
# Los 6 oleajes van ESCRITOS 6 VECES con vectores con nombre (W0..W5, V0..V5, E0..E5): sin arreglos ni bucles
# (Adreno, gotcha 399). Este script existe para no copiarlos a mano.
# Uso:  python gen_draw_sea_hlsl.py      -> escribe hlsl/DrawSea*.hlsl y hlsl/DrawDust*.hlsl
# Verificacion: python hlsl/DrawSea_check.py
from pathlib import Path

HL = Path(__file__).resolve().parent / "hlsl"
NW = 6
RULE = "// " + "-" * 104

# (nombre, tipo, origen en el grafo, descripcion)
SEA_VS_IN = (
    [("LP", "float3", "LocalPosition, pin XYZ", "posicion del vertice en el espacio del actor (cm); el disco es plano"),
     ("Part", "float", "ScalarParameter Part", "0 mar, 1 cielo (lo pone el Construction Script)"),
     ("PerfMode", "float", "ScalarParameter PerfMode", "banco: 1 y 3 = vertices baratos (sin oleaje)")]
    + [("W%d" % i, "float4", "VectorParameter W%d" % i, "oleaje %d: (d.x, d.y, k, omega) - lo escribe WaveConstants del BP" % i) for i in range(NW)]
    + [("V%d" % i, "float4", "VectorParameter V%d" % i, "oleaje %d: (A, fase, velocidad del grupo, fase del grupo)" % i) for i in range(NW)]
    + [("E%d" % i, "float4", "VectorParameter E%d" % i, "oleaje %d: (dir del grupo x, y, LOD desde, LOD hasta)" % i) for i in range(NW)]
    + [("GroupAmt", "float", "ScalarParameter GroupAmt", "0.75 (fuerza de los grupos de olas)"),
       ("GroupLen", "float", "ScalarParameter GroupLen", "9000 cm (largo de un grupo)"),
       ("Warp", "float", "ScalarParameter Warp", "120 cm (serpenteo de las crestas)"),
       ("WarpScale", "float", "ScalarParameter WarpScale", "4500 cm"),
       ("Advance", "float", "ScalarParameter Advance", "5 cm/s (el campo se desliza hacia el usuario, -X local)"),
       ("CalmR", "float", "ScalarParameter CalmR", "600 cm (radio de calma bajo el usuario)"),
       ("CalmMin", "float", "ScalarParameter CalmMin", "0.7 (amplitud en el centro)")]
)

SEA_PS_IN = [
    ("G", "float4", "VertexInterpolator_0 (pin PS) <- DrawSeaGradVS", "(h, dh/dx, dh/dy, 0)"),
    ("Vv", "float3", "WorldPosition - CameraPositionWS (nodos, LWC)", "de la camara al punto (cm); distancia REAL para la niebla"),
    ("Part", "float", "ScalarParameter Part", "0 mar, 1 cielo"),
    ("PerfMode", "float", "ScalarParameter PerfMode", "banco: 2 y 3 = pixeles baratos (color plano)"),
    ("DeepColor", "float3", "VectorParameter DeepColor", "cara en sombra (lineal)"),
    ("SurfColor", "float3", "VectorParameter SurfColor", "cara iluminada (lineal)"),
    ("CrestColor", "float3", "VectorParameter CrestColor", "tinte de las crestas (lineal)"),
    ("CrestAmt", "float", "ScalarParameter CrestAmt", "1"),
    ("SwellAmp", "float", "ScalarParameter SwellAmp", "22 cm (normaliza el tinte de cresta)"),
    ("LightAz", "float", "ScalarParameter LightAz", "40 grados (0 = +X local)"),
    ("LightEl", "float", "ScalarParameter LightEl", "22 grados"),
    ("WrapPow", "float", "ScalarParameter WrapPow", "1.6 (dureza de la luz mate)"),
    ("ZenithColor", "float3", "VectorParameter ZenithColor", "cielo arriba (lineal)"),
    ("HorizonColor", "float3", "VectorParameter HorizonColor", "cielo en el horizonte = color de la niebla (lineal)"),
    ("SkyPow", "float", "ScalarParameter SkyPow", "0.45"),
    ("GlowColor", "float3", "VectorParameter GlowColor", "resplandor del cielo (lineal)"),
    ("GlowAmt", "float", "ScalarParameter GlowAmt", "0.012"),
    ("GlowPow", "float", "ScalarParameter GlowPow", "30"),
    ("FogStart", "float", "ScalarParameter FogStart", "500 cm"),
    ("FogDensity", "float", "ScalarParameter FogDensity", "0.00017 /cm"),
    ("Dither", "float", "ScalarParameter Dither", "1 (dither estatico contra el banding, el del latido)"),
]

DUST_VS_IN = [
    ("UV0", "float2", "TexCoord 0", "esquina del quad (0..1)"),
    ("UV1", "float2", "TexCoord 1", "semilla x, y (0..1); la guarda SM_DrawDust_SC, igual en las 4 esquinas"),
    ("UV2", "float2", "TexCoord 2", "semilla z, w (0..1)"),
    ("CamWS", "float3", "CameraPositionWS", "camara (cm); el nivel esta cerca del origen (gotcha 398)"),
    ("VtxRel", "float3", "WorldPosition - CameraPositionWS (nodos, LWC)", "posicion original del vertice relativa a la camara"),
    ("Advance", "float", "ScalarParameter Advance", "5 cm/s (el mismo del mar)"),
    ("DustFollow", "float", "ScalarParameter DustFollow", "1 (cuanto sigue al avance)"),
    ("DustRise", "float", "ScalarParameter DustRise", "0.6 cm/s"),
    ("DustWobble", "float", "ScalarParameter DustWobble", "8 cm"),
    ("DustBox", "float", "ScalarParameter DustBox", "1400 cm (volumen que se repite alrededor de los ojos)"),
    ("DustSize", "float", "ScalarParameter DustSize", "0.9 cm (diametro de una mota)"),
]
DUST_ALPHA_IN = [x for x in DUST_VS_IN if x[0] not in ("UV0", "VtxRel")] + [
    ("DustNear", "float", "ScalarParameter DustNear", "35 cm (se apaga cerca de la cara)"),
    ("FogStart", "float", "ScalarParameter FogStart", "500 cm (la misma niebla del mar)"),
    ("FogDensity", "float", "ScalarParameter FogDensity", "0.00017 /cm"),
    ("SeaZ", "float", "ScalarParameter SeaZ", "Z de mundo de la superficie (la escribe el BP = Z del actor)"),
]
DUST_PS_IN = [
    ("A", "float", "VertexInterpolator_0 (pin PS) <- DrawDustAlphaVS", "alpha de la mota"),
    ("UV0", "float2", "TexCoord 0", "esquina del quad (0..1)"),
    ("DustColor", "float3", "VectorParameter DustColor", "lineal"),
    ("DustAmt", "float", "ScalarParameter DustAmt", "0.45"),
    ("DustBG", "float3", "VectorParameter DustBG", "fondo tipico detras de las motas (lineal); gotcha 485"),
]


def header(name, stage, cmot, out_desc, dest, ins, extra=""):
    lines = ["// %s - %s, %s. Generado por gen_draw_sea_hlsl.py: NO editar a mano." % (name, dest, stage),
             "// Plan: docs/PLAN-OCEANO-DIBUJO-2026-09-28.md. Prototipo: docs/prototipos/oceano-dibujo.html (v3)."]
    if extra:
        lines += ["// " + l for l in extra.split("\n")]
    lines += [RULE,
              "// NODO  MaterialExpressionCustom  Description \"%s\"  OutputType %s" % (name, cmot),
              "//       sin additionalOutputs ni IncludeFilePaths. Es el CUERPO de la funcion: termina en return.",
              "// SALIDA " + out_desc,
              "// ENTRADAS (%d, en este orden):" % len(ins)]
    w = max(len(n) for n, _, _, _ in ins)
    for i, (n, t, src, d) in enumerate(ins, 1):
        lines.append("//  %2d  %-*s  %-6s  %s  |  %s" % (i, w, n, t, src, d))
    lines.append("// TIEMPO: View.GameTime adentro (fp32, sin periodo; gotchas 185 y 382). No hay nodo Time.")
    lines.append(RULE)
    return "\n".join(lines) + "\n"


PRE_SEA = """float T = View.GameTime;
float pm = floor(PerfMode + 0.5);
if (Part > 0.5 || pm == 1.0 || pm == 3.0) { return %s; }
float2 P = LP.xy;
const float TAU = 6.2831853;
float kw = TAU / WarpScale;
float ax = P.y * kw + T * 0.071;
float ay = P.x * kw * 1.31 + T * 0.053 + 1.7;
"""


def wave_height(i):
    return """[branch] if (r < E{i}.w)
{{
  float x{i} = saturate((r - E{i}.z) / (E{i}.w - E{i}.z));
  float lod{i} = 1.0 - x{i} * x{i} * (3.0 - 2.0 * x{i});
  float m{i} = 1.0 + GroupAmt * sin(kg * (dot(qa, E{i}.xy) - V{i}.z * T) + V{i}.w);
  S += V{i}.x * lod{i} * m{i} * sin(W{i}.z * dot(W{i}.xy, qa) - W{i}.w * T + V{i}.y);
}}
""".format(i=i)


def wave_grad(i):
    return """[branch] if (r < E{i}.w)
{{
  float se{i}, ce{i};
  sincos(kg * (dot(qa, E{i}.xy) - V{i}.z * T) + V{i}.w, se{i}, ce{i});
  float m{i} = 1.0 + GroupAmt * se{i};
  float2 gm{i} = GroupAmt * ce{i} * kg * E{i}.xy;
  float x{i} = saturate((r - E{i}.z) / (E{i}.w - E{i}.z));
  float lod{i} = 1.0 - x{i} * x{i} * (3.0 - 2.0 * x{i});
  float dlod{i} = -6.0 * x{i} * (1.0 - x{i}) / (E{i}.w - E{i}.z);
  float s{i}, c{i};
  sincos(W{i}.z * dot(W{i}.xy, qa) - W{i}.w * T + V{i}.y, s{i}, c{i});
  S += V{i}.x * lod{i} * m{i} * s{i};
  gq += V{i}.x * lod{i} * (m{i} * W{i}.z * c{i} * W{i}.xy + s{i} * gm{i});
  gl += V{i}.x * dlod{i} * m{i} * s{i};
}}
""".format(i=i)


def height_vs():
    b = PRE_SEA % "float3(0.0, 0.0, 0.0)"
    b += """float2 qa = P + Warp * float2(sin(ax), sin(ay)) + float2(Advance * T, 0.0);
float r = max(length(P), 1.0);
float kg = TAU / GroupLen;
float S = 0.0;
"""
    b += "".join(wave_height(i) for i in range(NW))
    b += """float xc = saturate(r / CalmR);
return float3(0.0, 0.0, lerp(CalmMin, 1.0, xc * xc * (3.0 - 2.0 * xc)) * S);
"""
    return b


def grad_vs():
    b = PRE_SEA % "float4(0.0, 0.0, 0.0, 0.0)"
    b += """float dwx_dy = Warp * kw * cos(ax);
float dwy_dx = Warp * kw * 1.31 * cos(ay);
float2 qa = P + Warp * float2(sin(ax), sin(ay)) + float2(Advance * T, 0.0);
float r = max(length(P), 1.0);
float kg = TAU / GroupLen;
float S = 0.0;
float2 gq = float2(0.0, 0.0);
float gl = 0.0;
"""
    b += "".join(wave_grad(i) for i in range(NW))
    b += """// regla de la cadena del warp: grad_p = J^T grad_q
float2 gS = float2(gq.x + dwy_dx * gq.y, dwx_dy * gq.x + gq.y) + gl * P / r;
float xc = saturate(r / CalmR);
float fade = lerp(CalmMin, 1.0, xc * xc * (3.0 - 2.0 * xc));
float dfade = (1.0 - CalmMin) * 6.0 * xc * (1.0 - xc) / CalmR;
float2 g = fade * gS + S * dfade * P / r;
return float4(fade * S, g.x, g.y, 0.0);
"""
    return b


def sea_ps():
    return """float pm = floor(PerfMode + 0.5);
// dither estatico contra el banding: el MISMO de HeartScapePS (aprobado en visor)
float3 p3 = frac(float3(Parameters.SvPosition.xyx) * 0.1031);
p3 += dot(p3, p3.yzx + 33.33);
float dith = (frac((p3.x + p3.y) * p3.z) - 0.5) / 255.0 * Dither;
if (pm >= 2.0) { return SurfColor + dith; }
float az = LightAz * 0.017453292519943295;
float el = LightEl * 0.017453292519943295;
float3 L = float3(cos(el) * cos(az), cos(el) * sin(az), sin(el));
float dist = max(length(Vv), 1.0);
float3 V = Vv / dist;
float3 sdir = V;
if (Part < 0.5) { sdir = normalize(float3(V.xy, 0.015)); }
float3 sky = lerp(HorizonColor, ZenithColor, pow(saturate(sdir.z), SkyPow)) + GlowColor * GlowAmt * pow(saturate(dot(sdir, L)), GlowPow);
if (Part > 0.5) { return sky + dith; }
// MATE: solo difusa envolvente sobre la forma de la ola. Sin reflejo, sin especular.
float3 N = normalize(float3(-G.y, -G.z, 1.0));
float diff = pow(saturate(dot(N, L) * 0.5 + 0.5), WrapPow);
float3 col = lerp(DeepColor, SurfColor, diff);
float crest = saturate(G.x / (SwellAmp * 2.0) + 0.5);
col += CrestColor * CrestAmt * crest * crest;
float fog = 1.0 - exp(-max(dist - FogStart, 0.0) * FogDensity);
return lerp(col, sky, fog) + dith;
"""


DUST_PRE = """float T = View.GameTime;
float3 Seed = float3(UV1.x, UV1.y, UV2.x);   // la semilla va en las UV: la posicion de la malla solo da bounds
float SeedW = UV2.y;
float3 drift = float3(-Advance * DustFollow, 0.0, DustRise) * T;
float3 wob = DustWobble * float3(sin(T * 0.21 + SeedW * 6.28), sin(T * 0.17 + SeedW * 9.1), sin(T * 0.13 + SeedW * 4.3));
float3 boxOff = float3(0.0, 0.0, -0.25 * DustBox);
float3 f = frac((Seed * DustBox + drift - (CamWS + boxOff)) / DustBox);
float3 pr = boxOff + (f - 0.5) * DustBox + wob;      // centro de la mota, relativo a la camara
float dist = max(length(pr), 1.0);
float projScale = 0.5 * View.ViewSizeAndInvSize.y * ResolvedView.ViewToClip[1][1];
float px = DustSize * projScale / dist;             // diametro en pixeles
float px2 = max(px, 1.5);                           // nunca menos de 1,5 px...
"""


def dust_vs():
    return DUST_PRE + """float half_ = 0.5 * DustSize * px2 / max(px, 0.0001);   // ...agrandando el quad
float2 Cn = UV0 * 2.0 - 1.0;
float3 Rt = ResolvedView.ViewToTranslatedWorld[0].xyz;
float3 Up = ResolvedView.ViewToTranslatedWorld[1].xyz;
return pr + (Rt * Cn.x + Up * Cn.y) * half_ - VtxRel;   // WPO = destino - posicion original
"""


def dust_alpha():
    return DUST_PRE + """float3 e3 = 1.0 - abs(f - 0.5) * 2.0;                  // 0 en el borde de la caja: ahi se apaga
float edge = smoothstep(0.0, 0.18, min(min(e3.x, e3.y), e3.z));
float fog = 1.0 - exp(-max(dist - FogStart, 0.0) * FogDensity);
float nearF = smoothstep(DustNear, DustNear * 3.0, dist);
float tw = 0.65 + 0.35 * sin(T * 0.6 + SeedW * 31.0);
float above = step(SeaZ, CamWS.z + pr.z);
return edge * nearF * (1.0 - fog) * tw * above * min(1.0, (px * px) / (px2 * px2));   // energia conservada bajo 1,5 px
"""


def dust_ps():
    # gotcha 485: el prototipo (three.js, OETF en cada shader) suma el aditivo en sRGB CODIFICADO; la Quest suma en
    # LINEAL y las motas tenues salen ~2 veces mas apagadas. Contra un fondo conocido (DustBG) se suma en codificado
    # y se devuelve la diferencia lineal. OETF sRGB EXACTA (tramo lineal incluido); ternarios vectoriales no: lerp+step.
    return """float d = length(UV0 * 2.0 - 1.0);
float3 c = DustColor * (DustAmt * A * (1.0 - smoothstep(0.35, 1.0, d)));
float3 bg = max(DustBG, 0.0);
float3 eb = lerp(1.055 * pow(max(bg, 1e-7), 1.0 / 2.4) - 0.055, bg * 12.92, step(bg, 0.0031308));
float3 ec = lerp(1.055 * pow(max(c, 1e-7), 1.0 / 2.4) - 0.055, c * 12.92, step(c, 0.0031308));
float3 s = saturate(eb + ec);
float3 lin = lerp(pow(max((s + 0.055) / 1.055, 1e-7), 2.4), s / 12.92, step(s, 0.04045));
return max(lin - bg, 0.0);
"""


FILES = {
    "DrawSeaHeightVS": ("VERTEX SHADER -> Transform Local->World -> WPO. Solo la ALTURA", "CMOT_Float3",
                        "float3 = (0, 0, h) en local (cm). Part 1 o PerfMode 1/3 -> 0.", "M_DrawSea_SC", SEA_VS_IN, height_vs,
                        "Unreal compila el WPO y cada VertexInterpolator en funciones separadas: cada salida vuelve a\nllamar a su Custom (leccion del latido). Por eso este nodo calcula SOLO h."),
    "DrawSeaGradVS": ("VERTEX SHADER -> VertexInterpolator_0 -> G del PS", "CMOT_Float4",
                      "float4 = (h, dh/dx, dh/dy, 0), local. Gradiente EXACTO (regla de la cadena del warp). Part 1 o PerfMode 1/3 -> 0.",
                      "M_DrawSea_SC", SEA_VS_IN, grad_vs,
                      "Corte por oleaje: si el vertice esta mas alla de E.w, ese oleaje ya vale 0 y el bloque se salta\n(leccion del latido: asi llego a 72 fps)."),
    "DrawSeaPS": ("PIXEL SHADER -> Emissive", "CMOT_Float3", "float3 = color lineal (mate), con dither.", "M_DrawSea_SC", SEA_PS_IN, sea_ps, ""),
    "DrawDustVS": ("VERTEX SHADER -> WPO (mundo; SIN Transform)", "CMOT_Float3", "float3 = desplazamiento en mundo (destino - posicion original).",
                   "M_DrawDust_SC", DUST_VS_IN, dust_vs,
                   "Cada mota vive en una caja que se repite alrededor de la camara (campo infinito), deriva con el\navance, sube y ondula. Quad orientado a la camara, nunca menor a 1,5 px."),
    "DrawDustAlphaVS": ("VERTEX SHADER -> VertexInterpolator_0 -> A del PS", "CMOT_Float1", "float = alpha de la mota (0..1).",
                        "M_DrawDust_SC", DUST_ALPHA_IN, dust_alpha, "Misma cuenta de posicion que DrawDustVS (funcion separada en Unreal)."),
    "DrawDustPS": ("PIXEL SHADER -> Emissive (translucido ADITIVO)", "CMOT_Float3", "float3 = color lineal de la mota.",
                   "M_DrawDust_SC", DUST_PS_IN, dust_ps, ""),
}


def build():
    out = {}
    for name, (stage, cmot, out_desc, dest, ins, fn, extra) in FILES.items():
        out[name] = header(name, stage, cmot, out_desc, dest, ins, extra) + fn()
    return out


if __name__ == "__main__":
    HL.mkdir(exist_ok=True)
    for name, txt in build().items():
        (HL / (name + ".hlsl")).write_text(txt, encoding="ascii", newline="\n")
        print("escrito", name + ".hlsl", len(txt.splitlines()), "lineas")
