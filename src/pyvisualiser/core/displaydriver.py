#!/usr/bin/env python
"""
Display driver classes

Low level platform dynamics and ModernGL hardware acceleration.
Unified coordinate architecture supporting High-DPI (Retina) and embedded Linux.

v1.0 baloothebear4 1 Dec 2023   Original, based on Pygame visualiser mockups
v1.1 baloothebear4 Feb 2024     refactored as part of pyvisualiser
v2.0 baloothebear4 Feb 2026     Major upgrade to port to OpenGL for speed and visual complexity
v2.1 baloothebear4 Nov 2026     Unified DisplayMetrics & Zero-Break Additive Batching
"""

import sys
import os
import math
import warnings
import numpy as np
import pygame
from pygame.locals import *
import moderngl

from .components import Outline
from .backgrounds import Background
from pyvisualiser.core.render import RenderPass, RenderContext, RenderTarget, Compositor, DisplayMetrics
from pyvisualiser.styles.profiles import ProfileManager

# Suppress sRGB profile warnings from asset PNGs
warnings.filterwarnings("ignore", category=UserWarning, module="pygame")


class PygameRenderer:
    """Fallback 2D CPU renderer for legacy displays."""
    def __init__(self, surface):
        self.surface = surface

    def draw_rect(self, color, rect, width=0, **kwargs):
        pygame.draw.rect(self.surface, color, rect, width, **kwargs)

    def blit(self, source, dest, area=None, special_flags=0, **kwargs):
        self.surface.blit(source, dest, area, special_flags)

    def draw_line(self, color, start_pos, end_pos, width=1):
        pygame.draw.line(self.surface, color, start_pos, end_pos, width)

    def draw_lines(self, color, closed, points, width=1):
        pygame.draw.lines(self.surface, color, closed, points, width)


"""
Intelligently probes the active Linux session on Raspberry Pi 5 / Debian 
and sets the appropriate SDL_VIDEODRIVER environment variables.
"""
def detect_linux_display_backend() -> str:

    # 1. Wayland Desktop (Raspberry Pi OS Bookworm Default)
    if "WAYLAND_DISPLAY" in os.environ:
        os.environ["SDL_VIDEODRIVER"] = "wayland"
        print(f"DisplayBackend> Detected Wayland compositor: {os.environ['WAYLAND_DISPLAY']}")
        return "wayland"

    # 2. X11 Session
    if "DISPLAY" in os.environ:
        os.environ["SDL_VIDEODRIVER"] = "x11"
        print(f"DisplayBackend> Detected X11 server: {os.environ['DISPLAY']}")
        return "x11"

    # 3. Headless Console / Direct Framebuffer (KMS/DRM)
    os.environ["SDL_VIDEODRIVER"] = "kmsdrm"
    os.environ["SDL_NOMOUSE"] = "1"
    
    # Dynamically find the active DRM card (prefer card1 or card0)
    card_path = None
    for card_idx in [1, 0, 2]:
        candidate = f"/dev/dri/card{card_idx}"
        if os.path.exists(candidate):
            card_path = candidate
            break

    if card_path:
        os.environ["SDL_VIDEODEVICE"] = card_path
        print(f"DisplayBackend> Console mode: bound KMS/DRM to {card_path}")
    else:
        print("DisplayBackend> Warning: No /dev/dri/card* found. Relying on default SDL DRM.")

    return "kmsdrm"

class GraphicsDriverPi:
    """Raspberry Pi direct KMS/DRM framebuffer platform."""
    BACKGROUND_COLOR = (10, 10, 20)

    def __init__(self, events):
        profile = ProfileManager.get_profile()
        self.W = profile.target_resolution[0]
        self.H = profile.target_resolution[1]
        self.FPS = profile.framerate
        self.events = events
        self.PANEL = [self.W, self.H]

        self.clock = pygame.time.Clock()
        self.screen = self.init_display()
        self.renderer = PygameRenderer(self.screen)
        self.ave_area_pc = 0.0

        print(f"\nGraphicsDriverPi.init_display> Framebuffer Size: {self.screen.get_size()}")

    def init_display(self):
        os.environ['SDL_VIDEODRIVER'] = 'kmsdrm'
        if 'SDL_VIDEODEVICE' not in os.environ:
            os.environ['SDL_VIDEODEVICE'] = '/dev/dri/card1'

        os.environ['SDL_NOMOUSE'] = '1'

        pygame.display.init()
        pygame.font.init()

        self._physical_screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.virtual_surface = pygame.Surface((self.W, self.H))
        pygame.mouse.set_visible(False)

        self.background_surface = pygame.Surface(self.PANEL)
        self.background_surface.fill(GraphicsDriverPi.BACKGROUND_COLOR)
        self.background_surface = self.background_surface.convert()

        return self.virtual_surface

    def draw_start(self, text=None):
        if text is not None:
            pygame.display.set_caption(text)

    def draw_end(self):
        # Rotate -90 degrees for portrait-to-landscape Waveshare panel
        rotated_surface = pygame.transform.rotate(self.virtual_surface, -90)
        rotated_rect = rotated_surface.get_rect(center=self._physical_screen.get_rect().center)
        self._physical_screen.blit(rotated_surface, rotated_rect)
        pygame.display.flip()


class GraphicsDriverGL:
    """Hardware accelerated OpenGL/ModernGL platform using DisplayMetrics."""
    BACKGROUND_COLOR = (10, 10, 20)

    def __init__(self, events):
        profile = ProfileManager.get_profile()
        self.events = events
        self.W = profile.target_resolution[0]
        self.H = profile.target_resolution[1]
        self.FPS = profile.framerate
        self.PANEL = [self.W, self.H]

        self.clock = pygame.time.Clock()
        self.window = self.init_display()

        # 1. Determine High-DPI and Rotation Metrics cleanly
        logical_w, logical_h = self.W, self.H
        
        # Calculate scaling factor
        if sys.platform == "no_scale": # This prevents logical to pixel scaling
            # Mac would be "darwin" - but scaling does not work well so is deprecated
            # On macOS Cocoa with Retina backing, Pygame creates an OpenGL drawable 
            # whose physical resolution is double the logical points.
            desktop_sizes = pygame.display.get_desktop_sizes() if hasattr(pygame.display, 'get_desktop_sizes') else []
            dpi_scale = 2.0 if (desktop_sizes and desktop_sizes[0][0] > logical_w) else 1.0
        else:
            # Embedded Linux / Pi 5 defaults to native 1:1 pixel mapping
            dpi_scale = 1.0


        # Allow environment override
        if "PYVISUALISER_DPI_SCALE" in os.environ:
            dpi_scale = float(os.environ["PYVISUALISER_DPI_SCALE"])

        rotation = int(os.environ.get("PYVISUALISER_ROTATION", "0"))

        if sys.platform.startswith("linux"):
            detect_linux_display_backend()

        self.metrics = DisplayMetrics(
            logical_w=logical_w,
            logical_h=logical_h,
            dpi_scale=dpi_scale,
            rotation=rotation
        )

        print(f"\nGraphicsDriverGL.init_display> Logical: {self.metrics.logical_size}, "
              f"Physical: {self.metrics.physical_size}, DPI Scale: {self.metrics.dpi_scale:.2f}, "
              f"Aspect: {self.metrics.aspect_ratio:.2f}")

        # 2. ModernGL Core Pipeline Initialization
        # Context creation with OpenGL ES 3.1 fallback for Broadcom VideoCore VII (RPi 5)
        try:
            mgl_ctx = moderngl.create_context(require=330)
        except Exception as e:
            print(f"GraphicsDriverGL> OpenGL 3.3 Core unavailable ({e}). Falling back to OpenGL ES 3.1...")
            mgl_ctx = moderngl.create_context(require=310)

        # Query the actual physical drawable size from the pygame window / OpenGL surface
        # print(f"DEBUG: Default FBO 0 size: {mgl_ctx.fbo.size}")
        # if hasattr(mgl_ctx, 'screen') and mgl_ctx.screen:
        #     print(f"DEBUG: mgl_ctx.screen size: {mgl_ctx.screen.size}")

        self.render_context = RenderContext(mgl_ctx, self.metrics, platform=self)
        self.compositor = Compositor(self.render_context)

        # 3. GeometryPass handles 2D vector primitives and sharp UI
        self.geometry_pass = GeometryPass(self.render_context)
        self.compositor.add_ui_pass(self.geometry_pass)

        self.renderer = self.geometry_pass
        self.screen = pygame.Surface((self.W, self.H))
        self.ave_area_pc = 0.0



    def init_display(self):
        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)

        return pygame.display.set_mode((self.W, self.H), pygame.OPENGL | pygame.DOUBLEBUF)

    def draw_start(self, text=None):
        if text:
            pygame.display.set_caption(text)
        self.renderer.clear_batch()

    def draw_end(self):
        if getattr(self, 'show_debug_hud', False):
            self._render_debug_hud()
        self.compositor.render_frame()
        pygame.display.flip()

    def _render_debug_hud(self):
        controller = ProfileManager.get_controller()
        controls = controller.controls
        selected = controller.selected_parameter

        if not hasattr(self, '_hud_font'):
            self._hud_font = pygame.font.SysFont('monaco', 16)

        def fmt(name, key, val):
            prefix = "> " if name == selected else "  "
            return f"{prefix}{name.capitalize()[:8]:<8} ({key}): {val:.2f}"

        lines = [
            f"--- Profile HUD ({self.metrics.physical_w}x{self.metrics.physical_h} @ {self.metrics.dpi_scale}x) ---",
            fmt('intensity', 'q/a', controls.intensity),
            fmt('softness',  'w/s', controls.softness),
            fmt('threshold', 'z/x', controls.threshold),
            fmt('energy',    'e/d', controls.energy),
            fmt('warmth',    'c/v', controls.warmth),
            fmt('saturation','b/n', controls.saturation),
            fmt('vignette',  't/g', controls.vignette),
            fmt('sharpness', 'y/h', controls.sharpness),
            f"  Presets : 1/2/3",
            f"  Navigate: UP/DN/L/R"
        ]

        y = 10
        bg_surface = pygame.Surface((280, len(lines) * 20 + 10), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 180))
        self.renderer.blit(bg_surface, (5, 5))

        for line in lines:
            color = (255, 255, 255) if line.startswith(">") else (200, 255, 200)
            text_surface = self._hud_font.render(line, True, color)
            self.renderer.blit(text_surface, (10, y))
            y += 20


class GraphicsDriverMac:
    """Pygame CPU based platform for basic local debugging."""
    def __init__(self, events):
        profile = ProfileManager.get_profile()
        self.events = events
        self.W = profile.target_resolution[0]
        self.H = profile.target_resolution[1]
        self.FPS = profile.framerate
        self.PANEL = [self.W, self.H]

        self.screen = self.init_display()
        self.renderer = PygameRenderer(self.screen)
        self.clock = pygame.time.Clock()
        self.ave_area_pc = 0.0

        print(f"\nGraphicsDriverMac.init_display> Native Pygame Window: {self.screen.get_size()}")

    def init_display(self):
        pygame.init()
        return pygame.display.set_mode(self.PANEL)

    def draw_start(self, text=None):
        if text is not None:
            pygame.display.set_caption(text)

    def draw_end(self):
        pygame.display.flip()


class GraphicsDriver:
    """Unified Facade managing the active platform graphics backend."""
    def __init__(self, events, gfx='mac'):
        if gfx == 'pi_kms':
            self.gfx_driver = GraphicsDriverPi(events)
        elif gfx == 'gl':
            self.gfx_driver = GraphicsDriverGL(events)
        else:
            self.gfx_driver = GraphicsDriverMac(events)

        pygame.display.set_caption('pyvisualiser')
        self.screen = self.gfx_driver.screen

    def __getattr__(self, item):
        return getattr(self.gfx_driver, item)

    def refresh(self, rect=None):
        pygame.display.update(pygame.Rect(rect))

    def create_background(self, frame, background):
        return Background(frame, background)

    def create_outline(self, frame, outline):
        return Outline(frame, outline)

    def regulate_fps(self):
        self.gfx_driver.clock.tick(self.gfx_driver.FPS)

    def area_drawn(self):
        return self.gfx_driver.ave_area_pc

    def toggle_debug_hud(self):
        driver = self.gfx_driver
        driver.show_debug_hud = not getattr(driver, 'show_debug_hud', False)

    def clear_screen(self):
        self.screen.fill((0, 0, 0))

    @property
    def boundary(self):
        return [0, 0, self.gfx_driver.W - 1, self.gfx_driver.H - 1]

    @property
    def h(self):
        return self.gfx_driver.H

    @property
    def w(self):
        return self.gfx_driver.W

    @property
    def fps(self):
        return self.gfx_driver.FPS

    @property
    def wh(self):
        return (self.gfx_driver.W, self.gfx_driver.H)

    def graphics_end(self):
        pygame.quit()

    def checkKeys(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.events.KeyPress('exit')
            elif event.type == KEYDOWN:
                self.events.KeyPress(event.key)


# ==============================================================================
# GEOMETRY PASS (Unified Vector & SDF Quad Batcher)
# ==============================================================================

class GeometryPass(RenderPass):
    """
    Batched 2D geometry renderer.
    
    Transforms pure Logical Coordinates (Frame space: e.g. 0..1280, 0..400) directly 
    into OpenGL Normalized Device Coordinates (-1.0 to 1.0).
    The GPU automatically maps NDC to physical viewport pixels without CPU double-scaling.
    """
    def __init__(self, context: RenderContext):
        super().__init__(context)
        self.platform = context.platform
        self.metrics = context.metrics

        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.ONE, moderngl.ONE_MINUS_SRC_ALPHA
        self.current_additive = False

        self.prog = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec2 in_vert;
                in vec2 in_uv;
                in vec4 in_color;
                in float in_softness;
                in vec3 in_params;      // width, height, radius (logical pixels)
                in float in_stroke;      // stroke width (0 = fill)
                in vec2 in_segments;    // segment_size, gap_size
                in float in_axis;        // 0 = x (horz), 1 = y (vert)
                in float in_level;       // fill level or uv_scale.y
                in float in_use_tex;     // 0 = color, 1 = gradient, 2 = image
                in float in_is_additive; // 0.0 = normal alpha, 1.0 = additive glow

                out vec4 v_color;
                out vec2 v_uv;
                out vec2 v_uv_raw;
                out float v_softness;
                out vec3 v_params;
                out float v_stroke;
                out vec2 v_segments;
                out float v_axis;
                out float v_level;
                out float v_use_tex;
                out float v_is_additive;

                void main() {
                    gl_Position = vec4(in_vert, 0.0, 1.0);
                    v_color = in_color;
                    v_uv = in_uv;
                    v_uv_raw = in_uv;
                    v_softness = in_softness;
                    v_params = in_params;
                    v_stroke = in_stroke;
                    v_segments = in_segments;
                    v_axis = in_axis;
                    v_level = in_level;
                    v_use_tex = in_use_tex;
                    v_is_additive = in_is_additive;
                }
            """,
            fragment_shader="""
                #version 330
                in vec4 v_color;
                in vec2 v_uv;
                in vec2 v_uv_raw;
                in float v_softness;
                in vec3 v_params;
                in float v_stroke;
                in vec2 v_segments;
                in float v_axis;
                in float v_level;
                in float v_use_tex;
                in float v_is_additive;

                out vec4 f_color;
                uniform sampler2D gradient_tex;

                float sdRoundedBox(vec2 p, vec2 b, float r) {
                    vec2 q = abs(p) - b + r;
                    return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - r;
                }

                void main() {
                    vec2 size = v_params.xy;
                    float radius = v_params.z;
                    vec2 half_size = size * 0.5;
                    
                    vec2 pos = (v_uv - 0.5) * size;
                    float r = min(radius, min(half_size.x, half_size.y));
                    float dist = sdRoundedBox(pos, half_size, r);
                    
                    float seg_alpha = 1.0;
                    float alpha = 0.0;
                    
                    if (v_stroke < 0.0) {
                        float glow_radius = abs(v_stroke);
                        if (dist <= 0.0) {
                            alpha = smoothstep(-2.0, 0.0, dist);
                        } else if (dist < glow_radius) {
                            float falloff = dist / glow_radius;
                            alpha = pow(1.0 - falloff, 3.0) * exp(-falloff * 5.0);
                        } else {
                            alpha = 0.0;
                        }
                    } else if (v_stroke > 0.0) {
                        float blur = v_softness * 20.0;
                        float feather = max(0.5, blur);
                        float outer_alpha = 1.0 - smoothstep(-feather, feather, dist);
                        float inner_alpha = 1.0 - smoothstep(-feather, feather, dist + v_stroke);
                        alpha = outer_alpha - inner_alpha;
                    } else {
                        float min_dim = min(size.x, size.y);
                        float blur = v_softness * max(20.0, min_dim * 0.8); 
                        if (blur < 0.5) {
                            alpha = 1.0 - step(0.0, dist);
                        } else {
                            alpha = 1.0 - smoothstep(-blur, blur, dist);
                        }
                    }
                    
                    alpha *= seg_alpha;
                    vec4 final_color = v_color;
                    
                    if (v_use_tex > 1.5) {
                        vec2 tex_uv = v_segments + v_uv_raw * vec2(v_axis, v_level);
                        vec4 tex_col = texture(gradient_tex, tex_uv);
                        alpha = tex_col.a;
                        final_color = tex_col * v_color;
                    } else {
                        bool is_vert = (abs(v_axis) < 1.5);
                        float coord_uv = is_vert ? v_uv.y : v_uv.x;
                        if (v_axis < 0.0) coord_uv = 1.0 - coord_uv;
                        if (coord_uv > v_level) discard;

                        if (v_segments.x > 0.0 && v_segments.y > 0.0) {
                            float total_seg = v_segments.x + v_segments.y;
                            float size_px = is_vert ? size.y : size.x;
                            float coord_px = coord_uv * size_px;
                            float m = mod(coord_px, total_seg);
                            if (m > v_segments.x) discard;
                        }
                        
                        if (v_use_tex > 0.5) {
                            vec4 tex_col = texture(gradient_tex, vec2(coord_uv, 0.5));
                            final_color = vec4(tex_col.rgb, v_color.a);
                        }
                    }
                    
                    float out_alpha = final_color.a * alpha;
                    if (v_is_additive > 0.5) {
                        f_color = vec4(final_color.rgb * out_alpha * 2.0, 0.0);
                    } else {
                        f_color = vec4(final_color.rgb * out_alpha, out_alpha);
                    }
                }
            """
        )

        # 19 floats per vertex (18 base + in_is_additive)
        self.vbo = self.ctx.buffer(reserve=4 * 1024 * 1024)
        self.vao = self.ctx.simple_vertex_array(
            self.prog, self.vbo,
            'in_vert', 'in_uv', 'in_color', 'in_softness',
            'in_params', 'in_stroke', 'in_segments', 'in_axis',
            'in_level', 'in_use_tex', 'in_is_additive'
        )
        
        self.batches = []
        self.render_queue = []
        self.current_texture = None

    def clear_batch(self):
        self.batches.clear()
        self.render_queue.clear()
        self.current_texture = None

    def _push_batch(self):
        if self.render_queue:
            self.batches.append({
                'type': 'geometry',
                'texture': self.current_texture,
                'data': self.render_queue
            })
            self.render_queue = []

    def set_additive(self, additive):
        """Deprecated: No-op preserved for backward compatibility."""
        pass

    def draw_rect(self, color, rect, width=0, **kwargs):
        if hasattr(rect, 'rect'):
            coords = (rect.x, rect.y, rect.width, rect.height)
        elif isinstance(rect, (list, tuple)):
            coords = rect
        else:
            coords = (rect.x, rect.y, rect.width, rect.height)

        radius = kwargs.get('border_radius', 0.0)
        if radius == 0:
            radius = max(
                kwargs.get('border_top_left_radius', 0),
                kwargs.get('border_top_right_radius', 0),
                kwargs.get('border_bottom_left_radius', 0),
                kwargs.get('border_bottom_right_radius', 0)
            )

        segments = kwargs.get('segments', (0.0, 0.0))

        # Optional Drop Shadow
        shadow = kwargs.get('shadow')
        if shadow:
            s_offset = shadow.get('offset', (10, 10))
            s_color = shadow.get('color', (0, 0, 0))
            s_opacity = shadow.get('opacity', 128)
            s_softness = shadow.get('softness', 0.5)
            s_coords = (coords[0] + s_offset[0], coords[1] + s_offset[1], coords[2], coords[3])
            self.add_rect(s_coords, s_color, s_opacity, s_softness, 0, radius, (0.0, 0.0), axis=1.0, is_additive=0.0)

        opacity = color[3] if len(color) > 3 else 255
        softness = kwargs.get('softness', 0.0)
        gradient = kwargs.get('gradient')
        axis = kwargs.get('axis', 1.0)
        level = kwargs.get('level', 10.0)
        gradient_image = kwargs.get('gradient_image')
        texture_holder = kwargs.get('texture_holder')

        additive = kwargs.get('additive', False)
        is_additive = 1.0 if additive else 0.0

        if gradient_image:
            texture = None
            if texture_holder and hasattr(texture_holder, '_gl_texture') and texture_holder._gl_texture:
                texture = texture_holder._gl_texture
            
            if texture is None:
                if texture_holder and hasattr(texture_holder, '_gl_texture') and texture_holder._gl_texture is not None:
                    texture_holder._gl_texture.release()
                    texture_holder._gl_texture = None

                rgba_data = pygame.image.tostring(gradient_image, "RGBA", False)
                texture = self.ctx.texture(gradient_image.get_size(), 4, rgba_data)
                texture.build_mipmaps()
                texture.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
                
                if texture_holder:
                    texture_holder._gl_texture = texture

            if self.current_texture != texture:
                self._push_batch()
                self.current_texture = texture

            self.add_rect(coords, color, opacity, softness, width, radius, segments, gradient, axis, level, use_tex=1.0, is_additive=is_additive)
        else:
            self.add_rect(coords, color, opacity, softness, width, radius, segments, gradient, axis, level, use_tex=0.0, is_additive=is_additive)

    def add_rect(self, coords, color, opacity, softness, stroke_width, radius, segments, gradient=None, axis=1.0, level=1.0, use_tex=0.0, is_additive=0.0):
        """
        Maps LOGICAL coordinates (x, y, w, h) into Clip Space [-1.0, 1.0].
        No manual dpi_scale multiplication here; GPU viewports handle raster scaling.
        """
        x, y, w, h = coords
        if w <= 0 or h <= 0:
            return

        padding = 10.0 + abs(stroke_width)
        if softness > 0.0:
            min_dim = min(w, h)
            blur_radius = softness * max(20.0, min_dim * 0.8)
            padding += blur_radius * 1.5

        # Strictly use LOGICAL coordinates for NDC normalization
        sw, sh = float(self.context.metrics.logical_w), float(self.context.metrics.logical_h)

        x1 = ((x - padding) / sw) * 2.0 - 1.0
        y1 = 1.0 - ((y - padding) / sh) * 2.0
        x2 = ((x + w + padding) / sw) * 2.0 - 1.0
        y2 = 1.0 - ((y + h + padding) / sh) * 2.0

        r0, g0, b0 = [c / 255.0 for c in color[:3]]
        a = opacity / 255.0
        c_tl = c_tr = c_bl = c_br = (r0, g0, b0)

        if gradient:
            c_start, c_end = gradient
            rs, gs, bs = [pow(c / 255.0, 2.2) for c in c_start[:3]]
            re, ge, be = [pow(c / 255.0, 2.2) for c in c_end[:3]]

            if abs(axis) < 1.5:
                c_tl = c_tr = (rs, gs, bs)
                c_bl = c_br = (re, ge, be)
            else:
                c_tl = c_bl = (rs, gs, bs)
                c_tr = c_br = (re, ge, be)

        s = softness
        w_px, h_px = w, h
        seg_w, seg_gap = segments

        u_start = -padding / w
        u_end = 1.0 + padding / w
        v_start = -padding / h
        v_end = 1.0 + padding / h

        # 19 floats per vertex (6 vertices per quad)
        rect_data = [
            x1, y1, u_start, v_start, c_tl[0], c_tl[1], c_tl[2], a, s, w_px, h_px, radius, stroke_width, seg_w, seg_gap, axis, level, use_tex, is_additive,
            x2, y1, u_end,   v_start, c_tr[0], c_tr[1], c_tr[2], a, s, w_px, h_px, radius, stroke_width, seg_w, seg_gap, axis, level, use_tex, is_additive,
            x1, y2, u_start, v_end,   c_bl[0], c_bl[1], c_bl[2], a, s, w_px, h_px, radius, stroke_width, seg_w, seg_gap, axis, level, use_tex, is_additive,

            x1, y2, u_start, v_end,   c_bl[0], c_bl[1], c_bl[2], a, s, w_px, h_px, radius, stroke_width, seg_w, seg_gap, axis, level, use_tex, is_additive,
            x2, y1, u_end,   v_start, c_tr[0], c_tr[1], c_tr[2], a, s, w_px, h_px, radius, stroke_width, seg_w, seg_gap, axis, level, use_tex, is_additive,
            x2, y2, u_end,   v_end,   c_br[0], c_br[1], c_br[2], a, s, w_px, h_px, radius, stroke_width, seg_w, seg_gap, axis, level, use_tex, is_additive
        ]

        if (len(self.render_queue) + len(rect_data)) * 4 > self.vbo.size:
            self._push_batch()

        self.render_queue.extend(rect_data)

    def draw_line(self, color, start_pos, end_pos, width=1, softness=0.0, **kwargs):
        x1, y1 = start_pos
        x2, y2 = end_pos

        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)
        if length < 0.1:
            return

        ux = dx / length
        uy = dy / length
        px = -uy * width * 0.5
        py = ux * width * 0.5

        x_tl, y_tl = x1 + px, y1 + py
        x_tr, y_tr = x2 + px, y2 + py
        x_bl, y_bl = x1 - px, y1 - py
        x_br, y_br = x2 - px, y2 - py

        sw, sh = float(self.context.metrics.logical_w), float(self.context.metrics.logical_h)

        def to_gl(x, y):
            return (x / sw) * 2.0 - 1.0, 1.0 - (y / sh) * 2.0

        xtl, ytl = to_gl(x_tl, y_tl)
        xtr, ytr = to_gl(x_tr, y_tr)
        xbl, ybl = to_gl(x_bl, y_bl)
        xbr, ybr = to_gl(x_br, y_br)

        r, g, b = [pow(c / 255.0, 2.2) for c in color[:3]]
        a = (color[3] / 255.0) if len(color) > 3 else 1.0
        s = softness
        is_additive = 1.0 if kwargs.get('additive', False) else 0.0

        rect_data = [
            xtl, ytl, 0.0, 0.0, r, g, b, a, s, length, width, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, is_additive,
            xtr, ytr, 1.0, 0.0, r, g, b, a, s, length, width, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, is_additive,
            xbl, ybl, 0.0, 1.0, r, g, b, a, s, length, width, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, is_additive,

            xbl, ybl, 0.0, 1.0, r, g, b, a, s, length, width, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, is_additive,
            xtr, ytr, 1.0, 0.0, r, g, b, a, s, length, width, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, is_additive,
            xbr, ybr, 1.0, 1.0, r, g, b, a, s, length, width, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, is_additive
        ]

        if (len(self.render_queue) + len(rect_data)) * 4 > self.vbo.size:
            self._push_batch()

        self.render_queue.extend(rect_data)

    def draw_lines(self, color, closed, points, width=1, softness=0.0):
        if len(points) < 2:
            return

        for i in range(len(points) - 1):
            self.draw_line(color, points[i], points[i + 1], width, softness)

        if closed:
            self.draw_line(color, points[-1], points[0], width, softness)

    def render(self, **kwargs):
        self._push_batch()

        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.ONE, moderngl.ONE_MINUS_SRC_ALPHA

        for batch in self.batches:
            if batch['type'] == 'geometry':
                if batch['texture']:
                    batch['texture'].use(location=0)
                else:
                    self.context.empty_texture.use(location=0)
                self.prog['gradient_tex'].value = 0

                data = np.array(batch['data'], dtype='f4')
                self.vbo.write(data)
                self.vao.render(moderngl.TRIANGLES, vertices=len(data) // 19)

        self.batches.clear()
        self.render_queue.clear()

    def blit(self, source, dest, area=None, special_flags=0, **kwargs):
        texture = None
        texture_holder = kwargs.get('texture_holder')

        if texture_holder and hasattr(texture_holder, '_gl_texture') and texture_holder._gl_texture:
            texture = texture_holder._gl_texture

        if texture is None:
            if source.get_flags() & pygame.SRCALPHA:
                work_surf = source
            else:
                work_surf = source.convert_alpha()

            rgba_data = pygame.image.tostring(work_surf, "RGBA", False)

            if texture_holder and hasattr(texture_holder, '_gl_texture') and texture_holder._gl_texture is not None:
                texture_holder._gl_texture.release()
                texture_holder._gl_texture = None

            texture = self.ctx.texture(source.get_size(), 4, rgba_data)
            # ensure that images scale properly with logical coordinates and high-DPI displays
            texture = self.ctx.texture(source.get_size(), 4, rgba_data)
            texture.build_mipmaps()
            texture.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
            
            if texture_holder:
                texture_holder._gl_texture = texture

        if self.current_texture != texture:
            self._push_batch()
            self.current_texture = texture

        if hasattr(dest, 'x'):
            x, y = dest.x, dest.y
        else:
            x, y = dest[:2]

        opacity = kwargs.get('opacity', 255) / 255.0
        reflection = kwargs.get('reflection')
        is_additive = 1.0 if kwargs.get('additive', False) else 0.0

        w, h = source.get_size()
        sw, sh = float(self.context.metrics.logical_w), float(self.context.metrics.logical_h)

        # NDC conversion from pure logical coords
        x1 = (x / sw) * 2.0 - 1.0
        y1 = 1.0 - (y / sh) * 2.0
        x2 = ((x + w) / sw) * 2.0 - 1.0
        y2 = 1.0 - ((y + h) / sh) * 2.0

        tex_coords = kwargs.get('tex_coords', (0.0, 0.0, 1.0, 1.0))
        u_off, v_off, u_scale, v_scale = tex_coords

        img_data = [
            x1, y1, 0.0, 0.0, 1.0, 1.0, 1.0, opacity, 0.0, w, h, 0.0, 0.0, u_off, v_off, u_scale, v_scale, 2.0, is_additive,
            x2, y1, 1.0, 0.0, 1.0, 1.0, 1.0, opacity, 0.0, w, h, 0.0, 0.0, u_off, v_off, u_scale, v_scale, 2.0, is_additive,
            x1, y2, 0.0, 1.0, 1.0, 1.0, 1.0, opacity, 0.0, w, h, 0.0, 0.0, u_off, v_off, u_scale, v_scale, 2.0, is_additive,

            x1, y2, 0.0, 1.0, 1.0, 1.0, 1.0, opacity, 0.0, w, h, 0.0, 0.0, u_off, v_off, u_scale, v_scale, 2.0, is_additive,
            x2, y1, 1.0, 0.0, 1.0, 1.0, 1.0, opacity, 0.0, w, h, 0.0, 0.0, u_off, v_off, u_scale, v_scale, 2.0, is_additive,
            x2, y2, 1.0, 1.0, 1.0, 1.0, 1.0, opacity, 0.0, w, h, 0.0, 0.0, u_off, v_off, u_scale, v_scale, 2.0, is_additive
        ]

        self.render_queue.extend(img_data)

        if reflection:
            ref_size = 0.3
            ref_opacity = 0.5
            if isinstance(reflection, dict):
                ref_size = reflection.get('size', ref_size)
                ref_opacity = reflection.get('opacity', ref_opacity)

            h_gl = y1 - y2
            h_ref_gl = h_gl * ref_size
            y1_ref = y2
            y2_ref = y2 - h_ref_gl

            ref_data = [
                x1, y1_ref, 0.0, 1.0, 1.0, 1.0, 1.0, ref_opacity, 0.0, w, h_ref_gl, 0.0, 0.0, u_off, v_off, u_scale, v_scale, 2.0, is_additive,
                x2, y1_ref, 1.0, 1.0, 1.0, 1.0, 1.0, ref_opacity, 0.0, w, h_ref_gl, 0.0, 0.0, u_off, v_off, u_scale, v_scale, 2.0, is_additive,
                x1, y2_ref, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0,         0.0, w, h_ref_gl, 0.0, 0.0, u_off, v_off, u_scale, v_scale, 2.0, is_additive,

                x1, y2_ref, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0,         0.0, w, h_ref_gl, 0.0, 0.0, u_off, v_off, u_scale, v_scale, 2.0, is_additive,
                x2, y1_ref, 1.0, 1.0, 1.0, 1.0, 1.0, ref_opacity, 0.0, w, h_ref_gl, 0.0, 0.0, u_off, v_off, u_scale, v_scale, 2.0, is_additive,
                x2, y2_ref, 1.0, 0.0, 1.0, 1.0, 1.0, 0.0,         0.0, w, h_ref_gl, 0.0, 0.0, u_off, v_off, u_scale, v_scale, 2.0, is_additive
            ]

            self.render_queue.extend(ref_data)