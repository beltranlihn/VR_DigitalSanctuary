
import json
UM = 'UMGToolSet.UMGToolSet.'
OT = 'editor_toolset.toolsets.object.ObjectTools.'
BT = 'editor_toolset.toolsets.blueprint.BlueprintTools.'
AT = 'editor_toolset.toolsets.actor.ActorTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
F = '/Game/SoulCharger/Mechanics/Subtitles/'
WW = F + 'WBP_SubWord_SC.WBP_SubWord_SC'
WL = F + 'WBP_SubLine_SC.WBP_SubLine_SC'
BP = F + 'BP_Subtitles_SC.BP_Subtitles_SC'
DUMP = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/subtitles/build4_out.json'
DATA = {"VoIds": ["VO_01a", "VO_01b", "VO_01c", "VO_02", "VO_03", "VO_03h", "VO_04", "VO_05", "VO_06b", "VO_06c", "VO_06d", "VO_06e", "VO_06f", "VO_06g", "VO_07", "VO_10", "VO_11", "VO_11h", "VO_11b", "VO_12", "VO_12c", "VO_12f1", "VO_12f2", "VO_13", "VO_14", "VO_15", "VO_16", "VO_16h", "VO_17a", "VO_17c", "VO_18", "VO_19", "VO_20", "VO_22", "VO_23", "VO_23b", "VO_25", "VO_26", "VO_27", "VO_27d", "VO_27h", "VO_27b", "VO_27c", "VO_28", "VO_29", "VO_30", "VO_31", "VO_32", "VO_32d", "VO_32h", "VO_32b", "VO_32c", "VO_33", "VO_34a", "VO_34b", "VO_36b", "VO_36p", "VO_35b", "VO_35a", "VO_37"], "VoC0": [0, 2, 3, 5, 8, 10, 11, 14, 15, 16, 17, 19, 20, 21, 22, 24, 27, 29, 30, 32, 34, 36, 37, 38, 40, 42, 43, 45, 46, 48, 49, 51, 53, 55, 57, 58, 60, 62, 63, 65, 67, 68, 70, 71, 72, 73, 74, 77, 78, 80, 81, 82, 83, 84, 86, 89, 91, 92, 94, 95], "VoCN": [2, 1, 2, 3, 2, 1, 3, 1, 1, 1, 2, 1, 1, 1, 2, 3, 2, 1, 2, 2, 2, 1, 1, 2, 2, 1, 2, 1, 2, 1, 2, 2, 2, 2, 1, 2, 2, 1, 2, 2, 1, 2, 1, 1, 1, 1, 3, 1, 2, 1, 1, 1, 1, 2, 3, 2, 1, 2, 1, 4], "CS": [0.05, 3.87, 0.0, 0.0, 4.59, 0.0, 2.41, 5.17, 0.0, 5.476, 0.0, 0.05, 4.53, 6.82, 0.0, 0.0, 0.0, 0.0, 0.96, 0.0, 0.0, 0.0, 0.0, 2.08, 0.0, 2.03, 5.92, 0.0, 2.43, 0.0, 0.0, 2.5, 0.0, 2.759, 0.0, 1.719, 0.0, 0.0, 0.0, 3.936, 0.05, 3.31, 0.0, 0.0, 1.9, 0.0, 0.0, 2.26, 0.0, 0.08, 2.514, 0.04, 2.318, 0.0, 5.72, 0.0, 3.59, 0.0, 0.0, 2.0, 0.0, 3.21, 0.04, 0.0, 1.736, 0.0, 3.315, 0.0, 0.0, 2.7, 0.0, 0.0, 0.0, 0.0, 0.0, 5.205, 8.093, 0.0, 0.0, 4.05, 0.0, 0.0, 0.0, 0.0, 0.0, 1.805, 0.0, 4.56, 6.316, 0.0, 2.19, 0.0, 0.0, 4.047, 0.0, 0.07, 2.84, 4.51, 7.24], "CE": [3.85, 5.66, 2.43, 4.38, 7.17, 2.34, 5.15, 7.57, 5.456, 9.3, 1.85, 4.51, 6.8, 8.67, 5.57, 2.77, 3.44, 0.94, 3.34, 3.44, 3.91, 3.26, 2.06, 3.28, 1.79, 5.73, 8.72, 2.41, 5.96, 3.69, 2.38, 7.68, 2.739, 5.27, 1.699, 3.81, 1.01, 1.26, 3.916, 6.39, 3.23, 6.06, 3.85, 1.88, 3.98, 2.79, 2.2, 4.4, 2.94, 2.494, 5.36, 2.298, 5.11, 5.7, 7.91, 3.56, 7.3, 2.79, 1.98, 5.66, 3.19, 5.53, 4.51, 1.716, 6.34, 3.295, 5.38, 2.49, 2.46, 4.52, 2.88, 2.28, 2.77, 3.21, 5.185, 8.073, 10.45, 5.08, 4.03, 7.08, 2.62, 2.88, 4.55, 2.19, 1.785, 4.3, 4.54, 6.296, 10.54, 2.17, 5.41, 2.88, 4.027, 6.56, 2.4, 2.82, 4.32, 7.22, 9.27], "CW0": [0, 10, 16, 22, 34, 41, 44, 48, 52, 66, 75, 81, 90, 97, 101, 114, 121, 128, 129, 135, 141, 146, 155, 161, 163, 166, 172, 176, 182, 190, 198, 203, 214, 221, 226, 229, 230, 231, 232, 241, 246, 252, 256, 266, 272, 278, 284, 289, 294, 300, 306, 311, 317, 321, 334, 338, 344, 350, 357, 362, 371, 379, 383, 394, 398, 405, 418, 424, 432, 437, 441, 448, 453, 460, 466, 475, 481, 486, 499, 513, 521, 528, 534, 545, 550, 554, 558, 570, 574, 581, 588, 594, 602, 611, 616, 622, 630, 634, 640], "CWN": [10, 6, 6, 12, 7, 3, 4, 4, 14, 9, 6, 9, 7, 4, 13, 7, 7, 1, 6, 6, 5, 9, 6, 2, 3, 6, 4, 6, 8, 8, 5, 11, 7, 5, 3, 1, 1, 1, 9, 5, 6, 4, 10, 6, 6, 6, 5, 5, 6, 6, 5, 6, 4, 13, 4, 6, 6, 7, 5, 9, 8, 4, 11, 4, 7, 13, 6, 8, 5, 4, 7, 5, 7, 6, 9, 6, 5, 13, 14, 8, 7, 6, 11, 5, 4, 4, 12, 4, 7, 7, 6, 8, 9, 5, 6, 8, 4, 6, 5], "Words": ["What", "resonates", "inside", "you", "when", "you", "hear", "the", "word", "'soul'?...", "What", "does", "it", "mean", "to", "you?", "Listen", "to", "the", "sounds", "around", "you.", "As", "you", "get", "comfortable", "in", "your", "seat,", "take", "a", "moment", "to", "listen...", "What", "is", "the", "sound", "of", "your", "soul?", "Hi...", "I'm", "Alma.", "Here,", "your", "body", "speaks...", "and", "this", "place", "listens.", "Before", "we", "begin,", "take", "this", "sensor", "with", "the", "hand", "that", "feels", "most", "natural", "to", "you.", "It", "will", "be", "your", "connection", "with", "this", "place.", "Just", "reach", "out", "and", "take", "it.", "Now,", "choose", "the", "soul", "that", "best", "represents", "you", "today.", "Point", "at", "the", "one", "that", "calls", "you...", "and", "pull", "the", "trigger.", "This", "is", "your", "soul.", "It", "will", "grow", "with", "you", "through", "five", "different", "stages.", "Entering...", "you", "will", "breathe", "with", "the", "place.", "Recognizing...", "you", "will", "listen", "to", "your", "heart.", "Loving...", "you", "will", "let", "your", "mind", "rest.", "Attracting...", "create", "your", "soul's", "unique", "melody.", "Surrounding...", "express", "yourself", "through", "movement.", "Each", "stage", "will", "charge", "one", "part", "of", "your", "soul.", "There", "you", "are.", "Everything", "is", "ready.", "Follow", "me.", "This", "is", "Entering.", "Imagine", "your", "breath", "like", "gentle", "waves...", "moving", "naturally", "within", "you.", "Rest", "the", "sensor", "on", "your", "belly.", "Feel", "how", "it", "rises", "and", "falls", "with", "you.", "Just", "below", "your", "ribs...", "flat", "side", "toward", "you.", "Take", "a", "moment", "to", "explore...", "breathe", "as", "you", "like,", "and", "notice", "how", "everything", "moves", "with", "you.", "Now,", "let's", "do", "a", "simple", "breathing", "exercise.", "Follow", "me", "with", "your", "breath.", "Three...", "two...", "one...", "inhale.", "Hold.", "Exhale.", "Beautifully", "done...", "you", "and", "this", "place", "breathed", "as", "one.", "Now,", "let's", "charge", "your", "soul.", "Now...", "let's", "listen", "a", "little", "deeper.", "Let's", "continue", "to", "Recognizing.", "This", "is", "Recognizing.", "Let's", "bring", "the", "focus", "to", "the", "heart.", "Place", "the", "sensor", "on", "your", "chest...", "and", "stay", "still", "for", "a", "moment.", "A", "little", "higher...", "and", "very", "still.", "Can", "you", "hear", "your", "heartbeat?...", "Can", "you", "feel", "its", "rhythm?", "Does", "gratitude", "flow", "through", "your", "heartbeat?", "Well", "done...", "your", "heart", "has", "spoken.", "Now,", "let's", "charge", "your", "soul.", "Now,", "let", "your", "thoughts", "become", "quiet.", "Let's", "continue", "to", "Loving.", "This", "is", "Loving.", "What", "you", "are", "seeing", "around", "you", "is", "a", "visual", "representation", "of", "your", "brain", "activity.", "Observe", "your", "thoughts", "like", "distant", "constellations...", "each", "one", "quietly", "forming,", "then", "fading.", "Which", "thought", "carries", "a", "quiet", "wisdom", "today?", "Let's", "gather", "all", "these", "thoughts...", "and", "use", "this", "inner", "motion", "to", "charge", "your", "soul.", "Now...", "let's", "activate", "your", "body", "a", "little", "bit.", "Let's", "continue", "to", "Attracting.", "This", "is", "Attracting.", "Every", "sound", "around", "you", "is", "waiting", "for", "you.", "Reach", "into", "the", "space...", "every", "motion", "forms", "new", "connections,", "sounds,", "rhythms.", "Point", "at", "a", "sphere", "and", "pull", "the", "trigger", "to", "bring", "it", "to", "you...", "then", "place", "it", "on", "the", "shape.", "Point", "at", "a", "sphere", "and", "pull", "the", "trigger.", "Can", "you", "feel", "your", "magnetism?...", "What", "are", "you", "attracting?", "When", "it", "sounds", "like", "you,", "hold", "SAVE.", "Listen...", "this", "is", "your", "melody.", "Let's", "charge", "this", "melody", "into", "your", "soul.", "One", "last", "stage.", "Now...", "you", "create.", "This", "is", "Surrounding,", "the", "final", "stage", "of", "your", "journey.", "Use", "this", "space", "as", "a", "canvas...", "to", "create", "your", "own", "world.", "A", "painting", "of", "love,", "a", "dance", "of", "life,", "an", "image", "of", "the", "soul.", "Bring", "your", "brush", "close", "to", "a", "color", "on", "your", "other", "hand", "to", "choose", "it...", "then", "hold", "the", "trigger", "and", "move", "to", "draw.", "Press", "the", "trigger", "and", "move", "your", "hand.", "Can", "your", "emotions", "become", "visible", "textures?", "Take", "your", "time...", "and", "when", "you", "feel", "it's", "complete,", "hold", "SAVE.", "Your", "soul", "is", "fully", "charged.", "As", "you", "gently", "return...", "notice", "what", "has", "changed.", "Welcome", "back.", "This", "is", "what", "I", "could", "perceive", "of", "you:", "your", "breath...", "your", "heartbeat...", "your", "calm...", "your", "melody...", "and", "what", "you", "carry", "inside.", "Would", "you", "like", "to", "share", "your", "journey?", "Your", "soul", "would", "join", "the", "constellation.", "Point", "at", "your", "answer...", "and", "pull", "the", "trigger.", "Every", "soul", "that", "passed", "through", "here", "left", "a", "light.", "Now,", "yours", "is", "among", "them.", "Your", "soul", "will", "lead", "the", "way.", "If", "your", "soul", "left", "you", "a", "gift", "today...", "what", "would", "it", "be?", "Hold", "it", "softly", "throughout", "your", "day.", "Thank", "you", "for", "showing", "up."], "WS": [0.17, 0.424, 1.242, 1.683, 1.937, 2.191, 2.445, 2.699, 2.952, 3.206, 3.99, 4.193, 4.397, 4.6, 4.803, 5.007, 0.0, 0.461, 0.725, 0.99, 1.255, 1.715, 0.01, 0.24, 0.47, 0.7, 1.44, 1.67, 1.9, 2.32, 2.568, 2.817, 3.249, 3.498, 4.71, 4.997, 5.284, 5.571, 5.859, 6.146, 6.433, 0.1, 1.11, 1.395, 2.53, 3.47, 3.818, 4.422, 5.29, 5.676, 6.062, 6.448, 0.05, 0.567, 0.863, 1.57, 1.874, 2.179, 2.709, 3.013, 3.318, 3.622, 3.927, 4.231, 4.536, 5.291, 5.596, 6.38, 6.641, 6.901, 7.162, 7.422, 8.068, 8.329, 8.589, 0.01, 0.242, 0.473, 0.705, 0.937, 1.168, 0.17, 0.97, 1.288, 1.606, 1.924, 2.242, 2.56, 3.349, 3.667, 4.65, 4.933, 5.216, 5.499, 5.781, 6.064, 6.347, 6.94, 7.21, 7.48, 7.75, 0.07, 0.402, 0.734, 1.065, 1.397, 1.729, 2.061, 2.392, 2.724, 3.056, 3.388, 3.719, 4.543, 0.0, 0.679, 0.952, 1.226, 1.499, 1.773, 2.046, 0.0, 1.46, 1.687, 1.914, 2.309, 2.536, 2.763, 0.0, 1.08, 1.382, 1.683, 1.985, 2.287, 2.588, 0.0, 0.765, 1.073, 1.381, 1.689, 2.225, 0.0, 0.909, 1.547, 2.185, 2.551, 0.05, 0.357, 0.663, 0.97, 1.277, 1.583, 1.89, 2.197, 2.503, 0.01, 0.25, 0.49, 0.97, 1.532, 1.706, 2.2, 2.6, 0.07, 0.353, 0.637, 2.15, 3.017, 3.366, 3.715, 4.064, 4.672, 6.04, 6.544, 7.477, 7.981, 0.03, 0.317, 0.605, 1.105, 1.392, 1.68, 2.55, 2.889, 3.227, 3.566, 4.155, 4.494, 4.833, 5.171, 0.01, 0.351, 0.944, 1.284, 1.625, 1.966, 2.306, 2.899, 0.05, 0.34, 0.63, 1.135, 1.425, 2.62, 2.985, 3.35, 3.715, 4.43, 4.692, 5.147, 5.409, 6.251, 6.707, 6.968, 0.03, 0.316, 0.602, 0.888, 1.174, 1.671, 2.169, 2.879, 3.676, 3.962, 4.248, 4.534, 0.0, 0.613, 1.226, 1.839, 0.0, 0.0, 0.05, 1.129, 1.464, 1.799, 2.133, 2.468, 2.803, 3.386, 3.721, 4.056, 4.601, 4.935, 5.27, 5.605, 0.17, 1.1, 1.333, 1.738, 1.97, 2.375, 3.43, 3.743, 4.288, 4.601, 0.07, 0.327, 0.584, 1.412, 1.668, 1.925, 2.182, 2.629, 2.886, 3.143, 0.03, 0.287, 0.543, 0.99, 1.247, 1.503, 2.02, 2.244, 2.468, 2.692, 2.916, 3.14, 0.03, 0.262, 0.666, 1.26, 1.549, 2.051, 0.03, 0.33, 0.629, 0.929, 1.228, 2.38, 2.694, 3.008, 3.322, 3.636, 0.06, 0.356, 1.089, 1.384, 1.68, 1.976, 0.2, 0.561, 0.922, 1.283, 1.645, 2.006, 2.634, 3.205, 3.827, 4.188, 4.549, 0.16, 0.498, 0.836, 1.174, 1.512, 2.1, 2.438, 3.146, 3.734, 4.072, 0.0, 0.425, 0.85, 2.08, 2.34, 2.601, 2.861, 3.121, 3.574, 3.835, 4.095, 4.355, 4.809, 5.84, 6.101, 6.361, 6.621, 0.0, 0.558, 0.878, 1.199, 1.519, 2.077, 3.71, 4.071, 4.432, 5.061, 5.89, 6.24, 0.07, 0.316, 0.562, 0.991, 1.237, 1.483, 1.912, 0.03, 0.335, 0.865, 1.17, 1.475, 2.12, 2.415, 2.71, 3.004, 3.518, 4.031, 4.326, 4.62, 4.915, 0.05, 0.96, 1.157, 1.645, 1.842, 2.184, 2.381, 2.723, 3.33, 3.611, 4.101, 4.382, 0.16, 0.413, 0.665, 1.292, 1.918, 2.171, 2.61, 2.863, 3.115, 3.555, 3.807, 0.07, 0.447, 1.103, 1.48, 1.856, 2.792, 3.448, 3.824, 4.201, 5.136, 5.513, 0.01, 0.259, 0.508, 0.758, 1.007, 1.256, 1.505, 1.755, 2.188, 2.438, 2.687, 2.936, 3.185, 3.435, 3.684, 3.933, 4.182, 4.432, 4.681, 0.04, 0.269, 0.498, 0.726, 0.955, 1.184, 1.413, 1.642, 0.03, 0.335, 0.641, 0.946, 1.252, 2.82, 3.048, 3.276, 3.504, 0.05, 0.39, 0.73, 1.07, 1.41, 1.75, 2.09, 0.01, 0.449, 0.701, 0.953, 1.205, 0.06, 0.305, 0.55, 0.795, 1.403, 1.83, 2.075, 0.0, 0.36, 0.72, 1.27, 1.97, 2.365, 0.03, 0.387, 0.745, 1.631, 1.989, 2.611, 2.968, 3.325, 3.683, 5.325, 5.682, 6.039, 6.397, 6.754, 7.111, 8.213, 8.571, 8.928, 9.285, 9.643, 0.02, 0.292, 0.766, 1.038, 1.59, 1.905, 2.22, 2.535, 3.18, 3.433, 3.872, 4.125, 4.377, 0.07, 0.314, 0.558, 0.802, 1.047, 1.291, 1.535, 1.96, 2.204, 2.448, 2.873, 3.118, 3.362, 3.606, 4.17, 4.451, 4.733, 5.014, 5.504, 5.786, 6.067, 6.349, 0.05, 0.324, 0.598, 1.074, 1.348, 1.622, 1.896, 0.05, 0.263, 0.476, 1.004, 1.374, 1.902, 0.03, 0.337, 0.643, 1.23, 1.447, 1.663, 1.88, 2.096, 2.313, 2.93, 3.515, 0.06, 0.319, 0.578, 0.838, 1.289, 0.0, 0.351, 0.702, 1.314, 1.925, 2.536, 2.887, 3.239, 0.02, 0.533, 0.827, 1.462, 1.756, 2.051, 2.345, 2.64, 3.152, 3.447, 3.741, 4.036, 4.68, 4.975, 5.487, 6.142, 6.436, 6.731, 7.781, 8.476, 8.77, 9.065, 9.577, 0.09, 0.326, 0.563, 0.799, 1.036, 1.272, 1.508, 2.31, 2.632, 2.955, 3.277, 3.599, 3.921, 0.01, 0.265, 0.52, 0.776, 1.22, 1.475, 1.73, 1.986, 0.01, 0.85, 1.188, 1.526, 2.116, 2.454, 2.792, 3.131, 3.829, 4.167, 4.506, 4.844, 5.183, 5.772, 0.03, 0.35, 0.67, 0.99, 1.31, 1.63, 0.19, 0.457, 0.723, 0.99, 1.256, 1.523, 1.789, 2.056, 2.96, 3.188, 3.415, 3.643, 4.63, 4.92, 5.21, 5.715, 6.22, 6.51, 7.36, 7.614, 7.869, 8.123, 8.566]}
WCODE = {
 (WW, 'Setup', (('Word', 'string'),)): '(fn Setup (Word)\n  (Widget|SetText(Text) (Variables|WBP_SubWord_SC|GetT) (Utilities|Text|ToText(String) Word)))\n',
 (WL, 'Clear', ()): '(fn Clear ()\n  (Widget|Panel|ClearChildren (Variables|WBP_SubLine_SC|GetBox)))\n',
 (WL, 'AddWord', (('Word', 'string'),)): '(fn AddWord (Word)\n  (bind _w (UserInterface|CreateWidget :Class "/Game/SoulCharger/Mechanics/Subtitles/WBP_SubWord_SC.WBP_SubWord_SC_C" :OwningPlayer (Game|GetPlayerController 0)))\n  (Class|WBPSubWordSC|Setup :self _w :Word Word)\n  (Panel|AddChildtoWrapBox (Variables|WBP_SubLine_SC|GetBox) _w))\n',
 (WL, 'WordK', (('I', 'int'), ('K', 'float'), ('Dim', 'float'), ('Rise', 'float'))): '(fn WordK (I K Dim Rise)\n  (bind _c (Widget|Panel|GetChildAt (Variables|WBP_SubLine_SC|GetBox) I))\n  (Widget|SetRenderOpacity _c (+ Dim (* (- 1.0 Dim) K)))\n  (Widget|Transform|SetRenderTranslation _c (Math|Vector2D|MakeVector2D 0.0 (* (- 1.0 K) Rise))))\n',
 (WL, 'LineAlpha', (('A', 'float'),)): '(fn LineAlpha (A)\n  (Widget|SetRenderOpacity (Variables|WBP_SubLine_SC|GetBox) A))\n',
}
KNOBS = [('On', 'bool', True), ('Offset', 'Vector', {'x': 0.0, 'y': 10.0, 'z': 12.0}), ('Dim', 'float', 0.32), ('Rise', 'float', 9.0), ('WordFade', 'float', 0.16), ('LineFade', 'float', 0.22)]
ARR = [('VoIds', 'string'), ('VoC0', 'int'), ('VoCN', 'int'), ('CS', 'float'), ('CE', 'float'), ('CW0', 'int'), ('CWN', 'int'), ('Words', 'string'), ('WS', 'float')]
STATE = [('Cur', 'int', -1), ('Card', 'int', -1), ('T', 'float', 0.0), ('Was', 'bool', False), ('LastName', 'string', ''), ('Attached', 'bool', False), ('Alpha', 'float', 0.0)]
LOG = []
def T(name, payload):
    try:
        return True, execute_tool(name, json.dumps(payload))['returnValue']
    except BaseException as e:
        LOG.append(name.split('.')[-1] + ' :: ' + str(e)[:240])
        return False, None
def rp(x):
    return x['refPath'] if isinstance(x, dict) and 'refPath' in x else str(x)
def has_graph(bp, name):
    ok, gs = T(BT + 'list_graphs', {'blueprint': {'refPath': bp}})
    return (':' + name + "'") in str(gs) or (':' + name + '"') in str(gs)
def ft(g, f, n=8):
    ok, t = T(BT + 'find_node_types', {'graph': {'refPath': g}, 'type_id_filter': f, 'context_pins': []})
    return [x for x in (t or [])][:n]
def run():
    out = {}
    try:
        ok, pie = T('EditorToolset.EditorAppToolset.IsPIERunning', {})
        if pie:
            return {'err': 'PIE'}
        # ---- 1. funciones de los widgets (grafos nuevos)
        if has_graph(WL, 'ShowCard'):
            T(BT + 'remove_function_graph', {'blueprint': {'refPath': WL}, 'graph_name': 'ShowCard'})
        for (bp, fn, params), code in WCODE.items():
            if not has_graph(bp, fn):
                T(BT + 'add_function_graph', {'blueprint': {'refPath': bp}, 'graph_name': fn})
                for pn, pt in params:
                    T(BT + 'add_function_param', {'graph': {'refPath': bp + ':' + fn}, 'param_name': pn, 'param_type': pt, 'input_param': True})
        for bp in (WW, WL):
            T(UM + 'CompileWidgetBlueprint', {'widgetBlueprint': {'refPath': bp}})
        wr = {}
        for (bp, fn, params), code in WCODE.items():
            if bp == WL:
                T(UM + 'CompileWidgetBlueprint', {'widgetBlueprint': {'refPath': WW}})
            n0 = len(LOG)
            ok, w = T(BT + 'write_graph_dsl', {'graph': {'refPath': bp + ':' + fn}, 'code': code})
            wr[fn] = [ok, [e[:200] for e in LOG[n0:n0 + 1]]]
        out['widget_writes'] = wr
        for bp in (WW, WL):
            n0 = len(LOG)
            ok, cc = T(UM + 'CompileWidgetBlueprint', {'widgetBlueprint': {'refPath': bp}})
            out['wc_' + bp.split('.')[-1]] = [str(cc)[:160], LOG[n0:n0 + 1]]
        out['save_w'] = T(AS + 'save_assets', {'asset_paths': [F + 'WBP_SubWord_SC', F + 'WBP_SubLine_SC']})[0]
        # ---- 2. el actor
        ok, ex = T(AS + 'exists', {'path': F + 'BP_Subtitles_SC'})
        if not ex:
            out['create_bp'] = T(BT + 'create', {'folder_path': F, 'asset_name': 'BP_Subtitles_SC', 'asset_type': {'refPath': '/Script/Engine.Actor'}})[0]
        ok, cdo = T(BT + 'get_default_object', {'blueprint': {'refPath': BP}})
        ok, comps = T(AT + 'get_components', {'actor': cdo})
        if 'Sub' not in str(comps):
            ok, c = T(AT + 'add_component', {'owner': cdo, 'component_type': {'refPath': '/Script/UMG.WidgetComponent'}, 'name': 'Sub'})
            out['add_sub'] = [ok, rp(c) if ok else None]
        ok, comps = T(AT + 'get_components', {'actor': cdo})
        sub = None
        for c in (comps or []):
            if rp(c).endswith('Sub') or 'Sub_GEN' in rp(c) or rp(c).split('.')[-1].startswith('Sub'):
                sub = rp(c)
        out['sub'] = sub
        if sub:
            ok, pl = T(OT + 'list_properties', {'instance': {'refPath': sub}})
            pls = str(pl)
            want = ['widgetClass', 'drawSize', 'space', 'tickMode', 'pivot', 'relativeRotation', 'relativeScale3D', 'overrideMaterials', 'translucencySortPriority', 'blendMode', 'bIsTwoSided', 'castShadow', 'bManuallyRedraw', 'timingPolicy', 'geometryMode', 'bDrawAtDesiredSize']
            out['sub_has'] = [k for k in want if ('"' + k + '"') in pls or ("'" + k + "'") in pls]
            vals = {'widgetClass': {'refPath': F + 'WBP_SubLine_SC.WBP_SubLine_SC_C'}, 'drawSize': {'x': 900, 'y': 160}, 'space': 'World', 'tickMode': 'Automatic', 'pivot': {'x': 0.5, 'y': 0.5}, 'relativeRotation': {'pitch': 0.0, 'yaw': 180.0, 'roll': 0.0}, 'relativeScale3D': {'x': 0.04, 'y': 0.04, 'z': 0.04}, 'overrideMaterials': [{'refPath': '/Game/SoulCharger/Core/HUD/M_HudWidget_SC.M_HudWidget_SC'}], 'translucencySortPriority': 32720, 'blendMode': 'Transparent', 'castShadow': False}
            res = {}
            for k, v in vals.items():
                res[k] = T(OT + 'set_properties', {'instance': {'refPath': sub}, 'values': json.dumps({k: v})})[0]
            out['sub_set'] = res
        # ---- 3. variables
        ok, vs = T(BT + 'list_variables', {'blueprint': {'refPath': BP}})
        vss = str(vs)
        for n, t, d in KNOBS:
            if ("'" + n + "'") not in vss and ('"' + n + '"') not in vss:
                T(BT + 'add_variable', {'blueprint': {'refPath': BP}, 'name': ('b' + n) if t == 'bool' else n, 'type_name': t})
        for n, t in ARR:
            if ("'" + n + "'") not in vss:
                T(BT + 'add_variable', {'blueprint': {'refPath': BP}, 'name': n, 'type_name': t, 'container_type': 'Array'})
        for n, t, d in STATE:
            if ("'" + n + "'") not in vss and ("'b" + n + "'") not in vss:
                T(BT + 'add_variable', {'blueprint': {'refPath': BP}, 'name': ('b' + n) if t == 'bool' else n, 'type_name': t})
        if 'LineW' not in vss:
            T(BT + 'add_object_variable', {'blueprint': {'refPath': BP}, 'name': 'LineW', 'object_class': {'refPath': F + 'WBP_SubLine_SC.WBP_SubLine_SC_C'}})
        T(BT + 'compile_blueprint', {'blueprint': {'refPath': BP}})
        for n, t, d in KNOBS:
            vn = ('b' + n) if t == 'bool' else n
            T(BT + 'set_variable_instance_editable', {'blueprint': {'refPath': BP}, 'variable_name': vn, 'instance_editable': True})
            T(BT + 'set_variable_category', {'blueprint': {'refPath': BP}, 'variable_name': vn, 'category': 'Subtitulos'})
        for n, t in ARR:
            T(BT + 'set_variable_category', {'blueprint': {'refPath': BP}, 'variable_name': n, 'category': 'Datos'})
        T(BT + 'compile_blueprint', {'blueprint': {'refPath': BP}})
        ok, cdo = T(BT + 'get_default_object', {'blueprint': {'refPath': BP}})
        cv = {}
        for n, t, d in KNOBS:
            cv[('b' + n) if t == 'bool' else n] = d
        for n, t, d in STATE:
            cv[('b' + n) if t == 'bool' else n] = d
        out['cdo_knobs'] = T(OT + 'set_properties', {'instance': cdo, 'values': json.dumps(cv)})[0]
        dr = {}
        for n, t in ARR:
            dr[n] = T(OT + 'set_properties', {'instance': cdo, 'values': json.dumps({n: DATA[n]})})[0]
        out['cdo_data'] = dr
        ok, chk = T(OT + 'get_properties', {'instance': cdo, 'properties': ['VoIds', 'bOn', 'Offset', 'Dim', 'Cur']})
        out['cdo_check'] = str(chk)[:300]
        # ---- 4. funciones vacias del actor + ids
        for fn, params in [('SubTick', [('Dt', 'float')]), ('SubAttach', []), ('SubRef', []), ('SubStart', [('Name', 'string')]), ('SubCard', [('C', 'int')]), ('SubCards', []), ('SubDraw', [('Dt', 'float'), ('Playing', 'bool')])]:
            if not has_graph(BP, fn):
                T(BT + 'add_function_graph', {'blueprint': {'refPath': BP}, 'graph_name': fn})
                for pn, pt in params:
                    T(BT + 'add_function_param', {'graph': {'refPath': BP + ':' + fn}, 'param_name': pn, 'param_type': pt, 'input_param': True})
        T(BT + 'compile_blueprint', {'blueprint': {'refPath': BP}})
        g = BP + ':SubTick'
        ids = {}
        for f in ['IsPlaying', 'GetSound', 'GetVOComp', 'FindItem', 'GetUserWidgetObject', 'CastToWBP_SubLine_SC', 'AttachActorToActor', 'SetActorRelativeLocation', 'Clamp(Float)', 'GetObjectName', 'EqualExactly(String)', 'WBPSubLineSC|', 'GetSub', 'Variables|Subtitulos|Get', 'Variables|Datos|Get', 'SetVisibility']:
            ids[f] = ft(g, f, 14)
        out['ids'] = ids
        n0 = len(LOG)
        ok, cc = T(BT + 'compile_blueprint', {'blueprint': {'refPath': BP}})
        out['compile_bp'] = [ok, LOG[n0:n0 + 1]]
        out['save_bp'] = T(AS + 'save_assets', {'asset_paths': [F + 'BP_Subtitles_SC']})[0]
    except BaseException as e:
        LOG.append('run ' + str(e)[:200])
    out['log'] = [l[:240] for l in LOG[:10]]
    T(AS + 'write_file', {'file_path': DUMP, 'content': json.dumps(out)})
    return {'keys': list(out.keys()), 'nlog': len(LOG)}
