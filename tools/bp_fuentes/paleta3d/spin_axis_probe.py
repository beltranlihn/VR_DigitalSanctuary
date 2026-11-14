# Solo lectura: en que eje local del arte esta la normal del disco. execute_tool_script.
import json
OT='editor_toolset.toolsets.object.ObjectTools.'
AT='editor_toolset.toolsets.actor.ActorTools.'
SM='editor_toolset.toolsets.static_mesh.StaticMeshTools.'
ERRS=[]
def T(n,p):
    try:
        return execute_tool(n, json.dumps(p))['returnValue']
    except BaseException as e:
        ERRS.append(n.split('.')[-1]+' :: '+str(e)[:200]); return None
BP='/Game/SoulCharger/Mechanics/DrawPalette/BP_DrawPalette_SC.BP_DrawPalette_SC_C:'
def run():
    out={}
    try:
        out['bounds_base']=T(SM+'get_bounds',{'mesh':{'refPath':'/Game/SoulCharger/Mechanics/DrawPalette/SM_DrawPalette_Base_SC.SM_DrawPalette_Base_SC'}})
        for c in ['Base','Swatch','Color0','Knob','Slider','Undo']:
            ref=BP+c+'_GEN_VARIABLE'
            g=T(OT+'get_properties',{'instance':{'refPath':ref},'properties':['RelativeRotation']})
            p=T(AT+'get_parent_component',{'component':{'refPath':ref}})
            out[c]={'rot':g,'parent':p}
        g=T(OT+'get_properties',{'instance':{'refPath':'/Game/NeuralCanvas/TB/BP_TBPalette.BP_TBPalette_C:ArtAnchor_GEN_VARIABLE'},'properties':['RelativeRotation','RelativeLocation']})
        out['ArtAnchor']=g
    except BaseException as e:
        ERRS.append('run :: '+str(e)[:200])
    out['errs']=ERRS
    return out
