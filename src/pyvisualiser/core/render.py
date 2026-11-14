'''
Mar 2026 Baloothebeare4 v1

Core rendering abstractions, DisplayMetrics, and Compositor pipeline.
Unified coordinate architecture supporting High-DPI (Retina) and embedded Linux.
'''
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
import moderngl
import numpy as np

from pyvisualiser.core.framecore import get_asset_path

BACKGROUND_colour = (10, 10, 20)  # Dark Blue/Grey, standard Hi-Fi background


# ==============================================================================
# 1. DISPLAY METRICS (Single Source of Truth)
# ==============================================================================

@dataclass
class DisplayMetrics:
    """
    Central specification of display coordinate spaces.
    
    Invariants:
    - Logical: Fixed UI layout space (e.g., 1280x400) used by Frames and Components.
    - Physical: Actual framebuffer pixel count (logical * dpi_scale).
    - Aspect Ratio: Always calculated from logical coordinates.
    """
    logical_w: int = 1280
    logical_h: int = 400
    dpi_scale: float = 1.0
    rotation: int = 0  # 0, 90, 180, 270 degrees for panel rotation

    @property
    def physical_w(self) -> int:
        return int(round(self.logical_w * self.dpi_scale))

    @property
    def physical_h(self) -> int:
        return int(round(self.logical_h * self.dpi_scale))

    @property
    def aspect_ratio(self) -> float:
        return float(self.logical_w / max(1, self.logical_h))

    @property
    def logical_size(self) -> tuple[int, int]:
        return (self.logical_w, self.logical_h)

    @property
    def physical_size(self) -> tuple[int, int]:
        return (self.physical_w, self.physical_h)


# ==============================================================================
# 2. CONTEXT & BUFFER MANAGEMENT
# ==============================================================================

class RenderContext:
    """
    Wraps the ModernGL context, DisplayMetrics, and shared full-screen geometry.
    """
    def __init__(self, ctx: moderngl.Context, metrics: DisplayMetrics | tuple[int, int], platform=None, dpi_scale: float = 1.0):
        self.ctx = ctx
        self.platform = platform
        
        if isinstance(metrics, DisplayMetrics):
            self.metrics = metrics
        else:
            self.metrics = DisplayMetrics(logical_w=metrics[0], logical_h=metrics[1], dpi_scale=dpi_scale)

        # Full-screen Quad in Clip Space (-1.0 to 1.0)
        self.quad_data = np.array([
            -1.0, -1.0, 0.0, 0.0,  # Bottom-Left
             1.0, -1.0, 1.0, 0.0,  # Bottom-Right
            -1.0,  1.0, 0.0, 1.0,  # Top-Left
             1.0,  1.0, 1.0, 1.0,  # Top-Right
        ], dtype='f4')
        self.quad_buffer = self.ctx.buffer(self.quad_data)

        # 1x1 Dummy texture to keep texture unit 0 valid and prevent feedback loops
        self.empty_texture = self.ctx.texture((1, 1), 4)
        self.empty_texture.write(b'\x00\x00\x00\x00')

    def resize(self, size: tuple[int, int], dpi_scale: float | None = None):
        self.metrics.logical_w = size[0]
        self.metrics.logical_h = size[1]
        if dpi_scale is not None:
            self.metrics.dpi_scale = dpi_scale
        self.ctx.viewport = (0, 0, self.metrics.physical_w, self.metrics.physical_h)

    def clear(self, colour=(0.0, 0.0, 0.0, 1.0)):
        self.ctx.clear(*colour)

    def get_quad_buffer(self) -> moderngl.Buffer:
        return self.quad_buffer

    @property
    def width(self) -> int:
        return self.metrics.logical_w

    @property
    def height(self) -> int:
        return self.metrics.logical_h

    @property
    def physical_width(self) -> int:
        return self.metrics.physical_w

    @property
    def physical_height(self) -> int:
        return self.metrics.physical_h

    @property
    def dpi_scale(self) -> float:
        return self.metrics.dpi_scale

    def __del__(self):
        if hasattr(self, 'empty_texture') and self.empty_texture:
            try:
                self.empty_texture.release()
            except Exception:
                pass
            self.empty_texture = None
        if hasattr(self, 'quad_buffer') and self.quad_buffer:
            try:
                self.quad_buffer.release()
            except Exception:
                pass
            self.quad_buffer = None


class RenderTarget:
    """
    Manages an off-screen Texture and Framebuffer Object (FBO).
    Allocates at native physical resolution: int(logical * dpi_scale * scale).
    """
    def __init__(self, context_or_ctx, size: tuple[int, int] | None = None, scale: float = 1.0, components: int = 4, dtype: str = 'f1'):
        if isinstance(context_or_ctx, RenderContext):
            self.context = context_or_ctx
            self.ctx = context_or_ctx.ctx
            self._explicit_size = size
        else:
            self.context = None
            self.ctx = context_or_ctx
            self._explicit_size = size

        self.scale = scale
        self.components = components
        self.dtype = dtype
        self.texture: moderngl.Texture | None = None
        self.fbo: moderngl.Framebuffer | None = None
        self._build()

    def _build(self):
        if self.texture is not None:
            self.texture.release()
            self.texture = None
        if self.fbo is not None:
            self.fbo.release()
            self.fbo = None

        if self._explicit_size is not None:
            w = max(1, int(round(self._explicit_size[0] * self.scale)))
            h = max(1, int(round(self._explicit_size[1] * self.scale)))
        elif self.context is not None:
            w = max(1, int(round(self.context.metrics.physical_w * self.scale)))
            h = max(1, int(round(self.context.metrics.physical_h * self.scale)))
        else:
            w, h = 100, 100

        self.texture = self.ctx.texture((w, h), self.components, dtype=self.dtype)
        self.texture.repeat_x = False
        self.texture.repeat_y = False
        self.texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.fbo = self.ctx.framebuffer(color_attachments=[self.texture])

    @property
    def width(self) -> int:
        return self.texture.width if self.texture else 1

    @property
    def height(self) -> int:
        return self.texture.height if self.texture else 1

    def resize(self, size: tuple[int, int] | None = None):
        if size is not None:
            self._explicit_size = size
        self._build()

    def use(self):
        """Binds this FBO and sets the viewport to its exact physical texture resolution."""
        self.fbo.use()
        self.ctx.viewport = (0, 0, self.texture.width, self.texture.height)

    def clear(self, colour=(0, 0, 0, 0)):
        self.fbo.clear(*colour)

    def __del__(self):
        if hasattr(self, 'texture') and self.texture is not None:
            try:
                self.texture.release()
            except Exception:
                pass
            self.texture = None
        if hasattr(self, 'fbo') and self.fbo is not None:
            try:
                self.fbo.release()
            except Exception:
                pass
            self.fbo = None


class PingPongBuffer:
    """Helper for iterative passes like Gaussian blur."""
    def __init__(self, context_or_ctx, size: tuple[int, int] | None = None, scale: float = 1.0, dtype: str = 'f2'):
        self.read = RenderTarget(context_or_ctx, size=size, scale=scale, dtype=dtype)
        self.write = RenderTarget(context_or_ctx, size=size, scale=scale, dtype=dtype)

    def swap(self):
        self.read, self.write = self.write, self.read

    def resize(self, size: tuple[int, int] | None = None):
        self.read.resize(size)
        self.write.resize(size)


# ==============================================================================
# 3. PASS ABSTRACTIONS & POST-PROCESSING
# ==============================================================================

class RenderPass(ABC):
    """Abstract base class for all shader and geometry passes."""
    def __init__(self, context: RenderContext):
        self.context = context
        self.ctx = context.ctx

    @abstractmethod
    def render(self, **kwargs):
        pass

    def resize(self, size: tuple[int, int]):
        pass


class TextureBlitPass(RenderPass):
    """Blits an input texture directly onto the target or screen."""
    def __init__(self, context: RenderContext):
        super().__init__(context)
        self.prog = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec2 in_vert;
                in vec2 in_uv;
                out vec2 v_uv;
                void main() {
                    gl_Position = vec4(in_vert, 0.0, 1.0);
                    v_uv = in_uv;
                }
            """,
            fragment_shader="""
                #version 330
                uniform sampler2D source_texture;
                in vec2 v_uv;
                out vec4 f_colour;
                void main() {
                    f_colour = texture(source_texture, v_uv);
                }
            """
        )
        self.vao = self.ctx.simple_vertex_array(self.prog, self.context.get_quad_buffer(), 'in_vert', 'in_uv')

    def render(self, input_target: RenderTarget, output_target: RenderTarget = None, **kwargs):
        if output_target:
            output_target.use()
            self.ctx.viewport = (0, 0, output_target.texture.width, output_target.texture.height)
        else:
            if self.ctx.screen is not None:
                self.ctx.screen.use()
            else:
                self.ctx.fbo.use()
            self.ctx.viewport = (0, 0, self.context.physical_width, self.context.physical_height)

        self.ctx.disable(moderngl.BLEND)
        input_target.texture.use(location=0)
        self.prog['source_texture'].value = 0
        self.vao.render(moderngl.TRIANGLE_STRIP)
        self.ctx.enable(moderngl.BLEND)


class BlurPass(RenderPass):
    """Separable 5-tap Gaussian Blur."""
    def __init__(self, context: RenderContext, iterations: int = 2):
        super().__init__(context)
        self.iterations = iterations
        self.prog = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec2 in_vert;
                in vec2 in_uv;
                out vec2 v_uv;
                void main() {
                    gl_Position = vec4(in_vert, 0.0, 1.0);
                    v_uv = in_uv;
                }
            """,
            fragment_shader="""
                #version 330
                uniform sampler2D image;
                uniform bool horizontal;
                uniform float spread;
                in vec2 v_uv;
                out vec4 f_colour;
                
                uniform float weight[5] = float[](0.227027, 0.1945946, 0.1216216, 0.054054, 0.016216);

                void main() {
                    vec2 tex_offset = 1.0 / textureSize(image, 0); 
                    vec3 result = texture(image, v_uv).rgb * weight[0]; 
                    
                    if (horizontal) {
                        for (int i = 1; i < 5; ++i) {
                            result += texture(image, v_uv + vec2(tex_offset.x * i * spread, 0.0)).rgb * weight[i];
                            result += texture(image, v_uv - vec2(tex_offset.x * i * spread, 0.0)).rgb * weight[i];
                        }
                    } else {
                        for (int i = 1; i < 5; ++i) {
                            result += texture(image, v_uv + vec2(0.0, tex_offset.y * i * spread)).rgb * weight[i];
                            result += texture(image, v_uv - vec2(0.0, tex_offset.y * i * spread)).rgb * weight[i];
                        }
                    }
                    f_colour = vec4(result, 1.0);
                }
            """
        )
        self.quad_vao = self.ctx.simple_vertex_array(self.prog, context.get_quad_buffer(), 'in_vert', 'in_uv')

    def render(self, ping_pong: PingPongBuffer, spread: float = 1.0, **kwargs):
        self.ctx.disable(moderngl.BLEND)
        self.prog['spread'].value = float(spread)

        for _ in range(self.iterations):
            # Horizontal Pass
            ping_pong.write.use()
            ping_pong.read.texture.use(location=0)
            self.prog['image'].value = 0
            self.prog['horizontal'].value = True
            self.quad_vao.render(moderngl.TRIANGLE_STRIP)
            ping_pong.swap()

            # Vertical Pass
            ping_pong.write.use()
            ping_pong.read.texture.use(location=0)
            self.prog['image'].value = 0
            self.prog['horizontal'].value = False
            self.quad_vao.render(moderngl.TRIANGLE_STRIP)
            ping_pong.swap()


class CompositePass(RenderPass):
    """Combines emissive HDR scene and blurred bloom texture with dithering and color grade."""
    def __init__(self, context: RenderContext):
        super().__init__(context)
        self.prog = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec2 in_vert;
                in vec2 in_uv;
                out vec2 v_uv;
                void main() {
                    gl_Position = vec4(in_vert, 0.0, 1.0);
                    v_uv = in_uv;
                }
            """,
            fragment_shader="""
                #version 330
                uniform sampler2D scene;
                uniform sampler2D bloom;
                uniform float bloom_intensity;
                uniform float vignette;
                uniform float saturation;
                uniform float warmth;
                
                in vec2 v_uv;
                out vec4 f_colour;
                
                vec3 adjust_saturation(vec3 color, float value) {
                    const vec3 lumaWeight = vec3(0.2126, 0.7152, 0.0722);
                    float luminance = dot(color, lumaWeight);
                    return mix(vec3(luminance), color, value);
                }
                
                vec3 adjust_warmth(vec3 color, float value) {
                    float temp = value * 2.0 - 1.0; 
                    vec3 warm = vec3(temp * 0.2, temp * 0.1, -temp * 0.2); 
                    return max(color + warm * length(color), 0.0);
                }

                float dither(vec2 uv) {
                    return (fract(sin(dot(uv, vec2(12.9898, 78.233))) * 43758.5453) - 0.5) / 255.0;
                }

                void main() {
                    vec4 hdrcolour = texture(scene, v_uv);
                    vec3 bloomcolour = texture(bloom, v_uv).rgb;
                    
                    vec3 result = hdrcolour.rgb + (bloomcolour * bloom_intensity);
                    result = adjust_saturation(result, saturation);
                    result = adjust_warmth(result, warmth);
                    result += dither(v_uv);

                    if (vignette > 0.0) {
                        float dist = distance(v_uv, vec2(0.5, 0.5));
                        float vig = smoothstep(0.8, 0.2, dist * (1.0 + vignette));
                        result *= (1.0 - (1.0 - vig) * vignette);
                    }

                    f_colour = vec4(result, hdrcolour.a);
                }
            """
        )
        self.quad_vao = self.ctx.simple_vertex_array(self.prog, context.get_quad_buffer(), 'in_vert', 'in_uv')

    def render(self, scene_target: RenderTarget, bloom_target: RenderTarget, output_target: RenderTarget = None, intensity: float = 1.0, **kwargs):
        if output_target:
            output_target.use()
            self.ctx.viewport = (0, 0, output_target.texture.width, output_target.texture.height)
        else:
            if self.ctx.screen is not None:
                self.ctx.screen.use()
            else:
                self.ctx.fbo.use()
            # Viewport must fill physical screen backbuffer exactly
            self.ctx.viewport = (0, 0, self.context.physical_width, self.context.physical_height)

        self.ctx.disable(moderngl.BLEND)

        scene_target.texture.use(location=0)
        bloom_target.texture.use(location=1)

        self.prog['scene'].value = 0
        self.prog['bloom'].value = 1
        self.prog['bloom_intensity'].value = float(intensity)
        if 'vignette' in self.prog: self.prog['vignette'].value = float(kwargs.get('vignette', 0.0))
        if 'saturation' in self.prog: self.prog['saturation'].value = float(kwargs.get('saturation', 1.0))
        if 'warmth' in self.prog: self.prog['warmth'].value = float(kwargs.get('warmth', 0.5))

        self.quad_vao.render(moderngl.TRIANGLE_STRIP)


class GlowExtractionPass(RenderPass):
    """Extracts HDR highlights with a smooth knee curve for natural bloom onset."""
    def __init__(self, context: RenderContext, threshold: float = 1.0):
        super().__init__(context)
        self.threshold = threshold
        self.prog = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec2 in_vert;
                in vec2 in_uv;
                out vec2 v_uv;
                void main() {
                    gl_Position = vec4(in_vert, 0.0, 1.0);
                    v_uv = in_uv;
                }
            """,
            fragment_shader="""
                #version 330
                uniform sampler2D source_texture;
                uniform float threshold;
                uniform float energy;
                in vec2 v_uv;
                out vec4 f_colour;

                void main() {
                    vec3 colour = texture(source_texture, v_uv).rgb;
                    float brightness = max(max(colour.r, colour.g), colour.b);
                    float knee = 0.25;
                    float soft = smoothstep(threshold - knee, threshold + knee, brightness);
                    vec3 bright_colour = max(vec3(0.0), colour - (threshold - knee)) * soft;

                    f_colour = vec4(bright_colour * energy * 4.0, 1.0);
                }
            """
        )
        self.quad_vao = self.ctx.simple_vertex_array(self.prog, context.get_quad_buffer(), 'in_vert', 'in_uv')

    def render(self, input_target: RenderTarget, output_target: RenderTarget, **kwargs):
        output_target.use()
        output_target.clear()
        self.ctx.disable(moderngl.BLEND)
        input_target.texture.use(location=0)
        self.prog['source_texture'].value = 0
        self.prog['threshold'].value = float(self.threshold)
        if 'energy' in self.prog:
            self.prog['energy'].value = float(kwargs.get('energy', 0.5))
        self.quad_vao.render(moderngl.TRIANGLE_STRIP)


class ToneMappingPass(RenderPass):
    """Reinhard tone mapping + sRGB gamma correction for final display."""
    def __init__(self, context: RenderContext):
        super().__init__(context)
        self.prog = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec2 in_vert;
                in vec2 in_uv;
                out vec2 v_uv;
                void main() {
                    gl_Position = vec4(in_vert, 0.0, 1.0);
                    v_uv = in_uv;
                }
            """,
            fragment_shader="""
                #version 330
                uniform sampler2D tex;
                uniform float exposure;
                uniform float gamma;
                in vec2 v_uv;
                out vec4 f_colour;

                void main() {
                    vec4 color = texture(tex, v_uv);
                    vec3 hdr = color.rgb * exposure;
                    vec3 mapped = hdr / (hdr + vec3(1.0));
                    vec3 srgb = pow(mapped, vec3(1.0 / gamma));
                    f_colour = vec4(srgb, color.a);
                }
            """
        )
        self.quad_vao = self.ctx.simple_vertex_array(self.prog, context.get_quad_buffer(), 'in_vert', 'in_uv')

    def render(self, input_target: RenderTarget, output_target: RenderTarget = None, exposure: float = 1.0, gamma: float = 2.2, **kwargs):
        if output_target:
            output_target.use()
            self.ctx.viewport = (0, 0, output_target.texture.width, output_target.texture.height)
        else:
            if self.ctx.screen is not None:
                self.ctx.screen.use()
            else:
                self.ctx.fbo.use()
            self.ctx.viewport = (0, 0, self.context.physical_width, self.context.physical_height)

        self.ctx.disable(moderngl.BLEND)
        input_target.texture.use(location=0)
        self.prog['tex'].value = 0
        self.prog['exposure'].value = float(exposure)
        self.prog['gamma'].value = float(gamma)
        self.quad_vao.render(moderngl.TRIANGLE_STRIP)


class FXAAPass(RenderPass):
    """Fast Approximate Anti-Aliasing applied exclusively to 3D scenes."""
    def __init__(self, context: RenderContext):
        super().__init__(context)
        self.prog = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec2 in_vert;
                in vec2 in_uv;
                out vec2 v_uv;
                void main() {
                    gl_Position = vec4(in_vert, 0.0, 1.0);
                    v_uv = in_uv;
                }
            """,
            fragment_shader="""
                #version 330
                uniform sampler2D tex;
                uniform vec2 resolution;
                in vec2 v_uv;
                out vec4 f_colour;

                #ifndef FXAA_REDUCE_MIN
                  #define FXAA_REDUCE_MIN   (1.0 / 128.0)
                #endif
                #ifndef FXAA_REDUCE_MUL
                  #define FXAA_REDUCE_MUL   (1.0 / 8.0)
                #endif
                #ifndef FXAA_SPAN_MAX
                  #define FXAA_SPAN_MAX     8.0
                #endif

                void main() {
                    vec2 inverseVP = 1.0 / resolution;
                    vec3 rgbNW = texture(tex, v_uv + (vec2(-1.0, -1.0) * inverseVP)).xyz;
                    vec3 rgbNE = texture(tex, v_uv + (vec2(1.0, -1.0) * inverseVP)).xyz;
                    vec3 rgbSW = texture(tex, v_uv + (vec2(-1.0, 1.0) * inverseVP)).xyz;
                    vec3 rgbSE = texture(tex, v_uv + (vec2(1.0, 1.0) * inverseVP)).xyz;
                    vec3 rgbM  = texture(tex, v_uv).xyz;
                    vec3 luma = vec3(0.299, 0.587, 0.114);
                    float lumaNW = dot(rgbNW, luma);
                    float lumaNE = dot(rgbNE, luma);
                    float lumaSW = dot(rgbSW, luma);
                    float lumaSE = dot(rgbSE, luma);
                    float lumaM  = dot(rgbM,  luma);
                    float lumaMin = min(lumaM, min(min(lumaNW, lumaNE), min(lumaSW, lumaSE)));
                    float lumaMax = max(lumaM, max(max(lumaNW, lumaNE), max(lumaSW, lumaSE)));
                    vec2 dir;
                    dir.x = -((lumaNW + lumaNE) - (lumaSW + lumaSE));
                    dir.y =  ((lumaNW + lumaSW) - (lumaNE + lumaSE));
                    float dirReduce = max((lumaNW + lumaNE + lumaSW + lumaSE) * (0.25 * FXAA_REDUCE_MUL), FXAA_REDUCE_MIN);
                    float inverseDirAdjustment = 1.0 / (min(abs(dir.x), abs(dir.y)) + dirReduce);
                    dir = min(vec2(FXAA_SPAN_MAX, FXAA_SPAN_MAX),
                          max(vec2(-FXAA_SPAN_MAX, -FXAA_SPAN_MAX),
                          dir * inverseDirAdjustment)) * inverseVP;
                    vec3 rgbA = 0.5 * (
                        texture(tex, v_uv + dir * (1.0 / 3.0 - 0.5)).xyz +
                        texture(tex, v_uv + dir * (2.0 / 3.0 - 0.5)).xyz);
                    vec3 rgbB = rgbA * 0.5 + 0.25 * (
                        texture(tex, v_uv + dir * -0.5).xyz +
                        texture(tex, v_uv + dir * 0.5).xyz);
                    float lumaB = dot(rgbB, luma);
                    if ((lumaB < lumaMin) || (lumaB > lumaMax)) {
                        f_colour = vec4(rgbA, 1.0);
                    } else {
                        f_colour = vec4(rgbB, 1.0);
                    }
                }
            """
        )
        self.quad_vao = self.ctx.simple_vertex_array(self.prog, context.get_quad_buffer(), 'in_vert', 'in_uv')

    def render(self, input_target: RenderTarget, output_target: RenderTarget = None, **kwargs):
        if output_target:
            output_target.use()
            self.ctx.viewport = (0, 0, output_target.texture.width, output_target.texture.height)
        else:
            if self.ctx.screen is not None:
                self.ctx.screen.use()
            else:
                self.ctx.fbo.use()
            self.ctx.viewport = (0, 0, self.context.physical_width, self.context.physical_height)

        self.ctx.disable(moderngl.BLEND)
        input_target.texture.use(location=0)
        self.prog['tex'].value = 0
        self.prog['resolution'].value = (float(input_target.texture.width), float(input_target.texture.height))
        self.quad_vao.render(moderngl.TRIANGLE_STRIP)


class MaskPass(RenderPass):
    """Renders frame interior areas to a mask texture to prevent glow bleed."""
    def __init__(self, context: RenderContext):
        super().__init__(context)
        self.prog = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec2 in_vert;
                void main() { gl_Position = vec4(in_vert, 0.0, 1.0); }
            """,
            fragment_shader="""
                #version 330
                out vec4 f_colour;
                void main() { f_colour = vec4(1.0, 0.0, 0.0, 1.0); }
            """
        )
        self.vbo = self.ctx.buffer(reserve=6 * 2 * 4) 
        self.vao = self.ctx.simple_vertex_array(self.prog, self.vbo, 'in_vert')
        self.rects = []

    def add_mask(self, rect):
        self.rects.append(rect)

    def render(self, target: RenderTarget):
        target.use()
        target.clear()
        if not self.rects:
            return

        sw, sh = self.context.width, self.context.height
        for x, y, w, h in self.rects:
            x1, y1 = (x / sw) * 2 - 1, 1 - (y / sh) * 2
            x2, y2 = ((x + w) / sw) * 2 - 1, 1 - ((y + h) / sh) * 2
            data = [x1, y1, x2, y1, x1, y2, x2, y1, x2, y2, x1, y2]
            self.vbo.write(np.array(data, dtype='f4'))
            self.vao.render(moderngl.TRIANGLES, vertices=6)

        self.rects = []


class OutlineBlurPass(RenderPass):
    def __init__(self, context: RenderContext, frame, blur_radius: float = 10.0, glow_color=(1.0, 1.0, 1.0, 0.5)):
        super().__init__(context)
        self.frame = frame
        self.blur_radius = blur_radius
        self.glow_color = glow_color

        path = get_asset_path('shaders', "blur_mask.frag.glsl")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Shader blur_mask.frag.glsl not found at {path}")

        with open(path, 'r') as f:
            src = f.read()

        self.prog = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec2 in_vert;
                in vec2 in_texcoord;
                out vec2 v_texcoord;
                void main() {
                    gl_Position = vec4(in_vert, 0.0, 1.0);
                    v_texcoord = in_texcoord;
                }
            """,
            fragment_shader=src
        )
        vertices = np.array([
            -1.0, -1.0, 0.0, 0.0,
             1.0, -1.0, 1.0, 0.0,
            -1.0,  1.0, 0.0, 1.0,
             1.0,  1.0, 1.0, 1.0,
        ], dtype='f4')
        self.vbo = self.ctx.buffer(vertices)
        self.vao = self.ctx.vertex_array(self.prog, [(self.vbo, '2f 2f', 'in_vert', 'in_texcoord')])

    def render(self, **kwargs):
        x, y, w, h = self.frame.abs_rect()
        scale = self.context.dpi_scale
        
        self.prog['u_resolution'].value = (float(self.context.physical_width), float(self.context.physical_height))
        self.prog['u_blur_radius'].value = float(self.blur_radius * scale)
        self.prog['u_glow_color'].value = self.glow_color
        
        # In OpenGL, physical Y is measured from the bottom
        gl_y = self.context.height - (y + h)
        self.prog['u_mask_rect'].value = (float(x * scale), float(gl_y * scale), float(w * scale), float(h * scale))

        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        self.vao.render(moderngl.TRIANGLE_STRIP)
        self.ctx.disable(moderngl.BLEND)


# ==============================================================================
# 4. MASTER COMPOSITOR PIPELINE
# ==============================================================================

class Compositor:
    """
    Orchestrates the 5-Stage Rendering Pipeline:
    1. Emissive Pass (Backgrounds, Shaders, Spectrum Bars) -> emissive_target (HDR)
    2. Bloom Extraction -> glow_buffer (Downsampled 0.5x)
    3. Gaussian Ping-Pong Blur
    4. Composite Emissive + Bloom onto Screen (Full physical resolution)
    5. Sharp UI Pass (Vector Outlines, Needles, Text, Images) directly over composite
    """
    def __init__(self, context: RenderContext):
        self.context = context
        self.metrics = context.metrics

        # Buffer allocation at physical resolution
        self.emissive_target = RenderTarget(context, scale=1.0, dtype='f2')
        self.glow_buffer = PingPongBuffer(context, scale=0.5, dtype='f2')
        self.ui_target = RenderTarget(context, scale=1.0, dtype='f1')
        self.mask_target = RenderTarget(context, scale=1.0, dtype='f1')

        self.emissive_passes: list[RenderPass] = []
        self.ui_passes: list[RenderPass] = []
        self.pre_passes: list[RenderPass] = []

        self.glow_extraction_pass = GlowExtractionPass(context, threshold=1.0)
        self.blur_pass = BlurPass(context, iterations=4)
        self.composite_pass = CompositePass(context)
        self.final_blit_pass = TextureBlitPass(context)

        self.bloom_intensity = 0.8
        self.blur_spread = 1.0
        self.debug_view = None

    def add_emissive_pass(self, render_pass: RenderPass):
        self.emissive_passes.append(render_pass)

    def add_ui_pass(self, render_pass: RenderPass):
        self.ui_passes.append(render_pass)

    def add_pre_pass(self, render_pass: RenderPass):
        self.pre_passes.append(render_pass)

    def clear_passes(self):
        self.emissive_passes.clear()
        self.ui_passes.clear()
        self.pre_passes.clear()

    def resize(self, size: tuple[int, int], dpi_scale: float | None = None):
        self.context.resize(size, dpi_scale)
        self.emissive_target.resize()
        self.glow_buffer.resize()
        self.ui_target.resize()
        self.mask_target.resize()
        for p in self.emissive_passes:
            p.resize(size)
        for p in self.ui_passes:
            p.resize(size)

    def render_frame(self):
        # 1. Update Profile Controls
        from pyvisualiser.styles.profiles import ProfileManager
        controller = ProfileManager.get_controller()
        controller.apply_profile(self)

        controls = getattr(self, 'active_controls', None)
        vig = controls.vignette if controls else 0.0
        sat = controls.saturation if controls else 1.0
        wrm = controls.warmth if controls else 0.5
        blo = controls.intensity if controls else self.bloom_intensity
        thr = controls.threshold if controls else 1.0
        sft = controls.softness if controls else 0.5
        nrg = controls.energy if controls else 0.5

        if hasattr(self, 'blur_pass'):
            self.blur_pass.iterations = max(2, int(2 + sft * 8.0))
            self.blur_spread = max(1.0, 0.5 + sft * 1.5)

        if hasattr(self, 'glow_extraction_pass'):
            self.glow_extraction_pass.threshold = thr

        # --- STAGE 1: Render Emissive Pass ---
        self.emissive_target.use()
        bg = [c / 255.0 for c in BACKGROUND_colour]
        self.emissive_target.clear(colour=(bg[0], bg[1], bg[2], 1.0))

        self.context.ctx.enable(moderngl.BLEND)
        self.context.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

        for p in self.pre_passes:
            p.render(target=self.emissive_target)
        for p in self.emissive_passes:
            p.render(target=self.emissive_target)

        # --- STAGE 2: Glow Extraction ---
        self.glow_extraction_pass.render(
            input_target=self.emissive_target,
            output_target=self.glow_buffer.read,
            energy=nrg
        )

        # --- STAGE 3: Separable Ping-Pong Blur ---
        self.blur_pass.render(ping_pong=self.glow_buffer, spread=self.blur_spread)

        # --- STAGE 4: Composite Bloom onto Physical Screen ---
        if self.context.ctx.screen is not None:
            self.context.ctx.screen.use()
        else:
            self.context.ctx.fbo.use()

        # Viewport must fill 100% of the physical screen backbuffer
        self.context.ctx.viewport = (0, 0, self.context.physical_width, self.context.physical_height)

        if self.debug_view == 'glow':
            self.final_blit_pass.render(input_target=self.glow_buffer.read)
        elif self.debug_view == 'emissive':
            self.final_blit_pass.render(input_target=self.emissive_target)
        else:
            self.composite_pass.render(
                scene_target=self.emissive_target,
                bloom_target=self.glow_buffer.read,
                output_target=None,
                intensity=blo,
                vignette=vig,
                saturation=sat,
                warmth=wrm
            )

        # --- STAGE 5: Render Sharp UI Pass (Vectors, Text, Album Art) ---
        self.context.ctx.enable(moderngl.BLEND)
        self.context.ctx.blend_func = moderngl.ONE, moderngl.ONE_MINUS_SRC_ALPHA

        # Keep viewport at native physical resolution for pixel-sharp UI
        if self.context.ctx.screen is not None:
            self.context.ctx.screen.use()
        else:
            self.context.ctx.fbo.use()
        self.context.ctx.viewport = (0, 0, self.context.physical_width, self.context.physical_height)

        for p in self.ui_passes:
            p.render()

        self.pre_passes.clear()
        self.debug_view = None