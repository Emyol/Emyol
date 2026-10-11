"""Build original Silver Field vector artwork for the GitHub profile."""
from pathlib import Path
import math
import random
from html import escape
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets'
OUT.mkdir(exist_ok=True)
FONT = ROOT / 'tools/fonts/Geist[wght].ttf'
fonts = {}


def text(value, x, y, size=24, color='#f3f4f5', weight=400, tracking=0):
    if weight not in fonts:
        f = instantiateVariableFont(TTFont(FONT), {'wght': weight})
        fonts[weight] = (f, f.getGlyphSet(), f.getBestCmap())
    f, glyphs, cmap = fonts[weight]
    scale = size / f['head'].unitsPerEm
    result = []
    for char in value:
        name = cmap.get(ord(char), '.notdef')
        pen = SVGPathPen(glyphs)
        glyphs[name].draw(pen)
        result.append(f'<path d="{pen.getCommands()}" transform="translate({x:.3f} {y}) scale({scale:.6f} {-scale:.6f})"/>')
        x += glyphs[name].width * scale + tracking
    return f'<g fill="{color}" aria-label="{escape(value)}">' + ''.join(result) + '</g>'


def rect(x, y, w, h, fill, r=0, stroke='none'):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}"/>'


def path(d, stroke='#727881', width=1, fill='none', extra=''):
    return f'<path d="{d}" stroke="{stroke}" stroke-width="{width}" fill="{fill}" {extra}/>'


def circle(x, y, r, fill, stroke='none'):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}"/>'


DEFS = '''<defs>
<linearGradient id="shell" x2="1" y2="1"><stop stop-color="#777e87"/><stop offset=".23" stop-color="#30343b"/><stop offset=".68" stop-color="#15181d"/><stop offset="1" stop-color="#515761"/></linearGradient>
<linearGradient id="surface" x2="1" y2="1"><stop stop-color="#20242b"/><stop offset=".6" stop-color="#111419"/><stop offset="1" stop-color="#0a0d11"/></linearGradient>
<linearGradient id="silver" x2=".8" y2="1"><stop stop-color="#f7f8fa"/><stop offset=".4" stop-color="#b8bec7"/><stop offset=".65" stop-color="#656d79"/><stop offset="1" stop-color="#dfe3e9"/></linearGradient>
<radialGradient id="light"><stop stop-color="#8d96a5" stop-opacity=".25"/><stop offset="1" stop-color="#0b0e12" stop-opacity="0"/></radialGradient>
<clipPath id="clip"><rect width="1200" height="520" rx="30"/></clipPath>
</defs>'''


def save(name, height, body, title):
    source = f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}" viewBox="0 0 1200 {height}" role="img"><title>{escape(title)}</title>{DEFS}'
    source += rect(0, 0, 1200, height, 'url(#shell)', 30)
    source += rect(2, 2, 1196, height-4, '#0d1015', 28)
    source += body + '</svg>'
    (OUT / name).write_text(source, encoding='utf-8')


def arrow(x, y, light=False):
    return circle(x, y, 24, '#e8ebef' if light else '#252b33') + path(f'M{x-8} {y+8}l16 -16m-15 0h15v15', '#12161c' if light else '#dfe4ea', 2)


def hero():
    b = '<g clip-path="url(#clip)">' + rect(0, 0, 1200, 520, 'url(#surface)')
    b += '<ellipse cx="940" cy="220" rx="430" ry="370" fill="url(#light)"/>'
    # An original folded ribbon, formed from projected curves.
    for i in range(92):
        t = i / 91
        pts = []
        for j in range(150):
            a = j / 149 * math.pi * 2
            radius = 130 + 74*t
            xx = radius*math.cos(a)
            yy = radius*math.sin(a)
            z = 66*math.sin(a*2 + t*1.5)
            x = 948 + xx*.98 + yy*.22
            y = 259 + yy*.67 + z + xx*.16
            pts.append((x,y))
        d = 'M' + ' L'.join(f'{x:.2f} {y:.2f}' for x,y in pts) + 'Z'
        lum = int(84 + 135 * (0.5 + 0.5 * math.sin(t * math.pi * 3)))
        b += path(d, f'rgb({lum},{min(lum+5,255)},{min(lum+12,255)})', .85)
    b += '</g>'
    b += text('EM YOL'.replace(' ',''), 55, 64, 20, '#d1d5dc', 600, 4)
    b += text('MANILA, PH', 55, 110, 16, '#8c95a3', 400, 2)
    b += text('Amiel', 49, 242, 106, '#f5f6f8', 600, -5)
    b += text('Acuña.', 49, 345, 106, '#d5dbe4', 600, -5)
    b += text('Software, shaped around people.', 55, 411, 28, '#adb5c2')
    b += text('WEB  /  MOBILE  /  EXPERIMENTS', 55, 470, 15, '#858e9c', 500, 2)
    b += text('SILVER FIELD', 970, 477, 14, '#8d96a4', 400, 2)
    save('silver-field.svg', 520, b, 'Amiel Acuña. Software, shaped around people. Manila, Philippines.')


def base_card(title, category, lines, stack, light=False):
    b = rect(10,10,1180,330,'url(#surface)',23)
    b += text(category.upper(),40,56,17,'#9ea7b4',500,2)
    b += text(title,37,132,58,'#f3f5f8',600,-2)
    for i,line in enumerate(lines):
        b += text(line,40,183+i*32,24,'#b2bac6')
    b += text(stack,40,307,18,'#8e98a7',400)
    b += arrow(1138,54)
    return b


def kitako():
    b = base_card('KitaKo','Search, naturally',['Find a photo.','Use your own words.'],'Dart  /  Flutter  /  ONNX Runtime')
    b += '<g transform="translate(683 40) rotate(-5 210 140)">'
    b += rect(0,0,390,257,'url(#shell)',22)+rect(5,5,380,247,'#11151b',18)
    for row in range(2):
        for col in range(3):
            x=17+col*122;y=17+row*104
            b += rect(x,y,111,92,['#414a55','#59636e','#2c3540'][(row+col)%3],9)
            b += circle(x+80,y+24,10,'#b9c2ca')
            b += path(f'M{x+6} {y+84}L{x+40} {y+37}L{x+65} {y+66}L{x+82} {y+48}L{x+105} {y+84}Z','none',0,'#7b8895')
    b += '</g>'
    b += rect(654,222,440,72,'url(#silver)',20)
    b += circle(688,257,10,'none','#20262e') + path('M696 265l8 8','#20262e',2)
    b += text('kumakain sa beach',720,267,25,'#151a22',500)
    save('kitako.svg',350,b,'KitaKo — on-device semantic photo search with Taglish support. Conceptual illustration.')


def icare():
    b = base_card('iCARE Reservation','Space for learning',['Room bookings,','brought together.'],'JavaScript  /  React  /  Next.js')
    b += '<g transform="translate(675 74) rotate(3 205 110)">'
    b += rect(0,0,422,230,'url(#shell)',20)+rect(5,5,412,220,'#171c23',16)
    b += text('ROOM SCHEDULE',23,35,16,'#bec6d1',500,1)
    for x in range(20,402,64):b+=path(f'M{x} 60v143','#323a46',1)
    for y in range(60,218,38):b+=path(f'M20 {y}h382','#323a46',1)
    for x,y,w in [(24,68,119),(152,107,180),(280,145,117)]:
        b+=rect(x,y,w,27,'#b4bdca',6)
    b += '</g>'
    b += circle(1050,270,36,'#e1e5ec')+path('M1036 270l10 10 20 -23','#151a22',4)
    save('icare.svg',350,b,'iCARE Reservation — AVR and Training Room scheduling. Conceptual schedule illustration.')


def beki():
    b = base_card('BekiLang','Language with personality',['Philippine Swardspeak,','expressed in code.'],'Python  /  Flask')
    b += '<g transform="translate(653 66) rotate(-3 223 112)">'
    b += rect(0,0,446,233,'url(#shell)',22)+rect(5,5,436,223,'#10141a',18)
    for x in [25,41,57]:b+=circle(x,24,3,'#687484')
    b+=text('hello.beki',171,29,15,'#8e99a9')
    b+=text('chika greeting ay',25,83,23,'#a6b1c1',500)
    b+=text('"Hello, world!" periodt',25,116,23,'#f0f2f6',500)
    b+=text('parinig greeting periodt',25,162,23,'#a6b1c1',500)
    b+=path('M25 180h396','#303946',1)
    b+=text('> Hello, world!',25,211,19,'#e0e6ed')
    b+='</g>'
    save('bekilang.svg',350,b,'BekiLang — a Swardspeak-inspired programming language. Illustrated code example.')


def city():
    b=base_card('CitySense','A different view of the city',['Earth observation.','Urban perspective.'],'TypeScript  /  React  /  Leaflet')
    b+='<g transform="translate(677 75)">'
    for z in [70,35,0]:
        b+=path(f'M0 {65+z}L190 {z}L421 {61+z}L226 {147+z}Z','#556172',1,'#18212b')
    for i in range(13):
        y=30+i*5.2
        d=f'M{(13-i)*6} {y+24}'
        for j in range(31):
            x=(13-i)*6+j*9
            yy=y+24+math.sin(j/4+i*.39)*14+j*.09
            d+=f'L{x:.1f} {yy:.1f}'
        b+=path(d,'#718297',1)
    for x,y in [(129,68),(234,76),(307,69)]:
        b+=path(f'M{x} {y}v-32','#c1cbd9',1.4)+circle(x,y-34,5,'#e6ebf2')
    b+='</g>'
    save('citysense.svg',350,b,'CitySense — Earth observation layers for urban exploration. Conceptual map, not measured geographic data.')


def stack():
    b=''
    for x,title,subtitle,lines in [
        (12,'Web','INTERFACES',['JavaScript · TypeScript','React · Next.js','Tailwind CSS']),
        (408,'Mobile','ON-DEVICE SEARCH',['Dart · Flutter','ONNX Runtime']),
        (804,'Tools','LANGUAGE & MAPS',['Python · Flask','Leaflet'])]:
        b+=rect(x,12,384,266,'url(#surface)',20)
        b+=text(subtitle,x+26,51,14,'#8e99a9',500,1.4)
        b+=text(title,x+24,110,42,'#edf0f5',600,-1.5)
        for i,line in enumerate(lines):b+=text(line,x+26,164+i*34,21,'#b7c1ce')
    save('toolkit.svg',290,b,'Web: JavaScript, TypeScript, React, Next.js, Tailwind CSS. Mobile: Dart, Flutter, ONNX Runtime. Tools: Python, Flask, Leaflet.')


if __name__=='__main__':
    hero();kitako();icare();beki();city();stack()
    print('Built six original SVG assets with outlined Geist typography.')
