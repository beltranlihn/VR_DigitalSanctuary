// @uses FluidColor,AbsorbAt,SinCurl,RotR,RotRT,FlowAt,WrapHead,PCG,Bits,LiveClock,CellLobe,CellAmoeba
// @inputs LocalPos,CellI,PieceI,CamL,Head,Drift,DriftVel,Phase,Flow,Absorb,FTop,FMid,FBot,Glow,Caus,FarA,Extras,Light
// @outputs return:Float3,NrmC:Float4,FluidAb:Float4,Pw:Float4
// CÉLULAS MEDIAS (F2): hasta 16 amebas OPACAS con 3-5 bolas satélite, todas en UNA malla
// (SM_FluidMidCells_SC: por célula un núcleo de 642 vértices + 5 satélites de 42). Cada vértice
// trae su célula (UV1.x) y su pieza (UV2.x: 0 = núcleo, 1-5 = satélites); la posición del
// vértice es solo su DIRECCIÓN (la forma la arma este shader). Port de makeCell/layoutCell del
// prototipo + la ameba (CellAmoeba):
//   ancla = semilla de la célula en un cubo de Light.w cm (MidCellRange, 18 m; el prototipo usaba 26 m y
//   quedaban casi siempre a 6-10 m: 15 px) + arrastre, reciclada alrededor de la CABEZA
//   centro = ancla + CellFlow x remolinos; nunca a menos de 2,5 m (se achica) ni en el borde del
//   cubo (se achica: el reciclado no se ve). El desvanecido es COLOR (absorción), no transparencia.
// Extras = (VeilAmount, ShaftAmount, MidCellCount, MidCellScale) · FarA.z = CellFlow.
// Salidas: NrmC = (normal, N.V) · FluidAb = (color del medio, absorción) · Pw = posición (la cáustica va
// POR PÍXEL en el PS: por vértice, sobre la icoesfera de 642, dejaba facetas que se arrastraban, revisión MAT-4).
// Los valores al azar salen de PCG ENTEROS (exactos en las dos evaluaciones del Custom, gotcha 481):
// 2 por célula (4 campos cada uno) y 1 por satélite (5 campos); antes eran 22 hashes por vértice (COS-4).
// Una célula apagada (índice >= MidCellCount) o una pieza que no existe (satélite >= su cantidad)
// colapsa a un punto lejos, debajo: triángulos sin área, sin píxeles.
LVLib L;
float T = ResolvedView.GameTime;
if (!(T > -1.0e9 && T < 1.0e9)) { T = 0.0; }
float phF, phC;
float3 drift;
L.LiveClock(Phase, Caus, Drift, DriftVel, T, phF, phC, drift);
float ci = floor(CellI.x + 0.5);
float pk = floor(PieceI.x + 0.5);
NrmC = float4(0.0, 0.0, 1.0, 0.0);
FluidAb = float4(0.0, 0.0, 0.0, 1.0);
Pw = float4(0.0, 0.0, 0.0, 0.0);
float3 dead = Head.xyz - float3(0.0, 0.0, 5000.0) - LocalPos.xyz;
uint c1 = L.PCG(200.0 + ci * 5.3 + 0.11);                     // ancla (3 x 10 bits)
uint c2 = L.PCG(200.0 + ci * 5.3 + 0.29);                     // satélites, escala, giro (8 bits c/u)
float nSat = 3.0 + floor(L.Bits(c2, 0u, 8u) * 2.999);
if (ci > Extras.z - 0.5 || pk > nSat + 0.5) { return dead; }
// Light.w = MidCellRange; si no llegó (instancia vieja, gotcha 478), el valor de diseño: con 600 las
// rampas de cercanía y de borde se pisaban y las amebas quedaban en puntos (revisión INT-7).
float cube = (Light.w > 1.0) ? Light.w : 1800.0;
float3 sd = float3(L.Bits(c1, 0u, 10u), L.Bits(c1, 10u, 10u), L.Bits(c1, 20u, 10u));
float3 anchor = L.WrapHead(sd * cube + drift, Head.xyz, cube);
float3 Pc = anchor + FarA.z * L.FlowAt(anchor, phF, Flow);
float nearK = saturate((length(Pc - Head.xyz) - 250.0) / 150.0);
float3 rel = anchor - Head.xyz;
float farK = 1.0 - saturate((max(max(abs(rel.x), abs(rel.y)), abs(rel.z)) / cube - 0.4) / 0.1);
float sc = max(Extras.w, 0.0) * (0.75 + 0.5 * L.Bits(c2, 8u, 8u)) * nearK * farK;
if (sc < 1.0e-3) { return dead; }
float spin = (L.Bits(c2, 16u, 8u) - 0.5) * 0.08;
float th = T * spin + ci;
float3 u = normalize(LocalPos.xyz + float3(1.0e-4, 0.0, 0.0));
float coreR = 16.0;
float3 q;
float3 n;
if (pk < 0.5)
{
    float r = L.CellAmoeba(u, ci, T, 0.5, n);
    q = u * (coreR * r);
}
else
{
    // satélite pk-1 de nSat, en un anillo VERTICAL alrededor del núcleo. Más cerca que en el prototipo
    // (1,9-2,3 radios, no 2,7-3,3): pegados al núcleo se leen como UN ser, no como una constelación.
    uint sp  = L.PCG(300.0 + ci * 5.3 + pk * 0.71);
    float a0 = 1.5707963 + (pk - 1.0) * 6.2831853 / nSat + 0.35 * (L.Bits(sp, 0u, 6u) - 0.5);
    float rk = coreR * (1.9 + 0.4 * L.Bits(sp, 6u, 6u));
    float dz = coreR * 0.35 * (L.Bits(sp, 12u, 6u) - 0.5);
    float ph = 6.2831853 * L.Bits(sp, 18u, 7u);
    float sz = coreR * (0.30 + 0.12 * L.Bits(sp, 25u, 7u));
    float a  = a0 + T * spin + 0.05 * sin(T * 0.21 + ph);
    float3 S = float3(-(dz + 2.0 * sin(T * 0.33 + ph)), rk * cos(a), rk * sin(a) + 0.3 * dz);
    q = S + u * sz;
    n = u;
}
float cr = cos(th), sr = sin(th);
q = float3(cr * q.x - sr * q.y, sr * q.x + cr * q.y, q.z);
n = float3(cr * n.x - sr * n.y, sr * n.x + cr * n.y, n.z);
float3 P = Pc + q * sc;
float3 toP = P - CamL.xyz;
float dist = max(length(toP), 1.0);
NrmC = float4(n, dot(n, -toP / dist));              // .w = N.V (para el borde tipo gelatina del PS)
FluidAb = float4(L.FluidColor(toP / dist, FTop, FMid, FBot, Glow, Absorb), L.AbsorbAt(dist, Absorb));
Pw = float4(P, 0.0);
float3 off = P - LocalPos.xyz;
if (!(dot(off, off) < 1.0e12)) { off = float3(0.0, 0.0, 0.0); }
float ol = length(off);
return off * (min(ol, 20000.0) / max(ol, 1.0e-4));
