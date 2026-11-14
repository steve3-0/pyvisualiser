'''
Mar 2026 Baloothebear4 v1

Background system supporting both full-screen and localized sub-frame
GPU-accelerated procedural backgrounds, edge lighting, shaders, and textures.
'''

import os
import re
import time
import random
import pygame
import moderngl
import numpy as np

from pyvisualiser.core.framecore import Frame, Cache, Colour, get_asset_path
from pyvisualiser.core.components import Image
from pyvisualiser.core.render import RenderPass, RenderContext, RenderTarget
from pyvisualiser.styles.styles import *


class Background:
    """Legacy compatibility wrapper directing to modern OpenGL BackgroundBase."""
    def __init__(self, frame, background=None):
        self.frame = frame
        self.background = background
        self.background_base = None

        if background is None:
            self.background_base = None
        elif isinstance(background, BackgroundStyle):
            self.background_base = BackgroundBase(frame, background)
        else:
            # Fallback wrapper for string colors or legacy dicts
            self.background_base = BackgroundBase(frame, BackgroundStyle())

    def draw(self):
        if self.background_base is not None:
            self.background_base.draw()

    def is_per_frame_update(self):
        return True

    def __str__(self):
        return str(self.background)


class BackgroundLighting:
    """Manages audio-reactive state for background shaders and glows."""
    def __init__(self, style: BackgroundStyle):
        self.style = style
        self.reactive_intensity = 0.0
        self.peak_intensity = 0.0
        self.cloud_intensity = 0.0
        self.audio_vu = 0.0
        self.bass = 0.0
        self.treble = 0.0
        self.audio_analysis = {}
        self.last_update = time.time()

    def update(self, audio_processor):
        if not audio_processor:
            return

        now = time.time()
        dt = now - self.last_update
        self.last_update = now

        # 1. Reactive Glow
        rg = self.style.reactive_glow
        if rg:
            if not isinstance(rg, ReactiveGlowStyle):
                rg = ReactiveGlowStyle()
            target = 0.0
            if hasattr(audio_processor, 'vu'):
                vu = audio_processor.vu.get('mono', 0.0)
                if vu > rg.threshold:
                    target = (vu - rg.threshold) / max(0.001, (1.0 - rg.threshold))
            rate = rg.attack if target > self.reactive_intensity else rg.decay
            self.reactive_intensity += (target - self.reactive_intensity) * rate

        # 2. Peak Accent
        pa = self.style.peak_accent
        if pa:
            if not isinstance(pa, PeakAccentStyle):
                pa = PeakAccentStyle()
            target_peak = 0.0
            if hasattr(audio_processor, 'vu') and audio_processor.vu.get('mono', 0.0) > pa.threshold:
                target_peak = 1.0
            rate = pa.attack if target_peak > self.peak_intensity else pa.decay
            self.peak_intensity += (target_peak - self.peak_intensity) * rate

        # 3. Direct Audio Metrics
        if hasattr(audio_processor, 'vu'):
            self.audio_vu = float(audio_processor.vu.get('mono', 0.0))
            self.bass = float(getattr(audio_processor, 'bass', 0.0))
            self.treble = float(getattr(audio_processor, 'treble', 0.0))
            if hasattr(audio_processor, 'get_analysis'):
                self.audio_analysis = audio_processor.get_analysis() or {}


class BackgroundSurface:
    """Manages static background textures."""
    def __init__(self, style: BackgroundStyle, context: RenderContext):
        self.style = style
        self.context = context
        self.texture: moderngl.Texture | None = None
        self._load_texture()

    def _load_texture(self):
        if not self.style.texture_path:
            return

        try:
            path = get_asset_path('backgrounds', self.style.texture_path)
            surface = pygame.image.load(path).convert_alpha()
            rgba_data = pygame.image.tostring(surface, "RGBA", False)
            self.texture = self.context.ctx.texture(surface.get_size(), 4, rgba_data)
            self.texture.build_mipmaps()
            self.texture.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
        except Exception as e:
            print(f"BackgroundSurface> Failed to load texture '{self.style.texture_path}': {e}")

    def __del__(self):
        if hasattr(self, 'texture') and self.texture is not None:
            try:
                self.texture.release()
            except Exception:
                pass
            self.texture = None


class BackgroundRenderPass(RenderPass):
    """
    Dedicated pass rendering procedural background layers, edge lighting,
    and injected custom GLSL pattern shaders.
    """
    DEFAULT_VERT = """
        #version 330
        in vec2 in_vert;
        in vec2 in_uv;
        out vec2 v_uv;
        void main() {
            gl_Position = vec4(in_vert, 0.0, 1.0);
            v_uv = in_uv;
        }
    """

    FRAGMENT_TEMPLATE = """
        #version 330
        in vec2 v_uv;
        out vec4 f_colour;

        uniform vec3 u_colour;
        uniform float u_colour_opacity;
        uniform float iTime;
        uniform vec2 iResolution;

        // Texture
        uniform bool u_has_texture;
        uniform sampler2D u_texture;
        uniform float u_texture_opacity;
        // Audio Analysis Uniforms (Available to all background shaders)
        uniform float u_volume;
        uniform float u_centroid;
        uniform float u_flux;
        uniform bool  u_beat;
        uniform float u_kurtosis;
        uniform float u_vu;
        uniform float u_bass;
        uniform float u_treble;

        // Vignette
        uniform float u_vignette_strength;
        uniform float u_vignette_radius;
        uniform float u_vignette_softness;

        // Noise
        uniform float u_noise_strength;

        // Ambient Glow
        uniform vec3 u_ambient_colour;
        uniform float u_ambient_opacity;
        uniform float u_ambient_radius;
        uniform float u_ambient_softness;

        // Reactive Glow
        uniform vec3 u_reactive_colour;
        uniform float u_reactive_intensity;

        // Peak Accent
        uniform vec3 u_peak_accent_colour;
        uniform float u_peak_intensity;

        // Starfield
        uniform float u_starfield_density;
        uniform float u_starfield_speed;

        // Cloud
        uniform float u_cloud_opacity;

        // Panel Edge Lighting
        uniform vec3  u_edge_colour;
        uniform float u_edge_intensity;
        uniform float u_edge_width;
        uniform float u_edge_softness;
        uniform float u_edge_audio_reactivity;
        uniform float u_aspect_ratio;
        uniform float u_audio_vu;

        // Dynamic Pattern Support
        uniform bool u_use_pattern;
        uniform vec2 u_frame_offset;
        uniform vec2 u_frame_size;
        uniform vec2 u_screen_size;

        float random(vec2 st) {
            return fract(sin(dot(st.xy, vec2(12.9898, 78.233))) * 43758.5453123);
        }

        float hash(vec2 p) {
            return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
        }

        float noise(vec2 p) {
            vec2 i = floor(p);
            vec2 f = fract(p);
            float a = hash(i);
            float b = hash(i + vec2(1.0, 0.0));
            float c = hash(i + vec2(0.0, 1.0));
            float d = hash(i + vec2(1.0, 1.0));
            vec2 u = f * f * (3.0 - 2.0 * f);
            return mix(a, b, u.x) + (c - a) * u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
        }

        float edge_mask(vec2 uv) {
            vec2 d = min(uv, 1.0 - uv);
            d.x *= u_aspect_ratio;
            float edge_dist = min(d.x, d.y);
            float edge = smoothstep(u_edge_width * 0.1, 0.0, edge_dist);
            return pow(edge, u_edge_softness);
        }

        // --- INJECTED PATTERN CODE START ---
        %s
        // --- INJECTED PATTERN CODE END ---

        void main() {
            vec4 colour = vec4(u_colour, u_colour_opacity);

            // 1. Dynamic Pattern Shader
            if (u_use_pattern) {
                vec2 screen_coords = u_frame_offset + v_uv * u_frame_size;
                vec4 pattern_col = run_pattern(u_screen_size, screen_coords);
                colour.rgb = mix(colour.rgb, pattern_col.rgb, pattern_col.a);
            }

            // 2. Texture Layer
            if (u_has_texture) {
                vec4 texcolour = texture(u_texture, v_uv);
                colour = mix(colour, texcolour, u_texture_opacity);
            }

            // 3. Film Grain Noise
            if (u_noise_strength > 0.0) {
                float noise_val = random(v_uv + iTime * 0.1);
                colour.rgb += (noise_val - 0.5) * u_noise_strength;
            }

            // 4. Ambient Radial Glow
            if (u_ambient_opacity > 0.0) {
                vec2 centered_uv = v_uv - vec2(0.5, 0.0);
                centered_uv.x *= u_aspect_ratio;
                float dist = length(centered_uv);
                float glow = 1.0 - smoothstep(u_ambient_radius - u_ambient_softness, u_ambient_radius + u_ambient_softness, dist);
                colour.rgb = mix(colour.rgb, u_ambient_colour, clamp(glow * u_ambient_opacity, 0.0, 1.0));
            }

            // 5. Reactive Center Pulse
            if (u_reactive_intensity > 0.0) {
                vec2 centered = v_uv - vec2(0.5);
                centered.x *= u_aspect_ratio;
                float dist = length(centered);
                float glow = 1.0 - smoothstep(0.0, 0.6, dist);
                colour.rgb += u_reactive_colour * glow * u_reactive_intensity;
                colour.a = max(colour.a, glow * u_reactive_intensity);
            }

            // 6. Peak Flash Accent
            if (u_peak_intensity > 0.0) {
                vec2 centered = v_uv - vec2(0.5);
                centered.x *= u_aspect_ratio;
                float peak_dist = length(centered);
                float peak_glow = (1.0 - smoothstep(0.05, 0.2, peak_dist)) * u_peak_intensity;
                colour.rgb += u_peak_accent_colour * peak_glow;
                colour.a = max(colour.a, peak_glow);
            }

            // 7. Vignette
            if (u_vignette_strength > 0.0) {
                vec2 centered = v_uv - vec2(0.5);
                centered.x *= u_aspect_ratio;
                float d = length(centered);
                float v = smoothstep(u_vignette_radius, u_vignette_radius + u_vignette_softness, d);
                colour.rgb = mix(colour.rgb, vec3(0.0), clamp(v * u_vignette_strength, 0.0, 1.0));
            }

            // 8. Procedural Starfield
            if (u_starfield_density > 0.0) {
                for (float i = 1.0; i <= 3.0; i += 1.0) {
                    float speed = u_starfield_speed * 0.05 * i;
                    vec2 shift = vec2(iTime * speed, 0.0);
                    vec2 uv_scaled = v_uv * 10.0 * i + shift;
                    vec2 id = floor(uv_scaled);
                    vec2 pos = fract(uv_scaled) - 0.5;
                    float n = random(id);
                    if (n > (1.0 - u_starfield_density * 0.002)) {
                        float size = 0.1 * n;
                        float star = 1.0 - smoothstep(0.0, size, length(pos));
                        colour.rgb += vec3(star * n);
                    }
                }
            }

            // 9. Procedural Vapor Clouds
            if (u_cloud_opacity > 0.0) {
                vec2 center = v_uv - 0.5;
                center.x *= u_aspect_ratio;
                float dist = length(center);
                float vig = 1.0 - smoothstep(0.3, 0.9, dist);
                float t = iTime * 0.05;
                float n = noise(v_uv * 4.0 + vec2(t, t * 0.3));
                float n2 = noise(v_uv * 2.0 - vec2(t * 0.2, t * 0.5));
                float blend = mix(n, n2, 0.5);
                float brightness = pow(blend, 1.5) * 0.6 + 0.15 + pow(u_audio_vu, 0.5) * 0.05;
                vec3 col1 = max(u_colour * 4.0, vec3(0.01));
                vec3 col2 = u_colour * 25.0 + 0.05;
                vec3 cloud_rgb = mix(col1, col2, pow(blend, 1.4));
                colour.rgb = mix(colour.rgb, cloud_rgb * brightness * vig, u_cloud_opacity);
            }

            // 10. Panel Edge Ambient Lighting
            if (u_edge_intensity > 0.0) {
                float edge = edge_mask(v_uv);
                float audio_boost = 1.0 + pow(u_audio_vu, 0.5) * u_edge_audio_reactivity;
                vec3 edge_col = mix(u_colour, vec3(1.0), 0.7) + 0.05;
                colour.rgb += edge_col * edge * u_edge_intensity * audio_boost;
            }

            f_colour = colour;
        }
    """

    def __init__(self, context: RenderContext, style: BackgroundStyle, surface: BackgroundSurface, lighting: BackgroundLighting):
        super().__init__(context)
        self.style = style
        self.surface = surface
        self.lighting = lighting
        self.start_time = time.time()
        self.viewport: tuple[int, int, int, int] | None = None  # Physical (x, y, w, h) for sub-frames

        # Dynamic shader injection
        shader_name = style.shader
        if shader_name is True:
            shader_name = 'balatro'

        pattern_code = ""
        if shader_name:
            pattern_code = self._load_shader_pattern(shader_name)

        if not pattern_code:
            pattern_code = "vec4 run_pattern(vec2 s, vec2 c) { return vec4(0.0); }"

        self.prog = self.ctx.program(
            vertex_shader=self.DEFAULT_VERT,
            fragment_shader=self.FRAGMENT_TEMPLATE % pattern_code
        )
        self.quad_vao = self.ctx.simple_vertex_array(self.prog, context.get_quad_buffer(), 'in_vert', 'in_uv')

    def _load_shader_pattern(self, shader_name: str) -> str:
        try:
            path = None
            for ext in ['.glsl', '.frag.glsl']:
                try:
                    p = get_asset_path('shaders', f"{shader_name}{ext}")
                    if os.path.exists(p):
                        path = p
                        break
                except Exception:
                    pass

            if not path or not os.path.exists(path):
                return ""

            with open(path, 'r', encoding='utf-8') as f:
                src = f.read()

            src = re.sub(r'#version\s+\d+', '', src)
            common_to_strip = [
                'v_uv', 'iTime', 'iResolution', 'u_colour', 'u_colour_opacity',
                'u_volume', 'u_centroid', 'u_flux', 'u_beat', 'u_kurtosis',
                'u_vu', 'u_bass', 'u_treble'
            ]
            for u in common_to_strip:
                src = re.sub(rf'uniform\s+\w+\s+{u}\s*;', '', src)
                src = re.sub(rf'in\s+vec2\s+{u}\s*;', '', src)

            src = "vec4 pattern_out = vec4(0.0);\n" + src
            for out_name in ['f_colour', 'f_color', 'fragColor']:
                if re.search(rf'out\s+vec4\s+{out_name}\s*;', src) or out_name in src:
                    src = re.sub(rf'out\s+vec4\s+{out_name}\s*;', '', src)
                    src = re.sub(rf'\b{out_name}\b', 'pattern_out', src)

            if 'void main()' in src:
                src = re.sub(r'\bvoid\s+main\s*\(\s*\)', 'void pattern_main()', src)

            code = f"""
{src}
vec4 run_pattern(vec2 screenSize, vec2 screen_coords) {{
    pattern_out = vec4(0.0, 0.0, 0.0, 1.0);
    vec2 iResolution = screenSize;
    #ifdef PATTERN_USES_EFFECT
        pattern_out = effect(screenSize, screen_coords);
    #else
        pattern_main();
    #endif
    return pattern_out;
}}
"""
            if 'vec4 effect(' in src:
                code = "#define PATTERN_USES_EFFECT\n" + code
            elif 'pattern_main()' not in code:
                code += "\nvoid pattern_main() { pattern_out = vec4(1.0, 0.0, 1.0, 1.0); }\n"

            return code
        except Exception as e:
            print(f"BackgroundRenderPass> Error compiling shader '{shader_name}': {e}")
            return ""

    def render(self, target: RenderTarget | None = None, **kwargs):
        # 1. Target and Viewport / Scissor Configuration
        if target:
            target.use()
            target_w, target_h = target.width, target.height
        else:
            if self.ctx.screen is not None:
                self.ctx.screen.use()
            else:
                self.ctx.fbo.use()
            target_w, target_h = self.context.physical_width, self.context.physical_height

        # Handle Sub-Frame clipping vs Full-Screen rendering
        original_scissor = self.ctx.scissor
        if self.viewport is not None:
            vx, vy, vw, vh = self.viewport
            self.ctx.viewport = (vx, vy, vw, vh)
            # Setting ctx.scissor enables the scissor test in ModernGL automatically
            self.ctx.scissor = (vx, vy, vw, vh)
            aspect = float(vw / max(1, vh))
            eff_w, eff_h = vw, vh
            frame_off = (float(vx), float(vy))
            frame_sz = (float(vw), float(vh))
        else:
            self.ctx.viewport = (0, 0, target_w, target_h)
            # Setting ctx.scissor = None disables scissor testing
            self.ctx.scissor = None
            aspect = float(target_w / max(1, target_h))
            eff_w, eff_h = target_w, target_h
            frame_off = (0.0, 0.0)
            frame_sz = (float(target_w), float(target_h))

        # 2. Pipeline State
        self.ctx.disable(moderngl.DEPTH_TEST)
        self.ctx.disable(moderngl.CULL_FACE)
        self.ctx.depth_mask = False
        self.ctx.blend_func_separate = (
            moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA,
            moderngl.ONE, moderngl.ONE_MINUS_SRC_ALPHA
        )

        # 3. Time, Resolution & Coordinate Uniforms
        self.prog['iTime'].value = time.time() - self.start_time
        if 'iResolution' in self.prog:
            self.prog['iResolution'].value = (float(eff_w), float(eff_h))
        if 'u_screen_size' in self.prog:
            self.prog['u_screen_size'].value = (float(target_w), float(target_h))
        if 'u_frame_offset' in self.prog:
            self.prog['u_frame_offset'].value = frame_off
        if 'u_frame_size' in self.prog:
            self.prog['u_frame_size'].value = frame_sz
        if 'u_aspect_ratio' in self.prog:
            self.prog['u_aspect_ratio'].value = aspect

        # Audio Reactive Uniforms
        if 'u_volume' in self.prog:
            self.prog['u_volume'].value = float(self.lighting.audio_vu)
        if 'u_vu' in self.prog:
            self.prog['u_vu'].value = float(self.lighting.audio_vu)
        if 'u_bass' in self.prog:
            self.prog['u_bass'].value = float(self.lighting.bass)
        if 'u_treble' in self.prog:
            self.prog['u_treble'].value = float(self.lighting.treble)

        if hasattr(self.lighting, 'audio_analysis'):
            for key, val in self.lighting.audio_analysis.items():
                u_key = f"u_{key}"
                if u_key in self.prog:
                    self.prog[u_key].value = int(val) if isinstance(val, bool) else float(val)

        # Base Colour Uniforms
        resolver = getattr(self, 'colour_resolver', lambda x: (0.0, 0.0, 0.0))
        self.prog['u_colour'].value = resolver(self.style.colour)
        if 'u_colour_opacity' in self.prog:
            op = float(self.style.colour_opacity) if self.style.colour is not None else 0.0
            self.prog['u_colour_opacity'].value = op

        # Texture Uniforms
        if self.surface.texture:
            self.surface.texture.use(location=0)
            self.prog['u_texture'].value = 0
            self.prog['u_texture_opacity'].value = float(self.style.texture_opacity)
            self.prog['u_has_texture'].value = True
        else:
            self.context.empty_texture.use(location=0)
            self.prog['u_texture'].value = 0
            self.prog['u_has_texture'].value = False

        # Vignette
        v = self.style.vignette
        if v:
            if not isinstance(v, VignetteStyle):
                v = VignetteStyle()
            self.prog['u_vignette_strength'].value = float(v.strength)
            self.prog['u_vignette_radius'].value = float(v.radius)
            self.prog['u_vignette_softness'].value = float(v.softness)
        else:
            self.prog['u_vignette_strength'].value = 0.0

        # Noise
        n = self.style.noise
        if n:
            if not isinstance(n, NoiseStyle):
                n = NoiseStyle()
            self.prog['u_noise_strength'].value = float(n.strength)
        else:
            self.prog['u_noise_strength'].value = 0.0

        # Ambient Glow
        ag = self.style.ambient_glow
        if ag:
            if not isinstance(ag, AmbientGlowStyle):
                ag = AmbientGlowStyle()
            self.prog['u_ambient_colour'].value = resolver(ag.colour)
            self.prog['u_ambient_opacity'].value = float(ag.opacity)
            self.prog['u_ambient_radius'].value = float(ag.radius)
            self.prog['u_ambient_softness'].value = float(ag.softness)
        else:
            self.prog['u_ambient_opacity'].value = 0.0

        # Reactive Glow
        rg = self.style.reactive_glow
        if rg:
            if not isinstance(rg, ReactiveGlowStyle):
                rg = ReactiveGlowStyle()
            self.prog['u_reactive_colour'].value = resolver(rg.colour)
            self.prog['u_reactive_intensity'].value = float(self.lighting.reactive_intensity)
        else:
            self.prog['u_reactive_intensity'].value = 0.0

        # Peak Accent
        pa = self.style.peak_accent
        if pa:
            if not isinstance(pa, PeakAccentStyle):
                pa = PeakAccentStyle()
            self.prog['u_peak_accent_colour'].value = resolver(pa.colour)
            self.prog['u_peak_intensity'].value = float(self.lighting.peak_intensity)
        else:
            self.prog['u_peak_intensity'].value = 0.0

        # Starfield
        sf = self.style.starfield
        if sf:
            if not isinstance(sf, StarfieldStyle):
                sf = StarfieldStyle()
            self.prog['u_starfield_density'].value = float(sf.density)
            self.prog['u_starfield_speed'].value = float(sf.speed)
        else:
            self.prog['u_starfield_density'].value = 0.0

        # Cloud
        cloud = self.style.cloud
        if cloud:
            if not isinstance(cloud, CloudStyle):
                cloud = CloudStyle()
            if 'u_cloud_opacity' in self.prog:
                self.prog['u_cloud_opacity'].value = float(cloud.opacity)
        else:
            if 'u_cloud_opacity' in self.prog:
                self.prog['u_cloud_opacity'].value = 0.0

        # Panel Edge Lighting
        edge_style = self.style.edge_light
        if edge_style:
            self.prog['u_edge_intensity'].value = float(edge_style.intensity)
            self.prog['u_edge_width'].value = float(edge_style.width)
            self.prog['u_edge_softness'].value = float(edge_style.softness)
            self.prog['u_edge_audio_reactivity'].value = float(edge_style.audio_reactivity)
            self.prog['u_audio_vu'].value = float(self.lighting.audio_vu)
        else:
            self.prog['u_edge_intensity'].value = 0.0

        self.prog['u_use_pattern'].value = bool(self.style.shader)

        # 4. Render
        self.quad_vao.render(moderngl.TRIANGLE_STRIP)

        # 5. Restore Scissor State
        self.ctx.scissor = original_scissor


class BackgroundBase:
    """Public background binding coordinating state, texture, and the render pass."""
    def __init__(self, frame, style: BackgroundStyle):
        self.frame = frame
        self.style = style
        self.engine = frame.platform.gfx_driver

        if not hasattr(self.engine, 'render_context'):
            print("BackgroundBase> Warning: OpenGL Backgrounds require GraphicsDriverGL.")
            return

        self.lighting = BackgroundLighting(style)
        self.surface = BackgroundSurface(style, self.engine.render_context)
        self.render_pass = BackgroundRenderPass(self.engine.render_context, style, self.surface, self.lighting)
        self.render_pass.colour_resolver = self._resolve_colour

    def _resolve_colour(self, colour_name):
        if not colour_name:
            return (0.0, 0.0, 0.0)
        col = self.frame.colours.get(colour_name)
        return tuple(c / 255.0 for c in col[:3])

    def update(self):
        self.lighting.update(self.frame.platform)

    def draw(self):
        self.update()

        if hasattr(self.engine, 'compositor'):
            # Detect whether this frame is the full screen or a localized sub-frame
            x, y, w, h = self.frame.abs_background()
            screen_w = self.frame.platform.W
            screen_h = self.frame.platform.H
            dpi_scale = getattr(self.engine.render_context, 'dpi_scale', 1.0)

            # Check if this frame matches the full logical screen bounds
            is_fullscreen = (x <= 0 and y <= 0 and w >= screen_w and h >= screen_h)

            if is_fullscreen:
                self.render_pass.viewport = None
            else:
                # Sub-frame (e.g. VU meter background): compute physical pixel bounds with OpenGL bottom-up Y
                gl_y = screen_h - (y + h)
                phys_x = int(round(x * dpi_scale))
                phys_y = int(round(gl_y * dpi_scale))
                phys_w = int(round(w * dpi_scale))
                phys_h = int(round(h * dpi_scale))
                self.render_pass.viewport = (phys_x, phys_y, phys_w, phys_h)

            self.engine.compositor.add_pre_pass(self.render_pass)


class ParticleSystem:
    """Drifting particulate dust for atmospheric depth."""
    def __init__(self, frame, config):
        self.frame = frame
        self.count = config.get('count', 50)
        self.colour = config.get('colour', 'light')
        self.speed = config.get('speed', 1.0)
        self.size = config.get('size', 2)
        self.softness = config.get('softness', 0.5)
        self.react_to_music = config.get('react_to_music', True)
        self.particles = []

        for _ in range(self.count):
            self.particles.append(self._reset_particle(start_random=True))

    def _reset_particle(self, start_random=False):
        w, h = self.frame.abs_wh
        x = random.randint(0, max(1, int(w)))
        y = random.randint(0, max(1, int(h))) if start_random else 0
        vx = (random.random() - 0.5) * self.speed
        vy = (random.random() * self.speed) + 0.5
        life = random.randint(50, 200)
        return [x, y, vx, vy, life, life]

    def draw(self):
        w, h = self.frame.abs_wh
        origin_x, origin_y = self.frame.abs_origin()
        col = self.frame.colours.get(self.colour)

        speed_mult = 1.0
        if self.react_to_music and hasattr(self.frame.platform, 'vu'):
            vu = self.frame.platform.vu.get('mono', 0.0)
            speed_mult = 1.0 + (vu * 3.0)

        for p in self.particles:
            p[0] += p[2] * speed_mult
            p[1] += p[3] * speed_mult
            p[4] -= 1

            if p[1] > h or p[4] <= 0 or p[0] < 0 or p[0] > w:
                new_p = self._reset_particle()
                p[:] = new_p[:]

            alpha = int(255 * (p[4] / p[5]))
            draw_col = list(col[:3]) + [alpha]

            draw_x = origin_x + p[0]
            draw_y = origin_y + (h - p[1])
            rect = (draw_x, draw_y, self.size, self.size)
            self.frame.platform.renderer.draw_rect(draw_col, rect, softness=self.softness)