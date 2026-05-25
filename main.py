"""
StoryMap SOM -- Aplicación principal Kivy
Explorador visual de textos usando Self-Organizing Maps

Autores: Santiago Castañeda & Santiago Florez
Curso: Computación Blanda -- Proyecto Final
"""

import os
import sys
import threading
from kivy.config import Config

# Evita que el clic derecho cree puntos rojos de multitouch
Config.set('input', 'mouse', 'mouse,disable_multitouch')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line, Ellipse
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.animation import Animation
from kivy.properties import StringProperty
from kivy.utils import get_color_from_hex, platform
import random
import math
import re

# ??? Importar núcleo IA ??????????????????????????????????????????????????????
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.som_engine import StorySession, DEMO_STORIES

# ??? Paleta de colores ????????????????????????????????????????????????????????
C = {
    "bg":       get_color_from_hex("#0D0F1A"),
    "bg2":      get_color_from_hex("#141728"),
    "card":     get_color_from_hex("#1C2040"),
    "card2":    get_color_from_hex("#232850"),
    "accent":   get_color_from_hex("#7C5CBF"),
    "accent2":  get_color_from_hex("#A87CF0"),
    "gold":     get_color_from_hex("#F0C060"),
    "teal":     get_color_from_hex("#4EC9C0"),
    "rose":     get_color_from_hex("#E07090"),
    "green":    get_color_from_hex("#60D080"),
    "text":     get_color_from_hex("#E8E8F4"),
    "subtext":  get_color_from_hex("#9090B0"),
    "border":   get_color_from_hex("#2A2F55"),
    "white":    (1, 1, 1, 1),
    "clusters": [
        get_color_from_hex("#FF6B9D"),
        get_color_from_hex("#7C5CBF"),
        get_color_from_hex("#4EC9C0"),
        get_color_from_hex("#F0C060"),
        get_color_from_hex("#60D080"),
        get_color_from_hex("#FF9F43"),
        get_color_from_hex("#54A0FF"),
        get_color_from_hex("#EE5A24"),
    ],
}

Window.clearcolor = C["bg"]
IS_ANDROID = platform == "android"
UI_SCALE = 1.08 if IS_ANDROID else 1.0

Window.minimum_width = dp(360)
Window.minimum_height = dp(640)

# ??? Sesión global ????????????????????????????????????????????????????????????
session = StorySession()

# ??? Utilidades visuales ??????????????????????????????????????????????????????

def hex_color(h):
    return get_color_from_hex(h)

def blend(c1, c2, t):
    """Mezcla dos colores RGBA."""
    return tuple((a * (1 - t) + b * t) for a, b in zip(c1, c2))

def animate_widget_entrance(widget, delay=0.0, dy=dp(10), duration=0.22):
    """Animación de entrada suave para widgets.
    BUG FIX: se difiere la captura de 'y' hasta después del layout.
    """
    def _start(*_):
        try:
            widget.opacity = 0
            oy = widget.y
            widget.y = oy - dy
            anim = Animation(opacity=1, y=oy, d=duration, t='out_quad')
            anim.start(widget)
        except Exception:
            pass
    Clock.schedule_once(_start, delay)

def rgba_bg(widget, color):
    """Aplica un fondo de color sólido a cualquier widget."""
    with widget.canvas.before:
        Color(*color)
        widget._bg_rect = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(pos=lambda w, v: setattr(w._bg_rect, 'pos', v),
                size=lambda w, v: setattr(w._bg_rect, 'size', v))

def rounded_bg(widget, color, radius=dp(12)):
    with widget.canvas.before:
        Color(*color)
        widget._rnd_rect = RoundedRectangle(pos=widget.pos, size=widget.size,
                                             radius=[radius])
    widget.bind(pos=lambda w, v: setattr(w._rnd_rect, 'pos', v),
                size=lambda w, v: setattr(w._rnd_rect, 'size', v))


class StyledButton(Button):
    """Botón estilizado con fondo redondeado."""
    def __init__(self, bg_color=None, text_color=None, radius=dp(10), **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0)
        self.color = text_color or C["text"]
        self.font_size = sp(14 * UI_SCALE)
        self._bg = bg_color or C["accent"]
        self._base_bg = self._bg
        self._radius = radius
        self.bind(pos=self._draw, size=self._draw)
        self.bind(disabled=self._on_disabled)
        Clock.schedule_once(self._draw)

    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            # Sombra
            Color(0, 0, 0, 0.25)
            RoundedRectangle(pos=(self.x, self.y - dp(2)), size=self.size, radius=[self._radius])
            # Fondo principal
            Color(*self._bg)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[self._radius])
            # Borde
            Color(*blend(self._bg, C["white"], 0.35))
            Line(rounded_rectangle=[self.x, self.y, self.width, self.height, self._radius], width=1)

    def _on_disabled(self, *_):
        self._bg = blend(self._base_bg, C["bg2"], 0.55) if self.disabled else self._base_bg
        self._draw()

    def on_press(self):
        self._bg = blend(self._base_bg, C["white"], 0.08)
        self._draw()
        Animation(opacity=0.75, duration=0.05).start(self)

    def on_release(self):
        self._bg = self._base_bg
        self._draw()
        Animation(opacity=1.0, duration=0.1).start(self)


class SectionTitle(Label):
    def __init__(self, **kwargs):
        kwargs.setdefault('font_size', sp(18))
        kwargs.setdefault('bold', True)
        kwargs.setdefault('color', C["accent2"])
        kwargs.setdefault('size_hint_y', None)
        kwargs.setdefault('height', dp(36))
        kwargs.setdefault('halign', 'left')
        kwargs.setdefault('valign', 'middle')
        super().__init__(**kwargs)
        self.bind(size=lambda w, v: setattr(w, 'text_size', v))


class CardBox(BoxLayout):
    """BoxLayout con fondo de tarjeta."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._draw, size=self._draw)
        Clock.schedule_once(self._draw)

    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            # Capa inferior (profundidad)
            Color(0, 0, 0, 0.18)
            RoundedRectangle(pos=(self.x, self.y - dp(2)), size=self.size, radius=[dp(12)])
            # Fondo tarjeta
            Color(*C["card"])
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
            # Brillo superior sutil
            Color(1, 1, 1, 0.03)
            RoundedRectangle(pos=(self.x, self.y + self.height * 0.5),
                             size=(self.width, self.height * 0.5), radius=[dp(12)])
            Color(*C["border"])
            Line(rounded_rectangle=[self.x, self.y, self.width, self.height, dp(12)], width=1)


# ??? PANTALLA: Bienvenida ?????????????????????????????????????????????????????

class WelcomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._stars = []
        self._time = 0
        self._build_ui()
        Clock.schedule_interval(self._animate, 1/30)
        # Efecto typewriter de bienvenida (sin emojis)
        self._greet_text = "Hola -- soy MapBot. Te acompano en la exploracion [>>]"
        self._greet_idx = 0
        self._greet_event = None
        Clock.schedule_once(self._start_greeting, 0.6)

    def _start_greeting(self, *_):
        self._greet_event = Clock.schedule_interval(self._type_greeting, 0.04)

    def on_enter(self, *a):
        # Pequeño glow en el botón principal al entrar
        for w in self.walk(restrict=False):
            if isinstance(w, StyledButton) and w.text and 'EXPLORAR' in w.text:
                orig = w._base_bg
                def glow(btn=w):
                    btn._bg = C['accent2']
                    btn._draw()
                def unglow(btn=w, o=orig):
                    btn._bg = o
                    btn._draw()
                Clock.schedule_once(lambda *_: glow(), 0.02)
                Clock.schedule_once(lambda *_: unglow(), 0.4)
                break
        if hasattr(self, 'personality') and self.personality:
            self.personality.opacity = 0
            Animation(opacity=1, d=0.35, t='out_quad').start(self.personality)

    def _build_ui(self):
        # BUG FIX: usar BoxLayout como root en lugar de FloatLayout para que
        # el layout sea predecible sin necesitar pos_hint en cada widget.
        root = BoxLayout(orientation='vertical', padding=dp(24 * UI_SCALE),
                         spacing=dp(14 * UI_SCALE))
        rgba_bg(root, C["bg"])

        # Canvas de partículas (widget flotante encima)
        self._canvas_widget = Widget(size_hint=(1, 1), pos=(0, 0))
        # Se agrega al Screen directamente para que quede "detrás" del contenido visual
        # pero animado independientemente
        self.add_widget(self._canvas_widget)

        # Logo / título
        title_box = BoxLayout(orientation='vertical', size_hint_y=None,
                              height=dp(140), spacing=dp(6))

        # BUG FIX: reemplazado emoji por símbolo unicode
        icon_lbl = Label(
            text="SOM",  # icono principal
            font_size=sp(64 * UI_SCALE),
            size_hint_y=None, height=dp(80),
            color=C["accent2"],
        )
        title_box.add_widget(icon_lbl)

        title = Label(
            text="[b]StoryMap SOM[/b]",
            markup=True,
            font_size=sp(30 * UI_SCALE),
            color=C["accent2"],
            size_hint_y=None, height=dp(44),
        )
        title_box.add_widget(title)
        root.add_widget(title_box)

        # Subtítulo
        sub = Label(
            text="[i]Explorador Visual de Textos\nmediante Self-Organizing Maps[/i]",
            markup=True,
            font_size=sp(14 * UI_SCALE),
            color=C["subtext"],
            halign='center',
            size_hint_y=None, height=dp(48),
        )
        sub.bind(size=lambda w, v: setattr(w, 'text_size', v))
        root.add_widget(sub)

        # Autores -- BUG FIX: emoji de persona reemplazado por símbolo
        authors = Label(
            text=">>  Santiago Castaneda  .  Santiago Florez\n"
                 "Computacion Blanda -- Proyecto Final",
            font_size=sp(12 * UI_SCALE),
            color=C["gold"],
            halign='center',
            size_hint_y=None, height=dp(46),
        )
        authors.bind(size=lambda w, v: setattr(w, 'text_size', v))
        root.add_widget(authors)

        root.add_widget(Widget(size_hint_y=None, height=dp(8)))

        # Info cards
        info_scroll = ScrollView(size_hint=(1, None), height=dp(130))
        info_grid = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, padding=[0, 4])
        info_grid.bind(minimum_height=info_grid.setter('height'))

        # BUG FIX: todos los iconos son texto ASCII/unicode
        features = [
            ("*", "Self-Organizing Map\n(Red de Kohonen)"),
            ("=", "Vectores TF-IDF\ncon NLP"),
            ("(o)", "Clustering K-Means\nautomatico"),
            ("[F]", "Carga archivos .txt\ndesde el dispositivo"),
        ]
        for icon, text in features:
            card = CardBox(orientation='vertical', padding=dp(10), spacing=dp(4),
                           size_hint_y=None, height=dp(56))
            card.add_widget(Label(text=f"{icon} {text}", font_size=sp(11),
                                   color=C["text"], halign='center', markup=False))
            info_grid.add_widget(card)

        info_scroll.add_widget(info_grid)
        root.add_widget(info_scroll)

        root.add_widget(Widget(size_hint_y=1))

        # Botón principal
        btn_main = StyledButton(
            text=">> EXPLORAR AHORA",
            bg_color=C["accent"],
            size_hint=(0.85, None),
            height=dp(52),
            pos_hint={'center_x': 0.5},
            font_size=sp(16 * UI_SCALE),
            bold=True,
        )
        btn_main.bind(on_press=lambda *_: self._go_main())
        root.add_widget(btn_main)

        # Personalidad: etiqueta typewriter
        self.personality = Label(
            text="",
            font_size=sp(12 * UI_SCALE), color=C["teal"],
            size_hint_y=None, height=dp(22), halign='center'
        )
        self.personality.bind(size=lambda w, v: setattr(w, 'text_size', v))
        root.add_widget(self.personality)

        # Botón demo
        btn_demo = StyledButton(
            text="Cargar Demo (12 cuentos)",
            bg_color=C["teal"],
            text_color=(0.05, 0.1, 0.1, 1),
            size_hint=(0.85, None),
            height=dp(44),
            pos_hint={'center_x': 0.5},
            font_size=sp(13 * UI_SCALE),
        )
        btn_demo.bind(on_press=lambda *_: self._load_demo())
        root.add_widget(btn_demo)

        root.add_widget(Widget(size_hint_y=None, height=dp(16)))
        self.add_widget(root)

        # Animaciones de entrada (diferidas para que el layout ya esté listo)
        for i, w in enumerate([title_box, sub, authors, info_scroll, btn_main,
                                self.personality, btn_demo]):
            animate_widget_entrance(w, delay=0.08 + 0.05 * i)

    def _go_main(self):
        self.manager.transition = SlideTransition(direction='left', duration=0.3)
        self.manager.current = 'main'

    def _load_demo(self):
        session.clear()
        for title, text in DEMO_STORIES:
            session.add_document(title, text)
        popup = Popup(
            title='[OK] Demo cargado',
            content=Label(
                text=f"Se cargaron [b]{len(DEMO_STORIES)} cuentos clasicos[/b].\n\n"
                     "Ve a la seccion de [b]Documentos[/b] para ver\n"
                     "la lista, o a [b]Entrenar SOM[/b] para comenzar.",
                markup=True, halign='center', color=C["text"]
            ),
            size_hint=(0.85, 0.38),
            background_color=C["card"],
        )
        popup.open()
        Clock.schedule_once(lambda *_: popup.dismiss(), 3)
        self.manager.transition = SlideTransition(direction='left', duration=0.3)
        self.manager.current = 'main'

    def _animate(self, dt):
        self._time += dt
        w = self._canvas_widget
        if random.random() < 0.3 and len(self._stars) < 20:
            self._stars.append({
                'x': random.random(), 'y': random.random(),
                'r': random.uniform(1, 3), 'a': random.uniform(0.3, 1.0),
                'speed': random.uniform(0.2, 0.6),
            })
        w.canvas.clear()
        with w.canvas:
            for star in self._stars:
                star['y'] -= star['speed'] * dt / w.height if w.height > 0 else 0
                if star['y'] < 0:
                    star['y'] = 1
                alpha = star['a'] * (0.6 + 0.4 * math.sin(self._time * 2))
                Color(1, 1, 1, alpha)
                Ellipse(
                    pos=(star['x'] * w.width - star['r'], star['y'] * w.height - star['r']),
                    size=(star['r'] * 2, star['r'] * 2)
                )

    def _type_greeting(self, dt):
        """Efecto typewriter para el saludo inicial.
        BUG FIX: retorna False para cancelar el schedule_interval al terminar.
        """
        if not hasattr(self, 'personality') or self.personality is None:
            return False
        if self._greet_idx >= len(self._greet_text):
            return False  # Kivy cancela el interval al recibir False
        self._greet_idx += 1
        self.personality.text = self._greet_text[:self._greet_idx]
        return True  # continuar


# ??? PANTALLA: Principal (menú lateral) ??????????????????????????????????????

class MainScreen(Screen):
    current_tab = StringProperty('documents')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation='vertical')
        rgba_bg(root, C["bg"])

        # ?? Barra superior
        # BUG FIX: se usa un método _draw_bar separado y limpio en lugar de
        # bind con lambda anidado que acumulaba callbacks.
        topbar = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(52),
                           padding=[dp(12), dp(6)], spacing=dp(8))
        self._topbar = topbar
        self._apply_bar_bg(topbar, C["bg2"])

        back_btn = StyledButton(text="<", bg_color=C["card"],
                                size_hint=(None, 1), width=dp(40), font_size=sp(18))
        back_btn.bind(on_press=lambda *_: self._go_back())
        topbar.add_widget(back_btn)

        self.screen_title = Label(text="[b]StoryMap SOM[/b]", markup=True,
                                   font_size=sp(17), color=C["accent2"],
                                   halign='left', valign='middle')
        self.screen_title.bind(size=lambda w, v: setattr(w, 'text_size', v))
        topbar.add_widget(self.screen_title)

        info_btn = StyledButton(text="i", bg_color=C["card2"],
                                size_hint=(None, 1), width=dp(40), font_size=sp(16))
        info_btn.bind(on_press=lambda *_: self._show_about())
        topbar.add_widget(info_btn)

        root.add_widget(topbar)

        # ?? Navegación horizontal (tabs)
        nav = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(46),
                        padding=[dp(6), dp(4)], spacing=dp(6))
        self._nav = nav
        self._apply_bar_bg(nav, C["bg2"])

        self._tab_btns = {}
        tabs = [
            ('documents', 'Docs'),
            ('train',     'Entrenar'),
            ('map',       'Mapa'),
            ('analysis',  'Analisis'),
            ('settings',  'Config'),
        ]
        for key, label in tabs:
            btn = StyledButton(
                text=label,
                bg_color=C["accent"] if key == self.current_tab else C["card"],
                font_size=sp(11),
                size_hint=(1, 1),
            )
            btn.bind(on_press=lambda _, k=key: self._switch_tab(k))
            self._tab_btns[key] = btn
            nav.add_widget(btn)

        root.add_widget(nav)

        # ?? Contenido principal (cambia según tab)
        self.content_area = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        root.add_widget(self.content_area)

        self.add_widget(root)
        self._load_tab('documents')

    def _apply_bar_bg(self, widget, color):
        """Aplica y mantiene fondo de barra sin acumular callbacks.
        BUG FIX: un solo bind con redraw directo, sin Clock.schedule_once anidado.
        """
        with widget.canvas.before:
            _c = Color(*color)
            _r = Rectangle(pos=widget.pos, size=widget.size)
        widget.bind(
            pos=lambda w, v: setattr(_r, 'pos', v),
            size=lambda w, v: setattr(_r, 'size', v),
        )

    def _go_back(self):
        self.manager.transition = SlideTransition(direction='right', duration=0.3)
        self.manager.current = 'welcome'

    def _switch_tab(self, key):
        if key == self.current_tab:
            return
        self.current_tab = key
        for k, btn in self._tab_btns.items():
            btn._bg = C["accent"] if k == key else C["card"]
            btn._base_bg = btn._bg
            btn._draw()
        self.content_area.opacity = 0
        self._load_tab(key)
        Animation(opacity=1, d=0.16, t='out_quad').start(self.content_area)

    def _load_tab(self, key):
        self.content_area.clear_widgets()
        titles = {
            'documents': 'Documentos',
            'train':     'Entrenar SOM',
            'map':       'Mapa SOM',
            'analysis':  'Analisis',
            'settings':  'Configuracion',
        }
        self.screen_title.text = f"[b]{titles.get(key, 'StoryMap')}[/b]"

        if key == 'documents':
            self.content_area.add_widget(DocumentsTab())
        elif key == 'train':
            self.content_area.add_widget(TrainTab())
        elif key == 'map':
            self.content_area.add_widget(MapTab())
        elif key == 'analysis':
            self.content_area.add_widget(AnalysisTab())
        elif key == 'settings':
            self.content_area.add_widget(SettingsTab())

    def _show_about(self):
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(8))
        content.add_widget(Label(
            text="[b]StoryMap SOM v1.0[/b]\n\n"
                 "[b]Autores:[/b] Santiago Castaneda\n"
                 "              Santiago Florez\n\n"
                 "[b]Tecnica IA:[/b] Self-Organizing Map\n"
                 "(Red de Kohonen, 1982)\n\n"
                 "[b]NLP:[/b] TF-IDF + Clustering K-Means\n\n"
                 "[b]Framework:[/b] Kivy + Python 3.11\n\n"
                 "Computacion Blanda -- 2024",
            markup=True, font_size=sp(13), color=C["text"],
            halign='center', valign='top',
        ))
        btn = StyledButton(text="Cerrar", bg_color=C["accent"],
                           size_hint_y=None, height=dp(40))
        content.add_widget(btn)
        popup = Popup(title='Acerca de StoryMap SOM',
                      content=content, size_hint=(0.88, 0.7),
                      background_color=C["card"])
        btn.bind(on_press=popup.dismiss)
        popup.open()


# ??? TAB: Documentos ??????????????????????????????????????????????????????????

class DocumentsTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=dp(8), **kwargs)
        self._build()

    def _build(self):
        self.clear_widgets()

        # Barra de acciones
        action_bar = BoxLayout(orientation='horizontal', size_hint_y=None,
                               height=dp(42), spacing=dp(6))

        btn_add = StyledButton(text="+ Agregar texto", bg_color=C["accent"],
                               size_hint=(1, 1), font_size=sp(12))
        btn_add.bind(on_press=lambda *_: self._show_add_popup())
        action_bar.add_widget(btn_add)

        btn_file = StyledButton(text="Cargar .txt", bg_color=C["card2"],
                                size_hint=(1, 1), font_size=sp(12))
        btn_file.bind(on_press=lambda *_: self._load_file_popup())
        action_bar.add_widget(btn_file)

        btn_demo = StyledButton(text="Demo", bg_color=C["teal"],
                                text_color=(0.05, 0.1, 0.1, 1),
                                size_hint=(None, 1), width=dp(72), font_size=sp(12))
        btn_demo.bind(on_press=lambda *_: self._load_demo())
        action_bar.add_widget(btn_demo)

        btn_clear = StyledButton(text="Del", bg_color=C["rose"],
                                  size_hint=(None, 1), width=dp(44), font_size=sp(16))
        btn_clear.bind(on_press=lambda *_: self._confirm_clear())
        action_bar.add_widget(btn_clear)

        self.add_widget(action_bar)
        animate_widget_entrance(action_bar, delay=0.02)

        # Contador
        n = len(session.documents)
        ready = n >= 2
        _ready_str = "[OK] Listo para entrenar" if ready else "[!] Minimo 2 documentos"
        self.counter_lbl = Label(
            text=f"[b]{n}[/b] documento{'s' if n != 1 else ''}  -  {_ready_str}",
            markup=True, font_size=sp(12),
            color=C["green"] if ready else C["gold"],
            size_hint_y=None, height=dp(28), halign='left', valign='middle',
        )
        self.counter_lbl.bind(size=lambda w, v: setattr(w, 'text_size', v))
        self.add_widget(self.counter_lbl)
        animate_widget_entrance(self.counter_lbl, delay=0.04)

        # Lista de documentos
        scroll = ScrollView(size_hint=(1, 1))
        self.doc_list = GridLayout(cols=1, spacing=dp(6), size_hint_y=None, padding=[0, 4])
        self.doc_list.bind(minimum_height=self.doc_list.setter('height'))

        if not session.documents:
            empty = Label(
                text="Sin documentos.\nAgrega textos o carga el demo para comenzar.",
                font_size=sp(13), color=C["subtext"],
                halign='center', valign='middle',
                size_hint_y=None, height=dp(120),
            )
            empty.bind(size=lambda w, v: setattr(w, 'text_size', v))
            self.doc_list.add_widget(empty)
        else:
            for i, (title, text) in enumerate(zip(session.titles, session.documents)):
                self._add_doc_card(i, title, text)

        scroll.add_widget(self.doc_list)
        self.add_widget(scroll)
        animate_widget_entrance(scroll, delay=0.06)

    def _add_doc_card(self, idx, title, text):
        row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(64),
                        spacing=dp(6))

        card = CardBox(orientation='vertical', padding=[dp(10), dp(6)], spacing=dp(2),
                        size_hint=(1, 1))
        lbl_title = Label(text=f"[b]{title}[/b]", markup=True,
                           font_size=sp(13), color=C["accent2"],
                           halign='left', valign='middle',
                           size_hint_y=None, height=dp(22))
        lbl_title.bind(size=lambda w, v: setattr(w, 'text_size', v))
        card.add_widget(lbl_title)

        snippet = text[:80] + "..." if len(text) > 80 else text
        lbl_snippet = Label(text=snippet, font_size=sp(10), color=C["subtext"],
                             halign='left', valign='middle',
                             size_hint_y=None, height=dp(28))
        lbl_snippet.bind(size=lambda w, v: setattr(w, 'text_size', v))
        card.add_widget(lbl_snippet)
        row.add_widget(card)

        del_btn = StyledButton(text="Del", bg_color=C["rose"],
                                size_hint=(None, 1), width=dp(36), font_size=sp(16))
        del_btn.bind(on_press=lambda *_, i=idx: self._delete_doc(i))
        row.add_widget(del_btn)

        self.doc_list.add_widget(row)
        animate_widget_entrance(row, delay=0.02 * (idx % 8))

    def _delete_doc(self, idx):
        session.remove_document(idx)
        self._build()

    def _show_add_popup(self):
        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(10))
        content.add_widget(Label(text="Titulo del texto:", font_size=sp(13), color=C["text"],
                                  size_hint_y=None, height=dp(24)))
        title_inp = TextInput(
            hint_text="ej: Mi cuento favorito",
            multiline=False, size_hint_y=None, height=dp(40),
            background_color=C["card2"], foreground_color=C["text"],
            font_size=sp(13),
        )
        content.add_widget(title_inp)
        content.add_widget(Label(text="Contenido del texto:", font_size=sp(13), color=C["text"],
                                  size_hint_y=None, height=dp(24)))
        text_inp = TextInput(
            hint_text="Escribe o pega aqui el texto...",
            multiline=True,
            background_color=C["card2"], foreground_color=C["text"],
            font_size=sp(12),
        )
        content.add_widget(text_inp)

        btns = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        btn_cancel = StyledButton(text="Cancelar", bg_color=C["card2"])
        btn_add = StyledButton(text="+ Agregar", bg_color=C["accent"])
        btns.add_widget(btn_cancel)
        btns.add_widget(btn_add)
        content.add_widget(btns)

        popup = Popup(title='Agregar texto', content=content,
                      size_hint=(0.93, 0.8), background_color=C["card"])

        def do_add(*_):
            t = title_inp.text.strip() or f"Texto {len(session.documents)+1}"
            tx = text_inp.text.strip()
            if len(tx) < 10:
                title_inp.hint_text = "[!] El texto es muy corto!"
                return
            session.add_document(t, tx)
            popup.dismiss()
            self._build()

        btn_add.bind(on_press=do_add)
        btn_cancel.bind(on_press=popup.dismiss)
        popup.open()

    def _load_file_popup(self):
        """Popup para cargar archivo .txt."""
        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(10))
        content.add_widget(Label(
            text="Ingresa la ruta completa del archivo .txt:",
            font_size=sp(13), color=C["text"],
            size_hint_y=None, height=dp(36),
            halign='center',
        ))
        path_inp = TextInput(
            hint_text="/sdcard/Download/mi_cuento.txt",
            multiline=False, size_hint_y=None, height=dp(44),
            background_color=C["card2"], foreground_color=C["text"],
            font_size=sp(12),
        )
        content.add_widget(path_inp)

        content.add_widget(Label(text="Accesos rapidos:", font_size=sp(11),
                                  color=C["subtext"], size_hint_y=None, height=dp(20)))
        quick = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(6))
        for folder in ["/sdcard/Download", "/sdcard/Documents", "/storage/emulated/0/Download"]:
            short = folder.split("/")[-1]
            b = StyledButton(text=short, bg_color=C["card2"], font_size=sp(10))
            b.bind(on_press=lambda _, f=folder: setattr(path_inp, 'text', f + "/"))
            quick.add_widget(b)
        content.add_widget(quick)

        status_lbl = Label(text="", font_size=sp(11), color=C["rose"],
                            size_hint_y=None, height=dp(24), halign='center')
        content.add_widget(status_lbl)

        btns = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        btn_cancel = StyledButton(text="Cancelar", bg_color=C["card2"])
        btn_load = StyledButton(text="Cargar", bg_color=C["accent"])
        btns.add_widget(btn_cancel)
        btns.add_widget(btn_load)
        content.add_widget(btns)

        popup = Popup(title='Cargar archivo .txt', content=content,
                      size_hint=(0.93, 0.72), background_color=C["card"])

        def do_load(*_):
            path = path_inp.text.strip()
            if not os.path.exists(path):
                status_lbl.text = f"[X] Archivo no encontrado:\n{path}"
                return
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                title = os.path.basename(path).replace('.txt', '')
                session.add_document(title, text)
                popup.dismiss()
                self._build()
            except Exception as e:
                status_lbl.text = f"[X] Error: {str(e)[:60]}"

        btn_load.bind(on_press=do_load)
        btn_cancel.bind(on_press=popup.dismiss)
        popup.open()

    def _load_demo(self):
        session.clear()
        for title, text in DEMO_STORIES:
            session.add_document(title, text)
        self._build()

    def _confirm_clear(self):
        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(10))
        content.add_widget(Label(
            text="?Eliminar TODOS los documentos?",
            font_size=sp(14), color=C["text"], halign='center',
        ))
        btns = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        btn_no = StyledButton(text="Cancelar", bg_color=C["card2"])
        btn_yes = StyledButton(text="Borrar todo", bg_color=C["rose"])
        btns.add_widget(btn_no)
        btns.add_widget(btn_yes)
        content.add_widget(btns)
        popup = Popup(title='Confirmar', content=content,
                      size_hint=(0.8, 0.3), background_color=C["card"])

        def do_clear(*_):
            session.clear()
            popup.dismiss()
            self._build()

        btn_yes.bind(on_press=do_clear)
        btn_no.bind(on_press=popup.dismiss)
        popup.open()


# ??? TAB: Entrenar ????????????????????????????????????????????????????????????

class TrainTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=dp(10), **kwargs)
        self._training = False
        self._build()

    def _build(self):
        scroll = ScrollView()
        inner = BoxLayout(orientation='vertical', spacing=dp(10),
                           size_hint_y=None, padding=[0, 4])
        inner.bind(minimum_height=inner.setter('height'))

        inner.add_widget(SectionTitle(text="Parametros del SOM"))

        # Tamaño de grilla
        grid_card = CardBox(orientation='vertical', padding=dp(12), spacing=dp(6),
                             size_hint_y=None, height=dp(84))
        grid_card.add_widget(Label(
            text="Tamano de grilla (filas x cols)", font_size=sp(12),
            color=C["subtext"], size_hint_y=None, height=dp(20), halign='left'))
        grid_row = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(40))
        self.spin_rows = Spinner(values=['4', '6', '8', '10', '12'],
                                  text=str(session.grid_size[0]),
                                  size_hint=(1, 1), font_size=sp(14),
                                  background_color=C["accent"])
        self.spin_cols = Spinner(values=['4', '6', '8', '10', '12'],
                                  text=str(session.grid_size[1]),
                                  size_hint=(1, 1), font_size=sp(14),
                                  background_color=C["accent"])
        grid_row.add_widget(Label(text="Filas:", font_size=sp(12), color=C["text"],
                                   size_hint=(None, 1), width=dp(40)))
        grid_row.add_widget(self.spin_rows)
        grid_row.add_widget(Label(text="Cols:", font_size=sp(12), color=C["text"],
                                   size_hint=(None, 1), width=dp(40)))
        grid_row.add_widget(self.spin_cols)
        grid_card.add_widget(grid_row)
        inner.add_widget(grid_card)

        # Iteraciones
        iter_card = CardBox(orientation='vertical', padding=dp(12), spacing=dp(6),
                             size_hint_y=None, height=dp(84))
        self.iter_lbl = Label(
            text=f"Iteraciones de entrenamiento: [b]{session.max_iter}[/b]",
            markup=True, font_size=sp(12), color=C["subtext"],
            size_hint_y=None, height=dp(20), halign='left',
        )
        self.iter_lbl.bind(size=lambda w, v: setattr(w, 'text_size', v))
        iter_card.add_widget(self.iter_lbl)
        self.iter_slider = Slider(min=100, max=1000, value=session.max_iter, step=50,
                       value_track=True, value_track_color=C["accent"],
                       size_hint_y=None, height=dp(44))
        self.iter_slider.bind(value=self._on_iter_change)
        iter_card.add_widget(self.iter_slider)
        inner.add_widget(iter_card)

        # Clusters
        cluster_card = CardBox(orientation='vertical', padding=dp(12), spacing=dp(6),
                                size_hint_y=None, height=dp(84))
        self.clust_lbl = Label(
            text=f"Numero de clusters K-Means: [b]{session.n_clusters}[/b]",
            markup=True, font_size=sp(12), color=C["subtext"],
            size_hint_y=None, height=dp(20), halign='left',
        )
        self.clust_lbl.bind(size=lambda w, v: setattr(w, 'text_size', v))
        cluster_card.add_widget(self.clust_lbl)
        self.clust_slider = Slider(min=2, max=8, value=session.n_clusters, step=1,
                        value_track=True, value_track_color=C["gold"],
                        size_hint_y=None, height=dp(44))
        self.clust_slider.bind(value=self._on_cluster_change)
        cluster_card.add_widget(self.clust_slider)
        inner.add_widget(cluster_card)

        # Estado de documentos
        n = len(session.documents)
        status_card = CardBox(orientation='horizontal', padding=dp(12),
                               size_hint_y=None, height=dp(52))
        status_color = C["green"] if n >= 2 else C["rose"]
        status_icon = "[OK]" if n >= 2 else "[!]"
        status_card.add_widget(Label(
            text=f"{status_icon}  [b]{n}[/b] documento{'s' if n!=1 else ''} listo{'s' if n!=1 else ''}\n"
                 f"{'Listo para entrenar' if n >= 2 else 'Necesitas al menos 2 documentos'}",
            markup=True, font_size=sp(12), color=status_color,
            halign='left', valign='middle',
        ))
        inner.add_widget(status_card)

        # Progreso
        prog_card = CardBox(orientation='vertical', padding=dp(12), spacing=dp(6),
                             size_hint_y=None, height=dp(80))
        self.prog_lbl = Label(
            text="Listo para entrenar",
            font_size=sp(12), color=C["subtext"],
            size_hint_y=None, height=dp(22), halign='left',
        )
        self.prog_lbl.bind(size=lambda w, v: setattr(w, 'text_size', v))
        prog_card.add_widget(self.prog_lbl)
        self.prog_bar = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(12))
        prog_card.add_widget(self.prog_bar)
        inner.add_widget(prog_card)

        # Info teórica
        theory_card = CardBox(orientation='vertical', padding=dp(12), spacing=dp(4),
                               size_hint_y=None, height=dp(160))
        theory_card.add_widget(SectionTitle(text="¿Como funciona?"))
        theory_card.add_widget(Label(
            text="El [b]SOM de Kohonen[/b] aprende una proyeccion\n"
                 "topologica de vectores [b]TF-IDF[/b] al plano 2D.\n\n"
                 "- TF-IDF captura la importancia de cada palabra\n"
                 "- El SOM agrupa textos similares en neuronas cercanas\n"
                 "- K-Means colorea los grupos tematicos\n"
                 "- n(t) = n0.exp(-t/L)"
                 "   s(t) = s0.exp(-t/L_s)",
            markup=True, font_size=sp(11), color=C["subtext"],
            halign='left', valign='top',
        ))
        inner.add_widget(theory_card)

        scroll.add_widget(inner)
        self.add_widget(scroll)

        # Botón entrenar (fijo abajo)
        self.btn_train = StyledButton(
            text=">> ENTRENAR SOM",
            bg_color=C["accent"],
            size_hint_y=None, height=dp(52),
            font_size=sp(16 * UI_SCALE), bold=True,
        )
        self.btn_train.bind(on_press=lambda *_: self._start_training())
        self.add_widget(self.btn_train)
        animate_widget_entrance(self.btn_train, delay=0.08)

    def _on_iter_change(self, _, value):
        session.max_iter = int(value)
        self.iter_lbl.text = f"Iteraciones de entrenamiento: [b]{int(value)}[/b]"

    def _on_cluster_change(self, _, value):
        session.n_clusters = int(value)
        self.clust_lbl.text = f"Numero de clusters K-Means: [b]{int(value)}[/b]"

    def _start_training(self):
        if self._training:
            return
        if len(session.documents) < 2:
            self._show_error("Necesitas al menos 2 documentos.\nVe a la pestana 'Docs'.")
            return

        session.grid_size = (int(self.spin_rows.text), int(self.spin_cols.text))

        self._training = True
        self.btn_train.text = "... Entrenando..."
        self.btn_train._bg = C["card2"]
        self.btn_train._draw()
        self.prog_bar.value = 0

        def progress_cb(pct, qe):
            def _update(*_):
                self.prog_bar.value = pct
                self.prog_lbl.text = (
                    f"Progreso: {pct}%  -  Error de cuantizacion: {qe:.4f}"
                )
            Clock.schedule_once(_update)

        def worker():
            try:
                vocab_size = session.prepare()
                Clock.schedule_once(lambda *_: setattr(
                    self.prog_lbl, 'text',
                    f"Vocabulario: {vocab_size} palabras - Iniciando SOM..."
                ))
                session.train(callback=progress_cb)
                Clock.schedule_once(lambda *_: self._on_done())
            except Exception as e:
                Clock.schedule_once(lambda *_, err=str(e): self._on_error(err))

        threading.Thread(target=worker, daemon=True).start()

    def _on_done(self):
        self._training = False
        self.btn_train.text = "[OK] Entrenado"
        self.btn_train._bg = C["green"]
        self.btn_train._draw()
        self.prog_bar.value = 100
        self.prog_lbl.text = (
            f"Entrenamiento completo [OK]: {len(session.documents)} docs -> "
            f"{session.grid_size[0]}x{session.grid_size[1]} grilla"
        )
        self._show_done_popup()

    def _on_error(self, err):
        self._training = False
        self.btn_train.text = ">> ENTRENAR SOM"
        self.btn_train._bg = C["accent"]
        self.btn_train._draw()
        self._show_error(f"Error durante entrenamiento:\n{err}")

    def _show_done_popup(self):
        n_docs = len(session.documents)
        qe = session.som.quantization_errors[-1] if session.som else 0
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(8))
        content.add_widget(Label(
            text=f"[b]SOM entrenado exitosamente[/b]\n\n"
                  f"Documentos: {n_docs}\n"
                  f"Grilla: {session.grid_size[0]}x{session.grid_size[1]}\n"
                  f"Clusters: {session.n_clusters}\n"
                  f"Error final: {qe:.4f}\n\n"
                  f"Ve a la pestana [b][SOM] Mapa[/b] para visualizar.",
            markup=True, font_size=sp(13), color=C["text"],
            halign='center', valign='top',
        ))
        btn = StyledButton(text="Ver Mapa ->", bg_color=C["accent"],
                           size_hint_y=None, height=dp(44))
        content.add_widget(btn)
        popup = Popup(title='Entrenamiento completo',
                      content=content, size_hint=(0.88, 0.55),
                      background_color=C["card"])
        btn.bind(on_press=popup.dismiss)
        popup.open()

    def _show_error(self, msg):
        popup = Popup(title='Error', size_hint=(0.85, 0.35),
                      background_color=C["card"],
                      content=Label(text=msg, font_size=sp(13),
                                     color=C["rose"], halign='center'))
        popup.open()
        Clock.schedule_once(lambda *_: popup.dismiss(), 4)


# ??? TAB: Mapa SOM ????????????????????????????????????????????????????????????

class SOMMapWidget(Widget):
    """Canvas que dibuja el mapa SOM con puntos y U-Matrix."""

    def __init__(self, map_data, **kwargs):
        super().__init__(**kwargs)
        self.map_data = map_data
        self.bind(pos=self._draw, size=self._draw)
        Clock.schedule_once(self._draw)

    def _draw(self, *args):
        if not self.map_data or not self.width or not self.height:
            return
        data = self.map_data
        rows = data.get("grid_rows", 8)
        cols = data.get("grid_cols", 8)
        docs = data.get("documents", [])
        u_mat = data.get("u_matrix", [])

        self.canvas.clear()
        with self.canvas:
            # Fondo
            Color(*C["bg2"])
            Rectangle(pos=self.pos, size=self.size)

            cell_w = self.width / cols
            cell_h = self.height / rows

            # Dibujar U-Matrix
            if u_mat:
                flat = [v for row in u_mat for v in row]
                max_u = max(flat) if flat else 1
                for r in range(rows):
                    for c in range(cols):
                        u_val = u_mat[r][c] / (max_u + 1e-9)
                        Color(u_val * 0.3, u_val * 0.15, u_val * 0.5, 0.7)
                        x = self.x + c * cell_w
                        y = self.y + (rows - 1 - r) * cell_h
                        Rectangle(pos=(x, y), size=(cell_w, cell_h))

            # Grid
            Color(*C["border"])
            for r in range(rows + 1):
                y = self.y + r * cell_h
                Line(points=[self.x, y, self.x + self.width, y], width=0.5)
            for c in range(cols + 1):
                x = self.x + c * cell_w
                Line(points=[x, self.y, x, self.y + self.height], width=0.5)

            # Documentos
            for doc in docs:
                cluster = doc["cluster"]
                r_idx = doc["row"]
                c_idx = doc["col"]
                color = C["clusters"][cluster % len(C["clusters"])]

                cx = self.x + c_idx * cell_w + cell_w / 2
                cy = self.y + (rows - 1 - r_idx) * cell_h + cell_h / 2

                # Halo
                Color(color[0], color[1], color[2], 0.25)
                Ellipse(pos=(cx - cell_w * 0.4, cy - cell_h * 0.4),
                        size=(cell_w * 0.8, cell_h * 0.8))

                # Punto
                r_size = dp(8)
                Color(*color)
                Ellipse(pos=(cx - r_size / 2, cy - r_size / 2),
                        size=(r_size, r_size))

                # Borde
                Color(1, 1, 1, 0.6)
                Line(circle=(cx, cy, r_size / 2 + 1), width=1)


class MapTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=dp(8), **kwargs)
        self._build()

    def _build(self):
        if not session.positions:
            info = BoxLayout(orientation='vertical', spacing=dp(12), padding=dp(20))
            info.add_widget(Label(text="[ SOM ]", font_size=sp(40),
                                   color=C["accent2"], size_hint_y=None, height=dp(80)))
            info.add_widget(Label(
                text="El mapa SOM estara disponible\ndespues de entrenar el modelo.\n\n"
                     "1. Agrega textos en 'Docs'\n"
                     "2. Configura y entrena en 'Entrenar'\n"
                     "3. Vuelve aqui para visualizar",
                font_size=sp(14), color=C["subtext"], halign='center',
            ))
            self.add_widget(info)
            animate_widget_entrance(info, delay=0.03)
            return

        data = session.get_map_data()

        # Leyenda de clusters
        legend_scroll = ScrollView(size_hint=(1, None), height=dp(54))
        legend = BoxLayout(orientation='horizontal', size_hint_x=None,
                           spacing=dp(8), padding=[dp(6), dp(6)])
        legend.bind(minimum_width=legend.setter('width'))
        for i in range(session.n_clusters):
            color = C["clusters"][i % len(C["clusters"])]
            words = data["top_words"].get(i, [])[:2]
            label = ", ".join(words) if words else f"Cluster {i}"
            pill = CardBox(orientation='horizontal', size_hint=(None, None),
                           size=(dp(150), dp(34)), padding=[dp(8), dp(4)], spacing=dp(6))

            # BUG FIX: el dot se dibuja en _draw del CardBox; en lugar de
            # intentar mutar un Ellipse desde un bind externo (que fallaba),
            # usamos un Widget con su propio canvas limpio y redraw propio.
            dot = _ColorDot(color=color, size_hint=(None, None), size=(dp(10), dp(10)))
            pill.add_widget(dot)
            pill.add_widget(Label(text=label, font_size=sp(10 * UI_SCALE), color=C["text"],
                                  halign='left', valign='middle'))
            legend.add_widget(pill)
        legend_scroll.add_widget(legend)
        self.add_widget(legend_scroll)
        animate_widget_entrance(legend_scroll, delay=0.02)

        # Mapa
        map_widget = SOMMapWidget(map_data=data, size_hint=(1, 1))
        self.add_widget(map_widget)
        animate_widget_entrance(map_widget, delay=0.04)

        self.add_widget(SectionTitle(text="Documentos en el mapa"))

        doc_scroll = ScrollView(size_hint=(1, None), height=dp(160))
        doc_grid = GridLayout(cols=1, spacing=dp(4), size_hint_y=None, padding=[0, 2])
        doc_grid.bind(minimum_height=doc_grid.setter('height'))

        for doc in data["documents"]:
            color = C["clusters"][doc["cluster"] % len(C["clusters"])]
            row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(6))
            # BUG FIX: usando _ColorDot en lugar de Widget con bind externo
            dot = _ColorDot(color=color, size_hint=(None, None),
                            size=(dp(12), dp(12)), pos_hint={'center_y': 0.5})
            row.add_widget(dot)
            row.add_widget(Label(
                text=f"[b]{doc['title']}[/b]  [{doc['row']},{doc['col']}]  C{doc['cluster']}",
                markup=True, font_size=sp(11), color=C["text"],
                halign='left', valign='middle',
            ))
            doc_grid.add_widget(row)

        doc_scroll.add_widget(doc_grid)
        self.add_widget(doc_scroll)
        animate_widget_entrance(doc_scroll, delay=0.06)


class _ColorDot(Widget):
    """Punto de color simple que se redibuja correctamente al cambiar de tamaño/pos.
    BUG FIX: reemplaza el patrón dot.bind(...) que corrompía el canvas.
    """
    def __init__(self, color, **kwargs):
        super().__init__(**kwargs)
        self._color = color
        self.bind(pos=self._draw, size=self._draw)
        Clock.schedule_once(self._draw)

    def _draw(self, *_):
        self.canvas.clear()
        with self.canvas:
            Color(*self._color)
            Ellipse(pos=self.pos, size=self.size)


# ??? TAB: Análisis ????????????????????????????????????????????????????????????

class AnalysisTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=dp(8), **kwargs)
        self._build()

    def _build(self):
        if not session.positions:
            self.add_widget(Label(
                text="El analisis estara disponible\nluego de entrenar el SOM.",
                font_size=sp(14), color=C["subtext"], halign='center',
            ))
            return

        data = session.get_map_data()
        scroll = ScrollView()
        inner = BoxLayout(orientation='vertical', spacing=dp(10),
                           size_hint_y=None, padding=[0, 4])
        inner.bind(minimum_height=inner.setter('height'))

        # Métricas generales
        inner.add_widget(SectionTitle(text="> Metricas del modelo"))
        metrics_card = CardBox(orientation='vertical', padding=dp(12), spacing=dp(6),
                                size_hint_y=None, height=dp(110))
        qe_hist = data.get("qe_history", [])
        qe_final = qe_hist[-1] if qe_hist else 0
        qe_init = qe_hist[0] if qe_hist else 0
        mejora = ((qe_init - qe_final) / (qe_init + 1e-9)) * 100
        metrics_card.add_widget(Label(
            text=f"Vocabulario:  [b]{data['vocab_size']} palabras[/b]\n"
                 f"Documentos:  [b]{data['n_docs']}[/b]\n"
                 f"Grilla:       [b]{data['grid_rows']}x{data['grid_cols']}[/b]\n"
                 f"Error final:  [b]{qe_final:.4f}[/b]  (v{mejora:.1f}% mejora)",
            markup=True, font_size=sp(12), color=C["text"],
            halign='left', valign='top',
        ))
        inner.add_widget(metrics_card)

        # Curva de convergencia
        if qe_hist:
            inner.add_widget(SectionTitle(text="Convergencia del SOM"))
            conv_card = CardBox(orientation='vertical', padding=dp(8), spacing=dp(4),
                                 size_hint_y=None, height=dp(120))
            conv_widget = ConvergenceChart(qe_hist, size_hint_y=None, height=dp(80))
            conv_card.add_widget(conv_widget)
            conv_card.add_widget(Label(
                text=f"Error inicial: {qe_init:.4f}  ->  Error final: {qe_final:.4f}",
                font_size=sp(10), color=C["subtext"],
                size_hint_y=None, height=dp(20), halign='center',
            ))
            inner.add_widget(conv_card)

        # Palabras clave por cluster
        inner.add_widget(SectionTitle(text="Palabras clave por cluster"))
        for cluster_id, words in data["top_words"].items():
            color = C["clusters"][cluster_id % len(C["clusters"])]
            card = CardBox(orientation='vertical', padding=dp(10), spacing=dp(4),
                            size_hint_y=None, height=dp(64))
            docs_in_cluster = [d["title"] for d in data["documents"] if d["cluster"] == cluster_id]
            header = Label(
                text=f"[b]Cluster {cluster_id}[/b]  ({len(docs_in_cluster)} docs)",
                markup=True, font_size=sp(12), color=color,
                size_hint_y=None, height=dp(20), halign='left',
            )
            header.bind(size=lambda w, v: setattr(w, 'text_size', v))
            card.add_widget(header)
            kw = Label(
                text="  ".join(f"#{w}" for w in words[:6]),
                font_size=sp(11), color=C["subtext"],
                size_hint_y=None, height=dp(24), halign='left',
            )
            kw.bind(size=lambda w, v: setattr(w, 'text_size', v))
            card.add_widget(kw)
            inner.add_widget(card)

        # Guardar sesión
        inner.add_widget(SectionTitle(text="Guardar sesion"))
        save_card = CardBox(orientation='vertical', padding=dp(12), spacing=dp(8),
                             size_hint_y=None, height=dp(90))
        save_card.add_widget(Label(
            text="Guarda el modelo entrenado para continuar\nel analisis en sesiones futuras.",
            font_size=sp(11), color=C["subtext"], halign='left',
        ))
        btn_save = StyledButton(text="Guardar sesion JSON", bg_color=C["accent"],
                                 size_hint_y=None, height=dp(38), font_size=sp(12))
        btn_save.bind(on_press=lambda *_: self._save_session())
        save_card.add_widget(btn_save)
        inner.add_widget(save_card)

        inner.add_widget(Widget(size_hint_y=None, height=dp(20)))
        scroll.add_widget(inner)
        self.add_widget(scroll)
        animate_widget_entrance(scroll, delay=0.03)

    def _save_session(self):
        try:
            path = os.path.join(
                os.path.expanduser("~"), "storymapsom_session.json"
            )
            session.save_session(path)
            popup = Popup(
                title='Sesion guardada [OK]',
                content=Label(text=f"Guardado en:\n{path}", font_size=sp(12),
                               color=C["green"], halign='center'),
                size_hint=(0.85, 0.3), background_color=C["card"],
            )
            popup.open()
            Clock.schedule_once(lambda *_: popup.dismiss(), 3)
        except Exception as e:
            popup = Popup(
                title='Error', size_hint=(0.85, 0.3), background_color=C["card"],
                content=Label(text=str(e), font_size=sp(12), color=C["rose"]),
            )
            popup.open()


class ConvergenceChart(Widget):
    """Mini-gráfico de convergencia del error de cuantización."""

    def __init__(self, qe_history, **kwargs):
        super().__init__(**kwargs)
        self.qe = qe_history
        self.bind(pos=self._draw, size=self._draw)
        Clock.schedule_once(self._draw)

    def _draw(self, *args):
        # BUG FIX: guard contra lista vacía o un solo punto
        if not self.qe or not self.width or len(self.qe) < 2:
            return
        self.canvas.clear()
        with self.canvas:
            Color(*C["card2"])
            Rectangle(pos=self.pos, size=self.size)

            data = self.qe
            mn, mx = min(data), max(data)
            rng = mx - mn or 1
            n = len(data)
            pts = []
            for i, v in enumerate(data):
                x = self.x + (i / (n - 1)) * self.width
                y = self.y + ((v - mn) / rng) * self.height
                pts.extend([x, y])

            # BUG FIX: verificar longitud mínima antes de dibujar
            if len(pts) >= 4:
                Color(*C["accent2"])
                Line(points=pts, width=1.5)

                # Punto final
                Color(*C["gold"])
                ex, ey = pts[-2], pts[-1]
                Ellipse(pos=(ex - dp(4), ey - dp(4)), size=(dp(8), dp(8)))


# ??? TAB: Configuración ???????????????????????????????????????????????????????

class SettingsTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=dp(10), **kwargs)
        self._build()

    def _build(self):
        scroll = ScrollView()
        inner = BoxLayout(orientation='vertical', spacing=dp(10),
                           size_hint_y=None, padding=[0, 4])
        inner.bind(minimum_height=inner.setter('height'))

        inner.add_widget(SectionTitle(text="Configuracion"))

        info_card = CardBox(orientation='vertical', padding=dp(14), spacing=dp(6),
                             size_hint_y=None, height=dp(190))
        info_card.add_widget(Label(
            text="[b]StoryMap SOM v1.0[/b]\n\n"
                 "[b]Tecnica principal:[/b] Self-Organizing Map (SOM)\n"
                 "de Kohonen -- Computacion Blanda\n\n"
                 "[b]Preprocesamiento:[/b]\n"
                 "- Tokenizacion y eliminacion de stopwords\n"
                 "- Vectores TF-IDF para representacion semantica\n"
                 "- Clustering K-Means post-SOM\n\n"
                 "[b]Autores:[/b] Santiago Castaneda . Santiago Florez",
            markup=True, font_size=sp(11), color=C["text"],
            halign='left', valign='top',
        ))
        inner.add_widget(info_card)

        inner.add_widget(SectionTitle(text="Fundamento Teorico"))
        theory_card = CardBox(orientation='vertical', padding=dp(14), spacing=dp(6),
                               size_hint_y=None, height=dp(240))
        theory_card.add_widget(Label(
            text="[b]SOM de Kohonen (1982)[/b]\n\n"
                 "Red neuronal no supervisada que aprende una\n"
                 "representacion topologica 2D de datos de alta\n"
                 "dimension, preservando relaciones de vecindad.\n\n"
                 "[b]Actualizacion de pesos:[/b]\n"
                 "Dw = n(t) . h(i,t) . (x - w)\n\n"
                 "[b]Decaimiento exponencial:[/b]\n"
                 "n(t) = n0 . exp(-t/L)\n"
                 "s(t) = s0 . exp(-t/L_s)\n\n"
                 "[b]Funcion de vecindad gaussiana:[/b]\n"
                 "h(i,t) = exp(-d2/2s(t)2)",
            markup=True, font_size=sp(11), color=C["subtext"],
            halign='left', valign='top',
        ))
        inner.add_widget(theory_card)

        inner.add_widget(SectionTitle(text="> Acciones"))
        actions_card = CardBox(orientation='vertical', padding=dp(12), spacing=dp(8),
                                size_hint_y=None, height=dp(110))
        btn_reset = StyledButton(text="<< Reiniciar sesion",
                                  bg_color=C["rose"], size_hint_y=None, height=dp(40),
                                  font_size=sp(13))
        btn_reset.bind(on_press=lambda *_: self._confirm_reset())
        actions_card.add_widget(btn_reset)

        btn_reload = StyledButton(text="Recargar Demo",
                                   bg_color=C["teal"], text_color=(0.05, 0.1, 0.1, 1),
                                   size_hint_y=None, height=dp(40), font_size=sp(13))
        btn_reload.bind(on_press=lambda *_: self._reload_demo())
        actions_card.add_widget(btn_reload)
        inner.add_widget(actions_card)

        inner.add_widget(Widget(size_hint_y=None, height=dp(20)))
        scroll.add_widget(inner)
        self.add_widget(scroll)
        animate_widget_entrance(scroll, delay=0.03)

    def _confirm_reset(self):
        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(10))
        content.add_widget(Label(
            text="¿Reiniciar toda la sesion?\nSe perderan todos los documentos\ny el modelo entrenado.",
            font_size=sp(13), color=C["text"], halign='center',
        ))
        btns = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        btn_no = StyledButton(text="Cancelar", bg_color=C["card2"])
        btn_yes = StyledButton(text="<< Confirmar", bg_color=C["rose"])
        btns.add_widget(btn_no)
        btns.add_widget(btn_yes)
        content.add_widget(btns)
        popup = Popup(title='Confirmar', content=content,
                      size_hint=(0.85, 0.38), background_color=C["card"])

        def do_reset(*_):
            session.clear()
            popup.dismiss()

        btn_yes.bind(on_press=do_reset)
        btn_no.bind(on_press=popup.dismiss)
        popup.open()

    def _reload_demo(self):
        session.clear()
        for title, text in DEMO_STORIES:
            session.add_document(title, text)
        popup = Popup(
            title='Demo cargado',
            content=Label(text=f"[OK] {len(DEMO_STORIES)} cuentos cargados",
                           font_size=sp(14), color=C["green"], halign='center'),
            size_hint=(0.8, 0.25), background_color=C["card"],
        )
        popup.open()
        Clock.schedule_once(lambda *_: popup.dismiss(), 2)


# ??? ScreenManager y App ??????????????????????????????????????????????????????

class StoryMapApp(App):
    def build(self):
        self.title = "StoryMap SOM"
        sm = ScreenManager(transition=FadeTransition(duration=0.25))
        sm.add_widget(WelcomeScreen(name='welcome'))
        sm.add_widget(MainScreen(name='main'))
        return sm

    def on_pause(self):
        return True

    def on_resume(self):
        pass


if __name__ == '__main__':
    StoryMapApp().run()