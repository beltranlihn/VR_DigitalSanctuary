import json, ast
NL = chr(10)
def L(*xs):
    return NL.join(xs) + NL
SRE_SEQ = L('(fn StageRequestEnd ()',
            '  (Variables|Z-Estado|SetReqHasMelody false)',
            '  (for _s (Variables|Z-Estado|GetSlots)',
            '    (Utilities|IsValid _s',
            '      (:"Is Valid"',
            '        (Utilities|IsValid (Class|BPSeqSlotSC|GetOccupant _s)',
            '          (:"Is Valid"',
            '            (Variables|Z-Estado|SetReqHasMelody true))))))',
            '  (if (and (== (Variables|Z-Estado|GetPhase) 2) (Variables|Z-Estado|GetReqHasMelody))',
            '    (Development|PrintString "SEQ: la Obra pide cerrar la etapa - se guarda la melodia (SAVE)" false)',
            '    (CallFunction|SaveMelody)',
            '    (else',
            '      (Development|PrintString "SEQ: la Obra pide cerrar la etapa - sin melodia: queda lista (bStageDone)" false)',
            '      (Variables|Default|SetStageDone true))))')
TAIL = '''
SEQ = '/Game/SoulCharger/Core/Attracting/BP_Sequencer_SC.BP_Sequencer_SC'
CDO = '/Game/SoulCharger/Core/Attracting/BP_Sequencer_SC.Default__BP_Sequencer_SC_C'
SRE = %r
def run():
    out = {}
    try:
        lv = T(ST + 'get_current_level', {})[1]
        if 'Test_QuestCtrl' not in str(lv):
            return {'err': 'nivel no neutro', 'level': lv}
        out['vars'] = add_vars(SEQ, CDO, [('ReqHasMelody', 'bool', False, 'Z-Estado')])
        out['sre'] = write_graph(SEQ, 'StageRequestEnd', SRE)
        out['compiled'] = compile_ok(SEQ)
        if out['compiled'] and 'WROTE' in out['sre']:
            out['saved'] = T(AS + 'save_assets', {'asset_paths': ['/Game/SoulCharger/Core/Attracting/BP_Sequencer_SC']})[0]
        out['read'] = str(T(BT + 'read_graph_dsl', {'graph': {'refPath': SEQ + ':StageRequestEnd'}})[1])
    except BaseException as e:
        LOG.append('run ' + str(e)[:300])
    out['log'] = [l[:400] for l in LOG[:8]]
    return out
''' % SRE_SEQ
lib = open('surg_lib.py', encoding='utf-8').read()
i = lib.index('def node_map(')
j = lib.index('def add_vars(')
body = lib[:i] + lib[j:] + TAIL
ast.parse(body)
open('job_seqfix.json', 'w', encoding='utf-8').write(json.dumps({'script': body}))
print(len(body))
