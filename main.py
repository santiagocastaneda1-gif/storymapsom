"""
StoryMap SOM -- Aplicación principal Kivy
Explorador visual de textos usando Self-Organizing Maps

Autores: Santiago Castañeda & Santiago Florez
Curso: Computación Blanda -- Proyecto Final
"""

import os, sys, threading, math, random

from kivy.config import Config
Config.set('input', 'mouse', 'mouse,disable_multitouch')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line, Ellipse
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.animation import Animation
from kivy.utils import get_color_from_hex, platform
from kivy.uix.image import Image

# ── Registrar fuentes ─────────────────────────────────────────────────────────
_DIR = os.path.dirname(os.path.abspath(__file__))

LabelBase.register(
    name='Nunito-Regular',
    fn_regular=os.path.join(_DIR, 'Nunito-Regular.ttf'),
    fn_bold=os.path.join(_DIR, 'Nunito-Regular.ttf'),
)
LabelBase.register(
    name='Icons',
    fn_regular=os.path.join(_DIR, 'ionicons.ttf'),
)
LabelBase.register(
    name='Orbitron',
    fn_regular=os.path.join(_DIR, 'Orbitron-Bold.ttf'),
)

# ── Ionicons v3 codepoints ────────────────────────────────────────────────────
II = {
    'home':        '\uf116',  # flecha arriba / inicio
    'docs':        '\uf14f',  # documento
    'train':       '\uf113',  # play
    'map':         '\uf15d',  # brújula
    'analytics':   '\uf10a',  # capas/layers
    'settings':    '\uf136',  # llave/wrench
    'rocket':      '\uf14b',  # cohete
    'trash':       '\uf12f',  # tijeras / usa otro
    'add':         '\uf100',  # círculo con +
    'upload':      '\uf11a',  # flecha arriba
    'star':        '\uf13f',  # favorito broken heart... usa check
    'check':       '\uf147',  # check cuadrado
    'warning':     '\uf104',  # !
    'close':       '\uf14e',  # X círculo
    'arrow_r':     '\uf119',  # flecha derecha
    'save':        '\uf142',  # tarjeta/save
    'refresh':     '\uf135',  # reloj/refresh
    'info':        '\uf104',  # !
    'layers':      '\uf10a',  # capas
    'funnel':      '\uf443',  
    'book':        '\uf14f',  # documento
    'tag':         '\uf394',  
    'pulse':       '\uf13d',  # wifi/signal
    'code':        '\uf157',  # </>
    'grid':        '\uf11f',  # grid
    'flash':       '\uf138',  # bombilla
    'download':    '\uf125',  # flecha abajo
    'play':        '\uf113',  # play
    'shuffle':     '\uf10c',  # pencil/edit
    'eye':         '\uf150',  # ojo
    'list':        '\uf143',  # lista
    'vector':      '\uf188',  # vector
    'mundo':       '\uf18A',  # mundo
    'pc':          '\uf115',  # pc
    'subir':       '\uf11b',  # subir
    'demo':        '\uf13b',  # demo
}

# ── Paleta ────────────────────────────────────────────────────────────────────
def hx(h): return get_color_from_hex(h)

C = {
    'bg':      hx('#090b10'),
    'bg2':     hx('#0f1219'),
    'bg3':     hx('#161b26'),
    'bg4':     hx('#1e2535'),
    'cyan':    hx('#00f5e9'),
    'violet':  hx('#9d5cff'),
    'pink':    hx('#ff4d9e'),
    'amber':   hx('#ffb830'),
    'green':   hx('#39ff88'),
    'text':    hx('#e8eaf2'),
    'muted':   hx('#6b7499'),
    'border':  (1, 1, 1, 0.07),
    'clusters': [
        hx('#00f5e9'), hx('#9d5cff'), hx('#ff4d9e'), hx('#ffb830'),
        hx('#39ff88'), hx('#54a0ff'), hx('#ff6b6b'), hx('#ffeaa7'),
    ],
}

Window.clearcolor = C['bg']
IS_ANDROID = platform == 'android'
session    = None  # se asigna abajo tras el import

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.som_engine import StorySession, DEMO_STORIES
session = StorySession()

# ── Helpers ───────────────────────────────────────────────────────────────────
def apply_bg(w, color):
    with w.canvas.before:
        Color(*color)
        r = Rectangle(pos=w.pos, size=w.size)
    w.bind(pos=lambda ww,v: setattr(r,'pos',v),
           size=lambda ww,v: setattr(r,'size',v))

def apply_rounded_bg(w, color, radius=dp(14)):
    with w.canvas.before:
        Color(*color)
        r = RoundedRectangle(pos=w.pos, size=w.size, radius=[radius])
    w.bind(pos=lambda ww,v: setattr(r,'pos',v),
           size=lambda ww,v: setattr(r,'size',v))

def slide_in(widget, delay=0, dy=dp(10), dur=0.2):
    def _go(*_):
        try:
            widget.opacity = 0
            oy = widget.y; widget.y = oy - dy
            Animation(opacity=1, y=oy, d=dur, t='out_quad').start(widget)
        except: pass
    Clock.schedule_once(_go, delay)

def lbl(text, font='Nunito-Regular', size=sp(13), color=None, bold=False,
        halign='left', valign='middle', **kw):
    """Label con Nunito-Regular."""
    l = Label(text=text, font_name=font, font_size=size,
               color=color or C['text'], bold=bold,
               halign=halign, valign=valign, **kw)
    l.bind(size=lambda w,v: setattr(w,'text_size',v))
    return l

def ico(code, size=sp(22), color=None, **kw):
    """Label con Ionicons."""
    l = Label(text=code, font_name='Icons', font_size=size,
               color=color or C['cyan'], halign='center', valign='middle', **kw)
    return l

def ico_box(code, color, box_size=dp(40), ico_size=sp(20)):
    """Caja con fondo coloreado + icono Ionicons centrado."""
    box = BoxLayout(size_hint=(None, None), size=(box_size, box_size))
    with box.canvas.before:
        Color(color[0], color[1], color[2], 0.13)
        rr = RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(10)])
    box.bind(pos=lambda w,v,r=rr: setattr(r,'pos',v),
             size=lambda w,v,r=rr: setattr(r,'size',v))
    box.add_widget(ico(code, size=ico_size, color=color))
    return box

# ── Componentes base ──────────────────────────────────────────────────────────
class NeonButton(Button):
    def __init__(self, style='primary', text_color=None, radius=dp(10), **kw):
        kw.setdefault('font_name', 'Nunito-Regular')
        kw.setdefault('bold', True)
        super().__init__(**kw)
        self.background_normal = ''
        self.background_color  = (0, 0, 0, 0)
        self.color    = text_color or ((0.05,0.05,0.1,1) if style=='primary' else C['text'])
        self._style   = style
        self._radius  = radius
        self._pressed = False
        self.bind(pos=self._draw, size=self._draw)
        Clock.schedule_once(self._draw)

    def _draw(self, *_):
        self.canvas.before.clear()
        a = 0.75 if self._pressed else 1.0
        r = self._radius
        with self.canvas.before:
            if self._style == 'primary':
                # Fondo sólido cyan
                Color(0, 0.961*a, 0.914*a, 1)
                RoundedRectangle(pos=self.pos, size=self.size, radius=[self._radius])
                # Overlay violet muy sutil para darle profundidad
                Color(0.616, 0.361, 1, 0.05)
                RoundedRectangle(pos=self.pos, size=self.size, radius=[self._radius])
                Color(0.04, 0.04, 0.1, 0.25)
                RoundedRectangle(pos=self.pos, size=self.size, radius=[r])
            elif self._style == 'outline':
                Color(0,0.961,0.914,0.10); RoundedRectangle(pos=self.pos,size=self.size,radius=[r])
                Color(0,0.961,0.914,0.55); Line(rounded_rectangle=[self.x,self.y,self.width,self.height,r],width=1.2)
            elif self._style == 'danger':
                Color(1,0.302,0.620,0.12); RoundedRectangle(pos=self.pos,size=self.size,radius=[r])
                Color(1,0.302,0.620,0.45); Line(rounded_rectangle=[self.x,self.y,self.width,self.height,r],width=1)
            elif self._style == 'teal':
                Color(0,0.961,0.914,0.14); RoundedRectangle(pos=self.pos,size=self.size,radius=[r])
                Color(0,0.961,0.914,0.60); Line(rounded_rectangle=[self.x,self.y,self.width,self.height,r],width=1)
            elif self._style == 'sm':
                Color(*C['bg3']); RoundedRectangle(pos=self.pos,size=self.size,radius=[r])
                Color(*C['border']); Line(rounded_rectangle=[self.x,self.y,self.width,self.height,r],width=0.8)
            elif self._style == 'violet':
                Color(0.616,0.361,1,0.12); RoundedRectangle(pos=self.pos,size=self.size,radius=[r])
                Color(0.616,0.361,1,0.55); Line(rounded_rectangle=[self.x,self.y,self.width,self.height,r],width=1.2)

    def on_press(self):   self._pressed=True;  self._draw(); Animation(opacity=0.8,d=0.05).start(self)
    def on_release(self): self._pressed=False; self._draw(); Animation(opacity=1.0,d=0.1).start(self)


class NeonCard(BoxLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._hover = False
        self.bind(pos=self._draw, size=self._draw)
        Clock.schedule_once(self._draw)

    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*C['bg2']); RoundedRectangle(pos=self.pos,size=self.size,radius=[dp(14)])
            Color(*(0,0.961,0.914,0.22) if self._hover else C['border'])
            Line(rounded_rectangle=[self.x,self.y,self.width,self.height,dp(14)],width=1)

    def on_touch_down(self,t):
        if self.collide_point(*t.pos): self._hover=True; self._draw()
        return super().on_touch_down(t)
    def on_touch_up(self,t):
        self._hover=False; self._draw(); return super().on_touch_up(t)


class Badge(Label):
    _MAP = {
        'cyan':   (hx('#00f5e9'),(0,0.961,0.914,0.10),(0,0.961,0.914,0.28)),
        'violet': (hx('#9d5cff'),(0.616,0.361,1,0.10),(0.616,0.361,1,0.28)),
        'green':  (hx('#39ff88'),(0.224,1,0.533,0.10),(0.224,1,0.533,0.28)),
        'amber':  (hx('#ffb830'),(1,0.722,0.188,0.10),(1,0.722,0.188,0.28)),
        'pink':   (hx('#ff4d9e'),(1,0.302,0.620,0.10),(1,0.302,0.620,0.28)),
    }
    def __init__(self, color_key='cyan', **kw):
        tc,self._bg,self._bc = self._MAP.get(color_key,self._MAP['cyan'])
        kw.setdefault('color', tc)
        kw.setdefault('font_name', 'Nunito-Regular')
        kw.setdefault('font_size', sp(9))
        kw.setdefault('size_hint', (None,None))
        kw.setdefault('height', dp(20))
        super().__init__(**kw)
        self.bind(texture_size=lambda w,v: setattr(w,'width',v[0]+dp(16)))
        self.bind(pos=self._draw, size=self._draw)
        Clock.schedule_once(self._draw)
    def _draw(self,*_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._bg); RoundedRectangle(pos=self.pos,size=self.size,radius=[dp(10)])
            Color(*self._bc); Line(rounded_rectangle=[self.x,self.y,self.width,self.height,dp(10)],width=0.8)


class ColorDot(Widget):
    def __init__(self,color,**kw):
        super().__init__(**kw); self._color=color
        self.bind(pos=self._draw,size=self._draw); Clock.schedule_once(self._draw)
    def _draw(self,*_):
        self.canvas.clear()
        with self.canvas: Color(*self._color); Ellipse(pos=self.pos,size=self.size)

def section_title(text):
    return lbl(text.upper(), size=sp(9), color=C['muted'],
                size_hint_y=None, height=dp(26))

def make_header(title_text, sub_text, icon_code=None):
    hdr = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(58),
                    padding=[dp(16),dp(8)], spacing=dp(2))
    apply_bg(hdr, C['bg2'])
    with hdr.canvas.after:
        Color(*C['border']); hdr._bl = Line(points=[0,0,0,0], width=1)
    def _u(*_): hdr._bl.points = [hdr.x,hdr.y,hdr.x+hdr.width,hdr.y]
    hdr.bind(pos=_u, size=_u)

    tr = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(8))
    if icon_code:
        tr.add_widget(ico(icon_code, size=sp(20), color=C['cyan'],
                           size_hint_x=None, width=dp(26)))
    tr.add_widget(lbl(title_text, size=sp(18), color=C['cyan'], bold=True,
                       size_hint_y=None, height=dp(28)))
    hdr.add_widget(tr)
    hdr.add_widget(lbl(sub_text, size=sp(11), color=C['muted'],
                        size_hint_y=None, height=dp(16)))
    return hdr

# ── StatusBar ─────────────────────────────────────────────────────────────────
class StatusBar(BoxLayout):
    def __init__(self,**kw):
        kw.setdefault('size_hint_y',None); kw.setdefault('height',dp(26))
        kw.setdefault('padding',[dp(16),0])
        super().__init__(**kw)
        apply_bg(self,C['bg2'])
        self.add_widget(lbl('9:41',size=sp(9),color=C['muted'],
                              size_hint_x=None,width=dp(40)))
        self.add_widget(Widget())
        row = BoxLayout(size_hint_x=None,width=dp(56),spacing=dp(6))
        row.add_widget(ico(II['flash'],size=sp(12),color=C['muted'],size_hint_x=None,width=dp(14)))
        row.add_widget(ico(II['eye'],  size=sp(12),color=C['muted'],size_hint_x=None,width=dp(14)))
        self.add_widget(row)

# ── NavBar ────────────────────────────────────────────────────────────────────
class NavBar(BoxLayout):
    TABS = [
        ('welcome',  'Inicio',  II['home']),
        ('docs',     'Docs',    II['docs']),
        ('train',    'Entrena', II['train']),
        ('map',      'Mapa',    II['map']),
        ('analysis', 'Stats',   II['analytics']),
        ('config',   'Config',  II['settings']),
    ]

    def __init__(self, on_tab=None, **kw):
        kw.setdefault('size_hint_y',None); kw.setdefault('height',dp(64))
        super().__init__(**kw)
        self._on_tab = on_tab; self._current = 'welcome'; self._items = {}
        apply_bg(self,C['bg2'])
        with self.canvas.before:
            Color(*C['border']); self._tl = Line(points=[0,0,0,0],width=1)
        self.bind(pos=self._upd,size=self._upd)
        self._build()

    def _upd(self,*_):
        self._tl.points=[self.x,self.y+self.height,self.x+self.width,self.y+self.height]

    def _build(self):
        for key, label_text, icon_code in self.TABS:
            col = BoxLayout(orientation='vertical', spacing=dp(1), padding=[0,dp(5)])
            col._key = key

            # Indicador superior activo
            ind = Widget(size_hint_y=None, height=dp(3))
            col._ind = ind; col.add_widget(ind)

            # Icono Ionicons
            icon_lbl = ico(icon_code, size=sp(22), color=C['muted'],
                            size_hint_y=None, height=dp(26))
            col._ico = icon_lbl; col.add_widget(icon_lbl)

            # Texto con Nunito-Regular
            txt = lbl(label_text, size=sp(8), color=C['muted'],
                       halign='center', size_hint_y=None, height=dp(14))
            col._txt = txt; col.add_widget(txt)

            col.bind(on_touch_down=lambda w,t: self._hit(w,t))
            self._items[key] = col; self.add_widget(col)

    def _hit(self, box, touch):
        if box.collide_point(*touch.pos):
            self.set_active(box._key)
            if self._on_tab: self._on_tab(box._key)

    def set_active(self, key):
        self._current = key
        for k, item in self._items.items():
            active = (k == key)
            color  = C['cyan'] if active else C['muted']
            item._ico.color = color
            item._txt.color = color
            item._ind.canvas.clear()
            with item._ind.canvas:
                if active:
                    Color(*C['cyan'])
                    RoundedRectangle(pos=item._ind.pos,size=item._ind.size,radius=[dp(2)])

# ── AppShell ──────────────────────────────────────────────────────────────────
class AppShell(Screen):
    def __init__(self,**kw):
        super().__init__(**kw)
        apply_bg(self,C['bg'])
        self._current_tab = 'welcome'; self._build()

    def _build(self):
        root = BoxLayout(orientation='vertical')
        self.statusbar = StatusBar(); root.add_widget(self.statusbar)
        self.content   = BoxLayout(orientation='vertical'); root.add_widget(self.content)
        self.navbar    = NavBar(on_tab=self._switch_tab); root.add_widget(self.navbar)
        self.add_widget(root); self._load_tab('welcome')

    def _switch_tab(self, key):
        if key == self._current_tab: return
        self._current_tab = key; self.navbar.set_active(key)
        self.content.opacity = 0; self._load_tab(key)
        Animation(opacity=1, d=0.18, t='out_quad').start(self.content)

    def _load_tab(self, key):
        self.content.clear_widgets()
        cls = {'welcome':WelcomeTab,'docs':DocsTab,'train':TrainTab,
               'map':MapTab,'analysis':AnalysisTab,'config':ConfigTab}.get(key,WelcomeTab)
        self.content.add_widget(cls(shell=self))

# ── Partículas ────────────────────────────────────────────────────────────────
class ParticleWidget(Widget):
    def __init__(self,**kw):
        super().__init__(**kw); self._t=0
        self._pts=[{'x':random.random(),'y':random.random(),
                     'vx':(random.random()-.5)*.12,'vy':(random.random()-.5)*.12,
                     'r':random.uniform(1,2.5),
                     'c':random.choice([(0,.961,.914),(.616,.361,1),(1,.302,.62)])}
                   for _ in range(30)]
        Clock.schedule_interval(self._tick,1/30)

    def _tick(self,dt):
        self._t+=dt
        for p in self._pts:
            p['x']+=p['vx']*dt; p['y']+=p['vy']*dt
            if p['x']<0 or p['x']>1: p['vx']*=-1
            if p['y']<0 or p['y']>1: p['vy']*=-1
        self._redraw()

    def _redraw(self):
        self.canvas.clear()
        w=self.width or 1; h=self.height or 1
        ox=self.x; oy=self.y  # offset absoluto del widget
        with self.canvas:
            for p in self._pts:
                a=.45+.35*math.sin(self._t*2+p['x']*5)
                Color(p['c'][0],p['c'][1],p['c'][2],a)
                r=p['r']
                Ellipse(pos=(ox+p['x']*w-r, oy+p['y']*h-r+dp(350)),size=(r*3,r*3))
            for i,a in enumerate(self._pts):
                for b in self._pts[i+1:]:
                    dx=(a['x']-b['x'])*w; dy=(a['y']-b['y'])*h
                    d=math.sqrt(dx*dx+dy*dy)
                    if d<55:
                        Color(0,.961,.914,.12*(1-d/55))
                        Line(points=[ox+a['x']*w, oy+a['y']*h+dp(350),
                        ox+b['x']*w, oy+b['y']*h+dp(350)], width=1.5)

# ── WelcomeTab ────────────────────────────────────────────────────────────────
class WelcomeTab(BoxLayout):
    def __init__(self,shell=None,**kw):
        super().__init__(orientation='vertical',**kw)
        self._shell=shell; self._build()

    def _build(self):
        hero = FloatLayout(size_hint_y=None, height=dp(220))
        with hero.canvas.before:
            Color(*C['bg2'])
            _hbg = Rectangle(pos=hero.pos, size=hero.size)
            Color(.616,.361,1,.20)
            _e1 = RoundedRectangle(pos=(0,0), size=(1,1))
            Color(0,.961,.914,.10)
            _e2 = RoundedRectangle(pos=(0,0), size=(1,1))
        def _upd_hero(w, *_):
            _hbg.pos = w.pos; _hbg.size = w.size
            ew1 = w.width*0.8; eh1 = w.height*0.8
            _e1.pos = (w.x + (w.width-ew1)/2, w.y + (w.height-eh1)/1 - dp(10))
            _e1.size = (ew1, eh1); _e1.radius = [dp(30)]
            ew2 = w.width*0.7; eh2 = w.height*0.6
            _e2.pos = (w.x + (w.width-ew1)/1.3, w.y + (w.height-eh1)/0.65 - dp(10))
            _e2.size = (ew2, eh2); _e2.radius = [dp(30)]
        hero.bind(pos=_upd_hero, size=_upd_hero)

        # Particulas detras del logo — size_hint=(1,1) para llenar el hero
        particles = ParticleWidget(size_hint=(1,1))
        hero.add_widget(particles)

        # Logo: imagen a la izquierda del card, ambos en horizontal
        outer_box = BoxLayout(orientation='vertical', spacing=dp(4),
                              size_hint=(None,None), size=(dp(300),dp(90)),
                              pos_hint={'center_x':.58,'center_y':.55})

        # Fila horizontal: imagen | card con titulo
        logo_row = BoxLayout(orientation='horizontal', spacing=dp(8),
                             size_hint_y=None, height=dp(80))

        # Imagen a la izquierda, fuera del rectangulo
        logo_ico = Image(
                        source='cuento.png',
                        size_hint=(None,None),
                        size=(dp(60),dp(60)),
                        fit_mode='contain',
                        pos_hint={'center_y':.58}
                    )
        logo_row.add_widget(logo_ico)

        # Card con solo el titulo a la derecha
        logo_card = BoxLayout(size_hint=(1,None), height=dp(72),
                               padding=[dp(10),dp(6)], spacing=dp(10))
        

        title_col=BoxLayout(orientation='vertical',spacing=dp(2))
        title_col.add_widget(lbl('StoryMap', font='Orbitron',size=sp(24),color=C['cyan'],bold=True))
        title_col.add_widget(lbl('SOM Engine',font='Orbitron',size=sp(10),color=C['muted']))
        logo_card.add_widget(title_col)
        logo_row.add_widget(logo_card)

        outer_box.add_widget(logo_row)
        outer_box.add_widget(lbl('Explorador visual de textos con IA',
                                 size=sp(10),font='Orbitron',color=C['muted'],halign='center',
                                 size_hint_y=(5,None),height=dp(20)))
        logo_box = outer_box
        hero.add_widget(logo_box)
        self.add_widget(hero)

        # Stats
        stats=BoxLayout(size_hint_y=None,height=dp(58),padding=[dp(16),dp(6)],spacing=dp(10))
        apply_bg(stats,C['bg'])
        for val,label_text,color in [('12','Cuentos',C['cyan']),
                                      ('8x8','Grilla',C['violet']),
                                      ('500','Epocas',C['pink'])]:
            col=BoxLayout(orientation='vertical',spacing=dp(2))
            col.add_widget(lbl(val,size=sp(18),color=color,bold=True,halign='center'))
            col.add_widget(lbl(label_text,size=sp(9),color=C['muted'],halign='center'))
            stats.add_widget(col)
        self.add_widget(stats)

        # Features
        
        scroll=ScrollView(size_hint=(1,1))
        inner=BoxLayout(orientation='vertical',spacing=dp(8),
                         padding=[dp(14),dp(6)],size_hint_y=None)
        inner.bind(minimum_height=inner.setter('height'))

        features=[
            (II['shuffle'], C['cyan'],   'SOM de Kohonen',      'Red neuronal auto-organizada'),
            (II['vector'],    C['violet'], 'Vectores TF-IDF',     'Representacion semantica NLP'),
            (II['mundo'],    C['pink'],   'Mapa 2D interactivo', 'U-Matrix + clusters K-Means'),
            (II['pc'],   C['amber'],  'Computacion Blanda',  'Santiago C. & Santiago F.'),
        ]
        for i,(icon_code,color,tt,st) in enumerate(features):
            row=BoxLayout(size_hint_y=None,height=dp(52),spacing=dp(12))
            row.add_widget(ico_box(icon_code,color))
            col=BoxLayout(orientation='vertical',spacing=dp(2))
            col.add_widget(lbl(tt,size=sp(12),bold=True))
            col.add_widget(lbl(st,size=sp(10),color=C['muted']))
            row.add_widget(col)
            inner.add_widget(row); slide_in(row,delay=0.06*i)

        inner.add_widget(Widget(size_hint_y=None,height=dp(10)))

        # Boton con icono Ionicons incrustado
        btn_row=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(8))
        btn=NeonButton(text='Comenzar',style='primary',
                        text_color=(0.05,0.05,0.1,1),font_size=sp(14))
        btn.bind(on_press=lambda *_: self._shell._switch_tab('docs') if self._shell else None)
        btn_row.add_widget(btn)
        inner.add_widget(btn_row)
        inner.add_widget(Widget(size_hint_y=None,height=dp(8)))
        scroll.add_widget(inner); self.add_widget(scroll)
        slide_in(btn_row,delay=0.28)

# ── DocsTab ───────────────────────────────────────────────────────────────────
class DocsTab(BoxLayout):
    def __init__(self,shell=None,**kw):
        super().__init__(orientation='vertical',**kw)
        self._shell=shell; self._build()

    def _build(self):
        self.clear_widgets()
        self.add_widget(make_header('Documentos','Textos cargados para analizar',II['docs']))

        act=BoxLayout(size_hint_y=None,height=dp(44),padding=[dp(10),dp(5)],spacing=dp(6))
        apply_bg(act,C['bg'])

        def _icon_action_btn(icon_code,text_t,style,tc,cb,w=dp(96)):
            b=BoxLayout(size_hint=(None,1),width=w)
            with b.canvas.before:
                if style=='teal':
                    Color(0,0.961,0.914,0.12); RoundedRectangle(pos=b.pos,size=b.size,radius=[dp(9)])
                    Color(0,0.961,0.914,0.5); rr=RoundedRectangle(pos=b.pos,size=b.size,radius=[dp(9)])
                else:
                    Color(*C['bg3']); rr=RoundedRectangle(pos=b.pos,size=b.size,radius=[dp(9)])
                Color(*C['border']); ln=Line(rounded_rectangle=[*b.pos,*b.size,dp(9)],width=0.8)
            def _up(w2,v): rr.pos=v; ln.rounded_rectangle=[*v,*w2.size,dp(9)]
            def _us(w2,v): rr.size=v; ln.rounded_rectangle=[*w2.pos,*v,dp(9)]
            b.bind(pos=_up,size=_us)
            b.add_widget(ico(icon_code,size=sp(15),color=tc,size_hint_x=None,width=dp(20)))
            t=lbl(text_t,size=sp(11),color=tc)
            b.add_widget(t)
            b.bind(on_touch_down=lambda w2,ev: cb() if w2.collide_point(*ev.pos) else None)
            return b

        act.add_widget(_icon_action_btn(II['add'],   'Nuevo', 'sm',   C['text'], self._popup_add))
        act.add_widget(_icon_action_btn(II['subir'],'Cargar',  'sm',   C['text'], self._popup_file))
        act.add_widget(_icon_action_btn(II['demo'],  'Demo',  'teal', C['cyan'], self._load_demo))
        act.add_widget(Widget())
        n=len(session.documents); ready=n>=2
        act.add_widget(Badge(color_key='green' if ready else 'amber',
                              text='Listo' if ready else f'{n} docs',
                              size_hint=(None,None),height=dp(24)))
        self.add_widget(act)

        scroll=ScrollView(size_hint=(1,1))
        grid=GridLayout(cols=1,spacing=dp(6),padding=[dp(10),dp(6)],size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        BKEYS=['cyan','violet','pink','amber','green']
        if not session.documents:
            c=NeonCard(orientation='vertical',padding=dp(22),spacing=dp(10),
                        size_hint_y=None,height=dp(120))
            c.add_widget(ico(II['list'],size=sp(36),color=C['muted']))
            c.add_widget(lbl('Sin documentos.\nAgrega textos o carga el demo.',
                              size=sp(12),color=C['muted'],halign='center'))
            grid.add_widget(c)
        else:
            for i,(title,text) in enumerate(zip(session.titles,session.documents)):
                row=BoxLayout(size_hint_y=None,height=dp(64),spacing=dp(8))
                card=NeonCard(orientation='horizontal',padding=[dp(10),dp(8)],
                               spacing=dp(10),size_hint=(1,1))
                clr=C['clusters'][i%len(C['clusters'])]
                # Barra lateral
                bar=Widget(size_hint=(None,1),width=dp(4))
                with bar.canvas.before:
                    Color(*clr); brr=RoundedRectangle(pos=bar.pos,size=bar.size,radius=[dp(2)])
                bar.bind(pos=lambda w,v,r=brr:setattr(r,'pos',v),
                         size=lambda w,v,r=brr:setattr(r,'size',v))
                card.add_widget(bar)
                card.add_widget(ico(II['book'],size=sp(20),color=clr,
                                     size_hint_x=None,width=dp(26)))
                info=BoxLayout(orientation='vertical',spacing=dp(3))
                nl=lbl(f'[b]{title}[/b]',size=sp(12),bold=True,
                         size_hint_y=None,height=dp(22))
                nl.markup=True
                meta=BoxLayout(spacing=dp(6),size_hint_y=None,height=dp(18))
                meta.add_widget(lbl(f'{len(text.split())} tokens',size=sp(9),
                                     color=C['muted'],size_hint_x=None,width=dp(65)))
                meta.add_widget(Badge(color_key=BKEYS[i%len(BKEYS)],
                                       text='Cuento',size_hint=(None,None),height=dp(16)))
                meta.add_widget(Widget())
                info.add_widget(nl); info.add_widget(meta)
                card.add_widget(info); row.add_widget(card)
                db=NeonButton(text=II['close'],font_name='Icons',
                               style='danger',text_color=C['pink'],
                               font_size=sp(18),
                               size_hint=(None,1),width=dp(44))
                db.bind(on_press=lambda _,idx=i: self._delete(idx))
                row.add_widget(db); grid.add_widget(row); slide_in(row,delay=.03*i)

        scroll.add_widget(grid); self.add_widget(scroll)

        bot=BoxLayout(size_hint_y=None,height=dp(50),padding=[dp(10),dp(6)],spacing=dp(8))
        apply_bg(bot,C['bg'])
        bot.add_widget(lbl(f'{n} documentos',size=sp(10),color=C['muted'],
                            size_hint_x=None,width=dp(130)))
        cta=NeonButton(text='Continuar a Entrenar',
                        style='primary' if ready else 'sm',
                        text_color=(0.05,0.05,0.1,1) if ready else C['muted'],
                        font_size=sp(12))
        cta.bind(on_press=lambda *_: self._shell._switch_tab('train') if self._shell else None)
        bot.add_widget(cta); self.add_widget(bot)

    def _delete(self,idx): session.remove_document(idx); self._build()
    def _load_demo(self):
        session.clear()
        for t,tx in DEMO_STORIES: session.add_document(t,tx)
        self._build()

    def _popup(self, title_t, content, size=(0.93,0.8)):
        popup=Popup(title=title_t,content=content,size_hint=size,background_color=C['bg2'])
        return popup

    def _popup_add(self):
        ov=BoxLayout(orientation='vertical',padding=dp(12),spacing=dp(8))
        ov.add_widget(lbl('Titulo:',size=sp(11),color=C['muted'],size_hint_y=None,height=dp(20)))
        ti=TextInput(hint_text='Mi cuento favorito',multiline=False,font_name='Nunito-Regular',
                      size_hint_y=None,height=dp(40),background_color=C['bg3'],
                      foreground_color=C['text'],font_size=sp(13),cursor_color=C['cyan'])
        ov.add_widget(ti)
        ov.add_widget(lbl('Contenido:',size=sp(11),color=C['muted'],size_hint_y=None,height=dp(20)))
        tx=TextInput(hint_text='Escribe o pega el texto aqui...',font_name='Nunito-Regular',
                      background_color=C['bg3'],foreground_color=C['text'],
                      font_size=sp(12),cursor_color=C['cyan'])
        ov.add_widget(tx)
        btns=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(8))
        bc=NeonButton(text='Cancelar',style='sm')
        ba=NeonButton(text='Agregar',style='primary',text_color=(0.05,0.05,0.1,1))
        btns.add_widget(bc); btns.add_widget(ba); ov.add_widget(btns)
        popup=self._popup('Agregar texto',ov)
        def do(*_):
            t=ti.text.strip() or f'Texto {len(session.documents)+1}'
            if len(tx.text.strip())<10: return
            session.add_document(t,tx.text.strip()); popup.dismiss(); self._build()
        ba.bind(on_press=do); bc.bind(on_press=popup.dismiss); popup.open()

    def _popup_file(self):
        ov=BoxLayout(orientation='vertical',padding=dp(12),spacing=dp(8))
        ov.add_widget(lbl('Ruta del archivo .txt:',size=sp(12),color=C['muted'],
                            size_hint_y=None,height=dp(24)))
        pi=TextInput(hint_text='/sdcard/Download/cuento.txt',multiline=False,font_name='Nunito-Regular',
                      size_hint_y=None,height=dp(42),background_color=C['bg3'],
                      foreground_color=C['text'],font_size=sp(11),cursor_color=C['cyan'])
        ov.add_widget(pi)
        st=lbl('',size=sp(11),color=C['pink'],size_hint_y=None,height=dp(22))
        ov.add_widget(st)
        btns=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(8))
        bc=NeonButton(text='Cancelar',style='sm')
        bl=NeonButton(text='Cargar',style='primary',text_color=(0.05,0.05,0.1,1))
        btns.add_widget(bc); btns.add_widget(bl); ov.add_widget(btns)
        popup=self._popup('Cargar .txt',ov,size=(0.93,0.52))
        def do(*_):
            path=pi.text.strip()
            if not os.path.exists(path): st.text='Archivo no encontrado'; return
            try:
                with open(path,'r',encoding='utf-8',errors='ignore') as f: txt=f.read()
                session.add_document(os.path.basename(path).replace('.txt',''),txt)
                popup.dismiss(); self._build()
            except Exception as e: st.text=f'Error: {str(e)[:50]}'
        bl.bind(on_press=do); bc.bind(on_press=popup.dismiss); popup.open()

# ── NeonSlider ────────────────────────────────────────────────────────────────
class NeonSlider(BoxLayout):
    def __init__(self,label_text,mn,mx,val,step,clr_key='cyan',fmt='{:.0f}',**kw):
        kw.setdefault('orientation','vertical'); kw.setdefault('spacing',dp(3))
        kw.setdefault('size_hint_y',None); kw.setdefault('height',dp(62))
        super().__init__(**kw)
        clr={'cyan':C['cyan'],'violet':C['violet'],'pink':C['pink'],'amber':C['amber']}[clr_key]
        row=BoxLayout(size_hint_y=None,height=dp(20))
        row.add_widget(lbl(label_text,size=sp(11),color=C['muted']))
        self._vl=lbl(fmt.format(val),size=sp(12),color=clr,bold=True,
                      halign='right',size_hint_x=None,width=dp(48))
        row.add_widget(self._vl); self.add_widget(row)
        self._sl=Slider(min=mn,max=mx,value=val,step=step,size_hint_y=None,height=dp(34),
                         value_track=True,value_track_color=clr)
        self._sl.bind(value=lambda _,v: setattr(self._vl,'text',fmt.format(v)))
        self.add_widget(self._sl)

    @property
    def value(self): return self._sl.value

# ── TrainTab ──────────────────────────────────────────────────────────────────
class TrainTab(BoxLayout):
    def __init__(self,shell=None,**kw):
        super().__init__(orientation='vertical',**kw)
        self._shell=shell; self._training=False; self._build()

    def _build(self):
        self.add_widget(make_header('Entrenar SOM','Configura los hiperparametros',II['funnel']))
        scroll=ScrollView(size_hint=(1,1))
        inner=BoxLayout(orientation='vertical',spacing=dp(8),padding=[dp(12),dp(8)],size_hint_y=None)
        inner.bind(minimum_height=inner.setter('height'))

        # ── Card 1: Grilla del mapa ──
        gc=NeonCard(orientation='vertical',size_hint_y=None,height=dp(150),
                    padding=[dp(14),dp(12)],spacing=dp(10))
        gc.add_widget(section_title('Grilla del mapa'))

        row_filas=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(12))
        row_filas.add_widget(lbl('Filas',size=sp(12),color=C['muted'],
                                  size_hint_x=None,width=dp(70)))
        self.spin_rows=Spinner(values=['4','6','8','10','12'],text=str(session.grid_size[0]),
                                size_hint=(1,1),font_name='Nunito-Regular',font_size=sp(14),
                                background_color=C['bg3'],color=C['cyan'])
        row_filas.add_widget(self.spin_rows)
        gc.add_widget(row_filas)

        row_cols=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(12))
        row_cols.add_widget(lbl('Columnas',size=sp(12),color=C['muted'],
                                 size_hint_x=None,width=dp(70)))
        self.spin_cols=Spinner(values=['4','6','8','10','12'],text=str(session.grid_size[1]),
                                size_hint=(1,1),font_name='Nunito-Regular',font_size=sp(14),
                                background_color=C['bg3'],color=C['violet'])
        row_cols.add_widget(self.spin_cols)
        gc.add_widget(row_cols)
        inner.add_widget(gc)

        # ── Card 2: Entrenamiento ──
        pc=NeonCard(orientation='vertical',size_hint_y=None,height=dp(230),
                     padding=[dp(14),dp(12)],spacing=dp(8))
        pc.add_widget(section_title('Entrenamiento'))
        self.s_iter =NeonSlider('Iteraciones',100,1000,session.max_iter,50,'violet')
        self.s_clust=NeonSlider('Clusters K-Means',2,8,session.n_clusters,1,'pink')
        self.s_lr   =NeonSlider('Tasa aprendizaje',0.1,1.0,0.5,0.05,'amber','{:.2f}')
        for s in [self.s_iter,self.s_clust,self.s_lr]: pc.add_widget(s)
        inner.add_widget(pc)

        n=len(session.documents); ok=n>=2
        sc=NeonCard(orientation='horizontal',size_hint_y=None,height=dp(50),
                     padding=[dp(14),dp(8)],spacing=dp(10))
        sc.add_widget(ico(II['check'] if ok else II['warning'],size=sp(22),
                           color=C['green'] if ok else C['amber'],size_hint_x=None,width=dp(32)))
        col=BoxLayout(orientation='vertical',spacing=dp(2))
        col.add_widget(lbl(f'{n} doc{"s" if n!=1 else ""} {"listos" if ok else "cargados"}',
                            size=sp(12),color=C['green'] if ok else C['amber']))
        col.add_widget(lbl('Listo para entrenar' if ok else 'Necesitas al menos 2 docs',
                            size=sp(10),color=C['muted']))
        sc.add_widget(col); inner.add_widget(sc)

        self._pc=NeonCard(orientation='vertical',size_hint_y=None,height=dp(68),
                           padding=[dp(14),dp(10)],spacing=dp(6))
        prow=BoxLayout(size_hint_y=None,height=dp(20))
        self._pl=lbl('Listo para entrenar',size=sp(11),color=C['muted'])
        self._pct=lbl('',size=sp(11),color=C['cyan'],bold=True,
                       halign='right',size_hint_x=None,width=dp(40))
        prow.add_widget(self._pl); prow.add_widget(self._pct); self._pc.add_widget(prow)
        track=BoxLayout(size_hint_y=None,height=dp(6))
        apply_rounded_bg(track,C['bg3'],radius=dp(3))
        self._fill=Widget(size_hint=(0,1))
        with self._fill.canvas.before:
            Color(*C['cyan']); self._frr=RoundedRectangle(pos=self._fill.pos,
                                                            size=self._fill.size,radius=[dp(3)])
        self._fill.bind(pos=lambda w,v:setattr(self._frr,'pos',v),
                        size=lambda w,v:setattr(self._frr,'size',v))
        track.add_widget(self._fill); track.add_widget(Widget())
        self._pc.add_widget(track); inner.add_widget(self._pc)
        scroll.add_widget(inner); self.add_widget(scroll)

        bot=BoxLayout(size_hint_y=None,height=dp(52),padding=[dp(10),dp(4)])
        apply_bg(bot,C['bg'])
        self._btn=NeonButton(text='  Iniciar entrenamiento',style='primary',
                              text_color=(0.05,0.05,0.1,1),font_size=sp(14))
        self._btn.bind(on_press=lambda *_: self._start()); bot.add_widget(self._btn)
        self.add_widget(bot); slide_in(bot,delay=0.12)

    def _start(self):
        if self._training: return
        if len(session.documents)<2:
            self._err('Necesitas al menos 2 documentos.'); return
        session.grid_size=(int(self.spin_rows.text),int(self.spin_cols.text))
        session.max_iter=int(self.s_iter.value); session.n_clusters=int(self.s_clust.value)
        self._training=True; self._btn.text='  Entrenando...'; self._fill.size_hint_x=0
        def cb(pct,qe):
            def _u(*_):
                self._fill.size_hint_x=pct/100; self._pct.text=f'{pct}%'
                self._pl.text=f'Epoca {pct*session.max_iter//100}/{session.max_iter}  err:{qe:.3f}'
            Clock.schedule_once(_u)
        def worker():
            try:
                v=session.prepare()
                Clock.schedule_once(lambda *_: setattr(self._pl,'text',f'Vocabulario: {v} palabras'))
                session.train(callback=cb); Clock.schedule_once(lambda *_: self._done())
            except Exception as e: Clock.schedule_once(lambda *_,err=str(e): self._err(err))
        threading.Thread(target=worker,daemon=True).start()

    def _done(self):
        self._training=False; self._btn.text='  Completado'
        self._fill.size_hint_x=1; self._pct.text='100%'; self._popup_done()

    def _popup_done(self):
        qe=session.som.quantization_errors[-1] if session.som else 0
        ov=BoxLayout(orientation='vertical',padding=dp(16),spacing=dp(12))
        ov.add_widget(ico(II['check'],size=sp(40),color=C['green']))
        ov.add_widget(lbl(f'Entrenamiento completado\n\n'
                           f'Docs: {len(session.documents)}   '
                           f'Grilla: {session.grid_size[0]}x{session.grid_size[1]}\n'
                           f'Clusters: {session.n_clusters}   Error: {qe:.4f}',
                           size=sp(13),color=C['text'],halign='center'))
        btn=NeonButton(text='Ver mapa SOM',style='primary',text_color=(0.05,0.05,0.1,1),
                        size_hint_y=None,height=dp(44),font_size=sp(13))
        ov.add_widget(btn)
        popup=Popup(title='',content=ov,size_hint=(.88,.44),
                     background_color=C['bg2'],separator_height=0)
        btn.bind(on_press=lambda *_:(popup.dismiss(),
                                     self._shell._switch_tab('map') if self._shell else None))
        popup.open()

    def _err(self,msg):
        p=Popup(title='Error',size_hint=(.85,.28),background_color=C['bg2'],
                 content=lbl(msg,size=sp(12),color=C['pink'],halign='center'))
        p.open(); Clock.schedule_once(lambda *_: p.dismiss(),4)

# ── SOMCanvas ─────────────────────────────────────────────────────────────────
class SOMCanvas(Widget):
    def __init__(self,data,mode='clusters',**kw):
        super().__init__(**kw); self._data=data; self._mode=mode; self._on_select=None
        self.bind(pos=self._draw,size=self._draw); Clock.schedule_once(self._draw)
    def set_mode(self,mode): self._mode=mode; self._draw()
    def _draw(self,*_):
        if not self._data or not self.width or not self.height: return
        d=self._data; rows=d.get('grid_rows',8); cols=d.get('grid_cols',8)
        docs=d.get('documents',[]); umat=d.get('u_matrix',[])
        cw=self.width/cols; ch=self.height/rows
        self.canvas.clear()
        with self.canvas:
            Color(*C['bg2']); Rectangle(pos=self.pos,size=self.size)
            if self._mode=='umatrix' and umat:
                flat=[v for row in umat for v in row]; mx=max(flat) if flat else 1
                for r in range(rows):
                    for c in range(cols):
                        uv=umat[r][c]/(mx+1e-9); Color(uv*.4,uv*.1,uv*.9,.8)
                        Rectangle(pos=(self.x+c*cw,self.y+(rows-1-r)*ch),size=(cw,ch))
            elif self._mode=='hits':
                hmap={}
                for doc in docs: k=(doc['row'],doc['col']); hmap[k]=hmap.get(k,0)+1
                mh=max(hmap.values()) if hmap else 1
                for (r,c),h in hmap.items():
                    Color(.616,.361,1,h/mh*.7)
                    Rectangle(pos=(self.x+c*cw,self.y+(rows-1-r)*ch),size=(cw,ch))
            Color(*C['border'])
            for r in range(rows+1):
                y=self.y+r*ch; Line(points=[self.x,y,self.x+self.width,y],width=.5)
            for c in range(cols+1):
                x=self.x+c*cw; Line(points=[x,self.y,x,self.y+self.height],width=.5)
            for doc in docs:
                clr=C['clusters'][doc['cluster']%len(C['clusters'])]
                cx=self.x+doc['col']*cw+cw/2; cy=self.y+(rows-1-doc['row'])*ch+ch/2
                Color(clr[0],clr[1],clr[2],.15); Ellipse(pos=(cx-cw*.38,cy-ch*.38),size=(cw*.76,ch*.76))
                rs=dp(7); Color(clr[0],clr[1],clr[2],.9); Ellipse(pos=(cx-rs,cy-rs),size=(rs*2,rs*2))
                Color(clr[0],clr[1],clr[2],.4); Line(circle=(cx,cy,rs+dp(2)),width=1.2)

    def on_touch_down(self,touch):
        if not self.collide_point(*touch.pos) or not self._data: return super().on_touch_down(touch)
        d=self._data; rows=d.get('grid_rows',8); cols=d.get('grid_cols',8)
        cw=self.width/cols; ch=self.height/rows
        ci=int((touch.x-self.x)/cw); ri=rows-1-int((touch.y-self.y)/ch)
        for doc in d.get('documents',[]):
            if doc['row']==ri and doc['col']==ci:
                if self._on_select: self._on_select(doc)
        return True

# ── MapTab ────────────────────────────────────────────────────────────────────
class MapTab(BoxLayout):
    def __init__(self,shell=None,**kw):
        super().__init__(orientation='vertical',**kw)
        self._shell=shell; self._mode='clusters'; self._build()

    def _build(self):
        self.add_widget(make_header('Mapa SOM','Visualizacion topologica 2D',II['map']))
        if not session.positions:
            msg=BoxLayout(orientation='vertical',spacing=dp(14),padding=dp(24))
            msg.add_widget(ico(II['map'],size=sp(48),color=C['violet']))
            msg.add_widget(lbl('El mapa SOM estara disponible\ndespues de entrenar.\n\n'
                                '1. Agrega textos en Docs\n2. Configura y entrena\n3. Vuelve aqui',
                                size=sp(13),color=C['muted'],halign='center'))
            btn=NeonButton(text='Ir a Entrenar',style='outline',text_color=C['cyan'],
                            size_hint_y=None,height=dp(44),font_size=sp(13))
            btn.bind(on_press=lambda *_: self._shell._switch_tab('train') if self._shell else None)
            msg.add_widget(btn); self.add_widget(msg); return

        data=session.get_map_data()
        tb=BoxLayout(size_hint_y=None,height=dp(36),padding=[dp(10),dp(4)],spacing=dp(6))
        apply_bg(tb,C['bg'])
        self._mbtns={}
        for mode,label_text in [('clusters','Clusters'),('umatrix','U-Matrix'),('hits','Hits')]:
            act=(mode==self._mode)
            b=NeonButton(text=label_text,style='teal' if act else 'sm',
                          text_color=C['cyan'] if act else C['text'],size_hint=(1,1),font_size=sp(10))
            b.bind(on_press=lambda _,m=mode: self._set_mode(m))
            self._mbtns[mode]=b; tb.add_widget(b)
        self.add_widget(tb)

        leg_s=ScrollView(size_hint=(1,None),height=dp(40))
        leg=BoxLayout(orientation='horizontal',size_hint_x=None,spacing=dp(10),padding=[dp(10),dp(6)])
        leg.bind(minimum_width=leg.setter('width'))
        for i in range(session.n_clusters):
            clr=C['clusters'][i%len(C['clusters'])]
            words=data['top_words'].get(i,[])[:2]
            it=BoxLayout(size_hint_x=None,width=dp(110),spacing=dp(5))
            it.add_widget(ColorDot(color=clr,size_hint=(None,None),size=(dp(8),dp(8)),
                                    pos_hint={'center_y':.5}))
            it.add_widget(lbl(', '.join(words) if words else f'Cluster {i}',size=sp(9)))
            leg.add_widget(it)
        leg_s.add_widget(leg); self.add_widget(leg_s)

        self._canvas=SOMCanvas(data=data,mode=self._mode,size_hint=(1,1))
        self.add_widget(self._canvas)

        self._icard=NeonCard(orientation='horizontal',size_hint_y=None,height=dp(44),
                              padding=[dp(12),dp(8)],spacing=dp(8))
        self._icard.opacity=0
        self._idoc=lbl('--',size=sp(12),bold=True)
        self._imeta=lbl('',size=sp(10),color=C['muted'],halign='right',
                          size_hint_x=None,width=dp(80))
        self._icard.add_widget(self._idoc); self._icard.add_widget(self._imeta)
        self.add_widget(self._icard)
        def on_sel(doc):
            self._idoc.text=f'[b]{doc["title"]}[/b]'; self._idoc.markup=True
            self._imeta.text=f'C{doc["cluster"]} [{doc["row"]},{doc["col"]}]'
            Animation(opacity=1,d=0.18).start(self._icard)
        self._canvas._on_select=on_sel

        act=BoxLayout(size_hint_y=None,height=dp(44),padding=[dp(10),dp(5)])
        apply_bg(act,C['bg'])
        ba=NeonButton(text='Ir a Analisis',style='outline',text_color=C['cyan'],font_size=sp(12))
        ba.bind(on_press=lambda *_: self._shell._switch_tab('analysis') if self._shell else None)
        act.add_widget(ba); self.add_widget(act)

    def _set_mode(self,mode):
        self._mode=mode
        for k,b in self._mbtns.items():
            act=(k==mode); b._style='teal' if act else 'sm'
            b.color=C['cyan'] if act else C['text']; b._draw()
        if hasattr(self,'_canvas'): self._canvas.set_mode(mode)

# ── ConvergenceChart ──────────────────────────────────────────────────────────
class ConvergenceChart(Widget):
    def __init__(self,qe,**kw):
        super().__init__(**kw); self._qe=qe
        self.bind(pos=self._draw,size=self._draw); Clock.schedule_once(self._draw)
    def _draw(self,*_):
        if not self._qe or len(self._qe)<2 or not self.width: return
        data=self._qe; mn,mx=min(data),max(data); rng=mx-mn or 1; n=len(data)
        self.canvas.clear()
        with self.canvas:
            Color(*C['bg3']); RoundedRectangle(pos=self.pos,size=self.size,radius=[dp(6)])
            bw=max(1,self.width/n-1)
            for i,v in enumerate(data):
                h=((v-mn)/rng)*self.height*.85+self.height*.05
                Color(.616,.361,1,.35+.65*(v-mn)/rng)
                RoundedRectangle(pos=(self.x+i*(self.width/n),self.y),size=(max(1,bw),h),radius=[dp(2)])
            pts=[]
            for i,v in enumerate(data):
                pts.extend([self.x+(i/(n-1))*self.width,
                             self.y+((v-mn)/rng)*self.height*.85+self.height*.05])
            if len(pts)>=4:
                Color(*C['cyan']); Line(points=pts,width=1.5)
                Color(*C['amber']); Ellipse(pos=(pts[-2]-dp(3),pts[-1]-dp(3)),size=(dp(6),dp(6)))

# ── AnalysisTab ───────────────────────────────────────────────────────────────
class AnalysisTab(BoxLayout):
    def __init__(self,shell=None,**kw):
        super().__init__(orientation='vertical',**kw)
        self._shell=shell; self._build()

    def _build(self):
        self.add_widget(make_header('Analisis','Metricas y palabras clave',II['analytics']))
        if not session.positions:
            msg=BoxLayout(orientation='vertical',spacing=dp(12),padding=dp(24))
            msg.add_widget(ico(II['analytics'],size=sp(40),color=C['violet']))
            msg.add_widget(lbl('Disponible luego de entrenar el SOM.',
                                size=sp(13),color=C['muted'],halign='center'))
            self.add_widget(msg); return

        data=session.get_map_data(); qe_h=data.get('qe_history',[])
        qe_f=qe_h[-1] if qe_h else 0; qe_i=qe_h[0] if qe_h else 0
        mejora=((qe_i-qe_f)/(qe_i+1e-9))*100

        scroll=ScrollView(size_hint=(1,1))
        inner=BoxLayout(orientation='vertical',spacing=dp(8),
                         padding=[dp(10),dp(8)],size_hint_y=None)
        inner.bind(minimum_height=inner.setter('height'))

        mg=GridLayout(cols=2,spacing=dp(8),size_hint_y=None,height=dp(118))
        for val,label_text,clr,icon_code in [
            (f'{qe_f:.3f}','Error final',C['cyan'],II['pulse']),
            (f'{qe_i:.3f}','Error inicial',C['violet'],II['pulse']),
            (f'{mejora:.1f}%','Mejora',C['green'],II['check']),
            (str(data['n_docs']),'Documentos',C['amber'],II['docs'])]:
            card=NeonCard(orientation='vertical',padding=[dp(10),dp(8)],spacing=dp(3))
            hr=BoxLayout(size_hint_y=None,height=dp(22),spacing=dp(5))
            hr.add_widget(ico(icon_code,size=sp(13),color=clr,size_hint_x=None,width=dp(16)))
            hr.add_widget(lbl(label_text,size=sp(9),color=C['muted']))
            card.add_widget(hr)
            card.add_widget(lbl(val,size=sp(18),bold=True,color=clr))
            mg.add_widget(card)
        inner.add_widget(mg)

        if qe_h:
            cc=NeonCard(orientation='vertical',size_hint_y=None,height=dp(124),
                         padding=[dp(12),dp(10)],spacing=dp(4))
            cc.add_widget(section_title('Convergencia del SOM'))
            cc.add_widget(ConvergenceChart(qe_h,size_hint_y=None,height=dp(78)))
            er=BoxLayout(size_hint_y=None,height=dp(14))
            er.add_widget(lbl('Epoca 0',size=sp(8),color=C['muted']))
            er.add_widget(lbl(f'Epoca {session.max_iter}',size=sp(8),color=C['muted'],halign='right'))
            cc.add_widget(er); inner.add_widget(cc)

        kc=NeonCard(orientation='vertical',size_hint_y=None,
                     height=dp(28+56*session.n_clusters),padding=[dp(12),dp(10)],spacing=dp(8))
        kc.add_widget(section_title('Palabras clave por cluster'))
        for cl_id,words in data['top_words'].items():
            clr=C['clusters'][cl_id%len(C['clusters'])]
            cb=BoxLayout(orientation='vertical',size_hint_y=None,height=dp(50),spacing=dp(4))
            hr=BoxLayout(size_hint_y=None,height=dp(20),spacing=dp(6))
            hr.add_widget(ColorDot(color=clr,size_hint=(None,None),size=(dp(8),dp(8)),pos_hint={'center_y':.5}))
            n_cl=len([d for d in data['documents'] if d['cluster']==cl_id])
            hr.add_widget(lbl(f'[b]Cluster {cl_id}[/b]  ({n_cl} docs)',markup=True,size=sp(11),color=clr))
            cb.add_widget(hr)
            chips=BoxLayout(size_hint_y=None,height=dp(24),spacing=dp(4))
            for w in words[:5]:
                chips.add_widget(Badge(color_key='violet' if cl_id%2 else 'cyan',
                                        text=f'#{w}',size_hint=(None,None),height=dp(18)))
            chips.add_widget(Widget()); cb.add_widget(chips); kc.add_widget(cb)
        inner.add_widget(kc)
        inner.add_widget(Widget(size_hint_y=None,height=dp(8)))
        scroll.add_widget(inner); self.add_widget(scroll)

        btn=NeonButton(text='  Guardar sesion JSON',style='outline',text_color=C['cyan'],
                        size_hint_y=None,height=dp(44),font_size=sp(13))
        btn.bind(on_press=lambda *_: self._save()); self.add_widget(btn)

    def _save(self):
        try:
            path=os.path.join(os.path.expanduser('~'),'storymapsom_session.json')
            session.save_session(path)
            p=Popup(title='',size_hint=(.85,.22),background_color=C['bg2'],
                     content=lbl(f'Guardado:\n{path}',size=sp(11),color=C['green'],halign='center'))
            p.open(); Clock.schedule_once(lambda *_: p.dismiss(),3)
        except Exception as e:
            p=Popup(title='Error',size_hint=(.85,.22),background_color=C['bg2'],
                     content=lbl(str(e),size=sp(11),color=C['pink'])); p.open()

# ── ConfigTab ─────────────────────────────────────────────────────────────────
class ConfigTab(BoxLayout):
    def __init__(self,shell=None,**kw):
        super().__init__(orientation='vertical',**kw)
        self._shell=shell; self._build()

    def _build(self):
        self.add_widget(make_header('Configuracion','Ajustes y sesion',II['settings']))
        scroll=ScrollView(size_hint=(1,1))
        inner=BoxLayout(orientation='vertical',spacing=dp(4),
                         padding=[dp(10),dp(10)],size_hint_y=None)
        inner.bind(minimum_height=inner.setter('height'))

        def cfg_row(icon_code, clr, tt, st, right=None):
            row=NeonCard(orientation='horizontal',size_hint_y=None,height=dp(58),
                          padding=[dp(12),dp(8)],spacing=dp(10))
            row.add_widget(ico_box(icon_code,clr,box_size=dp(36),ico_size=sp(17)))
            col=BoxLayout(orientation='vertical',spacing=dp(2))
            col.add_widget(lbl(tt,size=sp(12),bold=True))
            col.add_widget(lbl(st,size=sp(10),color=C['muted']))
            row.add_widget(col)
            row.add_widget(right if right else ico(II['arrow_r'],size=sp(18),color=C['muted'],
                                                    size_hint_x=None,width=dp(20)))
            return row

        def toggle(on=True):
            box=BoxLayout(size_hint=(None,None),size=(dp(42),dp(24)))
            cy=list(C['cyan'][:3])+[0.15]
            cy2=list(C['cyan'][:3])+[0.50]
            with box.canvas.before:
                Color(*(cy if on else list(C['bg4'])))
                rr=RoundedRectangle(pos=box.pos,size=box.size,radius=[dp(12)])
                Color(*(cy2 if on else list(C['border'])))
                ln=Line(rounded_rectangle=[*box.pos,*box.size,dp(12)],width=1)
            def _p(w,v): rr.pos=v;  ln.rounded_rectangle=[*v,*w.size,dp(12)]
            def _s(w,v): rr.size=v; ln.rounded_rectangle=[*w.pos,*v,dp(12)]
            box.bind(pos=_p,size=_s)
            th=Widget(size_hint=(None,None),size=(dp(18),dp(18)),pos_hint={'center_y':.5})
            ox=dp(20) if on else dp(3)
            with th.canvas:
                Color(*(C['cyan'] if on else C['muted']))
                th._e=Ellipse(pos=(th.x+ox,th.y+dp(3)),size=(dp(18),dp(18)))
            box.add_widget(th); return box

        inner.add_widget(section_title('SESION'))
        rs=cfg_row(II['save'],C['cyan'],'Guardar sesion','Exportar .json con datos')
        rs.bind(on_touch_down=lambda w,t: self._save_touch(w,t))
        inner.add_widget(rs)
        inner.add_widget(cfg_row(II['download'],C['violet'],'Cargar sesion','Importar sesion guardada'))

        inner.add_widget(Widget(size_hint_y=None,height=dp(6)))
        inner.add_widget(section_title('VISUALIZACION'))
        for icon_code,clr,tt,st,on in [
            (II['layers'],  C['amber'], 'Mostrar U-Matrix',      'Fronteras de clusters',      True),
            (II['pulse'],   C['green'], 'Curva de convergencia', 'Graficar error',             True),
            (II['tag'],     C['pink'],  'Etiquetas en mapa',     'Nombres sobre celdas',       False),
        ]:
            inner.add_widget(cfg_row(icon_code,clr,tt,st,right=toggle(on)))

        inner.add_widget(Widget(size_hint_y=None,height=dp(6)))
        inner.add_widget(section_title('TEORIA SOM'))
        rt=cfg_row(II['code'],C['violet'],'Algoritmo de Kohonen','Ver formulas y explicacion')
        rt.bind(on_touch_down=lambda w,t: self._theory(w,t))
        inner.add_widget(rt)

        inner.add_widget(Widget(size_hint_y=None,height=dp(8)))
        inner.add_widget(section_title('PELIGRO'))
        rst=NeonButton(text='  Reiniciar sesion completa',style='danger',
                        text_color=C['pink'],size_hint_y=None,height=dp(44),font_size=sp(12))
        rst.bind(on_press=lambda *_: self._confirm_reset())
        inner.add_widget(rst)
        inner.add_widget(Widget(size_hint_y=None,height=dp(8)))

        inner.add_widget(section_title('ACERCA DE'))
        ab=NeonButton(text='  Acerca de StoryMap SOM',style='outline',text_color=C['violet'],
                       size_hint_y=None,height=dp(44),font_size=sp(12))
        ab.bind(on_press=lambda *_: self._about())
        inner.add_widget(ab)

        inner.add_widget(Widget(size_hint_y=None,height=dp(8)))
        inner.add_widget(lbl('v1.0.0  Python 3.11.9  Kivy 2.3.0',
                              size=sp(9),color=C['muted'],halign='center',
                              size_hint_y=None,height=dp(22)))
        scroll.add_widget(inner); self.add_widget(scroll)

    def _save_touch(self,w,t):
        if w.collide_point(*t.pos):
            try:
                path=os.path.join(os.path.expanduser('~'),'storymapsom_session.json')
                session.save_session(path)
                p=Popup(title='',size_hint=(.85,.22),background_color=C['bg2'],
                         content=lbl(f'Guardado:\n{path}',size=sp(11),color=C['green'],halign='center'))
                p.open(); Clock.schedule_once(lambda *_: p.dismiss(),3)
            except: pass

    def _theory(self,w,t):
        if not w.collide_point(*t.pos): return
        ov=BoxLayout(orientation='vertical',padding=dp(14),spacing=dp(8))
        ov.add_widget(lbl(
            '[b]SOM de Kohonen (1982)[/b]\n\n'
            'Red neuronal no supervisada que aprende\n'
            'una representacion topologica 2D.\n\n'
            '[b]Actualizacion de pesos:[/b]\n'
            'Dw = lr(t) * h(i,t) * (x - w)\n\n'
            '[b]Decaimiento exponencial:[/b]\n'
            'lr(t) = lr0 * exp(-t / lambda)\n'
            'sigma(t) = s0 * exp(-t / lambda_s)\n\n'
            '[b]Vecindad gaussiana:[/b]\n'
            'h(i,t) = exp(-d^2 / 2*sigma(t)^2)',
            markup=True,size=sp(12),color=C['text'],halign='left',valign='top'))
        btn=NeonButton(text='Cerrar',style='outline',text_color=C['cyan'],
                        size_hint_y=None,height=dp(40))
        ov.add_widget(btn)
        popup=Popup(title='Algoritmo de Kohonen',content=ov,
                     size_hint=(.9,.68),background_color=C['bg2'])
        btn.bind(on_press=popup.dismiss); popup.open()

    def _about(self):
        ov=BoxLayout(orientation='vertical',padding=dp(16),spacing=dp(12))
        apply_bg(ov,C['bg2'])
        ov.add_widget(lbl('StoryMap SOM v1.0',size=sp(16),color=C['cyan'],
                            bold=True,halign='center',size_hint_y=None,height=dp(28)))
        ov.add_widget(Widget(size_hint_y=None,height=dp(4)))
        for linea in [
            ('[b]Autores:[/b] Santiago Castaneda  |  Santiago Florez', C['text']),
            ('[b]Tecnica IA:[/b] Self-Organizing Map (Red de Kohonen, 1982)', C['text']),
            ('[b]NLP:[/b] TF-IDF + Clustering K-Means', C['text']),
            ('[b]Framework:[/b] Kivy + Python 3.11', C['text']),
            ('Computacion Blanda - 2026', C['muted']),
        ]:
            ov.add_widget(lbl(linea[0],markup=True,size=sp(12),color=linea[1],
                               halign='center',size_hint_y=None,height=dp(36)))
        btn=NeonButton(text='Cerrar',style='violet',text_color=C['violet'],
                        size_hint_y=None,height=dp(44))
        ov.add_widget(btn)
        popup=Popup(title='Acerca de StoryMap SOM',content=ov,
                     size_hint=(.9,.72),background_color=C['bg2'],
                     title_color=C['cyan'],title_size=sp(14))
        btn.bind(on_press=popup.dismiss); popup.open()

    def _confirm_reset(self):
        ov=BoxLayout(orientation='vertical',padding=dp(14),spacing=dp(12))
        ov.add_widget(lbl('Reiniciar toda la sesion?\nSe perderan todos los documentos\n'
                           'y el modelo entrenado.',size=sp(13),color=C['text'],halign='center'))
        btns=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(8))
        bn=NeonButton(text='Cancelar',style='sm')
        by=NeonButton(text='Confirmar reset',style='danger',text_color=C['pink'])
        btns.add_widget(bn); btns.add_widget(by); ov.add_widget(btns)
        popup=Popup(title='Confirmar',content=ov,size_hint=(.85,.36),background_color=C['bg2'])
        def do(*_): session.clear(); popup.dismiss()
        by.bind(on_press=do); bn.bind(on_press=popup.dismiss); popup.open()

# ── App ───────────────────────────────────────────────────────────────────────
class StoryMapApp(App):
    def build(self):
        self.title='StoryMap SOM'
        sm=ScreenManager(transition=FadeTransition(duration=0.2))
        sm.add_widget(AppShell(name='app'))
        return sm
    def on_pause(self):  return True
    def on_resume(self): pass

if __name__=='__main__':
    StoryMapApp().run()
