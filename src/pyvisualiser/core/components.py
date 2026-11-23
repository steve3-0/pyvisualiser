#!/usr/bin/env python
"""
Display driver classes

Low level platform dynamics

v1.0 baloothebear4 1 Dec 2023   Original, based on Pygame visualiser mockups
v1.1 baloothebear4 Feb 2024     refactored as part of pyvisualiseer
v2.0 baloothebear4 Feb 2026     Major upgrade to port to OpenGL for speed and visual complexity
v2.1 baloothebear4 Nov 2026     Static font cache manager & rendered surface cache optimization
"""
from  pyvisualiser.core.framecore import Frame, Cache, Colour, get_asset_path
from  pyvisualiser.styles.styles import *
from  pyvisualiser.styles.profiles import ProfileManager
from  pyvisualiser.core.render import OutlineBlurPass
from  pyvisualiser.core.frame_config import FrameConfig

import pygame
from   pygame.locals import *
import numpy as np

from   textwrap import shorten, wrap
from   io import BytesIO
import requests
import random
import warnings

""" Prevent image colour warnings: libpng warning: iCCP: known incorrect sRGB profile """
warnings.filterwarnings("ignore", category=UserWarning, module="pygame")

PI = np.pi


class FontCacheManager:
    """
    Caches pygame.font.Font instances keyed by (font_path, font_size).
    Shared across all Text components to eliminate duplicate disk reads
    and FreeType outline re-parsing.
    """
    _cache = {}

    @classmethod
    def get_font(cls, font_path: str, size: int) -> pygame.font.Font:
        int_size = max(1, int(size))
        key = (font_path, int_size)
        if key not in cls._cache:
            cls._cache[key] = pygame.font.Font(font_path, int_size)
        return cls._cache[key]

    @classmethod
    def clear(cls):
        cls._cache.clear()


class Bar(Frame):
    """
    Bars have parameters:
        - colour modes:
            'vert' according to y
            's' solid colour
            'horz' colour according to x
        - colour theme:  tuple of colours over which the colours range - one colour is fixed colour
        - leds ie discrete with colours -> LEDs have characteristics like, glow, intensity, colour, brick firmsness etc
        - vertical or horizontal,
        - left or right
        - peak lines
    """

    def __init__(self, parent, config:Optional[FrameConfig] = None, 
                 box_size=(100, 100), bar_style=None):

        Frame.__init__(self, parent, config=config)
        self.resize(box_size)

        profile = ProfileManager.get_profile()
        self.bar_style = bar_style if bar_style is not None else profile.get_style('bar')
        if self.bar_style is None:
            self.bar_style = BarStyle()
        
        self.effects = bar_style.effects if bar_style.effects is not None else profile.effects
        
        colour_range = self.h if self.bar_style.colour_mode == 'vert' else self.w
        self.colours = Colour(self.theme, colour_range)
        
        self.gradient_surface = self._create_gradient_surface()
        self._gl_texture = None
        self.bloom_states = {}

    def _create_gradient_surface(self):
        colors = self.colours.colours
        w = len(colors)
        if w == 0: return None
        surf = pygame.Surface((w, 1))
        for i, c in enumerate(colors):
            surf.set_at((i, 0), c)
        return surf

    def float_abs_rect(self, offset=(0, 0), wh=None):
        """ Calculates absolute coordinates keeping float precision to prevent jitter """
        xy_shrink = self.outline_w + self.padding
        wh_shrink = xy_shrink * 2
        
        w_frame = self.w
        h_frame = self.h
        
        w_target = w_frame - wh_shrink if wh is None else wh[0]
        h_target = h_frame - wh_shrink if wh is None else wh[1]
        
        x = self.x0 + xy_shrink + offset[0]
        y = self.screen_wh[1] - (self.y0 + h_frame - xy_shrink - offset[1])
        
        return (x, y, w_target, h_target)

    def draw_peak(self, peak_h, flip, peak_coords):
        if peak_h > 0.0:
            colour = self.colours.get(colour_index=peak_h, flip=flip)
            self.platform.renderer.draw_rect(colour, peak_coords, softness=self.bar_style.edge_softness)

    def _get_smoothed_bloom(self, key, target):
        current = self.bloom_states.get(key, 0.0)
        if target > current:
            current += (target - current) * self.effects.attack
        else:
            current += (target - current) * self.effects.decay
        
        if current < 0.001: current = 0.0
        self.bloom_states[key] = current
        return current

    def draw(self, offset, ypc, w, peak=0, colour_index=None):
        self.tip_radius = int(w / 2)
        if self.bar_style.orient == 'horz':
            self.drawH(offset, ypc, w, peak, colour_index)
        else:
            self.drawV(offset, ypc, w, peak, colour_index)

    def drawV(self, offset, ypc, w, peak=0, colour_index=None):
        """ Draw Vertical Bar """
        if self.bar_style.flip:
            coords = self.float_abs_rect(offset=(offset, 0), wh=[w, self.abs_h])

            c_top = self.colours.get(0, False)
            c_bot = self.colours.get(self.colours.num_colours, False)
            
            if colour_index is not None:
                c_top = c_bot = self.colours.get(colour_index)

            bloom_start = self.effects.threshold - 0.05
            alpha_ratio = 0.0
            if ypc > bloom_start:
                excess = (ypc - bloom_start) / max(0.001, 1.0 - bloom_start)
                alpha_ratio = max(0.0, min(1.0, excess)) ** self.effects.power

            smoothed_ratio = self._get_smoothed_bloom(offset, alpha_ratio)

            if smoothed_ratio > 0.01:
                current_alpha = self.effects.alpha * smoothed_ratio
                y_val = max(ypc, self.effects.threshold)
                bloom_h = (y_val - self.effects.threshold) * self.abs_h
                bloom_y = coords[1] + self.effects.threshold * self.abs_h
                
                c_tip = list(self.colours.get(ypc * self.colours.num_colours)[:3]) + [current_alpha]
                c_thresh = list(self.colours.get(self.effects.threshold * self.colours.num_colours)[:3]) + [current_alpha]
                
                inner_scale = 1.0 + (self.effects.scale - 1.0) * self.effects.inner_glow_scale
                b_w_inner = coords[2] * (inner_scale - 1.0)
                b_rect_inner = (coords[0] - b_w_inner / 2, bloom_y - b_w_inner / 2, coords[2] + b_w_inner, bloom_h + b_w_inner)
                self.platform.renderer.draw_rect(c_thresh, b_rect_inner, softness=self.effects.blur, gradient=(c_thresh, c_tip), axis=1.0, level=10.0, additive=True)

                outer_scale_mult = self.effects.outer_glow_scale_min + self.effects.outer_glow_scale_max * smoothed_ratio
                outer_scale = 1.0 + (self.effects.scale - 1.0) * outer_scale_mult
                b_w_outer = coords[2] * (outer_scale - 1.0)
                b_rect_outer = (coords[0] - b_w_outer / 2, bloom_y - b_w_outer / 2, coords[2] + b_w_outer, bloom_h + b_w_outer)
                c_outer_tip = c_tip[:3] + [current_alpha * self.effects.outer_glow_alpha_mult]
                c_outer_thresh = c_thresh[:3] + [current_alpha * 0.6]
                self.platform.renderer.draw_rect(c_outer_thresh, b_rect_outer, softness=self.effects.blur * self.effects.outer_glow_blur_mult, gradient=(c_outer_thresh, c_outer_tip), axis=1.0, level=10.0, additive=True)

            self.platform.renderer.draw_rect(c_top, coords, 
                                             border_radius=self.bar_style.corner_radius, 
                                             softness=self.bar_style.edge_softness,
                                             segments=(self.bar_style.segment_size, self.bar_style.segment_gap),
                                             gradient=(c_top, c_bot),
                                             axis=1,
                                             level=ypc,
                                             gradient_image=self.gradient_surface,
                                             texture_holder=self)

            pcoords = self.float_abs_rect(offset=(offset, peak * self.abs_h), wh=[w, self.bar_style.peak_h])
            self.draw_peak(peak * self.h, False, pcoords)
        else:
            coords = self.float_abs_rect(offset=(offset, 0), wh=[w, self.abs_h])
            
            c_top = self.colours.get(self.colours.num_colours, False)
            c_bot = self.colours.get(0, False)
            
            if colour_index is not None:
                c_top = c_bot = self.colours.get(colour_index)

            bloom_start = self.effects.threshold - 0.05
            alpha_ratio = 0.0
            if ypc > bloom_start:
                excess = (ypc - bloom_start) / max(0.001, 1.0 - bloom_start)
                alpha_ratio = max(0.0, min(1.0, excess)) ** self.effects.power

            smoothed_ratio = self._get_smoothed_bloom(offset, alpha_ratio)

            if smoothed_ratio > 0.01:
                current_alpha = self.effects.alpha * smoothed_ratio
                y_val = max(ypc, self.effects.threshold)
                bloom_h = (y_val - self.effects.threshold) * self.abs_h
                bloom_y = coords[1] + (1.0 - y_val) * self.abs_h
                
                c_tip = list(self.colours.get(ypc * self.colours.num_colours)[:3]) + [current_alpha]
                c_thresh = list(self.colours.get(self.effects.threshold * self.colours.num_colours)[:3]) + [current_alpha]
                
                inner_scale = 1.0 + (self.effects.scale - 1.0) * 0.2
                b_w_inner = coords[2] * (inner_scale - 1.0)
                b_rect_inner = (coords[0] - b_w_inner / 2, bloom_y - b_w_inner / 2, coords[2] + b_w_inner, bloom_h + b_w_inner)
                self.platform.renderer.draw_rect(c_tip, b_rect_inner, softness=self.effects.blur, gradient=(c_tip, c_thresh), axis=1.0, level=10.0, additive=True)

                outer_scale = 1.0 + (self.effects.scale - 1.0) * (0.5 + 0.5 * smoothed_ratio)
                b_w_outer = coords[2] * (outer_scale - 1.0)
                b_rect_outer = (coords[0] - b_w_outer / 2, bloom_y - b_w_outer / 2, coords[2] + b_w_outer, bloom_h + b_w_outer)
                
                c_outer_tip = c_tip[:3] + [current_alpha * 0.6]
                c_outer_thresh = c_thresh[:3] + [current_alpha * 0.6]
                
                self.platform.renderer.draw_rect(c_outer_tip, b_rect_outer, softness=self.effects.blur * 2.5, gradient=(c_outer_tip, c_outer_thresh), axis=1.0, level=10.0, additive=True)

            self.platform.renderer.draw_rect(c_top, coords, 
                                             border_radius=self.bar_style.corner_radius, 
                                             softness=self.bar_style.edge_softness,
                                             segments=(self.bar_style.segment_size, self.bar_style.segment_gap),
                                             gradient=(c_top, c_bot),
                                             axis=-1.0,
                                             level=ypc,
                                             gradient_image=self.gradient_surface,
                                             texture_holder=self)

            if self.effects.reflection:
                ref_size = 0.3
                ref_opacity = 0.5
                if isinstance(self.effects.reflection, dict):
                    ref_size = self.effects.reflection.get('size', ref_size)
                    ref_opacity = self.effects.reflection.get('opacity', ref_opacity)
                
                ref_coords = (coords[0], coords[1] + coords[3], coords[2], coords[3] * ref_size)
                
                def fade_c(c):
                    c_tuple = tuple(c)
                    if len(c_tuple) > 3: return c_tuple[:3] + (c_tuple[3] * ref_opacity,)
                    return c_tuple[:3] + (255 * ref_opacity,)

                c_top_ref, c_bot_ref = fade_c(c_top), fade_c(c_bot)

                self.platform.renderer.draw_rect(c_bot_ref, ref_coords, 
                                                 border_radius=self.bar_style.corner_radius, 
                                                 softness=self.bar_style.edge_softness,
                                                 segments=(self.bar_style.segment_size, self.bar_style.segment_gap),
                                                 gradient=(c_bot_ref, c_top_ref), 
                                                 axis=1.0,
                                                 level=ypc,
                                                 gradient_image=self.gradient_surface,
                                                 texture_holder=self)
                                                 
                if peak > 0.01:
                    p_offset_ref = self.abs_h + (peak * self.abs_h * ref_size)
                    pcoords_ref = self.float_abs_rect(offset=(offset, p_offset_ref), wh=[w, self.bar_style.peak_h])
                    c_peak_ref = fade_c(self.colours.get(self.colours.num_colours * peak, False))
                    self.platform.renderer.draw_rect(c_peak_ref, pcoords_ref, softness=self.bar_style.edge_softness)

            pcoords = self.float_abs_rect(offset=(offset, self.abs_h * (1 - peak)), wh=[w, self.bar_style.peak_h])
            self.draw_peak(peak * self.h, False, pcoords)

    def drawH(self, offset, ypc, w, peak=0, colour_index=None):
        """ Draw a horizontal bar """
        width = self.abs_w
        if self.bar_style.flip:
            coords = self.float_abs_rect(offset=(0, offset), wh=[width, w])
            
            c_left = self.colours.get(self.colours.num_colours, False)
            c_right = self.colours.get(0, False)
            
            if colour_index is not None:
                c_left = c_right = self.colours.get(colour_index)

            bloom_start = self.effects.threshold - 0.05
            alpha_ratio = 0.0
            if ypc > bloom_start:
                excess = (ypc - bloom_start) / max(0.001, 1.0 - bloom_start)
                alpha_ratio = max(0.0, min(1.0, excess)) ** self.effects.power

            smoothed_ratio = self._get_smoothed_bloom(offset, alpha_ratio)

            if smoothed_ratio > 0.01:
                current_alpha = self.effects.alpha * smoothed_ratio
                y_val = max(ypc, self.effects.threshold)
                bloom_w = (y_val - self.effects.threshold) * self.abs_w
                bloom_x = coords[0] + (1.0 - y_val) * self.abs_w
                
                c_tip = list(self.colours.get(ypc * self.colours.num_colours)[:3]) + [current_alpha]
                c_thresh = list(self.colours.get(self.effects.threshold * self.colours.num_colours)[:3]) + [current_alpha]

                inner_scale = 1.0 + (self.effects.scale - 1.0) * 0.2
                b_h_inner = coords[3] * (inner_scale - 1.0)
                b_rect_inner = (bloom_x - b_h_inner / 2, coords[1] - b_h_inner / 2, bloom_w + b_h_inner, coords[3] + b_h_inner)
                self.platform.renderer.draw_rect(c_tip, b_rect_inner, softness=self.effects.blur, gradient=(c_tip, c_thresh), axis=2.0, level=10.0, additive=True)

                outer_scale = 1.0 + (self.effects.scale - 1.0) * (0.5 + 0.5 * smoothed_ratio)
                b_h_outer = coords[3] * (outer_scale - 1.0)
                b_rect_outer = (bloom_x - b_h_outer / 2, coords[1] - b_h_outer / 2, bloom_w + b_h_outer, coords[3] + b_h_outer)
                
                c_outer_tip = c_tip[:3] + [current_alpha * 0.6]
                c_outer_thresh = c_thresh[:3] + [current_alpha * 0.6]
                self.platform.renderer.draw_rect(c_outer_tip, b_rect_outer, softness=self.effects.blur * 2.5, gradient=(c_outer_tip, c_outer_thresh), axis=2.0, level=10.0, additive=True)

            self.platform.renderer.draw_rect(c_left, coords, 
                                             border_radius=self.bar_style.corner_radius, 
                                             softness=self.bar_style.edge_softness,
                                             segments=(self.bar_style.segment_size, self.bar_style.segment_gap),
                                             gradient=(c_left, c_right),
                                             axis=-2.0,
                                             level=ypc,
                                             gradient_image=self.gradient_surface,
                                             texture_holder=self)

            peak_w = width * peak
            pcoords = self.float_abs_rect(offset=(width * (1 - peak), offset), wh=[self.bar_style.peak_h, w])
            self.draw_peak(peak_w, False, pcoords)

        else:
            coords = self.float_abs_rect(offset=(0, offset), wh=[width, w])
            
            c_left = self.colours.get(0, False)
            c_right = self.colours.get(self.colours.num_colours, False)
            
            if colour_index is not None:
                c_left = c_right = self.colours.get(colour_index)

            bloom_start = self.effects.threshold - 0.05
            alpha_ratio = 0.0
            if ypc > bloom_start:
                excess = (ypc - bloom_start) / max(0.001, 1.0 - bloom_start)
                alpha_ratio = max(0.0, min(1.0, excess)) ** self.effects.power

            smoothed_ratio = self._get_smoothed_bloom(offset, alpha_ratio)

            if smoothed_ratio > 0.01:
                current_alpha = self.effects.alpha * smoothed_ratio
                y_val = max(ypc, self.effects.threshold)
                bloom_w = (y_val - self.effects.threshold) * self.abs_w
                bloom_x = coords[0] + self.effects.threshold * self.abs_w
                
                c_tip = list(self.colours.get(ypc * self.colours.num_colours)[:3]) + [current_alpha]
                c_thresh = list(self.colours.get(self.effects.threshold * self.colours.num_colours)[:3]) + [current_alpha]

                inner_scale = 1.0 + (self.effects.scale - 1.0) * 0.2
                b_h_inner = coords[3] * (inner_scale - 1.0)
                b_rect_inner = (bloom_x - b_h_inner / 2, coords[1] - b_h_inner / 2, bloom_w + b_h_inner, coords[3] + b_h_inner)
                self.platform.renderer.draw_rect(c_thresh, b_rect_inner, softness=self.effects.blur, gradient=(c_thresh, c_tip), axis=2.0, level=10.0, additive=True)

                outer_scale = 1.0 + (self.effects.scale - 1.0) * (0.5 + 0.5 * smoothed_ratio)
                b_h_outer = coords[3] * (outer_scale - 1.0)
                b_rect_outer = (bloom_x - b_h_outer / 2, coords[1] - b_h_outer / 2, bloom_w + b_h_outer, coords[3] + b_h_outer)
                
                c_outer_tip = c_tip[:3] + [current_alpha * 0.6]
                c_outer_thresh = c_thresh[:3] + [current_alpha * 0.6]
                self.platform.renderer.draw_rect(c_outer_thresh, b_rect_outer, softness=self.effects.blur * 2.5, gradient=(c_outer_tip, c_outer_thresh), axis=2.0, level=10.0, additive=True)

            self.platform.renderer.draw_rect(c_left, coords, 
                                             border_radius=self.bar_style.corner_radius, 
                                             softness=self.bar_style.edge_softness,
                                             segments=(self.bar_style.segment_size, self.bar_style.segment_gap),
                                             gradient=(c_left, c_right),
                                             axis=2.0,
                                             level=ypc,
                                             gradient_image=self.gradient_surface,
                                             texture_holder=self)

            peak_w = peak * width
            pcoords = self.float_abs_rect(offset=(peak_w, offset), wh=[self.bar_style.peak_h, w])
            self.draw_peak(peak_w, False, pcoords)

    def __del__(self):
        if hasattr(self, '_gl_texture') and self._gl_texture is not None:
            try:
                self._gl_texture.release()
            except Exception:
                pass
            self._gl_texture = None

class Image:
    DEFAULT_OPACITY = 255
    DEFAULT_CACHE   = 300
    def __init__(self, parent, wh=None, path=None, align=None, scalers=None, opacity=None, outline=None, target_wh=None, reflection=None):
        self.image_cache = Cache(Image.DEFAULT_CACHE)
        self.path        = path
        self.parent      = parent
        self.opacity     = Image.DEFAULT_OPACITY if opacity is None or opacity > Image.DEFAULT_OPACITY else opacity
        self.old_image_data = None
        self.target_wh   = parent.abs_rect()[-2:] if target_wh is None else target_wh 
        self._gl_texture = None
        self.reflection  = reflection

        if path is not None:
            self.scaleInProportion(path)

    def download_image(self, url):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return BytesIO(response.content)
        except requests.exceptions.RequestException as e:
            print(f"Image.download_image ERROR: Failed to fetch image from URL {url}: {e}")
            return None
        
    def scaleInProportion_and_crop(self, imagesurface, target_wh):
        W_target, H_target = target_wh
        W_orig, H_orig = imagesurface.get_size()

        scale_w = W_target / W_orig
        scale_h = H_target / H_orig
        
        scale_factor = max(scale_w, scale_h)

        W_scaled = int(W_orig * scale_factor)
        H_scaled = int(H_orig * scale_factor)
        
        scaled_image = pygame.transform.scale(imagesurface, (W_scaled, H_scaled))

        crop_x_offset = (W_scaled - W_target) // 2
        crop_y_offset = (H_scaled - H_target) // 2
        
        cropped_surface = pygame.Surface((W_target, H_target), pygame.SRCALPHA)
        cropped_surface.blit(scaled_image, (-crop_x_offset, -crop_y_offset))
        return cropped_surface

    def scaleInProportion(self, image_ref, target_wh=None):
        if image_ref is None: return
        if target_wh is None: target_wh = self.target_wh

        imagesurface = None
        try:
            if 'http' in image_ref:
                path = self.download_image(image_ref) 
                if path is None: return None
            else:
                path = image_ref

            imagesurface = pygame.image.load(path).convert_alpha()
            
        except pygame.error as e:
            print(f"Image.scaleInProportion ERROR: Pygame failed to load image '{image_ref}'. Error: {e}")
            return None
        except Exception as e:
            print(f"Image.scaleInProportion UNEXPECTED ERROR during load '{image_ref}': {e}")
            return None

        if imagesurface is None:
            return None

        image = self.scaleInProportion_and_crop(imagesurface, target_wh)
        self.image_cache.add(image_ref, image)
        return image

    def new_content_available(self, image_data=None):
        if image_data is None:  image_data = self.path  
        return image_data != self.old_image_data

    def draw(self, image_data=None, coords=None):   
        if coords is None: coords = self.parent.abs_origin()
        if image_data is None:  image_data = self.path   

        image = self.image_cache.find(image_data)
        if image is None:   
            image = self.scaleInProportion(image_data)

        if image is not None:
            if image_data != self.old_image_data:
                self._gl_texture = None

            self.parent.platform.renderer.blit(image, coords, texture_holder=self, opacity=self.opacity, reflection=self.reflection)
            self.old_image_data = image_data

    def __del__(self):
        if hasattr(self, '_gl_texture') and self._gl_texture is not None:
            try:
                self._gl_texture.release()
            except Exception:
                pass
            self._gl_texture = None

    def draw(self, image_data=None, coords=None):   
        if coords is None: coords = self.parent.abs_origin()
        if image_data is None:  image_data = self.path   

        image = self.image_cache.find(image_data)
        if image is None:   
            image = self.scaleInProportion(image_data)

        if image is not None:
            if image_data != self.old_image_data:
                # Release old texture immediately on image change
                if self._gl_texture is not None:
                    self._gl_texture.release()
                    self._gl_texture = None

            self.parent.platform.renderer.blit(image, coords, texture_holder=self, opacity=self.opacity, reflection=self.reflection)
            self.old_image_data = image_data

class ArcsOctaves(Frame):
    """ Lines are for drawing meter needles, oscilogrammes etc """
    def __init__(self, parent, config:Optional[FrameConfig] = None, wh=None, colour=None,  NumOcts=5):
        self.NumOcts = NumOcts

        resolved_config = config if config is not None else parent.config
        Frame.__init__(self, parent, config=resolved_config)
        if wh is not None: self.resize(wh)

        self.scalar  = self.h / (NumOcts) / 2
        self.colours = Colour(self.theme, 12)

    def draw(self, octave, notes):
        Oct1    = self.h / self.NumOcts
        arc     = 2 * PI / len(notes)
        top     = -PI / 2
        box     = Oct1 * (octave + 1)
        for i in range(0, len(notes)):
            if np.isinf(notes[i]): break
            amp = int(self.bounds((notes[i] * self.scalar), 0, 100))
            colour = self.colours.get(i)
            pygame.draw.arc(self.platform.screen, colour, [self.centre[0] - box // 2, self.centre[1] - box // 2, box, box], arc * i + top, arc * i + (0.9 * arc) + top, amp)

    def bounds(self, v, a=0, b=255):
        if v > b:
            return b
        elif v < a:
            return a
        else:
            return v


class Box(Frame):
    def __init__(self, parent, config:Optional[FrameConfig] = None, colour_index=0, box=None, width=None, radius=5):
        self.width    = box[1] if width is None else width
        self.radius   = radius

        Frame.__init__(self, parent, config=config)
        if box is not None:  self.resize(box)

        self.colour_index = colour_index
        self.colours      = Colour(self.theme, self.w)

    def draw(self, offset=(0, 0), colour_index=0, wh=None, pc=None):
        if colour_index is None: colour_index = self.colour_index
        if wh is None: wh = self.wh
        if pc is not None: wh = [self.wh[0] * pc, self.wh[1]]
        coords = self.abs_rect(offset=offset, wh=wh)
        colour = self.colours.get(colour_index)
        self.platform.renderer.draw_rect(colour, coords, width=self.width)

    def drawH(self, pc, flip=False, colour_index=None, offset=(0, 0)):
        if flip:
            coords = self.abs_rect(offset=(self.w * pc + offset[0], offset[1]), wh=[self.w * (1 - pc), self.width])
        else:
            coords = self.abs_rect(offset=offset, wh=[self.w * pc, self.width])

        colour = self.colours.get(self.w * pc, False) if colour_index is None else self.colours.get(colour_index)
        self.platform.renderer.draw_rect(colour, coords, border_radius=self.radius)


class Line(Frame):
    def __init__(self, parent, config:Optional[FrameConfig] = None, colour=None, width=1, 
                  circle=True, endstops=(PI / 2, 3 * PI / 2), radius=100, centre_offset=0, tick_pc=1.0, amp_scale=0.9):

        self.width     = width
        self.circle    = circle
        self.radius    = radius
        self.tick_pc   = tick_pc
        self.linespace = []
        self.amp_scale = amp_scale

        Frame.__init__(self, parent, config=config)
        self.anglescale(radius, endstops, centre_offset)

        self.colour    = colour
        self.colours   = Colour(self.theme, self.radius)

    def draw(self, offset, colour=None):
        if colour is None: colour = self.colour
        coords = self.abs_rect()
        colour_index = self.colours.get(colour)
        self.platform.renderer.draw_line(colour_index, coords[:2], coords[2:], self.width)

    def drawFrameCentredVector(self, val, colour=None, width=0, amplitude=1.0, gain=0, tick_pc=None, opacity=255, **kwargs):
        if colour is None: colour = self.colour
        if width == 0: width = self.width
        if tick_pc is None: tick_pc = self.tick_pc
        xy = self.anglexy(val, self.radius, amp_scale=amplitude, gain=gain)
        ab = self.anglexy(val, self.radius * (1 - tick_pc))

        # print(f"[LINE TELEMETRY] val={val} | line_radius={self.radius} | "
        #       f"min_offset={self.min_offset} | circle_scale={self.circle_scale} | "
        #       f"xy={xy} | ab={ab}")


        frame_rect = self.abs_rect()
        frame_bottom = frame_rect[1] + frame_rect[3]
        
        limit_y = frame_bottom - (width / 2.0)
        
        if ab[1] > limit_y:
            dy = xy[1] - ab[1]
            if abs(dy) > 0.1:
                t = (limit_y - ab[1]) / dy
                if 0 <= t <= 1:
                    ab = (ab[0] + t * (xy[0] - ab[0]), limit_y)

        colour_index = self.colours.get(colour, opacity=opacity)
        self.platform.renderer.draw_line(colour_index, ab, xy, width, **kwargs)

    def draw_mod_line(self, points, colour=None, amplitude=1.0, gain=1.0):
        size   = len(points)
        yscale = self.h
        xscale = self.w / size

        line = []
        for i, v in enumerate(points):
            if self.circle:
                line.append(self.anglexy(i / size, self.radius, gain=v * gain, amp_scale=self.amp_scale * amplitude, xyscale=self.xyscale))
            else:
                line.append(self.abs_origin(offset=(xscale * i, 0.5 * yscale * (1 + v * amplitude * self.amp_scale))))

        colour = self.radius * (self.amp_scale * amplitude) if colour is None else 'alert'
        colour_index = self.colours.get(colour)
        self.platform.renderer.draw_lines(colour_index, self.circle, line, width=self.width)

    def make_ripple(self, size):
        wh = (self.xyscale[0] * size, self.xyscale[1] * size)
        xy = self.abs_origin(offset=(self.centre[0] - wh[0] // 2, self.centre[1] - wh[1] // 2))
        return pygame.Rect(xy, wh)

    def draw_mod_ripples(self, points, trigger={}, colour=None, amplitude=1.0):
        xc, yc       = self.centre[0], self.centre[1]
        aspect_ratio = self.w / self.h
        xyscale      = (aspect_ratio, 1.0) if self.w > self.h else (1.0, aspect_ratio)
        frame        = pygame.Rect(self.abs_rect(screen_h=self.platform.h))
        gain         = 1.01
        col          = 'light'

        if 'bass' in trigger:
            col = 'alert'

        if 'treble' in trigger:
            col = 'foreground'

        for ripple in self.linespace:
            self.linespace.remove(ripple)
            new_size = int(gain * ripple[0].height)
            new_ripple = self.make_ripple(new_size)
            if frame.contains(new_ripple) and len(self.linespace) < 1:
                self.linespace.append((new_ripple, ripple[1]))

        if amplitude > 0.8 and len(self.linespace) < 1:
            ripple = self.make_ripple(self.radius * (self.amp_scale * amplitude) * 2)
            colour_index = self.colours.get(col)
            self.linespace.append((ripple, colour_index))

        for ripple in self.linespace:
            pygame.draw.ellipse(self.platform.screen, ripple[1], ripple[0], width=1)

    def drawFrameCentredArc(self, val, colour=None):
        if colour is None: colour = self.colour
        
        points = []
        steps = 32
        for i in range(steps + 1):
            pc = i / steps
            points.append(self.anglexy(pc, self.radius))
            
        colour_index = self.colours.get(colour)
        self.platform.renderer.draw_lines(colour_index, False, points, width=self.width)


class Text:
    """
    Text is all about creating words & numbers that are scaled to fit within
    rectangles.

    Fonts are scaled to fit and cached via FontCacheManager.
    Rendered line surfaces are cached across frames to eliminate FreeType rasterization.
    """
    def __init__(self, parent, text='Default text', fontmax=None, reset=True, wrap=False, justify=('centre', 'middle'),
                 endstops=(PI / 2, 3 * PI / 2), radius=100, centre_offset=0, colour=None, style=None, z_order=0):

        self.text     = text
        self.wrap     = wrap
        self.reset    = reset
        self.radius   = radius
        self.justify  = justify if len(justify) == 2 else (justify, 'middle')
        self.parent   = parent
        self.z_order  = z_order

        profile = ProfileManager.get_profile()
        self.style = style if style is not None else profile.get_style('text')
        if self.style is None:
             self.style = TextStyle()

        self.fontfile = get_asset_path('fonts', self.style.typeface)

        self.cache    = Cache()
        self.colour   = colour
        self.colours  = parent.colours
        self.fontmax  = parent.abs_h if fontmax is None else fontmax 
        self.rendered_surface = None
        self.last_params      = None
        self._gl_texture      = None

        # Dirty-check attributes for scalefont
        self._last_text = None
        self._last_fontwh = None
        self._last_fontmax = None
        self.font = None
        self.fontwh = [0, 0]
        self.drawtext = [text]

        # Steady-state rendered surface cache for multi-line and single-line draw()
        self._cached_rendered_lines = None
        self._cached_draw_params = None

        self.update()

    def __del__(self):
        if hasattr(self, '_gl_texture') and self._gl_texture is not None:
            try:
                self._gl_texture.release()
            except Exception:
                pass
            self._gl_texture = None
        if hasattr(self, '_line_holders'):
            for h in self._line_holders:
                if hasattr(h, '_gl_texture') and h._gl_texture is not None:
                    try:
                        h._gl_texture.release()
                    except Exception:
                        pass
                    h._gl_texture = None

    def update(self, text=None, fontmax=None):
        try:
            if text is None: text = self.text
            
            current_wh = tuple(self.parent.abs_wh)
            current_fontmax = self.fontmax if fontmax is None else fontmax

            # Dirty check: skip scaling if text, frame size, and max height are identical
            if (text == self._last_text and
                current_wh == self._last_fontwh and
                current_fontmax == self._last_fontmax and
                self.font is not None):
                return

            self._last_text = text
            self._last_fontwh = current_wh
            self._last_fontmax = current_fontmax

            # Clear cached rendered surfaces on scale change
            self._cached_rendered_lines = None
            self.rendered_surface = None
            self.last_params = None

            self.drawtext = self.cache.find(text)
            self.font, self.fontwh = self.scalefont(current_wh, text, current_fontmax)

            if self.drawtext is None:
                self.cache.add(text, self.drawtext)

        except Exception as e:
            print("Text.update> ERROR > %s > wh %s, fontwh %s, text<%s>, %s " % (
                e, getattr(self.parent, 'abs_wh', None), getattr(self, 'fontwh', None), text,
                getattr(self.parent, 'geostr', lambda: '')()
            ))

    def new_content_available(self, text=None):
        if text is None: text = self.text
        return text != self.text        

    @property
    def fontsize(self):
        return self.fontwh[1]
    
    def shrink_fontsize(self, wh, text, fontmax=None):
        """ Shrink the font to fit the rect using cached font objects and font.size """
        fontsize = max(1, int(self.fontmax if fontmax is None else fontmax))
        font = FontCacheManager.get_font(self.fontfile, fontsize)
        fontwh = list(self.textsize(text, font)) 

        if fontwh[0] > wh[0] and fontwh[0] > 0:  
            fontsize = max(1, int(fontsize * wh[0] / fontwh[0]))
            font = FontCacheManager.get_font(self.fontfile, fontsize)
            fontwh = list(self.textsize(text, font))

        if fontwh[1] > wh[1] and fontwh[1] > 0:  
            fontsize = max(1, int(fontsize * wh[1] / fontwh[1]))
            font = FontCacheManager.get_font(self.fontfile, fontsize)
            fontwh = list(self.textsize(text, font))

        return font, fontwh

    def scalefont(self, wh, text, fontmax):
        """ Scale the font to fit the rect, with a min fontsize """
        if '\n' in text:
            self.drawtext = text.split('\n')
            num_lines = len(self.drawtext)
            longest_line = max(self.drawtext, key=len)
            line_wh = (wh[0], wh[1] / num_lines)
            font, fontwh = self.shrink_fontsize(line_wh, longest_line, fontmax)
            fontwh[1] *= num_lines
            return font, fontwh

        font, fontwh = self.shrink_fontsize(wh, text, fontmax)

        if self.wrap and fontwh[1] < self.style.min_size:
            try:
                self.drawtext = wrap(text, width=1 + len(text) // 2, max_lines=self.style.max_lines)
                font, fontwh = self.shrink_fontsize(wh, self.drawtext[0], fontmax)
                fontwh[1] *= 2
            except ValueError as error:
                print("Text.scalefont> textwrap failed", error)
                self.drawtext = [text[:(1 + len(text) // 2)]]
                font, fontwh = self.shrink_fontsize(wh, self.drawtext[0], fontmax)
        else:
            self.drawtext = [text]

        return font, fontwh


    def draw(self, text=None, offset=(0, 0), coords=None, colour=None, fontmax=None, z_order=None):
        if text is not None and text != self.text:
            # Release old texture immediately on text change
            if self._gl_texture is not None:
                self._gl_texture.release()
                self._gl_texture = None
            if hasattr(self, '_line_holders'):
                for h in self._line_holders:
                    if hasattr(h, '_gl_texture') and h._gl_texture is not None:
                        h._gl_texture.release()
                        h._gl_texture = None
            self._cached_rendered_lines = None
            self.rendered_surface = None
            self.text = text
        elif text is None:
            text = self.text 
        if z_order is None: z_order = self.z_order

        fontmax = self.fontmax if fontmax is None else fontmax

        if self.reset: self.update(text, fontmax)

        if coords is None: coords = self.parent.abs_origin()    
        if colour is None: colour = self.colour
        colour_index = self.colours.get(colour)

        if hasattr(self, 'font') and self.font is not None:
            lines = self.drawtext if isinstance(self.drawtext, list) else [self.drawtext[0]]
            line_height = self.font.get_height()
            total_height = line_height * len(lines)
            
            # Line texture holders for multi-line support without leaks
            if len(lines) == 1:
                holder = self
            else:
                if not hasattr(self, '_line_holders'):
                    self._line_holders = []
                while len(self._line_holders) < len(lines):
                    class LineHolder:
                        _gl_texture = None
                    self._line_holders.append(LineHolder())
                holder = None

            col_key = tuple(colour_index) if isinstance(colour_index, (list, tuple)) else colour_index
            draw_params = (tuple(lines), col_key, id(self.font))

            if self._cached_rendered_lines is not None and self._cached_draw_params == draw_params:
                rendered_lines = self._cached_rendered_lines
            else:
                rendered_lines = []
                for line in lines:
                    try:
                        rendered_lines.append(self.font.render(line, True, colour_index))
                    except pygame.error as e:
                        print(f"Text.draw Pygame Render ERROR for line '{line}': {e}")
                        rendered_lines.append(None)
                self._cached_rendered_lines = rendered_lines
                self._cached_draw_params = draw_params
            
            for i, info in enumerate(rendered_lines):
                if info is None:
                    continue
                size = info.get_rect()
                line_coords = list(self.parent.align_coords(coords, size[-2:], self.justify))
                start_y_offset = -(total_height / 2) + (line_height / 2)
                line_coords[1] += int(start_y_offset + (i * line_height))
                
                line_holder = holder if holder is not None else self._line_holders[i]
                self.parent.platform.renderer.blit(info, line_coords, texture_holder=line_holder, z_order=z_order)

    def drawVectoredText(self, val, text=None, colour=None, z_order=None):
        if z_order is None: z_order = self.z_order
        if text is None:
            text = self.text

        xy = self.parent.anglexy(val, self.radius)
        w, h = self.textsize(text)

        # print(f"[TEXT TELEMETRY] text='{text}' | val={val} | text_radius={self.radius} | "
        #       f"parent_type={type(self.parent).__name__} | "
        #       f"parent_centre={getattr(self.parent, 'centre', 'N/A')} | "
        #       f"parent_min_offset={getattr(self.parent, 'min_offset', 'N/A')} | "
        #       f"parent_circle_scale={getattr(self.parent, 'circle_scale', 'N/A')} | "
        #       f"computed_xy={xy} | text_size=({w}, {h})")

        x = int(xy[0] - w / 2)
        y = int(xy[1] - h / 2)
        if colour is None: colour = self.colour
        colour_index = self.colours.get(colour)
        col_key = tuple(colour_index) if isinstance(colour_index, (list, tuple)) else colour_index

        if text == self.text and self.rendered_surface and self.last_params == (text, col_key, id(self.font)):
            surface = self.rendered_surface
            self.parent.platform.renderer.blit(surface, (x, y), texture_holder=self, z_order=z_order)
        else:
            surface = self.font.render(text, True, colour_index)
            self.rendered_surface = surface
            self.last_params = (text, col_key, id(self.font))
            self.parent.platform.renderer.blit(surface, (x, y), z_order=z_order)

    def textsize(self, text=None, font=None):
        """ Return (w, h) metrics directly from font metrics without surface allocation """
        if text is None: text = self.text
        if font is None: font = self.font
        if font is None: return (0, 0)
        return font.size(text)


class Outline:
    def __init__(self, frame, outline):
        self.frame = frame
        self.blur_pass = None 

        if isinstance(outline, dict):
            self.style = OutlineStyle(**outline)
        elif isinstance(outline, OutlineStyle):
            self.style = outline
        else:
            self.style = None

    def draw(self, coords=None):
        if self.style is None:
            return [0, 0, 0, 0]

        if self.style.glow_intensity > 0 and self.style.softness > 0:
            gfx = getattr(self.frame.platform, 'gfx_driver', None)
            if gfx and hasattr(gfx, 'compositor'):
                g_col_name = self.style.glow_colour if self.style.glow_colour is not None else self.style.colour
                glow_color = self.frame.colours.get(g_col_name)
                
                hdr_color = [c * self.style.glow_intensity * 2.5 for c in glow_color[:3]] + [255]
                glow_w = max(4.0, self.style.width + (self.style.softness * 40.0))
                
                base_coords = self.frame.abs_outline()
                
                self.frame.platform.renderer.draw_rect(
                    hdr_color,
                    base_coords,
                    border_radius=self.style.radius,
                    width=-glow_w,
                    softness=self.style.softness, 
                    additive=True
                )

        if coords is None:
            coords = self.frame.abs_outline()

        colour_index = self.frame.colours.get(self.style.colour, opacity=self.style.opacity * 255)
        
        if self.style.width > 0:
            self.frame.platform.renderer.draw_rect(
                colour_index,
                coords,
                border_radius=self.style.radius,
                width=self.style.width
            )
        
        return coords     

    @property
    def w(self):
        if self.style is None:
            return 0
        else: 
            return self.style.width