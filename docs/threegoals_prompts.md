
## Modular prompts for the big push
Here is the execution blueprint and modular prompt suite.

To ensure success on lower-capability AI models, each task is scoped to a single file or a tightly coupled pair, includes all required type signatures and code logic, and mandates a self-contained test harness that validates the fix without needing live audio hardware or a Roon connection.

Step-by-Step Execution Workflow
Code
[Main Branch]
      │
      ├──> git checkout -b task-1.1-font-cache
      │    Run Prompt 1.1 ──> Run tests/test_task_1_1.py ──> PASS ──> Merge
      │
      ├──> git checkout -b task-1.2-vram-leak
      │    Run Prompt 1.2 ──> Run tests/test_task_1_2.py ──> PASS ──> Merge
      │
      └──> (Repeat sequentially through Phase 3)
One Task, One Branch, One Commit: Never combine prompts. Implement one task at a time on an isolated branch (git checkout -b task-X.Y).

Execute the Standalone Test Harness First: Every prompt specifies a test harness script (saved in tests/test_task_X_Y.py). If the test fails, prompt the model with the traceback until it passes.

Verify Regression with tests/test_instantiations.py: After a test harness passes, run the existing instantiation suite:

Bash
python tests/test_instantiations.py
Merge and Baseline: Run tests/vis.py on screen H1 and verify the reduction in loop time against the baseline (33.28 ms 
→
→
target 
≤
16.6
 ms
≤16.6 ms
).

Phase 1: Core Performance & Memory Fixes
Prompt 1.1: Font Instantiation Elimination & Static Caching
Markdown
You are an expert Python systems performance engineer.
Your task is to fix a major CPU bottleneck in `pyvisualiser` where fonts are loaded from disk and re-instantiated multiple times per frame.

### Problem:
In `src/pyvisualiser/core/components.py`, `Text.shrink_fontsize()` and `Text.textsize()` call `pygame.font.Font(self.fontfile, int(fontsize))` up to three times per frame per text element. Furthermore, `textsize()` renders a dummy surface just to measure width and height. This wastes 15-20ms of CPU time per frame.

### Requirements:
1. Create a dedicated `FontCacheManager` class in `src/pyvisualiser/core/components.py` (or as a separate module imported there).
   - Cache loaded `pygame.font.Font` instances keyed by `(font_path, font_size)`.
   - Implement `get_font(font_path: str, size: int) -> pygame.font.Font`.
2. Refactor `Text.shrink_fontsize()` to:
   - Use `FontCacheManager.get_font(...)` instead of `pygame.font.Font(...)`.
3. Refactor `Text.textsize(text, font)` to:
   - Use `font.size(text)` directly (built-in SDL_ttf method), removing the expensive `font.render()` surface allocation.
4. Add a dirty check in `Text.update(text, fontmax)`:
   - Only call `self.scalefont()` if `text != self.text` or if the bounding box dimensions have changed.
5. Do NOT break existing API signatures in `Text` or `TextFrame`.

### Verification Test Harness:
Create a standalone script `tests/test_task_1_1.py`:
- Initialize Pygame in headless mode (`os.environ["SDL_VIDEODRIVER"] = "dummy"`).
- Mock or create a dummy parent frame with `abs_wh = (400, 50)`.
- Create a `Text` instance with `text="Now Playing - Test Artist"`.
- Run a benchmark loop of 1,000 iterations calling `text.draw("Now Playing - Test Artist")` and measure elapsed time.
- Verify that `pygame.font.Font` constructor is NOT called after the initial warmup (use `unittest.mock.patch` on `pygame.font.Font`).
- Assert that 1,000 updates complete in less than 50ms total.

Provide the complete updated code for the affected sections and the full test script.
Prompt 1.2: VRAM Memory Leak Elimination in Texture Management
Markdown
You are an expert OpenGL and ModernGL graphics programmer.
Your task is to eliminate a GPU VRAM memory leak in `pyvisualiser` where orphaned OpenGL textures are abandoned without calling `.release()`.

### Problem:
In `src/pyvisualiser/core/displaydriver.py` (`GeometryPass.blit`) and `src/pyvisualiser/core/components.py` (`Text.draw`, `Image.draw`), when text changes or album art updates, the old ModernGL texture reference is cleared with `self._gl_texture = None` or overwritten with `self.ctx.texture(...)`. ModernGL does not automatically garbage-collect texture memory immediately, causing continuous GPU memory growth.

### Requirements:
1. In `src/pyvisualiser/core/displaydriver.py`, update `GeometryPass.blit()`:
   - Before uploading a new texture into `texture_holder._gl_texture`, check if `texture_holder._gl_texture` exists.
   - If it exists, call `texture_holder._gl_texture.release()` before assigning the new texture.
2. In `src/pyvisualiser/core/components.py`:
   - In `Image.draw()` and `Text.draw()`, if `self._gl_texture` is reset on content change, explicitly call:
     ```python
     if self._gl_texture is not None:
         self._gl_texture.release()
         self._gl_texture = None
     ```
   - In `Image.__del__()` and `Text.__del__()`, safely release `_gl_texture` if still allocated.
3. In `src/pyvisualiser/core/render.py`:
   - Inspect `RenderTarget._build()` and ensure `self.texture.release()` and `self.fbo.release()` are called safely when resizing.

### Verification Test Harness:
Create a standalone script `tests/test_task_1_2.py`:
- Initialize Pygame in dummy mode and create a ModernGL standalone context (`ctx = moderngl.create_context(standalone=True)`).
- Create a mock `texture_holder` with `_gl_texture = None`.
- Run a loop 500 times simulating a track change: generate a dummy 64x64 surface, call `blit()`, change the text/surface, and call `blit()` again.
- Inspect `ctx.info['GL_VRAM_USAGE']` or count allocated ModernGL resources via `len(ctx.glo_objects)` (or mock `ctx.texture`).
- Assert that total allocated textures in the context do not grow linearly with iterations (must remain constant).

Provide the code modifications and the complete test script.
Prompt 1.3: Additive Blend Batching & Draw Call Optimization
Markdown
You are an elite graphics systems engineer specializing in OpenGL draw-call batching.
Your task is to fix batch shattering in `pyvisualiser` caused by switching blend modes inside the bar rendering loop.

### Problem:
In `src/pyvisualiser/core/displaydriver.py`, `GeometryPass.set_additive()` calls `self._push_batch()` whenever the additive state toggles. In `Bar.drawV()`, every vertical bar in a spectrum toggles additive mode for inner/outer glow and normal mode for the bar body. For a 48-band spectrum, this results in over 100 individual draw calls and Python list-to-NumPy array conversions per frame, causing a 26ms frame draw time.

### Requirements:
1. In `src/pyvisualiser/core/displaydriver.py`:
   - Modify the vertex format in `GeometryPass`: Add `in_is_additive` (float, 0.0 or 1.0) to the vertex attributes.
   - Update `VERTEX_SHADER` and `FRAGMENT_SHADER` in `GeometryPass`:
     - Pass `v_is_additive` to the fragment shader.
     - In the fragment shader, when `v_is_additive > 0.5`, adjust output color using premultiplied alpha:
       ```glsl
       if (v_is_additive > 0.5) {
           f_color = vec4(final_color.rgb * 2.0, final_color.a * alpha);
       } else {
           f_color = vec4(final_color.rgb, final_color.a * alpha);
       }
       ```
   - In `GeometryPass.render()`, configure a single blend mode compatible with both normal and additive blending using premultiplied alpha:
     ```python
     self.ctx.enable(moderngl.BLEND)
     self.ctx.blend_func = moderngl.ONE, moderngl.ONE_MINUS_SRC_ALPHA
     ```
   - Remove `self.set_additive()` batch flushes from `draw_rect()` and `draw_line()`. Encode `is_additive` directly into the vertex data.
2. In `src/pyvisualiser/core/components.py`:
   - Update `Bar.drawV()` and `Bar.drawH()` so glow layers pass `additive=True` without triggering GPU state flushes.

### Verification Test Harness:
Create a standalone script `tests/test_task_1_3.py`:
- Create a ModernGL standalone context.
- Instantiate `GeometryPass` and a mock platform.
- Queue 50 alternating normal and additive rectangles (simulating a 50-band spectrum with glow).
- Intercept draw calls by monkey-patching `vao.render`.
- Assert that all 50 bars are submitted in **1 single draw call** (or 2 if texture-bound), not 50+.

Provide the updated `displaydriver.py` methods, the modified shaders, and the complete test script.
Prompt 1.4: Cross-Platform Packaging & Dependencies Hardening
Markdown
You are a Python packaging and embedded Linux specialist.
Your task is to fix `pyproject.toml` and `requirements.txt` in `pyvisualiser` to support both macOS development and embedded Raspberry Pi 5 Linux deployment.

### Problem:
`requirements.txt` contains macOS-exclusive packages (`pyobjc-core`, `pyobjc-framework-Cocoa`, `pyobjc-framework-Quartz`, etc.). Running `pip install -r requirements.txt` on Raspberry Pi OS (Debian 12 Bookworm, ARM64) crashes during build.

### Requirements:
1. Refactor `pyproject.toml`:
   - Split dependencies into core, macOS-specific, and test/dev groups.
   - Use PEP 508 environment markers for platform-specific dependencies:
     ```toml
     dependencies = [
         "numpy>=1.24.0",
         "scipy>=1.10.0",
         "pygame>=2.5.0",
         "moderngl>=5.8.0",
         "pyaudio>=0.2.13",
         "aubio>=0.4.9",
         "requests>=2.28.0",
         "roonapi>=0.1.6",
         "events>=0.5",
         "pillow>=10.0.0",
         "pyobjc-core>=10.0; sys_platform == 'darwin'",
         "pyobjc-framework-Cocoa>=10.0; sys_platform == 'darwin'",
         "pyobjc-framework-Quartz>=10.0; sys_platform == 'darwin'",
     ]
     ```
2. Refactor `requirements.txt`:
   - Provide clean base `requirements.txt` pointing to `.` or standard platform-independent wheels.
   - Create `requirements-pi.txt` optimized for Raspberry Pi (excluding all Apple frameworks and pinning lightweight alternatives).
3. In `src/pyvisualiser/__init__.py`:
   - Ensure no macOS-specific frameworks are imported at root level. Wrap optional imports in `try/except ImportError` blocks.

### Verification Test Harness:
Create a standalone validation script `tests/test_task_1_4.py`:
- Parse `pyproject.toml` using `tomllib` (Python 3.11+ built-in).
- Validate all dependency marker strings with `packaging.markers.Marker`.
- Simulate evaluate markers on `sys_platform == 'linux'` and verify that no `pyobjc` packages are included in the Linux dependency resolution.

Provide the updated packaging files and the test script.
Phase 2: Visual Clarity & Pipeline Overhaul
Prompt 2.1: Render Pipeline Reordering for Sharp Text & UI Overlays
Markdown
You are a senior graphics engine architect specializing in compositing pipelines.
Your task is to eliminate blurry text and smudged metadata in `pyvisualiser` by reordering the render passes.

### Problem:
In `src/pyvisualiser/core/render.py` (`Compositor.render_frame`), `GeometryPass` renders ALL elements (backgrounds, spectrum bars, and text labels) into `self.main_target` in Stage 1. 
In Stage 2, `GlowExtractionPass` extracts any pixel with luminance > threshold. High-contrast white text ($RGB=1.0$) is extracted into the bloom ping-pong buffer, blurred, and additively recombined over itself. This creates a fuzzy glow around all track information and volume numbers.

### Requirements:
1. In `src/pyvisualiser/core/render.py`, redesign `Compositor` to maintain three distinct target categories:
   - `emissive_target`: For background shaders, audio spectrum bars, and glowing shapes (Passes through Bloom/Blur).
   - `glow_buffer`: Downsampled ping-pong buffer for bloom blur.
   - `ui_target` (or direct backbuffer draw): For needle outlines, vector borders, text, and album art (Bypasses Bloom/Blur entirely).
2. Modify `Compositor.render_frame()` to enforce this execution sequence:
   - Step 1: Render background shaders and audio visualizers into `emissive_target`.
   - Step 2: Extract glow from `emissive_target` into `glow_buffer`.
   - Step 3: Blur `glow_buffer`.
   - Step 4: Composite `emissive_target` + `glow_buffer` onto the screen backbuffer.
   - Step 5: Render vector UI elements, text, and album art directly onto the backbuffer on top of the composited scene.
3. In `src/pyvisualiser/core/screenhandler.py`, ensure `screen.update_screen()` routes text and vector elements to the sharp UI pass.

### Verification Test Harness:
Create a standalone script `tests/test_task_2_1.py`:
- Initialize a headless ModernGL context.
- Instantiate `Compositor`.
- Submit an emissive cyan box ($RGB=2.0$) and a pure white text box ($RGB=1.0$).
- Inspect the pixels in `glow_buffer`:
  - Assert that the emissive box pixels ARE present in the glow buffer.
  - Assert that the white text box pixels are NOT present in the glow buffer (luminance in that region == 0).
- Assert that text rendered in Step 5 retains 100% sharp pixel edges in the final composite.

Provide the updated `render.py` classes and the complete test script.
Prompt 2.2: Retina & High-DPI Resolution Awareness
Markdown
You are an expert in cross-platform desktop UI rendering (macOS Cocoa and Linux Wayland).
Your task is to fix the 2x blur bug on macOS Retina displays in `pyvisualiser`.

### Problem:
On macOS Retina screens, `pygame.display.set_mode((1280, 400))` creates a window with logical dimensions of 1280x400, but the underlying OpenGL drawable framebuffer has 2560x800 physical pixels (scale factor = 2.0).
`GraphicsDriverGL` currently sets ModernGL's viewport and all FBO textures to 1280x400. macOS stretches this 1280x400 texture across the 2560x800 surface, causing blurriness across all lines, text, and meter dials.

### Requirements:
1. In `src/pyvisualiser/core/displaydriver.py` (`GraphicsDriverGL.init_display`):
   - Detect the high-DPI scaling ratio:
     ```python
     window_w, window_h = pygame.display.get_window_size()
     # Get physical drawable size from OpenGL/SDL
     drawable_w, drawable_h = pygame.display.gl_get_drawable_size() if hasattr(pygame.display, 'gl_get_drawable_size') else (window_w, window_h)
     self.dpi_scale = drawable_w / window_w
     ```
2. In `src/pyvisualiser/core/render.py` (`RenderContext` and `RenderTarget`):
   - Store `dpi_scale`.
   - When allocating `RenderTarget` FBO textures (`main_target`, `ui_target`), allocate at physical size:
     `w = int(base_w * scale * dpi_scale)`
     `h = int(base_h * scale * dpi_scale)`
   - Keep the virtual coordinate system (1280x400) unchanged for UI layout logic, but multiply vertex projection transformations by `dpi_scale` so vector strokes render at native hardware pixel density.
3. Ensure downsampling for the bloom buffer is calculated relative to native physical resolution.

### Verification Test Harness:
Create a standalone script `tests/test_task_2_2.py`:
- Mock `pygame.display.get_window_size` returning `(1280, 400)` and `gl_get_drawable_size` returning `(2560, 800)`.
- Initialize `RenderContext` and `RenderTarget`.
- Verify that `RenderTarget.texture.size` is initialized to `(2560, 800)`.
- Verify that normalized device coordinates in `GeometryPass` map correctly to the full 2560x800 buffer without clipping.

Provide the modified classes and the test script.
Prompt 2.3: Texture Filtering & Mipmapping Architecture
Markdown
You are a senior graphics programmer specializing in texture filtering and antialiasing.
Your task is to implement a strict texture filtering policy in `pyvisualiser` to eliminate moiré patterns and bilinear smearing on album artwork and UI textures.

### Problem:
In `src/pyvisualiser/core/displaydriver.py` and `components.py` (`Image.scaleInProportion`), textures are uploaded to ModernGL with default filtering (`NEAREST` or un-mipmapped `LINEAR`). Downscaling a 1000x1000 album cover into a 150x150 frame causes severe aliasing/shimmering, while scaling up causing blurring.

### Requirements:
1. In `src/pyvisualiser/core/displaydriver.py` (`GeometryPass.blit`):
   - When creating a texture for static artwork or images:
     - Generate mipmaps: `texture.build_mipmaps()`
     - Set standard high-fidelity filtering:
       ```python
       texture.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
       ```
2. In `src/pyvisualiser/core/render.py` (`RenderTarget`):
   - For intermediate full-screen render targets (FBOs), do NOT build mipmaps, but enforce:
     ```python
     self.texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
     self.texture.repeat_x = False
     self.texture.repeat_y = False
     ```
3. In `src/pyvisualiser/core/components.py` (`Image.scaleInProportion_and_crop`):
   - Ensure surface conversion uses `convert_alpha()` with consistent 32-bit RGBA byte order before passing to GPU.

### Verification Test Harness:
Create a standalone script `tests/test_task_2_3.py`:
- Initialize a ModernGL standalone context.
- Generate a 512x512 high-frequency test pattern (checkerboard).
- Upload to ModernGL texture through the updated loader.
- Verify that `texture.filter` matches `(moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)`.
- Render the texture into a 64x64 FBO and assert that the sampled output is free of severe aliasing artifacts (compute variance of pixel neighborhoods).

Provide the code modifications and the complete test script.
Prompt 2.4: FXAA Scoping & Exclusion for Text and Metadata
Markdown
You are an OpenGL shader engineer.
Your task is to fix `FXAAPass` in `pyvisualiser` so that it smooths 3D shader edges without degrading 2D typography.

### Problem:
In `src/pyvisualiser/core/render.py`, `FXAAPass` is applied to the final composite target when `self.fxaa_enabled = True`. Because FXAA is a screen-space post-process, it blurs the high-contrast edges of glyphs, making track titles and needle numbers appear muddy.

### Requirements:
1. In `src/pyvisualiser/core/render.py`:
   - Restrict `FXAAPass` so it operates ONLY on the 3D background / raymarching pass output before UI composition.
   - Or, implement luma-masking in `FXAAPass.fragment_shader`:
     - Add a `uniform sampler2D u_ui_mask;`
     - In the shader, if `texture(u_ui_mask, v_uv).r > 0.0` (indicating UI/text pixel), skip FXAA filtering and return the unmodified pixel:
       ```glsl
       if (texture(u_ui_mask, v_uv).r > 0.1) {
           f_colour = texture(tex, v_uv);
           return;
       }
       ```
2. In `Compositor.render_frame()`:
   - Ensure the post-process pipeline never blurs typography.

### Verification Test Harness:
Create a standalone script `tests/test_task_2_4.py`:
- Set up a headless ModernGL context.
- Create an image buffer with sharp high-contrast text lines and aliased diagonal lines.
- Run `FXAAPass` with the updated exclusion mask.
- Verify that diagonal lines are smoothed by FXAA while text pixel contrast remains 100% sharp (measure Laplacian sharpness on text regions before and after).

Provide the updated shader, Python pass code, and test script.
Phase 3: Architecture & Embedded Hardware Hardening
Prompt 3.1: Decouple UI Frames from Monolithic Platform via State Carriers
Markdown
You are an expert software architect specializing in decoupling and testability.
Your task is to refactor `pyvisualiser` so UI components do not depend on the monolithic `Platform` God-object.

### Problem:
In `src/pyvisualiser/visualisers/metadata.py`, `spectrum.py`, and `vumeters.py`, frames access audio and track data via `self.platform.samples`, `self.platform.vu['mono']`, `self.platform.track`, and `self.platform.elapsed`. UI widgets cannot be unit-tested without initializing sound drivers and network connections.

### Requirements:
1. Create an immutable data container in `src/pyvisualiser/core/state.py`:
   ```python
   @dataclass(frozen=True)
   class AudioState:
       vu: dict[str, float]
       peaks: dict[str, float]
       bins: dict[str, np.ndarray]
       waveform: dict[str, np.ndarray]
       bass: float = 0.0
       treble: float = 0.0
       bpm: float = 0.0
       is_beat: bool = False

   @dataclass(frozen=True)
   class PlaybackState:
       track: str = ""
       artist: str = ""
       album: str = ""
       duration: float = 0.0
       elapsed: float = 0.0
       volume_db: float = 0.0
       source: str = "Local"
In src/pyvisualiser/core/framecore.py, update Frame.update_screen():

Accept audio_state: AudioState and playback_state: PlaybackState as arguments.

Pass these states recursively to all child frames.

Update SpectrumFrame, VUFrame, and MetaDataFrame to read from the passed state objects instead of querying self.platform.

Provide backward compatibility so self.platform remains accessible during the transition period.

Verification Test Harness:
Create a standalone script tests/test_task_3_1.py:

Instantiate SpectrumFrame, VUMeter, and MetaDataFrame in complete isolation (passing platform=None).

Create mock AudioState and PlaybackState instances with synthetic sine-wave FFT data and fake track metadata.

Call update_screen(audio_state, playback_state).

Assert that all frames compute coordinates and queue geometry without raising AttributeError.

Provide the new state.py, updated frame classes, and the complete test script.

Code
---

### Prompt 3.2: Lock-Free Audio Ring Buffer Implementation

```markdown
You are a real-time DSP systems engineer.
Your task is to replace the audio queue in `pyvisualiser` with a lock-free circular ring buffer to prevent buffer overruns and latency spikes.

### Problem:
In `src/pyvisualiser/core/processaudio.py`, `AudioProcessor.callback()` puts audio chunks into a `queue.Queue(maxsize=10)`. Under heavy rendering loads, the main thread stalls, causing `status & pyaudio.paInputOverflow` warnings, dropped frames, and audio stutter.

### Requirements:
1. Implement a thread-safe, lock-free circular ring buffer `AudioRingBuffer` in `src/pyvisualiser/core/ring_buffer.py`:
   - Backed by a contiguous `numpy.ndarray(shape=(capacity,), dtype=np.int16)`.
   - Maintain atomic read and write pointers using integer index wrapping.
   - Non-blocking write: if the buffer is full, drop or overwrite the oldest unread samples gracefully.
   - Non-blocking read: retrieve the most recent $N$ samples (e.g., 1024 or 2048) in a single slice without memory allocations.
2. Update `AudioProcessor` in `src/pyvisualiser/core/processaudio.py`:
   - Replace `self.audio_queue` with `AudioRingBuffer`.
   - In PyAudio `callback()`, write raw PCM bytes directly into the ring buffer.
   - In `is_audio_available()`, query available samples from the ring buffer.

### Verification Test Harness:
Create a standalone script `tests/test_task_3_2.py`:
- Initialize `AudioRingBuffer` with a capacity of 16,384 samples.
- Spawn a high-frequency producer thread writing 512-sample chunks at 44.1 kHz (every ~11.6 ms).
- Spawn a consumer thread simulating erratic 30-60 FPS frame times (sleeping 15-35 ms).
- Run for 5 seconds.
- Assert zero unhandled exceptions, verify that data read is monotonically sequential, and verify memory footprint remains 100% constant.

Provide the ring buffer implementation, the updated `processaudio.py` sections, and the test script.
Prompt 3.3: Raspberry Pi 5 KMS/DRM & Wayland EGL Driver Engine
Markdown
You are an embedded Linux systems specialist with expertise in Raspberry Pi 5 graphics drivers (Mesa v3d, KMS/DRM, and Wayland).
Your task is to make `pyvisualiser` boot reliably on Raspberry Pi 5 whether running under Wayland Desktop or headless KMS/DRM console.

### Problem:
In `src/pyvisualiser/core/displaydriver.py`, `GraphicsDriverPi` hardcodes `os.environ['SDL_VIDEODRIVER'] = 'kmsdrm'` and `os.environ['SDL_VIDEODEVICE'] = '/dev/dri/card1'`. 
On Raspberry Pi OS Bookworm, Wayfire / Labwc uses Wayland by default, causing SDL KMS/DRM to crash with permission errors (`Permission denied: /dev/dri/card*`). Conversely, on Raspberry Pi OS Lite, Wayland is absent and direct DRM/KMS must be used.

### Requirements:
1. In `src/pyvisualiser/core/displaydriver.py`, implement an intelligent driver initialization routine `detect_linux_display_backend()`:
   - Check if `WAYLAND_DISPLAY` is present in `os.environ`:
     - If yes, configure SDL for Wayland: `os.environ['SDL_VIDEODRIVER'] = 'wayland'`.
   - If not, check if `DISPLAY` is present:
     - If yes, use X11: `os.environ['SDL_VIDEODRIVER'] = 'x11'`.
   - If neither, fallback to KMS/DRM:
     - Scan `/dev/dri/by-path/` or probe `/dev/dri/card*` dynamically for the active connector instead of hardcoding `card1`.
     - Set `os.environ['SDL_VIDEODRIVER'] = 'kmsdrm'`.
2. Configure ModernGL context creation to support OpenGL ES 3.1 fallback if Desktop OpenGL 3.3 Core is unavailable:
   ```python
   try:
       ctx = moderngl.create_context(require=330)
   except Exception:
       ctx = moderngl.create_context(require=310) # Fallback to GLES 3.1
Support the 90-degree rotated panel (1280x400 on physical 400x1280) natively in the vertex projection matrix without requiring CPU surface rotation.

Verification Test Harness:
Create a standalone script tests/test_task_3_3.py:

Test environment detection logic by mocking os.environ with (a) Wayland present, (b) X11 present, and (c) Headless console.

Verify correct SDL video driver selection for each case.

Test ModernGL context initialization with fallback handling.

Provide the updated display driver code and the test script.

Code
---

### Prompt 3.4: Dynamic Parameter Specification & Bound Validation

```markdown
You are a Python software engineer.
Your task is to fix parameter bound clamping in `pyvisualiser`'s live tuning profile controller.

### Problem:
In `src/pyvisualiser/styles/profiles.py`, `ProfileController.adjust()` clamps all parameters to `[0.0, 2.0]`:
```python
new_val = max(0.0, min(2.0, current + delta))
This breaks properties like vignette, softness, or sharpness which require bounds of [0.0, 1.0], as well as parameters that need larger ranges (e.g., blur spread or particle limits).

Requirements:
In src/pyvisualiser/styles/profiles.py, create a ParameterSpec dataclass:

Python
@dataclass(frozen=True)
class ParameterSpec:
    name: str
    min_val: float
    max_val: float
    default: float
    step: float
    description: str = ""
Define a master specification map PARAMETER_SPECS:

intensity: (0.0, 3.0, default=0.8, step=0.05)

softness: (0.0, 1.0, default=0.5, step=0.05)

threshold: (0.1, 2.0, default=1.0, step=0.05)

energy: (0.0, 1.0, default=0.5, step=0.05)

vignette: (0.0, 1.0, default=0.2, step=0.02)

sharpness: (0.0, 1.0, default=0.6, step=0.05)

warmth: (0.0, 1.0, default=0.5, step=0.05)

saturation: (0.0, 2.0, default=0.8, step=0.05)

Refactor ProfileController.adjust():

Query PARAMETER_SPECS for the parameter's specific bounds.

Clamp strictly within [spec.min_val, spec.max_val].

Prevent silent failures on unknown keys by logging a warning.

Verification Test Harness:
Create a standalone script tests/test_task_3_4.py:

Instantiate ProfileController.

Call adjust('vignette', 5.0) 
→
→
 assert clamped to 1.0.

Call adjust('vignette', -5.0) 
→
→
 assert clamped to 0.0.

Call adjust('intensity', 10.0) 
→
→
 assert clamped to 3.0.

Verify that HUD string formatting reflects the configured step sizes and precision.

Provide the updated profiles.py file and the complete test script.

Code
---

### Suggested Execution Order

Execute the prompts in this exact order to build up functionality without regressions:

$$\text{1.4 (Packaging)} \longrightarrow \mathbf{1.1 \text{ (Font Cache)}} \longrightarrow \mathbf{1.2 \text{ (VRAM Leak)}} \longrightarrow \mathbf{1.3 \text{ (Batching)}}$$
$$\downarrow$$
$$\mathbf{2.1 \text{ (Pipeline Order)}} \longrightarrow \text{2.2 (Retina DPI)} \longrightarrow \text{2.3 (Texture Filter)} \longrightarrow \text{2.4 (FXAA Masking)}$$
$$\downarrow$$
$$\text{3.4 (Parameter Specs)} \longrightarrow \text{3.2 (Ring Buffer)} \longrightarrow \text{3.1 (State Carriers)} \longrightarrow \text{3.3 (RPi5 Driver)}$$

By the end of **Prompt 1.3**, the 26.73 ms "Draw" bottleneck will be resolved, bringing total loop time well under the 16.6 ms target (60 FPS). Phase 2 eliminates visual artifacts, and Phase 3 hardens the codebase for deployment on the Raspberry Pi 5 preamplifier hardware.