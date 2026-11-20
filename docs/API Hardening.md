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

### Architectural Roadmap: When & How We Execute the Mass Cleanup

You are spot on: **transitional shims are temporary safety nets, not permanent architecture.** The entire goal of this modernization is to delete the cruft, eliminate constructor soup, and enforce a clean, strongly typed API.

Here is the exact strategy for when and how the mass cleanup happens without stalling development.

---

### The 3-Step "Strangler" Strategy

```
Phase 2 & 3: Bridge Phase (Dual-Mode)
├─ New API is introduced (FrameConfig, MeterBallistics, StrEnums, Snapshots).
├─ Legacy arguments trigger a one-line DeprecationWarning (non-fatal).
└─ Old screens continue to run while new tests validate the modern contracts.
       │
       ▼
Phase 5: Modernize the Screen Library (The Migration Wave)
├─ Batch-migrate screens:
│   ├─ tests/screens3.py (Hero screens H1–H9) -> 100% FrameConfig & Enums
│   ├─ tests/desktop_hero.py -> 100% FrameConfig & Enums
│   └─ tests/VUscreens.py & tests/gltest.py -> Updated to new API
└─ The test screens themselves become executable examples of the new clean API.
       │
       ▼
Phase 6: The "Mass Purge" (Complete Tech Debt Deletion)
├─ Strip all legacy `*args`, loose `**kwargs`, and dictionary fallback paths.
├─ Remove dict-based outline/background unpacking (`if isinstance(b, dict): ...`).
├─ Enforce `FrameConfig` and strict dataclasses everywhere.
└─ Delete obsolete test scripts, leaving a unified, modern test suite.
```

---

### Exact Timing: The Phased Plan

| Milestone | What Happens | State of Tech Debt |
| :--- | :--- | :--- |
| **Phase 2 (Current)** | Implement `FrameConfig` and integrate into `Frame.__init__`. Allow both `FrameConfig` and legacy kwargs. | New clean path available; legacy path still operational. |
| **Phase 3 & 4** | Decouple ballistics (`MeterBallistics`, `FFTBallistics`), fix polar math, and wire up `ShaderDescriptor`. | Visualiser components upgraded to clean contracts. |
| **Phase 5** | Reorganize Presets (`vu_analog_presets.py`, `spectrum_presets.py`, etc.). Refactor Hero Screens (`H1–H9`, `desktop_hero.py`) to use only the new API. | All primary screens running exclusively on the modern API. |
| **Phase 6 (The Purge)** | **DELETE all legacy parameter parsing across the entire codebase.** Delete dict unpacking, delete obsolete test files (`screens.py`, `screens2.py`, stray scratch files in `trials/`), and lock down the API. | **100% Tech Debt Eradicated.** Zero legacy code remains. |

