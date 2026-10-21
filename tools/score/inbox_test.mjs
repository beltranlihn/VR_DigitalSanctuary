// inbox_test.mjs — the WAV files of the sounds made in the editor (found in a session of a film editor loading sounds): what a file has to
// be to be accepted (PCM only, not empty, not cut short; WAVE_FORMAT_EXTENSIBLE is PCM when its sub-format says so), the name a sound
// takes from a file (accents dropped, the prefix of what it is), and the plan that keeps obra/audio/inbox/ in agreement with the score
// after undo, replace, delete and copy. Logic: web/editor-obra/app/js/inbox.js. Nothing is read or written on disk.
//   node tools/score/inbox_test.mjs
import path from 'path';
import { createRequire } from 'module';
import { fileURLToPath } from 'url';
const require = createRequire(import.meta.url);
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const I = require(path.join(ROOT, 'web/editor-obra/app/js/inbox.js'));
let fails = 0;
const check = (name, ok, info) => { console.log((ok ? '  ok   ' : '  FAIL ') + name + (info ? '  · ' + info : '')); if (!ok) fails++; };

// ---- WAV files made by hand ----
const u16 = v => [v & 255, (v >> 8) & 255], u32 = v => [v & 255, (v >> 8) & 255, (v >> 16) & 255, (v >>> 24) & 255];
const ascii = s => [...s].map(c => c.charCodeAt(0));
function wav({ tag = 1, ch = 1, sr = 48000, bits = 16, bytes = null, seconds = 1, sub = null, declared = null, extra = [], skipFmt = false, skipData = false }) {
  const align = ch * Math.ceil(bits / 8), byteRate = sr * align, n = bytes != null ? bytes : Math.round(seconds * byteRate);
  const fmt = [...u16(tag), ...u16(ch), ...u32(sr), ...u32(byteRate), ...u16(align), ...u16(bits), ...(tag === 0xFFFE ? [...u16(22), ...u16(bits), ...u32(3), ...u16(sub), ...new Array(14).fill(0)] : [])];
  const head = [...ascii('RIFF'), ...u32(0), ...ascii('WAVE'), ...(skipFmt ? [] : [...ascii('fmt '), ...u32(fmt.length), ...fmt]), ...extra];
  if (!skipData) head.push(...ascii('data'), ...u32(declared != null ? declared : n));
  const out = new Uint8Array(head.length + (skipData ? 0 : n)); out.set(head);   // the samples are silence: zeros
  return out;
}
const ok = (name, f, pred) => { const r = I.check(f); check(name, r.ok && (!pred || pred(r)), JSON.stringify(r)); };
const no = (name, f, re) => { const r = I.check(f); check(name, !r.ok && re.test(r.why), r.why); };

console.log('what a file has to be');
ok('16-bit mono 48 kHz, 1 s: its length comes from the header', wav({}), r => r.dur === 1 && r.sr === 48000 && r.ch === 1 && r.bits === 16 && r.pcm);
ok('24-bit stereo 44.1 kHz, 3 s', wav({ ch: 2, sr: 44100, bits: 24, seconds: 3 }), r => r.dur === 3 && r.ch === 2 && r.bits === 24 && r.sr === 44100);
ok('a 0.05 s blip is a sound', wav({ seconds: 0.05 }), r => Math.abs(r.dur - 0.05) < 1e-9);
ok('WAVE_FORMAT_EXTENSIBLE with a PCM sub-format is PCM (what a DAW exports for 24-bit)', wav({ tag: 0xFFFE, sub: 1, ch: 2, bits: 24 }), r => r.pcm && r.bits === 24 && r.ch === 2);
no('WAVE_FORMAT_EXTENSIBLE with a float sub-format is not PCM', wav({ tag: 0xFFFE, sub: 3, bits: 32 }), /floating point/);
no('32-bit float is refused, saying what it is and what to do', wav({ tag: 3, bits: 32 }), /floating point, not PCM.*16 or 24-bit/);
no('ADPCM is refused', wav({ tag: 2, bits: 4, sr: 22050 }), /ADPCM/);
no('a WAV with no sound in it (header only) is refused', wav({ bytes: 0 }), /no sound/);
no('a single sample is no sound either', wav({ bytes: 2 }), /no sound/);
no('a file cut short is refused, with both lengths', wav({ declared: 200000, bytes: 1000 }), /cut short.*2\.08 s.*0\.01 s/);
ok('one byte short (a missing pad byte) is not cut short', wav({ declared: 96001, bytes: 96000 }), r => r.dur === 1);
ok('a streamed header (0xFFFFFFFF) takes the file as the sound', wav({ declared: 0xFFFFFFFF, seconds: 0.5 }), r => r.dur === 0.5);
ok('chunks before the data (LIST, an odd size padded) are skipped', wav({ extra: [...ascii('LIST'), ...u32(3), 1, 2, 3, 0], seconds: 2 }), r => r.dur === 2);
no('something that is not RIFF/WAVE is refused', new Uint8Array(ascii('ID3\u0004 this is an mp3 pretending'.padEnd(64, ' '))), /not a WAV file/);
no('RIFF/WAVE with junk after it: no format chunk', new Uint8Array([...ascii('RIFF'), 36, 0, 0, 0, ...ascii('WAVE'), ...new Array(500).fill(7)]), /format chunk is missing/);
no('a format but no sound data', wav({ skipData: true }), /no sound data/);
no('no format chunk', wav({ skipFmt: true }), /format chunk is missing/);
no('empty file', new Uint8Array(0), /not a WAV file/);
check('it reads an ArrayBuffer as well as a Uint8Array', I.check(wav({}).buffer).ok);

console.log('the name a sound takes');
const nm = (v, t) => I.nameFor(v, t);
check('accents are dropped: Voz de prueba ñandú.wav → FX_Voz_de_prueba_nandu', nm('Voz de prueba ñandú.wav', 'sound') === 'FX_Voz_de_prueba_nandu', nm('Voz de prueba ñandú.wav', 'sound'));
check('a sound effect never takes a voice name: VO_10.wav → FX_10', nm('VO_10.wav', 'sound') === 'FX_10');
check('…nor an ambience one: AMB_04 → FX_04', nm('AMB_04.wav', 'sound') === 'FX_04');
check('fx_door.WAV → FX_door (the prefix is the sound effect one, in capitals)', nm('fx_door.WAV', 'sound') === 'FX_door');
check('hap_buzz → FX_buzz (a haptic is not a prefix of its own)', nm('hap_buzz.wav', 'sound') === 'FX_buzz');
check('FX_DISCLAIMER.wav stays FX_DISCLAIMER (the clash with Unreal is the caller\'s check)', nm('FX_DISCLAIMER.wav', 'sound') === 'FX_DISCLAIMER');
check('a voice takes VO_: "My line" → VO_My_line, and FX_x typed on a voice → VO_x', nm('My line', 'vo') === 'VO_My_line' && nm('FX_x', 'vo') === 'VO_x');
check('an ambience takes AMB_', nm('wind.wav', 'ambience') === 'AMB_wind');
check('nothing left of the name → FX_NEW_SOUND', nm('', 'sound') === 'FX_NEW_SOUND' && nm('___.wav', 'sound') === 'FX_NEW_SOUND' && nm('日本語', 'sound') === 'FX_NEW_SOUND');
check('take 1.wav and take-1.wav give the same name (the caller makes it unique)', nm('take 1.wav', 'sound') === nm('take-1.wav', 'sound'));

console.log('the inbox follows the score');
const sc = els => ({ elements: Object.fromEntries(Object.entries(els).map(([id, h]) => [id, h === undefined ? {} : h === null ? { audio: { dur: 1 } } : { audio: { hash: h } }])) });
const held = (...hs) => h => hs.includes(h);
let p = I.plan(sc({ el_aaa: 'h1' }), {}, { held: held('h1') });
check('a loaded file that is not there yet is sent', p.upload.length === 1 && p.upload[0].id === 'el_aaa' && p.upload[0].hash === 'h1' && !p.upload[0].from && !p.missing.length && !p.remove.length);
p = I.plan(sc({ el_aaa: 'h1' }), { el_aaa: 'h1' }, { held: held('h1') });
check('a file that is there and is the one: nothing to do', !p.upload.length && !p.missing.length && !p.remove.length);
p = I.plan(sc({ el_aaa: 'h1' }), { el_aaa: 'h2' }, { held: held('h1', 'h2') });
check('undo of Replace WAV: the score says h1, the inbox has h2 → h1 is sent again', p.upload.length === 1 && p.upload[0].hash === 'h1');
p = I.plan(sc({ el_aaa: 'h1' }), { el_aaa: 'h2' }, {});
check('…and if this page no longer has the bytes (reloaded), it is said, never guessed', p.missing.length === 1 && p.missing[0].id === 'el_aaa' && !p.upload.length);
p = I.plan(sc({ el_bbb: 'h1' }), { el_aaa: 'h1' }, {});
check('a duplicate of a sound loaded in an earlier session: its file is copied from the original', p.upload.length === 1 && p.upload[0].from === 'el_aaa' && p.upload[0].id === 'el_bbb');
p = I.plan(sc({}), { el_aaa: 'h1' }, { mine: new Set(['el_aaa']) });
check('a sound deleted (or its load undone): the file this page put there goes', p.remove.join() === 'el_aaa');
p = I.plan(sc({}), { el_aaa: 'h1' }, { mine: new Set(['el_aaa']), keep: [sc({ el_aaa: 'h1' })] });
check('…unless the score saved on disk still names it', !p.remove.length);
p = I.plan(sc({}), { el_aaa: 'h1' }, { mine: new Set() });
check('a file nobody here wrote is never taken out', !p.remove.length);
p = I.plan(sc({ el_aaa: 'h1' }), { el_aaa: 'h1', el_zzz: 'h9' }, { mine: new Set(['el_zzz']) });
check('what the score still names stays, an orphan of this page goes', p.remove.join() === 'el_zzz');
p = I.plan(sc({ el_aaa: undefined, el_bbb: null }), {}, { held: held() });
check('an element with no file, or with a file known only by its length (an old score), is not the inbox\'s business', !p.upload.length && !p.missing.length);
p = I.plan(sc({ VO_10: 'h1', 'not an id': 'h2' }), {}, { held: held('h1', 'h2') });
check('an id the server would not take as a name is left out', !p.upload.length && !p.missing.length);
check('the path of a file is by element id', I.pathOf('el_aaa') === 'obra/audio/inbox/el_aaa.wav');

console.log('the file the saved score names stays until a save (Replace WAV, then a reload, a closed tab or an undo)');
const saved = sc({ el_aaa: 'h1' });
p = I.plan(sc({ el_aaa: 'h2' }), { el_aaa: 'h1' }, { held: held('h2'), keep: [saved] });
check('Replace WAV on a saved sound: the new file waits (defer), the saved one is not overwritten', !p.upload.length && p.defer.length === 1 && p.defer[0].id === 'el_aaa' && p.defer[0].hash === 'h2' && p.defer[0].was === 'h1' && !p.missing.length, JSON.stringify(p));
p = I.plan(sc({ el_aaa: 'h2' }), { el_aaa: 'h1' }, { held: held('h2'), keep: [saved], final: true });
check('…it is sent with the save (final), and the plan says which file it overwrites', p.upload.length === 1 && p.upload[0].was === 'h1' && !p.defer.length, JSON.stringify(p));
p = I.plan(sc({ el_aaa: 'h2' }), { el_aaa: 'h1' }, { held: held('h2') });
check('a file no saved score names (a sound made here, not saved yet) is overwritten at once', p.upload.length === 1 && !p.defer.length && p.upload[0].was === 'h1');
p = I.plan(sc({ el_aaa: 'h2' }), { el_aaa: 'h3' }, { held: held('h2'), keep: [saved] });
check('…and so is a file the saved score does not name for that sound, whatever else it names', p.upload.length === 1 && !p.defer.length);
p = I.plan(sc({ el_aaa: 'h1' }), { el_aaa: 'h1' }, { held: held('h1', 'h2'), keep: [saved] });
check('undo back to the saved file with the inbox still holding it: nothing to do', !p.upload.length && !p.defer.length && !p.missing.length);
p = I.plan(sc({ el_aaa: 'h2' }), { el_aaa: 'h1' }, { held: held(), keep: [saved] });
check('a draft that names a file this page does not have, over a saved one: missing, and it says another file is there', p.missing.length === 1 && p.missing[0].was === 'h1' && !p.defer.length && !p.upload.length, JSON.stringify(p));
p = I.plan(sc({ el_aaa: 'h2' }), {}, { held: held(), keep: [saved] });
check('…and a file that is not there at all says nothing of another one', p.missing.length === 1 && p.missing[0].was === undefined);
p = I.plan(sc({ el_aaa: 'h2', el_bbb: 'h1' }), { el_aaa: 'h1' }, { held: held('h2'), keep: [saved] });
check('a copy of the saved file that waits for its own file in the inbox is not blocked by the sound it was copied from', p.upload.length === 1 && p.upload[0].id === 'el_bbb' && p.upload[0].from === 'el_aaa' && p.defer.length === 1);

console.log('\n' + (fails ? fails + ' FAILED' : 'all ok'));
process.exit(fails ? 1 : 0);
