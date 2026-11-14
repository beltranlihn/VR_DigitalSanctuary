import json
BT='editor_toolset.toolsets.blueprint.BlueprintTools.'
SC='editor_toolset.toolsets.scene.SceneTools.'
B='/Game/SoulCharger/Mechanics/Results/BP_JourneyContent_SC.BP_JourneyContent_SC'
GR=["JcSetTex", "JcSetFade", "JcQuad", "JcTarget", "JcEnsure", "JcData", "JcFromHub", "JcSample", "JcSampleOne", "JcStats", "JcStatOne", "JcText", "JcRect", "JcDash", "JcRing", "JcDisc", "JcLighten", "JcCard", "JcPaint", "JcTitle", "JcGraph", "JcGraphBody", "JcPts", "JcPtOne", "JcAreaTris", "JcTriPair", "JcLine", "JcBand", "JcBandReset", "JcBandScan", "JcBandMark", "JcBandDraw", "JcBandOne", "JcBreath", "JcBreathOne", "JcMelody", "JcTipDraw", "JcTipBody", "JcWrapLoop", "JcWrapWord", "JcWrapFlush", "Build", "SetTip", "JcTipSound", "SetBreathScores", "SetMinutes", "JcTipStep", "JcTipSwap", "JcFadeStep", "JcFadeFrom", "JcFadeK", "EventGraph", "UserConstructionScript", "JcBreathGlow"]
def run():
    out={'hits':{}, 'err':{}, 'n':0}
    try:
        r=execute_tool(SC+'find_actors', json.dumps({'name':'','tag':'','collision_channels':[]}))
        v=json.loads(r) if isinstance(r,str) else r
        if isinstance(v,dict) and ('returnValue' in v):
            v=v['returnValue']
        out['actors']=len(v)
        out['atype']=str(type(v))
    except BaseException as e:
        out['actorsErr']=str(e)[:150]
    for g in GR:
        try:
            r=str(execute_tool(BT+'find_nodes', json.dumps({'graph':B+':'+g,'title':'Gain'})))
            out['n']+=1
            if 'Gain' in r:
                out['hits'][g]=r[:240]
        except BaseException as e:
            out['err'][g]=str(e)[:120]
    return out
