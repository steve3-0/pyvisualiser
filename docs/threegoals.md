<!-- >> This analysis was performed by gemini-flash3.8 on the codebase dated 13 Nov 26 for the prompt pasted in below-->

## 1. Architectural & API Audit (Goal A)

### 1.1 Structural Evaluation of the Current Architecture

```
Current Coupling:
[ScreenController] ──creates──> [Platform] (AudioProcessor + MetaData + GraphicsDriver + HWInterface)
                                    ▲
                                    │ (Direct Attribute Snooping: self.platform.vu, .track, .elapsed)
[Frame] ◄──inherits── [SpectrumFrame] ◄──mixes-in── [Spectrum]
```

1. **Monolithic God-Object (`Platform`):** 
   In `src/pyvisualiser/core/screenhandler.py`, `Platform` inherits simultaneously from `AudioProcessor`, `MetaData`, `GraphicsDriver`, and `HWInterface`. UI components reach directly into this God-object across multiple levels of hierarchy (e.g., `self.platform.samples`, `self.platform.vu['mono']`, `self.platform.elapsed`). This creates tight coupling: no UI component can be previewed or tested in isolation without spinning up PyAudio hardware capture, an active Roon network connection, and a Pygame OpenGL context.
2. **Brittle Multiple Inheritance Mixins:**
   In `src/pyvisualiser/visualisers/spectrum.py`, `class SpectrumFrame(Frame, Spectrum)` uses `Spectrum` as an uninitialized mixin. `Spectrum.__init__` accesses `self.platform.createBands` before verifying if `self.platform` exists in its class signature.
3. **Inconsistent Naming and Config Bloat:**
   Constructor arguments mix snake_case and camelCase abbreviations (`barw_min`, `barsize_pc`, `led_h`, `led_gap`, `Valign`, `Halign`, `padpc`). Styles are fragmented across `BarStyle`, `BarEffects`, `SpectrumStyle`, `VUMeterStyle`, and generic Python dictionaries (`outline={'width': 4, 'colour': 'light'}`).
4. **Destructive Layout Recalculation:**
   In `src/pyvisualiser/core/framecore.py`, `AxisFramer._apply_layout()` modifies child geometry immediately upon `__iadd__`. If frames are added dynamically or hidden at runtime, the layout recalculates eagerly rather than deferring to a clean layout pass.

### 1.2 Proposed Idiomatic, Declarative Screen API

Replace ad-hoc container nesting with a clean declarative component model:
* Decouple data consumption using an immutable, strongly typed `RenderContextState` / `AudioFrameData`.
* Use explicit, standardized component constructors with builder or props patterns.

```python
# Proposed Declarative API Example
from dataclasses import dataclass
from typing import Optional
import numpy as np

@dataclass(frozen=True)
class AudioTelemetry:
    vu_left: float
    vu_right: float
    vu_mono: float
    spectrum_bins: np.ndarray  # Normalized 0.0 - 1.0 (float32)
    waveform: np.ndarray       # Raw audio time-domain window
    bass_energy: float
    treble_energy: float
    bpm: float
    is_beat: bool

@dataclass(frozen=True)
class MediaMetadata:
    title: str = "Unknown Track"
    artist: str = "Unknown Artist"
    album: str = "Unknown Album"
    duration_sec: float = 0.0
    elapsed_sec: float = 0.0
    format_info: str = "44.1kHz 16-bit FLAC"
    artwork_path: Optional[str] = None

class ScreenDefinition:
    """Base class for declarative screens."""
    def build(self) -> "ComponentNode":
        raise NotImplementedError

# Example of declarative Screen Builder
class CleanStudioDashboard(ScreenDefinition):
    def build(self):
        return Row(padding=12, gap=8)(
            # Left: Left VU needle
            VUNeedle(channel="left", style="vintage_warm"),
            
            # Center: Stacked Album Art, Track Info, and Spectrum
            Column(flex=2, gap=6)(
                Row(flex=3)(
                    AlbumArt(reflection=True, corner_radius=8),
                    Column(flex=2, justify="center")(
                        Label(binding="metadata.title", size=24, weight="bold"),
                        Label(binding="metadata.artist", size=18, color="accent"),
                        Label(binding="metadata.format_info", size=12, color="dimmed"),
                    )
                ),
                PlayProgressBar(height=16, style="segmented_led"),
                SpectrumAnalyzer(channel="mono", bands=48, style="neon_clean")
            ),
            
            # Right: Right VU needle & Hardware Status
            Column(flex=1)(
                VUNeedle(channel="right", style="vintage_warm"),
                RotaryVolumeDisplay(size=64)
            )
        )
```

### 1.3 Cross-Platform Failure Points: macOS vs. Raspberry Pi 5

| Subsystem | macOS (Desktop / Dev) | Raspberry Pi 5 (Embedded Preamplifier) | Architectural Risk & Resolution |
| :--- | :--- | :--- | :--- |
| **Dependencies** | Uses `pyobjc-framework-*` for window management / CoreAudio. | `pyproject.toml` / `requirements.txt` will fail immediately on ARM64 Linux. | **Action:** Isolate macOS dependencies in `pyproject.toml` using platform markers: `pyobjc; sys_platform == 'darwin'`. |
| **Display Server & Drivers** | Cocoa windowing with Apple Metal / OpenGL Compatibility shim. | Raspberry Pi OS Bookworm defaults to **Wayfire / Labwc (Wayland)** using Mesa `v3d` (VideoCore VII). | **Action:** Do not rely on legacy `SDL_VIDEODRIVER=kmsdrm` without checking if a Wayland compositor is running. Implement EGL/DRM native surface detection. |
| **OpenGL API Level** | ModernGL uses desktop OpenGL 3.3 / 4.1 Core profile. | Broadcom VideoCore VII supports **OpenGL ES 3.1** and desktop **OpenGL 3.3 Core**. | **Action:** Avoid desktop-only features (e.g. `glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)`). ModernGL context creation must explicitly target `require=330` on Desktop and fallback to GLES 3.1 on Pi. |
| **Audio Loopback** | macOS uses virtual loopback (e.g., `BlackHole 2ch`). | Raspberry Pi uses hardware ALSA `snd-aloop` kernel module (`pcm.loopin`). | **Action:** Provide a declarative audio backend abstraction (`CoreAudioLoopback` vs. `AlsaLoopback`) so switching environments only requires changing a config flag. |

---

## 2. Performance Bottleneck Analysis & Remediation (Goal B)

### 2.1 Dissecting the 26.73 ms "Draw" Bottleneck

Your telemetry log revealed the critical problem:
$$\text{Loop: } 33.28\text{ ms} \quad \Big( \text{Audio: } 0.54\text{ ms} \;\vert\; \mathbf{Draw: 26.73\text{ ms}} \;\vert\; \text{Render: } 6.02\text{ ms} \Big)$$

Analyzing `src/pyvisualiser/core/components.py`, `displaydriver.py`, and `vumeters.py` reveals the root causes:

#### Cause 1: Per-Frame Font Loading and Rasterization (CPU Disaster)
In `Text.update()` called by `Text.draw()` every frame:
```python
# components.py:L826-841
font = pygame.font.Font(self.fontfile, int(fontsize))
fontwh = self.textsize(text, font)
```
Inside `shrink_fontsize()`, `pygame.font.Font` opens the TTF file from disk, parses FreeType vector outlines, and allocates raster memory up to **three times per text element per frame**. With track title, artist, album, format, elapsed time, remaining time, and needle labels, **the CPU performs 20–40 disk reads and font rasterizations per frame**.

#### Cause 2: Batch Shattering via Additive Mode Toggling
In `GeometryPass` (`displaydriver.py`):
```python
def set_additive(self, additive):
    if additive != self.current_additive:
        self._push_batch()
        self.current_additive = additive
```
In `Bar.drawV()`, for every vertical bar in a 48-band spectrum:
1. Inner glow is queued with `additive=True` $\rightarrow$ `_push_batch()` flushes.
2. Outer glow is queued with `additive=True`.
3. Bar base is queued with `additive=False` $\rightarrow$ `_push_batch()` flushes.
4. Peak line is queued.

For a 48-band spectrum, `GeometryPass` splits rendering into over **100 independent draw calls**.

#### Cause 3: Python-Level Array Serialization Inside the Hot Loop
In `GeometryPass.render()`:
```python
for batch in self.batches:
    data = np.array(batch['data'], dtype='f4')  # Allocates and converts Python list to NumPy
    self.vbo.write(data)                         # Sync CPU-to-GPU memory copy
    self.vao.render(moderngl.TRIANGLES, vertices=len(data)//18)
```
Building Python lists (`18 floats * 6 vertices = 108 floats` per rectangle) and converting them with `np.array()` in a Python loop 100+ times per frame accounts for **12–15 ms of pure CPython interpreter overhead**.

---

### 2.2 Concrete Fixes: 60 FPS Target Architecture

To bring `Draw` time from **26.73 ms down to < 2.5 ms**:
1. **Pre-allocated Double-Buffered VBO with Zero-Copy Numpy Buffer:** Eliminate Python float list appends. Write directly to a pre-allocated contiguous `float32` array using memoryviews.
2. **Eliminate Additive Batch Breaks in Shaders:** Move the blend mode calculation inside the fragment shader or encode `is_additive` into vertex flags, allowing the entire UI pass to draw in a **single draw call**.
3. **Texture Atlas & Dynamic Font Caching:** Rasterize glyphs into an atlas once or cache rendered surfaces by string hash.

#### Optimized Implementation: Zero-Copy Geometry Batcher

Replace `GeometryPass` with this unified, single-draw-call batcher:

```python
# src/pyvisualiser/core/fast_batcher.py
import numpy as np
import moderngl

# 12 floats per vertex:
# x, y (pos), u, v (tex/sdf), r, g, b, a (color), stroke_or_mode, radius, softness, is_additive
VERTEX_DTYPE = np.dtype([
    ('in_vert',     np.float32, 2),
    ('in_uv',       np.float32, 2),
    ('in_color',    np.float32, 4),
    ('in_params',   np.float32, 4), # stroke, radius, softness, is_additive
])

class FastGeometryBatcher:
    """High-performance single-buffer 2D renderer using batched instanced quad data."""
    def __init__(self, ctx: moderngl.Context, max_quads: int = 4096):
        self.ctx = ctx
        self.max_quads = max_quads
        self.max_vertices = max_quads * 6

        # Pre-allocate static CPU staging memory (Zero allocations during frame loop)
        self.cpu_buffer = np.zeros(self.max_vertices, dtype=VERTEX_DTYPE)
        self.quad_count = 0

        # Pre-allocated dynamic GPU buffer
        self.vbo = self.ctx.buffer(reserve=self.cpu_buffer.nbytes, dynamic=True)

        self.prog = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec2 in_vert;
                in vec2 in_uv;
                in vec4 in_color;
                in vec4 in_params; // [stroke, radius, softness, is_additive]

                out vec2 v_uv;
                out vec4 v_color;
                out vec4 v_params;

                void main() {
                    gl_Position = vec4(in_vert, 0.0, 1.0);
                    v_uv = in_uv;
                    v_color = in_color;
                    v_params = in_params;
                }
            """,
            fragment_shader="""
                #version 330
                in vec2 v_uv;
                in vec4 v_color;
                in vec4 v_params;

                out vec4 f_color;
                uniform sampler2D u_main_texture;

                float sdRoundedBox(vec2 p, vec2 b, float r) {
                    vec2 q = abs(p) - b + r;
                    return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - r;
                }

                void main() {
                    float stroke = v_params.x;
                    float radius = v_params.y;
                    float softness = v_params.z;
                    float is_additive = v_params.w;

                    // Signed Distance Field evaluation
                    vec2 p = v_uv - vec2(0.5);
                    float d = sdRoundedBox(p, vec2(0.5), radius);
                    float alpha = 1.0 - smoothstep(-softness, softness, d);

                    vec4 tex_color = texture(u_main_texture, v_uv);
                    vec4 col = v_color * tex_color;
                    col.a *= alpha;

                    // When additive flag is set, premultiply differently
                    if (is_additive > 0.5) {
                        col.rgb *= col.a * 2.0; // Boost glow intensity
                    }

                    f_color = col;
                }
            """
        )
        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.vbo, "2f 2f 4f 4f", "in_vert", "in_uv", "in_color", "in_params")]
        )

    def reset(self):
        """Reset the buffer pointer at the start of a frame."""
        self.quad_count = 0

    def add_quad(self, x: float, y: float, w: float, h: float,
                 color: tuple, screen_w: float, screen_h: float,
                 radius: float = 0.0, softness: float = 0.01,
                 is_additive: float = 0.0):
        if self.quad_count >= self.max_quads:
            return # Protect against overflow

        # Convert coordinates to OpenGL Normalized Device Coordinates (-1.0 to 1.0)
        x0 = (x / screen_w) * 2.0 - 1.0
        y0 = 1.0 - (y / screen_h) * 2.0
        x1 = ((x + w) / screen_w) * 2.0 - 1.0
        y1 = 1.0 - ((y + h) / screen_h) * 2.0

        r, g, b, a = color
        params = (0.0, radius, softness, is_additive)

        idx = self.quad_count * 6
        view = self.cpu_buffer[idx:idx+6]

        # Triangle 1 (TL, TR, BL)
        view[0] = ((x0, y0), (0.0, 0.0), (r, g, b, a), params)
        view[1] = ((x1, y0), (1.0, 0.0), (r, g, b, a), params)
        view[2] = ((x0, y1), (0.0, 1.0), (r, g, b, a), params)

        # Triangle 2 (BL, TR, BR)
        view[3] = ((x0, y1), (0.0, 1.0), (r, g, b, a), params)
        view[4] = ((x1, y0), (1.0, 0.0), (r, g, b, a), params)
        view[5] = ((x1, y1), (1.0, 1.0), (r, g, b, a), params)

        self.quad_count += 1

    def flush(self):
        """One-shot GPU upload and single draw call for the entire UI frame."""
        if self.quad_count == 0:
            return

        vertex_count = self.quad_count * 6
        byte_length = vertex_count * VERTEX_DTYPE.itemsize

        # Zero-copy memoryview upload to GPU
        self.vbo.write(memoryview(self.cpu_buffer)[:byte_length])

        # Dual blend: standard alpha and additive elements co-exist via premultiplied alpha
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.ONE, moderngl.ONE_MINUS_SRC_ALPHA
        
        self.vao.render(moderngl.TRIANGLES, vertices=vertex_count)
```

#### Optimized Implementation: Font Cache with String Hashing

Eliminate TTF parsing from the per-frame loop in `components.py`:

```python
# src/pyvisualiser/core/font_manager.py
import pygame
from typing import Dict, Tuple

class FontCacheManager:
    """Global caching engine for FreeType rasterized fonts and rendered surfaces."""
    _font_instances: Dict[Tuple[str, int], pygame.font.Font] = {}
    _surface_cache: Dict[Tuple[str, int, tuple], pygame.Surface] = {}

    @classmethod
    def get_font(cls, font_path: str, size: int) -> pygame.font.Font:
        key = (font_path, int(size))
        if key not in cls._font_instances:
            cls._font_instances[key] = pygame.font.Font(font_path, int(size))
        return cls._font_instances[key]

    @classmethod
    def get_rendered_text(cls, text: str, font_path: str, size: int, color: tuple) -> pygame.Surface:
        cache_key = (text, int(size), color)
        if cache_key not in cls._surface_cache:
            font = cls.get_font(font_path, size)
            # Render with antialiasing enabled
            cls._surface_cache[cache_key] = font.render(text, True, color[:3])
            
            # Bound cache size to prevent memory leaks over long listening sessions
            if len(cls._surface_cache) > 512:
                cls._surface_cache.clear()
                
        return cls._surface_cache[cache_key]
```

---

## 3. Render Pipeline & Visual Fidelity Enhancements (Goal C)

### 3.1 Diagnosis: Why Text and Images Appear Fuzzy

Inspection of your screenshots (`H1.png`, `H2.png`, `H5.png`, `H6.png`) and engine code reveals three distinct visual bugs causing fuzziness:

```
Current Flawed Pipeline:
[Background Pass] ──> [Geometry & TEXT Drawn to HDR FBO] ──> [Glow Threshold Extraction]
                                                                        │
                                                                        ▼
[Final Screen] <── [Blit with FXAA on Whole Scene] <── [Blurred Bloom Added OVER Text]
```

#### 1. Text is Positioned Lower in the Pipeline than Bloom (The "Bloom Smear" Bug)
In `render.py`, all UI geometry—including `TextFrame` and album art—is rendered into `self.main_target` during **Pass 1**.
Then in **Pass 2**, `GlowExtractionPass` extracts bright pixels from `self.main_target`. Because white text ($R=1.0, G=1.0, B=1.0$) exceeds or matches `threshold=1.0`, **the text glyphs are extracted into the blur ping-pong buffer**. In `CompositePass`, the blurred version of the text is added back on top of the original text. The result is a fuzzy halo around all track metadata, timecodes, and dial labels.

#### 2. FXAA Post-Processing Pass Applied to Text & Album Art
In `Compositor.render_frame()`:
```python
if self.fxaa_enabled:
    self.composite_pass.render(...)
    self.fxaa_pass.render(input_target=self.post_process_target)
```
Fast Approximate Anti-Aliasing (FXAA) operates via screen-space edge contrast heuristics. When run across High-DPI screens or small typographic strokes, FXAA mistakes subpixel font serifs and high-contrast character edges for aliasing artifacts and blurs them, producing muddy text.

#### 3. macOS Retina / High-DPI Framebuffer Disconnect
On modern macOS, Pygame creates an SDL window where:
```python
window_size = pygame.display.get_window_size()       # e.g., (1280, 400)
framebuffer_size = pygame.display.get_surface().get_size() # On Retina: (2560, 800)
```
In `GraphicsDriverGL`, `RenderContext` initializes viewport and FBOs using `(1280, 400)`:
```python
self.main_target = RenderTarget(context.ctx, context.size, scale=1.0, dtype='f2')
```
Because `main_target` is rendered at $1280 \times 400$ and then stretched by macOS Cocoa to fill the $2560 \times 800$ Retina physical backing surface, **the entire visualizer is undergoing a 2x bilinear upscale**, blurring all 1px vector borders, needle meters, and text edges.

---

### 3.2 The Optimal 6-Stage Render Pipeline

To guarantee sharp typography and clean bloom, UI and metadata must be drawn **after** the bloom composite pass:

```
Optimal Pipeline Architecture:
┌─────────────────────────────────────────────────────────────┐
│ 1. Emissive Layer (Background Shaders + FFT Spectrum Bars)  │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Downsampled Glow Extraction (Half/Quarter Resolution)    │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Separable Gaussian Ping-Pong Blur                        │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Composite & Tone-Mapping (Emissive Scene + Bloom)       │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Sharp Vector & UI Pass (Needles, Outlines, Progress Bar) │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Crisp Typography & Native Resolution Metadata Layer      │
└─────────────────────────────────────────────────────────────┘
```

#### Implementation: Corrected Compositor Loop

```python
# src/pyvisualiser/core/compositor_refactor.py

class CorrectedCompositor:
    def render_frame(self, scene_emissive_pass, ui_vector_pass, text_overlay_pass):
        """
        Executes rendering in strictly correct optical order:
        Emissive Graphics -> Bloom PostFX -> Sharp Vector UI -> Crisp Typography.
        """
        # --- STAGE 1: Render Emissive Visualisers & Shaders ---
        self.hdr_emissive_target.use()
        self.hdr_emissive_target.clear(colour=(0.02, 0.02, 0.04, 1.0))
        scene_emissive_pass.render()

        # --- STAGE 2: Downsampled Bloom Extraction ---
        # Run on a half-resolution buffer (saves 75% fill-rate on RPi 5)
        self.glow_buffer.read.use()
        self.glow_extraction_pass.render(
            input_target=self.hdr_emissive_target,
            threshold=self.active_controls.threshold
        )

        # --- STAGE 3: Separable Blur Ping-Pong ---
        self.blur_pass.render(ping_pong=self.glow_buffer, spread=self.blur_spread)

        # --- STAGE 4: Composite Bloom Over Scene ---
        # Composite directly into the main backbuffer
        self.ctx.screen.use()
        self.ctx.clear(0.0, 0.0, 0.0, 1.0)
        
        self.composite_pass.render(
            scene_target=self.hdr_emissive_target,
            bloom_target=self.glow_buffer.read,
            intensity=self.active_controls.intensity,
            vignette=self.active_controls.vignette
        )

        # --- STAGE 5: Sharp Vector UI Layer (Meters, Borders) ---
        # Rendered directly to backbuffer with standard premultiplied alpha
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.ONE, moderngl.ONE_MINUS_SRC_ALPHA
        ui_vector_pass.render()

        # --- STAGE 6: Crisp Text & Album Art Overlay ---
        # NO BLOOM, NO FXAA, 1:1 Pixel Mapping
        text_overlay_pass.render()
```

---

## 4. Implementation Punchlist & Risk Matrix

### Phase 1: Core Bottlenecks & Low-Hanging Fruit (Immediate 60 FPS Fix)

| # | Task | Objective & Scope | Code Files Affected | Risk / Complexity | Verification Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1.1** | **Font Instantiation Elimination** | Remove `pygame.font.Font()` calls from `Text.shrink_fontsize()` and `textsize()`. Implement static cache in `FontCacheManager`. | `src/pyvisualiser/core/components.py` | **LOW** | Profiler shows zero file I/O during execution; `Draw` time drops by $\ge 8\text{ ms}$. |
| **1.2** | **VBO Leak Resolution** | Explicitly invoke `old_texture.release()` whenever a texture reference is discarded or reassigned. | `src/pyvisualiser/core/displaydriver.py`, `components.py` | **LOW** | VRAM usage remains flat over a 30-minute run. |
| **1.3** | **Additive State Batching Fix** | Stop calling `_push_batch()` on every single additive toggle in `Bar.draw()`. Pass an `is_additive` float attribute per vertex. | `src/pyvisualiser/core/displaydriver.py`, `components.py` | **MEDIUM** | Number of draw calls per frame on `H1` drops from $>100$ to $<5$. |
| **1.4** | **Packaging Cleanup for Pi** | Remove macOS-exclusive dependencies (`pyobjc-*`) from core dependencies. Use PEP 508 environment markers. | `requirements.txt`, `pyproject.toml` | **LOW** | `pip install -e .` succeeds in a clean Debian 12 (ARM64) container without PyObjC errors. |

---

### Phase 2: Pipeline Refactor & Visual Clarity (Crisp Rendering)

| # | Task | Objective & Scope | Code Files Affected | Risk / Complexity | Verification Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **2.1** | **Pipeline Reordering** | Separate the render pass graph: (1) Background/Shaders/Spectrum $\rightarrow$ (2) Bloom $\rightarrow$ (3) Compositing $\rightarrow$ (4) UI Overlay/Text. | `src/pyvisualiser/core/render.py`, `screenhandler.py` | **HIGH** | Text remains crisp; labels never develop a blurred halo even when `intensity` is set to 2.0. |
| **2.2** | **Retina & High-DPI Awareness** | Query `pygame.display.get_window_size()` vs. `gl_get_drawable_size()`. Scale FBO dimensions by the window DPI scale factor. | `src/pyvisualiser/core/displaydriver.py`, `render.py` | **MEDIUM** | 1px outlines on macOS Retina displays render sharply at native resolution without blurring. |
| **2.3** | **Texture Filtering Policy** | Enforce `moderngl.LINEAR_MIPMAP_LINEAR` minification and `moderngl.LINEAR` magnification with auto mipmap generation on album art. | `src/pyvisualiser/core/components.py`, `backgrounds.py` | **LOW** | Album artwork downscaled into metadata frames shows no moiré or aliasing artifacts. |
| **2.4** | **FXAA Exclusion for UI Text** | Remove full-screen FXAA pass from running across typography, or limit FXAA strictly to the emissive scene FBO. | `src/pyvisualiser/core/render.py` | **MEDIUM** | Text character edges remain distinct and subpixel-sharp under all profile modes. |

---

### Phase 3: Architecture & Embedded Hardware Hardening (RPi 5 Production)

| # | Task | Objective & Scope | Code Files Affected | Risk / Complexity | Verification Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **3.1** | **Decouple UI from `Platform`** | Introduce an immutable `AudioTelemetry` data carrier. UI frames read from state arguments instead of reaching into `self.platform`. | `src/pyvisualiser/core/framecore.py`, `metadata.py`, `spectrum.py` | **HIGH** | Components can be unit-tested using synthetic mock arrays without audio or display hardware. |
| **3.2** | **Audio Buffer Ring Synchronization** | Replace the unbounded queue with a fixed-size lockless circular ring-buffer between PyAudio capture and the main render loop. | `src/pyvisualiser/core/processaudio.py` | **MEDIUM** | Zero audio buffer overruns/underruns (`paInputOverflow`) under 100% CPU spikes. |
| **3.3** | **RPi 5 Wayland / DRM Driver Support** | Implement runtime detection for `WAYLAND_DISPLAY` vs. direct Linux KMS framebuffer (`/dev/dri/card*`) with proper EGL context creation. | `src/pyvisualiser/core/displaydriver.py` | **HIGH** | Visualizer runs at native 60 FPS on Raspberry Pi 5 under both Bookworm Desktop and headless Lite (KMS). |
| **3.4** | **Parameter Specification Validation** | Implement `Dict[str, ParameterSpec]` with distinct `(min, max)` boundaries to replace hardcoded `[0.0, 2.0]` clamping. | `src/pyvisualiser/styles/profiles.py` | **LOW** | Keyboard controls smoothly clamp parameters to their valid operational ranges. |

---

### Risk Assessment & Mitigation

```
Risk Matrix:
┌──────────┬────────────────────────────────────────────────────────┐
│ CRITICAL │ 3.1 Decouple UI from Platform (High refactoring blast) │
├──────────┼────────────────────────────────────────────────────────┤
│ HIGH     │ 2.1 Pipeline Reordering (Alters visual output order)   │
│          │ 3.3 RPi 5 DRM/Wayland EGL compatibility                 │
├──────────┼────────────────────────────────────────────────────────┤
│ MEDIUM   │ 1.3 Additive State Batching (Shader syntax changes)    │
│          │ 2.2 Retina Framebuffer Scaling (FBO coordinate math)   │
│          │ 3.2 Lockless Ring Buffer (Thread synchronization)      │
├──────────┼────────────────────────────────────────────────────────┤
│ LOW      │ 1.1 Font Cache, 1.2 VRAM Leak, 1.4 Package Markers     │
└──────────┴────────────────────────────────────────────────────────┘
```

* **Mitigation for Task 2.1 & 3.1 (High Architectural Blast Radius):** Implement the `FastGeometryBatcher` and `FontCacheManager` first under the existing interface. Once the frame budget drops below 16.6 ms, extract the `AudioTelemetry` data structure without breaking the existing `Frame` hierarchy.
* **Mitigation for Task 3.3 (RPi 5 Display Compatibility):** Test via ModernGL's headless context capabilities (`moderngl.create_context(standalone=False)`) ensuring that EGL context initialization is handled cleanly whether running inside X11, Wayland, or direct KMS/DRM console mode.




# Prompt
Here is the codebase package and instrumentation.   Screenshots are in doc/screenshots eg H1 is H1.png.  docs/runtime_instrumentation.txt is a scrape of the screen output when running, showing how the screens perform.  The screens are defined in tests/screens3.py, the start point is tests/vis.py.  You can ignore the other test scripts in tests.  Shaders and vertex glsl is in assets/shaders.  The repo python is all in the src/... tree.  I have attached a profile for h1.pstats.    architectural questions:

moderngl over pygame.  Raspberry Pi TBC

aubio is on its own thread

text and 2d primitive drawing - you will have to look at the code

Full render pass management is being done

You are acting as an elite Graphics Systems Engineer and Python Systems Architect.
I have uploaded the source code, profiling data, and visual artifacts for pyvisualiser—a cross-platform audio visualisation engine targeting macOS (desktop/dev) and Raspberry Pi 5 (embedded high-end audio preamplifier).

Context & Artifacts Provided:
Source Code Archive: [ATTACHED ZIP]

Performance Profile: [ATTACHED .pstats / logs]

Visual Defect Screenshots: [ATTACHED IMAGES]

Target Embedded Environment: Raspberry Pi 5 (VideoCore VII, GLES 3.1 / OpenGL 3.3 Core), Target Resolution: [INSERT RESOLUTION]

Windowing Toolkit: [e.g., GLFW / moderngl-window]

Performance Baseline:
Target: Solid 60 FPS (<= 16.6ms total frame budget)

Current H1 Screen: ~33.28ms (Audio: 0.54ms, Draw: 26.73ms, Render: 6.02ms) @ ~29.6 FPS.

Deliverables Required:
Conduct an exhaustive, code-level review and produce a technical architecture report structured as follows:

ARCHITECTURAL & API AUDIT (Goal A):

Evaluate the current  screen/widget  API for ergonomics, extensibility, and clarity.

Propose an intuitive, idiomatic API design allowing developers to define complex screens declaratively or cleanly in code.

Identify cross-platform failure points (macOS vs. Linux/RPi 5 driver differences, GLES compatibility, thread models).

PERFORMANCE BOTTLENECK ANALYSIS & REMEDIATION (Goal B):

Dissect the 26.73ms "Draw" bottleneck using the provided code and profiling data.

Detail concrete fixes to hit 60 FPS (CPU-to-GPU data transfer reductions, draw-call batching, ModernGL VAO/VBO reuse, zero-copy buffer updates).

Provide concrete, drop-in Python and GLSL code snippets demonstrating before-and-after optimization.

RENDER PIPELINE & VISUAL FIDELITY ENHANCEMENTS (Goal C):

Diagnose why text and images appear fuzzy (investigate DPI scaling, framebuffer blitting, texture filtering, and compositing order).

Provide an optimal rendering pipeline order (e.g., Background Shaders -> Dynamic Audio Visuals -> Compositing -> Sharp UI / Text Overlay).

Supply a robust implementation strategy for crisp text rendering (e.g., SDF/MSDF text rendering or properly scaled texture atlasing with correct blending).

IMPLEMENTATION PUNCHLIST & RISK MATRIX:

Provide an engineering punchlist broken into sequential phases: Phase 1 (Core Bottlenecks & Low-Hanging Fruit), Phase 2 (Pipeline Refactor & Text Overhaul), Phase 3 (API Polish & RPi Validation).

For every task, outline: Objective, Code Files Affected, Risk/Complexity Level, and Verification Criteria.