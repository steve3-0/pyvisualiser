### Architectural Proposals & Discussion Points

---

### 1. Refinements to Core Foundations

* **`base_defs.py` & British English Standardization:**  
  All foundational enumerations will reside in `src/pyvisualiser/core/base_defs.py`. In accordance with British English conventions used across the project (`Colour`, `centre`), enumerations and configuration properties will use:
  * `ThemeColour` (`FOREGROUND`, `BACKGROUND`, `LIGHT`, `MID`, `DARK`, `ALERT`)
  * `HorizontalAlign` (`LEFT`, `CENTRE`, `RIGHT`, `COLUMN`)
  * `VerticalAlign` (`TOP`, `MIDDLE`, `BOTTOM`, `ROW`)
  * `Channel` (`LEFT`, `RIGHT`, `MONO`)
  * `Orientation` (`VERTICAL`, `HORIZONTAL`)
  * `MetadataKey` (`TRACK`, `ARTIST`, `ALBUM`, `DURATION`, `ELAPSED`, `VOLUME`, `SOURCE`, `SAMPLE_RATE`, `FORMAT`)
  * Both `centre` and `center` aliases will be supported at the boundary to prevent breaking external scripts.

* **Standardizing Component Data Ingestion via `core/state.py`:**  
  Currently, widgets access data through ad-hoc queries (`self.platform.vu['mono']`, `self.platform.track`, `self.platform.elapsed`).  
  Under the unified model:
  * `AudioSnapshot` and `MediaSnapshot` become the single source of truth passed down during `Frame.update_screen(audio_state, media_state)`.
  * Components implement a clean contract:
    ```python
    def update_screen(self, audio: AudioSnapshot, media: MediaSnapshot): ...
    ```
  * Legacy fallback `self.platform.*` will be retained as a read-only property during the transition so older custom screens do not break.

* **GLSL Contract & Rapid Prototyping Template Generator:**  
  To eliminate regex-based shader string manipulation and support instant shader experimentation, `ShaderDescriptor` will provide:
  1. An explicit uniform block matching `AudioSnapshot`:
     * `u_vu_mono`, `u_vu_left`, `u_vu_right`
     * `u_bass`, `u_treble`, `u_bpm`, `u_is_beat`
     * `u_centroid`, `u_flux`, `u_kurtosis`
     * `u_time`, `u_resolution`, `u_frame_offset`, `u_frame_size`, `u_palette_colour`
  2. A CLI/Python template generator `ShaderDescriptor.create_template("my_effect.frag.glsl")` that generates a ready-to-run fragment shader boilerplate with audio uniforms wired up.

* **VUMeter Polar Math & Edge Cases:**  
  The bounding-box solver `compute_safe_meter_radius` will be treated as an exact constraint optimization problem. It calculates needle length, arc radius, and tick marks using the bounding envelope:
  $$R_{\text{max}} = \min \left( \frac{\frac{W}{2} - \text{margin}}{\max(|\sin\theta_{\min}|, |\sin\theta_{\max}|)}, \; \frac{H(1 - y_{\text{pivot}}) - \text{margin}}{1 + \max(\cos\theta)} \right)$$
  Unit tests will specifically target extreme aspect ratios ($3.2:1$ ultrawide down to $1:3$ vertical meter strips) and extreme pivot points ($-1.5$ to $+0.5$).

---

### 2. Proposal: Reusable Style $\rightarrow$ Preset $\rightarrow$ Profile Hierarchy

To make the styling system intuitive and allow components to be created once and shared across profiles, we establish a strict three-tier hierarchy:

```
┌────────────────────────────────────────────────────────────────────────┐
│ LEVEL 1: STYLES (Atomic Dataclasses)                                   │
│ Immutable property definitions for visual geometry.                   │
│ e.g., NeedleStyle, ScaleStyle, BarStyle, BackgroundStyle, OutlineStyle │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ instances of styles
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ LEVEL 2: PRESETS (Curated, Reusable Component Specifications)          │
│ Concrete, named visual packages that define a specific component look.│
│ e.g., VintageNeedle, ModernStudioScale, SegmentedNeonBar, GlassOutline │
│ A preset defines dimensions, tick marks, ballistics, and needle shape. │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ grouped into
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ LEVEL 3: PROFILES (System Environment & Dynamic Theme Engine)          │
│ Top-level context (EmbeddedHiFiProfile, DesktopWidgetProfile).         │
│ Resolves: Screen resolution, FPS, active Colour theme ('hifi', 'amber'),│
│ global Background, Master ProfileControls, and default Presets.        │
└────────────────────────────────────────────────────────────────────────┘
```

#### How Resolution Works in Practice
1. **A Component Declares Its Visual Preset:**  
   `VUMeter(cols, channel=Channel.LEFT, preset=VUMeterPresets.TUNGSTEN)`  
   The preset specifies the scale arcs, tick proportions, needle length, and ballistics.
2. **The Profile Resolves Dynamic Palette & Global Overrides:**  
   The preset uses symbolic theme colours (`ThemeColour.LIGHT`, `ThemeColour.ALERT`). When rendered inside `EmbeddedHiFiProfile`, `ThemeColour.LIGHT` resolves to cyan `#00BEF0`. When rendered inside `VintageLuxuryProfile`, it resolves to warm amber `#FFB84D`.
3. **Cross-Profile Reusability:**  
   A `VUMeter` preset configured for high-end studio monitoring can be placed directly onto an embedded 1280×400 preamplifier console or scaled down inside a 400×300 floating desktop widget without rewriting any coordinates.

---

### 3. Diagnosis & Solution: Fixing the Interactive HUD

#### Why the Current HUD Does Not Work
1. **Broken Attribute Delegation:** `ScreenController.keyEvents` toggles `self.platform.toggle_debug_hud()`, which sets `show_debug_hud` on `GraphicsDriverGL`. However, `EventHandler.KeyAction` checks `hasattr(self.platform, 'show_debug_hud')`. Because `Platform` did not expose or forward this property directly, navigation keys (`LEFT`/`RIGHT`/`UP`/`DOWN`) never reach the parameter controller.
2. **Texture Memory Thrashing in HUD Render:** `_render_debug_hud` calls `self.renderer.blit()` without a persistent `texture_holder`. Every frame, 11 new OpenGL textures are uploaded for text lines and never released, causing immediate frame drops.
3. **Key Conflicts:** In `ScreenController.keyEvents`, numeric keys `1`, `2`, `3`, `4` were overridden to toggle OpenGL debug views (`FULL SCENE`, `BACKGROUND`, `UI`, `GLOW`), disconnecting preset switching (`LUXURY`, `NEON`, `MINIMAL`).
4. **Disconnected Reactive Propagation:** `ProfileController.adjust` updates `ProfileControls`, which only sets two uniforms in `Compositor`. None of the active screen components (spectrum bars, needle ballistics, colors) receive notifications when parameters are tuned live.

#### The Modernized Live HUD Engine
1. **Dedicated Overlay Pass (`HUDOverlayPass`):**  
   The HUD is isolated from the main geometry batch. It renders directly into the UI overlay using a single static font cache and a dedicated, persistent text texture buffer.
2. **Two-Way Dynamic Propagation:**  
   When a profile control is adjusted (e.g., `energy` or `softness`), `ProfileController` updates compositor bloom parameters *and* notifies active screen components via an `on_profile_update(controls)` hook, enabling instantaneous visual feedback.
3. **Preset Serialization (`S` key):**  
   Pressing `S` in tuning mode serializes the currently tuned parameters directly to the console or a JSON snippet, allowing tuned looks to be pasted directly into `presets.py`.

---

### 4. Layered Documentation Architecture (`docs/API_REFERENCE.md`)

The revised documentation will be organized into three clear, progressive tiers:

* **Level 1: Beginner Tutorial & Declarative UI Quickstart**
  * Building a working Hi-Fi dashboard in under 30 lines of declarative Python.
  * Understanding container hierarchy: `Frame`, `ColFramer`, `RowFramer`.
  * Using pre-built widgets (`VUMeter`, `SpectrumFrame`, `MetaDataFrame`, `PlayProgressFrame`).
* **Level 2: Advanced Guide (Presets, Styles, Shaders & Ballistics)**
  * Customizing component aesthetics via dataclasses (`BarStyle`, `VUMeterVisuals`, `OutlineStyle`).
  * Tuning motion dynamics with `MeterBallistics` and `FFTBallistics`.
  * Authoring custom GLSL background shaders with the new template generator.
  * Developing and registering custom Presets.
* **Level 3: Full Core Architecture & API Specification**
  * Complete class and function signatures with type hints.
  * Coordinate math, `DisplayMetrics`, and High-DPI physical-to-logical translation.
  * The 5-stage compositing pipeline (`Compositor`, `RenderTarget`, `PingPongBuffer`).
  * Audio loopback capture, ring buffer mechanics, and Roon/MPD metadata bridge.

---

## Staged Implementation Punchlist

Below is the modular punchlist. Each task is self-contained, specifies exact target files, and includes an automated test harness that lower-capability models can execute to verify correctness without live audio hardware.

---

### Phase 1: Core Definitions, State Carriers & Metadata Ingestion

#### Task 1.1: Foundational Definitions (`base_defs.py`)
* **Objective:** Create `src/pyvisualiser/core/base_defs.py` containing typed `StrEnum` classes with British English naming (`Channel`, `Orientation`, `HorizontalAlign`, `VerticalAlign`, `ThemeColour`, `MetadataKey`, `RenderLayer`).
* **Target Files:**
  * Create: `src/pyvisualiser/core/base_defs.py`
  * Update: `src/pyvisualiser/core/__init__.py`, `src/pyvisualiser/__init__.py`
* **Test Harness (`tests/harness/test_task1_1_base_defs.py`):**
  * Verify string equality (`Channel.LEFT == "left"`).
  * Verify British English and alias mappings (`HorizontalAlign.CENTRE == "centre"`, `HorizontalAlign.CENTER == "centre"`).
  * Verify all enumerations import cleanly on Python 3.10 and 3.11+.

#### Task 1.2: Standardized Metadata State Ingestion
* **Objective:** Refactor `MetaData`, `TextFrame`, and `MetaImages` in `src/pyvisualiser/visualisers/metadata.py` to ingest strongly typed `AudioSnapshot` and `MediaSnapshot` from `core/state.py`.
* **Target Files:**
  * `src/pyvisualiser/visualisers/metadata.py`
  * `src/pyvisualiser/core/framecore.py`
* **Test Harness (`tests/harness/test_task1_2_metadata_state.py`):**
  * Instantiate `MetaDataFrame` and `PlayProgressFrame` in a headless environment.
  * Pass synthetic `MediaSnapshot(track="Test Track", artist="Test Artist", duration=300.0, elapsed=150.0)`.
  * Assert elapsed calculation, progress bar level (0.5), and text drawing without querying `self.platform`.

---

### Phase 2: Layout Engine & Component Configuration

#### Task 2.1: Unified `FrameConfig` Architecture
* **Objective:** Introduce `FrameConfig` in `src/pyvisualiser/core/config.py`. Update `Frame.__init__` in `framecore.py` to accept `config: Optional[FrameConfig] = None` while preserving backward compatibility for positional arguments.
* **Target Files:**
  * Create: `src/pyvisualiser/core/config.py`
  * Update: `src/pyvisualiser/core/framecore.py`
* **Test Harness (`tests/harness/test_task2_1_frame_config.py`):**
  * Instantiate nested frames using `FrameConfig(scalers=(0.5, 1.0), padding=10, theme="hifi")`.
  * Validate coordinate calculations, padding deduction, and bounds clamping.

#### Task 2.2: Pure-NumPy Gradient Generator Validation
* **Objective:** Replace `Colour.colourmap` in `framecore.py` with pure-NumPy interpolation, removing all `matplotlib` imports.
* **Target Files:**
  * `src/pyvisualiser/core/framecore.py`
* **Test Harness (`tests/harness/test_task2_2_numpy_gradient.py`):**
  * Verify `generate_gradient_lut` produces a continuous 256-entry RGBA table matching expected RGB endstops.
  * Verify that neither `matplotlib` nor `pylab` is loaded in `sys.modules`.

---

### Phase 3: Decoupled Ballistics & Bounding-Box Safe VU Meter

#### Task 3.1: Decouple Ballistics from Visual Styling
* **Objective:** Create `src/pyvisualiser/styles/ballistics.py` with `MeterBallistics` and `FFTBallistics`. Refactor `VUMeter` and `VU` classes in `vumeters.py` to accept an isolated ballistics model.
* **Target Files:**
  * Create: `src/pyvisualiser/styles/ballistics.py`
  * Update: `src/pyvisualiser/visualisers/vumeters.py`
  * Update: `src/pyvisualiser/styles/styles.py`
* **Test Harness (`tests/harness/test_task3_1_ballistics.py`):**
  * Feed step-function audio values ($0.0 \rightarrow 1.0 \rightarrow 0.0$) through `VU(ballistics=MeterBallistics(decay_rate=0.2))`.
  * Verify decay curve monotonicity, peak hold persistence, and zero impact from needle style changes.

#### Task 3.2: Bounding-Box Safe Polar Coordinate Engine
* **Objective:** Implement `compute_safe_meter_radius` in `vumeters.py` to guarantee needle tips, ticks, and scale text never clip or overflow the parent frame.
* **Target Files:**
  * `src/pyvisualiser/visualisers/vumeters.py`
* **Test Harness (`tests/harness/test_task3_2_safe_polar_math.py`):**
  * Test narrow ($W=200, H=400$), wide ($W=600, H=200$), and square frames with extreme pivots ($-0.8$).
  * Verify all computed coordinate points $(x_i, y_i)$ lie strictly within $[0, W] \times [0, H]$.

---

### Phase 4: GLSL Contract & Rapid Prototyping Template Generator

#### Task 4.1: Standardized GLSL Shader Interface & Header Injection
* **Objective:** Refactor `GLSLFrame` and `BackgroundRenderPass` in `glwrapper.py` and `backgrounds.py` to use `ShaderDescriptor` and clean GLSL uniform preamble injection.
* **Target Files:**
  * `src/pyvisualiser/core/glwrapper.py`
  * `src/pyvisualiser/core/backgrounds.py`
* **Test Harness (`tests/harness/test_task4_1_shader_contract.py`):**
  * Compile a minimal test shader using the injected header.
  * Verify all `AudioSnapshot` uniforms (`u_vu_mono`, `u_bass`, `u_bpm`, `u_palette_colour`) bind without compilation errors.

#### Task 4.2: Fragment Shader Prototyping Template Generator
* **Objective:** Implement `ShaderDescriptor.create_template(output_path)` to generate clean boilerplate fragment shaders for rapid user experimentation.
* **Target Files:**
  * `src/pyvisualiser/core/glwrapper.py`
* **Test Harness (`tests/harness/test_task4_2_shader_template.py`):**
  * Generate a template shader to a temporary file.
  * Verify file creation, compile with ModernGL, and assert valid shader linkage.

---

### Phase 5: Style $\rightarrow$ Preset $\rightarrow$ Profile Hierarchy & Interactive HUD

#### Task 5.1: Structured Preset Library & Profile Manager Refactor
* **Objective:** Reorganize `presets.py` and `profiles.py` into the three-tier hierarchy (`Styles`, `Presets`, `Profiles`). Add helper methods for component preset assignment.
* **Target Files:**
  * `src/pyvisualiser/styles/styles.py`
  * `src/pyvisualiser/styles/presets.py`
  * `src/pyvisualiser/styles/profiles.py`
* **Test Harness (`tests/harness/test_task5_1_preset_hierarchy.py`):**
  * Verify cross-profile component instantiation (e.g., assigning `VUMeterPresets.LUXURY_AMBER` under `EmbeddedHiFiProfile`).
  * Verify dynamic theme color resolution.

#### Task 5.2: Live Interactive HUD Engine & Preset Serialization
* **Objective:** Implement a dedicated, leak-free `ProfileHUD` overlay in `displaydriver.py` and `screenhandler.py`. Fix keyboard navigation (`LEFT`/`RIGHT`/`UP`/`DOWN`), live component updates, and JSON parameter dumping (`S` key).
* **Target Files:**
  * `src/pyvisualiser/core/displaydriver.py`
  * `src/pyvisualiser/core/screenhandler.py`
  * `src/pyvisualiser/styles/profiles.py`
* **Test Harness (`tests/harness/test_task5_2_interactive_hud.py`):**
  * Simulate keypresses toggling the HUD and adjusting `softness` and `intensity`.
  * Assert parameter clamping and verify zero texture allocation leaks over 100 HUD render iterations.

---

### Phase 6: Consolidated QA Suite & Documentation

#### Task 6.1: Unified Test Runner (`run_tests.py`)
* **Objective:** Merge all modular task harnesses and existing unit tests into a single test runner script executable via `python run_tests.py` or `pytest`.
* **Target Files:**
  * Create: `run_tests.py`
  * Consolidate: `tests/3goals/` $\rightarrow$ `tests/unit/`
* **Test Harness (`tests/test_suite_runner.py`):**
  * Execute entire suite and return exit code 0 only when 100% of headless tests pass.

#### Task 6.2: Three-Tier API Documentation Revision
* **Objective:** Revise `docs/API_REFERENCE.md` into the three-tier format: Level 1 (Beginner Tutorial), Level 2 (Presets & Shader Guide), Level 3 (Complete Architectural Specification).
* **Target Files:**
  * `docs/API_REFERENCE.md`
* **Verification:**
  * Manual architectural review and documentation completeness check.

---

### Questions Before Commencing Execution

1. **Preset Library Location:** Should component presets (e.g., `VUMeterPresets`, `SpectrumPresets`, `OutlinePresets`) reside in `src/pyvisualiser/styles/presets.py` or alongside their respective component modules (e.g., `src/pyvisualiser/visualisers/vumeters.py`)?
2. **Preset Export Format:** For the live HUD parameter dumper (`S` key), is standard Python code output (e.g., `ProfileControls(intensity=1.1, ...)`) preferred, or should it dump a `.json` file that can be loaded dynamically at runtime?
3. **HUD Activation Key:** Currently `K_l` toggles the HUD. Would you prefer a dedicated key combination (such as `F12` or `Tab`) to avoid clashes with text search or screen hotkeys?

---

*Awaiting your review and authorization to proceed with Task 1.1.*

Refactored Plan:

### Preliminary Architectural Assessment & Engineering Strategy

Before breaking down every task and sub-task, we must establish the **High-Integrity Execution Protocol**. 

To balance risk and allow safe rollback at every point, each work unit is structured as an **atomic, bisectable micro-milestone**:
1. **Branch & Rollback Granularity:** Every sub-task maps directly to an isolated Git feature branch (`feat/task-X.Y`). A sub-task is merged into `main` **only** when its dedicated headless verification harness passes *and* the accumulated regression test suite (`tests/run.py`) shows zero regressions. If a sub-task introduces visual or computational instability, a single `git switch main` cleanly aborts the change.
2. **Dual-Harness Validation Strategy:** Every sub-task includes:
   * **A Headless Synthetic Test Harness:** Executes in under 1 second using mock platforms (no audio hardware, no live display, no Roon network dependencies) to test mathematics, types, memory lifecycles, and edge conditions.
   * **Integration with Live Test Screens:** Updates existing test screens in `tests/` so you can visually verify the exact visual behavior using your selective runner:
     ```bash
     python tests/run.py --vua     # Analogue VU meters
     python tests/run.py --spec    # Spectrum analysers
     python tests/run.py --hero    # Hero screens
     ```
3. **Strict Invariant Rule:** A sub-task must touch no more than **one core concept or component family** at a time. No refactoring of backgrounds while touching spectrum mathematics; no modifying layout framers while adjusting shaders.

---

### Questions & Clarifications Before Decomposing

To ensure the sub-task decomposition fits your operational workflow, please confirm the following:

1. **Preset Directory Structure:**  
   Shall we place all modular presets in `src/pyvisualiser/presets/` (e.g. `vu_analog_presets.py`, `spectrum_presets.py`, `bar_presets.py`), or inside `src/pyvisualiser/styles/presets/` to maintain the existing top-level namespace?
2. **Strictness of Deprecation Warnings:**  
   During Phase 4 (prior to the Phase 5 Purge), should legacy dictionary passing emit a standard `warnings.warn(..., DeprecationWarning)` to the console, or should it log silently to an audit list (e.g., `Platform.deprecation_log`) to avoid cluttering your visual test terminal?
3. **Execution Cadence:**  
   Would you prefer to review the decomposition plan as a whole first, or should we output the decomposed blueprint for **Phase 4 (Sub-tasks 4.1.1 through 4.3.5)** immediately so you can inspect the prompt and test harness format before generating subsequent phases?

---

### Master Decomposed Sub-Task Index (Overview)

Below is how the remaining phases are decomposed into high-integrity micro-tasks designed for mixed automated/human execution:

```
PHASE 3: BALLISTICS DECOUPLING & FREQUENCY CALIBRATION
├─ Sub-task 3.1.1: MeterBallistics Integration & Decay Curve Tests (VU Analogue & Digital)
└─ Sub-task 3.1.2: FFTBallistics Integration & Spectrum Temporal Damping Calibration

PHASE 4: SYSTEMATIC DATACLASS API MIGRATION & ERGONOMICS DOGFOODING
├─ Workstream 4.1: Component Constructor Modernization
│   ├─ Sub-task 4.1.1: VUMeter & Needle/Scale Dataclass Binding
│   ├─ Sub-task 4.1.2: VUFrame & BarStyle Dataclass Binding
│   ├─ Sub-task 4.1.3: SpectrumFrame & SpectrumStyle Dataclass Binding
│   ├─ Sub-task 4.1.4: MetaImages, ArtFrame & ReflectionStyle Dataclass Binding
│   ├─ Sub-task 4.1.5: MetaData, TextFrame & PlayProgressFrame Dataclass Binding
│   └─ Sub-task 4.1.6: ShaderFrame & GLSLFrame Dataclass Binding
├─ Workstream 4.2: Domain Preset Library Separation
│   ├─ Sub-task 4.2.1: Bar & Indicator Presets (bar_presets.py)
│   ├─ Sub-task 4.2.2: Analogue VU Meter Presets (vu_analog_presets.py)
│   ├─ Sub-task 4.2.3: Digital VU Meter Presets (vu_digital_presets.py)
│   ├─ Sub-task 4.2.4: Spectrum Analyzer Presets (spectrum_presets.py)
│   ├─ Sub-task 4.2.5: Atmospheric & Background Presets (background_presets.py)
│   └─ Sub-task 4.2.6: Vector Outline & Bezel Presets (outline_presets.py)
└─ Workstream 4.3: Screen Archetype Dogfooding & Verification
    ├─ Sub-task 4.3.1: Archetype 1 - Studio Analogue Console (H1 Refactor)
    ├─ Sub-task 4.3.2: Archetype 2 - Reflective Horizon Spectrum (H2 Refactor)
    ├─ Sub-task 4.3.3: Archetype 3 - Art-Centric Hi-Fi Streamer (H6 Refactor)
    ├─ Sub-task 4.3.4: Archetype 4 - 3D Shader Immersion (H3/H7 Refactor)
    └─ Sub-task 4.3.5: Archetype 5 - Floating Desktop Companion (desktop_hero.py Refactor)

PHASE 5: THE MASTER PURGE & ARCHITECTURE HARDENING
├─ Sub-task 5.1: Purge Dictionary Unpacking in Outlines & Backgrounds
├─ Sub-task 5.2: Purge Loose *args and **kwargs in Frame & AxisFramers
├─ Sub-task 5.3: Purge Legacy Platform Snooping in Components
└─ Sub-task 5.4: Repository Hygiene (Deprecate screens.py, screens2.py, trials/)

PHASE 6: GLSL SHADER PIPELINE & TEMPLATE ENGINE
├─ Sub-task 6.1: Clean GLSL Header Injection & Audio Uniform Bridge
└─ Sub-task 6.2: Fragment Shader Boilerplate Prototyping Generator

PHASE 7: QA SUITE CONSOLIDATION & THREE-TIER DOCUMENTATION
├─ Sub-task 7.1: Master Unified Test Runner (run_tests.py / pytest consolidation)
├─ Sub-task 7.2: Level 1 Documentation - Beginner Declarative Quickstart
├─ Sub-task 7.3: Level 2 Documentation - Presets, Atmospheres & Shaders Guide
├─ Sub-task 7.4: Level 3 Documentation - Full Architectural & Mathematical Reference
└─ Sub-task 7.5: Baseline Freeze & v2.1.0 Tagging

PHASE 8: REAL-TIME INTERACTIVE DESIGN TOOL (HUD)
├─ Sub-task 8.1: Dedicated Zero-Leak HUD Overlay Pass
├─ Sub-task 8.2: Dynamic Parameter Propagation Engine
└─ Sub-task 8.3: Single-Key Python Preset Code Serializer
```

---

*Awaiting your response to the 3 questions above, after which we will immediately begin generating the detailed sub-task specifications, prompts, and test harnesses.*

### Phase 4 Architectural Review: Interface Harmonization & Golden Standard

To eliminate fragmentation across the library, every component in `pyvisualiser` must follow the identical design pattern set by **`VUMeter`** and **`SpectrumFrame`**.

---

### The Golden Standard Component Contract

Every component constructor adheres to an invariant signature hierarchy:

```python
Component(
    parent,                               # 1. Structural Container
    [domain_binding],                     # 2. Primary Data Binding (Channel, MetadataKey, or Shader Name)
    config: Optional[FrameConfig] = None, # 3. Spatial & Container Envelope (Scalers, Align, Bounds, Theme, Outline)
    visuals: Optional[VisualsDataclass]   # 4. Component Aesthetics (SDF shapes, colors, ticks, textures)     
                                          # 6. [secondary_visuals]                Nested Sub-elements (e.g. BarStyle inside a Progress Bar)
    [ballistics: Optional[Ballistics]],   # 5. Motion Dynamics (Decay, smoothing, inertia, peak hold)

)
```

---

## 1. Resolution of the Two Specific Shortcomings

### A. Integrating `barsize_pc` directly into `BarStyle`
Previously, `barsize_pc` floated loosely as an ad-hoc argument in `VUFrame(barsize_pc=0.7)`, `PlayProgressFrame(barsize_pc=0.5)`, `SpectrumStyle(barsize_pc=2.0)`, and `OscillogrammeStyle(barsize_pc=2.0)`.

**Architectural Fix:**
* The thickness, height percentage, and fill proportion of a bar are intrinsic geometric properties of the bar itself.
* `barsize_pc: float = 0.7` is consolidated directly into **`BarStyle`**.
* Components drawing bars (`VUFrame`, `PlayProgressFrame`, `SpectrumFrame`, `OscilogrammeBar`) read their thickness directly from `bar_visuals.barsize_pc`. Loose floating parameters are completely eliminated.

```python
@dataclass(frozen=True)
class BarStyle:
    """Unified visual geometry and sizing for solid and segmented LED bars."""
    barsize_pc: float = 0.7           # Thickness / fill ratio relative to container (0.0 to 1.0)
    led_h: int = 10                   # Height of individual LED segments (pixels)
    led_gap: int = 2                  # Gap between LED segments (0 = continuous solid bar)
    peak_h: int = 2                   # Thickness of floating peak hold marker
    radius: int = 2                   # Corner rounding radius for bar / segments
    orient: Orientation = Orientation.VERTICAL
    flip: bool = False                # Reverse growth direction
    tip: bool = False                 # Rounded or emphasized tip segment
    colour_mode: str = "horz"         # 'horz' (spread across bands) or 'vert' (height gradient)
    edge_softness: float = 0.0        # Subpixel SDF edge anti-aliasing
    effects: BarEffects = field(default_factory=BarEffects) # HDR Bloom & Peak Flash
```

---

### B. Developing First-Class Dataclasses for 4.1.4 & 4.1.5

#### 1. Media Artwork Interface (`MetaImages` & `ArtFrame` in 4.1.4)
Previously, `MetaImages` took loose arguments (`art_type='album'`, `opacity=1.0`, `reflection=None`, `**kwargs`).

**Harmonized Contract:**
We introduce **`ImageStyle`** to encapsulate all visual attributes of raster artwork:

```python
@dataclass(frozen=True)
class ImageStyle:
    """Aesthetic styling for album art and artist photography."""
    opacity: float = 1.0                              # Texture alpha transparency (0.0 to 1.0)
    reflection: Optional[ReflectionStyle] = None      # Mirrored floor reflection
    corner_radius: int = 0                            # Rounded bezel corners
    border_width: int = 0                             # Inner picture frame border
    border_colour: str = "mid"
    glow_intensity: float = 0.0                       # Additive outer edge aura
    glow_colour: Optional[str] = None
```

**Resulting `MetaImages` Constructor:**
```python
MetaImages(
    parent,
    key: MetadataKey = MetadataKey.ALBUM,
    config: Optional[FrameConfig] = None,
    visuals: Optional[ImageStyle] = None
)
```

---

#### 2. Typography & Text Interface (`TextFrame` & `MetaData` in 4.1.5)
Previously, `TextFrame` scattered parameters across `text`, `font_size`, `wrap`, `justify`, and `colour`.

**Harmonized Contract:**
We expand **`TextStyle`** to be the definitive typography specification:

```python
@dataclass(frozen=True)
class TextStyle:
    """Complete typographic visual specification."""
    typeface: str = "Inter/Inter-VariableFont_opsz,wght.ttf"
    font_size: Optional[int] = None                   # Fixed size cap; None = auto-scale to frame
    colour: str = "foreground"                        # Theme colour index
    justify: Tuple[str, str] = ("centre", "middle")   # (horizontal, vertical) anchoring
    wrap: bool = False                                # Multi-line text wrapping toggle
    max_lines: int = 1                                # Line clamp limit
    glow_intensity: float = 0.0                       # Text drop-shadow or bloom aura
```

**Resulting `TextFrame` & `MetaData` Constructors:**
```python
TextFrame(
    parent,
    text: str = "",
    config: Optional[FrameConfig] = None,
    visuals: Optional[TextStyle] = None,
    update_fn: Optional[Callable[..., str]] = None
)

MetaData(
    parent,
    key: MetadataKey = MetadataKey.TRACK,
    config: Optional[FrameConfig] = None,
    visuals: Optional[TextStyle] = None
)
```

---

#### 3. Transport Progression Interface (`PlayProgressFrame` in 4.1.5)
Previously, `PlayProgressFrame` took up to 12 loose parameters (`barsize_pc`, `orient`, `led_h`, `led_gap`, `radius`, `barw_min`, `barw_max`, `tip`, `theme`, `flip`, `outline`).

**Harmonized Contract:**
A progress bar is a composite widget: a central dynamic bar flanked by timecode labels. Its interface takes `bar_visuals` (`BarStyle`) and `text_visuals` (`TextStyle`):

```python
PlayProgressFrame(
    parent,
    config: Optional[FrameConfig] = None,
    bar_visuals: Optional[BarStyle] = None,
    text_visuals: Optional[TextStyle] = None
)
```

---

## 2. Exhaustive Phase 4 API Consistency Matrix

Every component across the library is now aligned with the `VUMeter` and `SpectrumFrame` pattern:

| Component | Domain Binding | Layout & Container | Primary Visuals | Motion Dynamics / Ballistics | Sub-Element Visuals |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`VUMeter`** | `channel: Channel` | `config: FrameConfig` | `visuals: VUMeterStyle` | `ballistics: MeterBallistics` | — |
| **`VUFrame`** | `channel: Channel` | `config: FrameConfig` | `bar_visuals: BarStyle` | `ballistics: MeterBallistics` | — |
| **`SpectrumFrame`** | `channel: Channel` | `config: FrameConfig` | `visuals: SpectrumStyle` | `ballistics: FFTBallistics` | `bar_visuals: BarStyle` |
| **`Diamondiser`** | `channel: Channel` | `config: FrameConfig` | `visuals: SpectrumStyle` | `ballistics: FFTBallistics` | — |
| **`Oscilogramme`** | `channel: Channel` | `config: FrameConfig` | `visuals: OscillogrammeStyle` | — | — |
| **`OscilogrammeBar`** | `channel: Channel` | `config: FrameConfig` | `visuals: OscillogrammeStyle` | — | `bar_visuals: BarStyle` |
| **`MetaImages`** | `key: MetadataKey` | `config: FrameConfig` | `visuals: ImageStyle` | — | `reflection: ReflectionStyle` |
| **`TextFrame`** | `text: str` | `config: FrameConfig` | `visuals: TextStyle` | — | — |
| **`MetaData`** | `key: MetadataKey` | `config: FrameConfig` | `visuals: TextStyle` | — | — |
| **`PlayProgressFrame`**| — | `config: FrameConfig` | `bar_visuals: BarStyle` | — | `text_visuals: TextStyle` |
| **`ShaderFrame`** | `shader: str` | `config: FrameConfig` | `visuals: ShaderVisuals` | — | — |

---

## 3. Updated Phase 4 Implementation Workstreams

```
                     UPDATED PHASE 4 WORKSTREAMS
                                  │
     ┌────────────────────────────┼────────────────────────────┐
     ▼                            ▼                            ▼
Workstream 4.1: Component    Workstream 4.2: Domain        Workstream 4.3: Screen
Constructors Modernization   Presets Separation            Ergonomics Dogfooding
(4.1.1 VUMeter               (4.2.1 bar_presets            (4.3.1 Studio Console
 4.1.2 VUFrame                4.2.2 vu_analog_presets       4.3.2 Reflective Horizon
 4.1.3 SpectrumFrame          4.2.3 vu_digital_presets      4.3.3 Art Streamer
 4.1.4 MetaImages (ImageStyle)4.2.4 spectrum_presets        4.3.4 3D Immersion
 4.1.5 MetaData & Progress    4.2.5 background_presets      4.3.5 Desktop Widget)
 4.1.6 ShaderFrame)           4.2.6 outline_presets)
```

### Detailed Sub-Tasks for Workstream 4.1:

* **Sub-task 4.1.1: `VUMeter` Harmonization**
  * `VUMeter(parent, channel=Channel.LEFT, config=FrameConfig(), visuals=VUMeterStyle(), ballistics=MeterBallistics())`
* **Sub-task 4.1.2: `VUFrame` Harmonization**
  * `VUFrame(parent, channel=Channel.LEFT, config=FrameConfig(), bar_visuals=BarStyle(barsize_pc=0.7), ballistics=MeterBallistics())`
  * Loose `barsize_pc` moved into `BarStyle`.
* **Sub-task 4.1.3: `SpectrumFrame` Harmonization**
  * `SpectrumFrame(parent, channel=Channel.MONO, config=FrameConfig(), visuals=SpectrumStyle(), bar_visuals=BarStyle(), ballistics=FFTBallistics())`
* **Sub-task 4.1.4: `MetaImages` & `ArtFrame` Harmonization**
  * Introduce `ImageStyle` dataclass.
  * `MetaImages(parent, key=MetadataKey.ALBUM, config=FrameConfig(), visuals=ImageStyle())`
* **Sub-task 4.1.5: `MetaData`, `TextFrame` & `PlayProgressFrame` Harmonization**
  * Expand `TextStyle` to encompass font size, justification, and wrapping.
  * `TextFrame(parent, text="...", config=FrameConfig(), visuals=TextStyle())`
  * `MetaData(parent, key=MetadataKey.TRACK, config=FrameConfig(), visuals=TextStyle())`
  * `PlayProgressFrame(parent, config=FrameConfig(), bar_visuals=BarStyle(), text_visuals=TextStyle())`
* **Sub-task 4.1.6: `ShaderFrame` Harmonization**
  * `ShaderFrame(parent, shader="liquidorb", config=FrameConfig(), visuals=ShaderVisuals(colour="mid"))`

---

## Ready for Execution

With `barsize_pc` unified into `BarStyle` and first-class dataclasses (`ImageStyle`, `TextStyle`) defined for artwork, typography, and progress widgets, all components now reflect a single architectural pattern.

We are ready to proceed with **Sub-task 3.1.1 (MeterBallistics Integration & Decay Verification)**.