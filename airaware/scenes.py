"""Original flat-style SVG scene illustrations for AirAware AI.

Pure markup assets (brand palette, accessibility-labelled). Split out
of ui.py so the design-system helpers stay readable; ``ui.scene``
re-exports :func:`scene` for existing call sites.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Illustration library - original flat-style SVG scenes in the brand palette
# ---------------------------------------------------------------------------

_SCENES: dict[str, str] = {}


def _scene(name: str, inner: str, w: int = 480, h: int = 320) -> str:
    _SCENES[name] = inner
    return inner


def scene(name: str) -> str:
    """Return a full <svg class="scene"> illustration by name."""
    inner = _SCENES.get(name, _SCENES.get("city", ""))
    return inner


# Shared defs injected per-scene (ids are unique per scene via prefix).
def _defs(p: str) -> str:
    return (
        f'<defs>'
        f'<linearGradient id="{p}sky" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#e6f0e4"/>'
        f'<stop offset="1" stop-color="#f6f5ec"/></linearGradient>'
        f'<linearGradient id="{p}hill1" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#b9cfae"/><stop offset="1" stop-color="#8fae85"/>'
        f'</linearGradient>'
        f'<linearGradient id="{p}hill2" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#7fa27c"/><stop offset="1" stop-color="#5c8262"/>'
        f'</linearGradient>'
        f'</defs>')


_scene("city", f'''
<svg class="scene" viewBox="0 0 480 320" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Illustration of a green city skyline with trees and birds">
{_defs("c")}
<rect width="480" height="320" fill="url(#csky)"/>
<circle cx="392" cy="62" r="30" fill="#f0d9a0"/>
<circle cx="392" cy="62" r="44" fill="#f0d9a0" opacity=".3"/>
<g fill="#ffffff" opacity=".9">
<ellipse cx="96" cy="58" rx="42" ry="14"/><ellipse cx="128" cy="48" rx="30" ry="12"/>
<ellipse cx="300" cy="110" rx="36" ry="11"/><ellipse cx="326" cy="103" rx="24" ry="9"/>
</g>
<g stroke="#ffffff" stroke-width="3" stroke-linecap="round" opacity=".8" fill="none">
<path d="M70 130 q7 -9 0 -18 q-7 -9 0 -18"/><path d="M108 108 q6 -8 0 -16 q-6 -8 0 -16"/>
</g>
<path d="M0 205 Q120 165 240 195 T480 188 V320 H0 Z" fill="url(#chill1)"/>
<path d="M0 255 Q140 220 260 248 T480 240 V320 H0 Z" fill="url(#chill2)"/>
<g>
<rect x="52" y="212" width="9" height="46" rx="3" fill="#173E32"/>
<circle cx="56" cy="200" r="26" fill="#173E32"/>
<circle cx="40" cy="212" r="15" fill="#245B46"/>
<circle cx="72" cy="212" r="15" fill="#245B46"/>
<rect x="410" y="222" width="8" height="36" rx="3" fill="#173E32"/>
<circle cx="414" cy="212" r="20" fill="#173E32"/>
<circle cx="402" cy="221" r="11" fill="#245B46"/>
<circle cx="426" cy="221" r="11" fill="#245B46"/>
</g>
<g>
<rect x="180" y="196" width="34" height="58" rx="4" fill="#F8F7F0" stroke="#d8dccb"/>
<rect x="186" y="204" width="9" height="9" rx="1" fill="#A8BCA3"/>
<rect x="199" y="204" width="9" height="9" rx="1" fill="#cfe0cd"/>
<rect x="186" y="218" width="9" height="9" rx="1" fill="#cfe0cd"/>
<rect x="199" y="218" width="9" height="9" rx="1" fill="#A8BCA3"/>
<rect x="186" y="232" width="22" height="6" rx="2" fill="#245B46"/>
</g>
<path d="M0 320 V300 Q240 282 480 300 V320 Z" fill="#173E32" opacity=".16"/>
</svg>''')

_scene("home", f'''
<svg class="scene" viewBox="0 0 480 320" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Illustration of a cozy home with plants and clean indoor air">
{_defs("h")}
<rect width="480" height="320" fill="url(#hsky)"/>
<circle cx="80" cy="60" r="26" fill="#f0d9a0" opacity=".9"/>
<path d="M0 240 Q120 210 240 232 T480 226 V320 H0 Z" fill="url(#hhill1)"/>
<path d="M0 275 Q140 250 260 268 T480 262 V320 H0 Z" fill="url(#hhill2)"/>
<g>
<path d="M170 200 L250 140 L330 200 Z" fill="#245B46"/>
<rect x="185" y="200" width="130" height="80" rx="6" fill="#F8F7F0" stroke="#d8dccb"/>
<rect x="228" y="232" width="34" height="48" rx="4" fill="#245B46"/>
<circle cx="254" cy="256" r="3" fill="#F8F7F0"/>
<rect x="200" y="218" width="26" height="24" rx="3" fill="#cfe0cd" stroke="#d8dccb"/>
<rect x="284" y="218" width="26" height="24" rx="3" fill="#cfe0cd" stroke="#d8dccb"/>
<rect x="246" y="146" width="12" height="26" fill="#173E32"/>
<path d="M206 148 h88 v-12 a44 14 0 0 0 -88 0 Z" fill="#173E32"/>
</g>
<g>
<rect x="330" y="212" width="34" height="44" rx="6" fill="#E8F0E6" stroke="#A8BCA3"/>
<path d="M347 218 v-10 M338 222 l-6 -8 M356 222 l6 -8" stroke="#245B46" stroke-width="3" stroke-linecap="round" fill="none"/>
<path d="M342 240 c0-10 4-16 10-16 s10 6 10 16" stroke="#245B46" stroke-width="3" fill="none" stroke-linecap="round"/>
</g>
<g fill="#ffffff" opacity=".85">
<circle cx="120" cy="120" r="4"/><circle cx="150" cy="96" r="3"/><circle cx="420" cy="90" r="3.5"/>
</g>
</svg>''')

_scene("wellness", f'''
<svg class="scene" viewBox="0 0 480 320" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Illustration of a person breathing fresh air during a morning walk">
{_defs("w")}
<rect width="480" height="320" fill="url(#wsky)"/>
<circle cx="88" cy="70" r="34" fill="#f0d9a0"/>
<circle cx="88" cy="70" r="50" fill="#f0d9a0" opacity=".28"/>
<path d="M0 235 Q130 195 250 222 T480 214 V320 H0 Z" fill="url(#whill1)"/>
<path d="M0 268 Q150 240 270 258 T480 252 V320 H0 Z" fill="url(#whill2)"/>
<g stroke="#ffffff" stroke-width="3.5" stroke-linecap="round" opacity=".85" fill="none">
<path d="M330 90 q8 -10 0 -20 q-8 -10 0 -20"/><path d="M365 120 q7 -9 0 -18 q-7 -9 0 -18"/>
<path d="M300 140 q6 -8 0 -16 q-6 -8 0 -16"/>
</g>
<g>
<circle cx="240" cy="128" r="20" fill="#E8B98F"/>
<path d="M214 122 a26 26 0 0 1 52 0 l-4 10 h-44 Z" fill="#3d2f26"/>
<path d="M206 205 q34 -26 68 0 l6 60 h-80 Z" fill="#245B46"/>
<path d="M226 205 v-14 M254 205 v-14" stroke="#E8B98F" stroke-width="9" stroke-linecap="round"/>
<path d="M212 250 l-16 34 M268 250 l16 34" stroke="#26352E" stroke-width="10" stroke-linecap="round"/>
<path d="M196 286 l-8 14 M284 286 l8 14" stroke="#26352E" stroke-width="8" stroke-linecap="round"/>
</g>
<g>
<rect x="52" y="252" width="8" height="44" rx="3" fill="#173E32"/>
<circle cx="56" cy="240" r="24" fill="#173E32"/>
<circle cx="38" cy="254" r="14" fill="#245B46"/>
<circle cx="74" cy="254" r="14" fill="#245B46"/>
</g>
</svg>''')

_scene("impact", f'''
<svg class="scene" viewBox="0 0 480 320" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Illustration of a growing plant beside a rising green chart">
{_defs("i")}
<rect width="480" height="320" fill="url(#isky)"/>
<circle cx="400" cy="66" r="28" fill="#f0d9a0" opacity=".9"/>
<path d="M0 250 Q120 215 250 240 T480 232 V320 H0 Z" fill="url(#ihill1)"/>
<path d="M0 285 Q150 258 280 276 T480 270 V320 H0 Z" fill="url(#ihill2)"/>
<g>
<rect x="70" y="150" width="120" height="14" rx="7" fill="#E8F0E6" stroke="#A8BCA3"/>
<rect x="70" y="178" width="86" height="14" rx="7" fill="#E8F0E6" stroke="#A8BCA3"/>
<rect x="70" y="206" width="52" height="14" rx="7" fill="#E8F0E6" stroke="#A8BCA3"/>
<path d="M84 148 L110 128 L136 112 L168 92 L196 74" stroke="#245B46" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="196" cy="74" r="9" fill="#A8BCA3"/>
<circle cx="168" cy="92" r="7" fill="#A8BCA3"/>
<circle cx="136" cy="112" r="6" fill="#A8BCA3"/>
</g>
<g>
<path d="M330 260 q-26 -34 -8 -66 q24 6 20 34 q18 -30 44 -22 q-8 40 -56 54z" fill="#245B46"/>
<path d="M340 258 q-4 -60 26 -86" stroke="#173E32" stroke-width="7" fill="none" stroke-linecap="round"/>
<circle cx="368" cy="166" r="14" fill="#A8BCA3"/>
<circle cx="352" cy="180" r="11" fill="#cfe0cd"/>
</g>
<g fill="#ffffff" opacity=".8">
<circle cx="180" cy="90" r="3.5"/><circle cx="220" cy="60" r="2.8"/><circle cx="120" cy="120" r="2.5"/>
</g>
</svg>''')

_scene("family", f'''
<svg class="scene" viewBox="0 0 480 320" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Illustration of a family walking together on a clean-air day">
{_defs("f")}
<rect width="480" height="320" fill="url(#fsky)"/>
<circle cx="400" cy="60" r="30" fill="#f0d9a0"/>
<circle cx="400" cy="60" r="46" fill="#f0d9a0" opacity=".25"/>
<g fill="#ffffff" opacity=".9">
<ellipse cx="90" cy="66" rx="40" ry="13"/><ellipse cx="122" cy="56" rx="28" ry="11"/>
<ellipse cx="260" cy="120" rx="34" ry="10"/>
</g>
<path d="M0 250 Q130 212 260 240 T480 232 V320 H0 Z" fill="url(#fhill1)"/>
<path d="M0 282 Q150 255 280 272 T480 266 V320 H0 Z" fill="url(#fhill2)"/>
<g>
<circle cx="190" cy="176" r="17" fill="#E8B98F"/>
<path d="M172 172 a18 18 0 0 1 36 0 l-3 9 h-30 Z" fill="#26352E"/>
<path d="M160 252 q30 -24 60 0 l5 46 h-70 Z" fill="#245B46"/>
<path d="M182 252 v-12 M208 252 v-12" stroke="#E8B98F" stroke-width="8" stroke-linecap="round"/>
<path d="M166 292 l-14 28 M224 292 l14 28" stroke="#26352E" stroke-width="9" stroke-linecap="round"/>
</g>
<g>
<circle cx="300" cy="196" r="13" fill="#E8B98F"/>
<path d="M287 193 a14 14 0 0 1 26 0 l-2 7 h-22 Z" fill="#6b4a2f"/>
<path d="M274 262 q26 -20 52 0 l4 36 h-60 Z" fill="#A8BCA3"/>
<path d="M292 262 v-10 M318 262 v-10" stroke="#E8B98F" stroke-width="7" stroke-linecap="round"/>
<path d="M276 294 l-12 22 M324 294 l12 22" stroke="#26352E" stroke-width="8" stroke-linecap="round"/>
</g>
<g>
<circle cx="110" cy="210" r="10" fill="#E8B98F"/>
<path d="M100 208 a11 11 0 0 1 20 0 l-2 6 h-16 Z" fill="#3d2f26"/>
<path d="M88 268 q22 -16 44 0 l3 28 h-50 Z" fill="#c9a24b"/>
<path d="M102 268 v-8 M118 268 v-8" stroke="#E8B98F" stroke-width="6" stroke-linecap="round"/>
<path d="M90 292 l-10 18 M130 292 l10 18" stroke="#26352E" stroke-width="7" stroke-linecap="round"/>
</g>
<g>
<rect x="60" y="240" width="7" height="40" rx="3" fill="#173E32"/>
<circle cx="63" cy="230" r="20" fill="#173E32"/>
<circle cx="48" cy="242" r="11" fill="#245B46"/>
<circle cx="78" cy="242" r="11" fill="#245B46"/>
</g>
</svg>''')

_scene("indoor", '''
<svg class="scene" viewBox="0 0 480 320" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Illustration of a clean, well-ventilated living room">
<rect width="480" height="320" fill="#E8F0E6"/>
<rect x="0" y="0" width="480" height="210" fill="#F8F7F0"/>
<rect x="0" y="210" width="480" height="110" fill="#D8CBB2"/>
<g>
<rect x="60" y="50" width="120" height="120" rx="8" fill="#cfe0cd" stroke="#b9cfae" stroke-width="6"/>
<line x1="120" y1="50" x2="120" y2="170" stroke="#b9cfae" stroke-width="4"/>
<line x1="60" y1="110" x2="180" y2="110" stroke="#b9cfae" stroke-width="4"/>
<path d="M80 160 q20 -30 40 -12 q10 -22 30 -8" stroke="#fff" stroke-width="5" fill="none" opacity=".8" stroke-linecap="round"/>
</g>
<g>
<rect x="330" y="60" width="90" height="110" rx="8" fill="#fdf6e0" stroke="#e0d3a8" stroke-width="5"/>
<rect x="338" y="68" width="74" height="70" rx="4" fill="#f0d9a0" opacity=".5"/>
<circle cx="375" cy="112" r="16" fill="#f0d9a0"/>
</g>
<g>
<rect x="230" y="150" width="150" height="46" rx="12" fill="#245B46"/>
<rect x="222" y="138" width="34" height="56" rx="10" fill="#173E32"/>
<rect x="364" y="138" width="34" height="56" rx="10" fill="#173E32"/>
<rect x="240" y="130" width="52" height="26" rx="8" fill="#A8BCA3"/>
<rect x="292" y="130" width="52" height="26" rx="8" fill="#cfe0cd"/>
</g>
<g>
<rect x="120" y="238" width="26" height="34" rx="6" fill="#c96f4a"/>
<path d="M118 238 q15 -34 30 0" fill="#245B46"/>
<path d="M126 226 q8 -14 22 -12" stroke="#245B46" stroke-width="4" fill="none" stroke-linecap="round"/>
</g>
<rect x="0" y="272" width="480" height="48" fill="#C4B49A"/>
<rect x="330" y="196" width="10" height="76" fill="#8a7a5c"/>
<circle cx="335" cy="190" r="18" fill="#A8BCA3"/>
<circle cx="320" cy="200" r="11" fill="#cfe0cd"/>
<circle cx="350" cy="200" r="11" fill="#cfe0cd"/>
</svg>''')

_scene("transport", f'''
<svg class="scene" viewBox="0 0 480 320" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Illustration comparing car, bus and bicycle travel">
{_defs("t")}
<rect width="480" height="320" fill="url(#tsky)"/>
<circle cx="80" cy="58" r="26" fill="#f0d9a0" opacity=".9"/>
<path d="M0 250 Q140 215 280 240 T480 232 V320 H0 Z" fill="url(#thill1)"/>
<path d="M0 282 Q150 258 280 272 T480 266 V320 H0 Z" fill="url(#thill2)"/>
<g>
<rect x="52" y="196" width="86" height="40" rx="10" fill="#b7c9bd" stroke="#8fae85"/>
<rect x="60" y="188" width="56" height="20" rx="8" fill="#dfeee2"/>
<circle cx="76" cy="240" r="12" fill="#26352E"/><circle cx="76" cy="240" r="5" fill="#F8F7F0"/>
<circle cx="114" cy="240" r="12" fill="#26352E"/><circle cx="114" cy="240" r="5" fill="#F8F7F0"/>
<path d="M140 202 h22" stroke="#8fae85" stroke-width="4" stroke-linecap="round"/>
</g>
<g>
<rect x="210" y="172" width="110" height="66" rx="12" fill="#245B46"/>
<rect x="220" y="182" width="24" height="22" rx="4" fill="#cfe0cd"/>
<rect x="252" y="182" width="24" height="22" rx="4" fill="#cfe0cd"/>
<rect x="284" y="182" width="24" height="22" rx="4" fill="#cfe0cd"/>
<circle cx="238" cy="246" r="13" fill="#26352E"/><circle cx="238" cy="246" r="5" fill="#F8F7F0"/>
<circle cx="292" cy="246" r="13" fill="#26352E"/><circle cx="292" cy="246" r="5" fill="#F8F7F0"/>
</g>
<g>
<circle cx="392" cy="252" r="17" stroke="#173E32" stroke-width="5" fill="none"/>
<circle cx="392" cy="252" r="5" fill="#173E32"/>
<path d="M392 252 L408 226 M408 226 h18 M408 226 l10 4" stroke="#173E32" stroke-width="5" fill="none" stroke-linecap="round"/>
<circle cx="430" cy="222" r="9" fill="#E8B98F"/>
<path d="M418 218 a11 11 0 0 1 22 0 l-2 8 h-18 Z" fill="#3d2f26"/>
<path d="M408 246 q-6 -22 12 -30" stroke="#245B46" stroke-width="6" fill="none" stroke-linecap="round"/>
</g>
<path d="M0 310 H480" stroke="#173E32" stroke-width="4" opacity=".25"/>
</svg>''')

_scene("lab", f'''
<svg class="scene" viewBox="0 0 480 320" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Illustration of air-quality measurement and CPCB methodology">
{_defs("l")}
<rect width="480" height="320" fill="url(#lsky)"/>
<path d="M0 250 Q140 215 280 240 T480 232 V320 H0 Z" fill="url(#lhill1)"/>
<path d="M0 285 Q150 260 280 275 T480 270 V320 H0 Z" fill="url(#lhill2)"/>
<g>
<path d="M190 110 h44 v60 l34 66 a10 10 0 0 1 -9 15 H165 a10 10 0 0 1 -9 -15 l34 -66 Z" fill="#F8F7F0" stroke="#A8BCA3" stroke-width="4"/>
<path d="M172 190 h70 l-14 -30 H186 Z" fill="#E8F0E6"/>
<path d="M180 178 h54 l-8 -18 h-38 Z" fill="#245B46" opacity=".85"/>
<circle cx="212" cy="160" r="6" fill="#A8BCA3"/><circle cx="224" cy="150" r="4" fill="#A8BCA3"/><circle cx="200" cy="146" r="4.5" fill="#A8BCA3"/>
<path d="M178 96 h68" stroke="#A8BCA3" stroke-width="5" stroke-linecap="round"/>
</g>
<g>
<rect x="300" y="150" width="90" height="14" rx="7" fill="#E8F0E6" stroke="#A8BCA3"/>
<rect x="300" y="176" width="64" height="14" rx="7" fill="#E8F0E6" stroke="#A8BCA3"/>
<rect x="300" y="202" width="40" height="14" rx="7" fill="#E8F0E6" stroke="#A8BCA3"/>
<path d="M310 148 L330 134 L350 122 L372 108 L392 96" stroke="#245B46" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="392" cy="96" r="8" fill="#A8BCA3"/>
</g>
<g fill="#ffffff" opacity=".8">
<circle cx="120" cy="100" r="4"/><circle cx="150" cy="76" r="3"/><circle cx="330" cy="60" r="3"/>
</g>
</svg>''')

_scene("checklist", f'''
<svg class="scene" viewBox="0 0 480 320" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Illustration of a household checklist and healthy habits">
{_defs("k")}
<rect width="480" height="320" fill="url(#ksky)"/>
<path d="M0 250 Q140 215 280 240 T480 232 V320 H0 Z" fill="url(#khill1)"/>
<path d="M0 285 Q150 260 280 275 T480 270 V320 H0 Z" fill="url(#khill2)"/>
<g>
<rect x="120" y="60" width="240" height="210" rx="16" fill="#F8F7F0" stroke="#d8dccb" stroke-width="3"/>
<rect x="142" y="88" width="110" height="14" rx="7" fill="#A8BCA3"/>
<g>
<rect x="142" y="118" width="22" height="22" rx="6" fill="#245B46"/>
<path d="M147 129 l4 4 8 -9" stroke="#fff" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
<rect x="176" y="122" width="150" height="10" rx="5" fill="#e4e8dd"/>
</g>
<g>
<rect x="142" y="156" width="22" height="22" rx="6" fill="#fff" stroke="#A8BCA3" stroke-width="3"/>
<path d="M147 167 l4 4 8 -9" stroke="#245B46" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
<rect x="176" y="160" width="120" height="10" rx="5" fill="#e4e8dd"/>
</g>
<g>
<rect x="142" y="194" width="22" height="22" rx="6" fill="#245B46"/>
<path d="M147 205 l4 4 8 -9" stroke="#fff" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
<rect x="176" y="198" width="170" height="10" rx="5" fill="#e4e8dd"/>
</g>
<g>
<rect x="142" y="232" width="22" height="22" rx="6" fill="#fff" stroke="#A8BCA3" stroke-width="3"/>
<path d="M147 243 l4 4 8 -9" stroke="#245B46" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
<rect x="176" y="236" width="95" height="10" rx="5" fill="#e4e8dd"/>
</g>
</g>
<g>
<circle cx="80" cy="240" r="26" fill="#173E32"/>
<path d="M66 236 q14 -22 28 0" fill="#245B46"/>
<path d="M74 226 q8 -16 20 -14" stroke="#245B46" stroke-width="4" fill="none" stroke-linecap="round"/>
<rect x="76" y="264" width="8" height="30" rx="3" fill="#173E32"/>
</g>
</svg>''')

_scene("plan", f'''
<svg class="scene" viewBox="0 0 480 320" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Illustration of a day planned around air quality">
{_defs("p")}
<rect width="480" height="320" fill="url(#psky)"/>
<circle cx="240" cy="150" r="60" fill="#f0d9a0" opacity=".9"/>
<circle cx="240" cy="150" r="86" fill="#f0d9a0" opacity=".22"/>
<path d="M0 262 Q140 228 280 252 T480 246 V320 H0 Z" fill="url(#phill1)"/>
<path d="M0 292 Q150 268 280 284 T480 278 V320 H0 Z" fill="url(#phill2)"/>
<g stroke="#ffffff" stroke-width="3" stroke-linecap="round" opacity=".85" fill="none">
<path d="M90 80 q8 -10 0 -20 q-8 -10 0 -20"/><path d="M130 110 q6 -8 0 -16 q-6 -8 0 -16"/>
</g>
<g>
<rect x="200" y="96" width="80" height="150" rx="14" fill="#F8F7F0" stroke="#d8dccb" stroke-width="3"/>
<rect x="212" y="112" width="56" height="8" rx="4" fill="#A8BCA3"/>
<rect x="212" y="132" width="40" height="8" rx="4" fill="#e4e8dd"/>
<rect x="212" y="152" width="48" height="8" rx="4" fill="#e4e8dd"/>
<rect x="212" y="172" width="34" height="8" rx="4" fill="#e4e8dd"/>
<circle cx="240" cy="220" r="20" fill="#245B46"/>
<path d="M228 220 l8 8 16 -16" stroke="#fff" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
</g>
<g>
<rect x="330" y="120" width="60" height="60" rx="12" fill="#E8F0E6" stroke="#A8BCA3"/>
<path d="M344 156 l10 -20 10 14 12 -18" stroke="#245B46" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
</g>
</svg>''')

_scene("companion", '''
<svg class="scene" viewBox="0 0 480 320" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Illustration of a friendly AI air companion">
<rect width="480" height="320" fill="#F8F7F0"/>
<path d="M0 250 Q140 215 280 240 T480 232 V320 H0 Z" fill="url(#chill1)" opacity=".5"/>
<defs><linearGradient id="chill1" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#cfe0cd"/><stop offset="1" stop-color="#a8bca3"/></linearGradient></defs>
<g>
<rect x="150" y="80" width="180" height="150" rx="26" fill="#173E32"/>
<rect x="168" y="102" width="144" height="96" rx="16" fill="#1f5040"/>
<circle cx="212" cy="150" r="13" fill="#A8BCA3"/>
<circle cx="212" cy="150" r="6" fill="#F8F7F0"/>
<circle cx="268" cy="150" r="13" fill="#A8BCA3"/>
<circle cx="268" cy="150" r="6" fill="#F8F7F0"/>
<path d="M216 186 q24 16 48 0" stroke="#A8BCA3" stroke-width="6" fill="none" stroke-linecap="round"/>
<rect x="228" y="232" width="24" height="20" rx="6" fill="#173E32"/>
<rect x="196" y="252" width="88" height="14" rx="7" fill="#A8BCA3"/>
</g>
<g fill="#A8BCA3">
<path d="M120 120 l4 10 10 4 -10 4 -4 10 -4 -10 -10 -4 10 -4 Z"/>
<path d="M372 96 l3 8 8 3 -8 3 -3 8 -3 -8 -8 -3 8 -3 Z"/>
<circle cx="390" cy="170" r="5"/>
</g>
</svg>''')


