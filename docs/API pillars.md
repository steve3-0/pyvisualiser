## 1. Exhaustive Inventory: The Core Functional Elements of `pyvisualiser`

A comprehensive review of the code reveals that `pyvisualiser` is not merely a collection of VU meters and spectrum bars. It is an **emissive audio-reactive design engine** built on six distinct pillars:

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           THE PYVISUALISER DESIGN PILLARS                               │
├─────────────────┬─────────────────┬──────────────────┬─────────────────┬────────────────┤
│   1. LAYOUT     │ 2. ATMOSPHERES  │   3. GEOMETRY    │  4. BALLISTICS  │ 5. EMISSIVE FX │
│  ARCHITECTURE   │ & BACKGROUNDS   │   & OUTLINES     │   & DYNAMICS    │   & SHADERS    │
├─────────────────┼─────────────────┼──────────────────┼─────────────────┼────────────────┤
│ • Relative      │ • Panel colors  │ • SDF rounded    │ • Inertia &     │ • HDR Bloom    │
│   Scaling       │ • Procedural    │   quads & rims   │   temporal      │ • Additive tip │
│ • Hierarchical  │   Clouds &      │ • Specular glass │   smoothing     │   glow         │
│   Axis Framers  │   Starfields    │   arcs & needles │ • Exponential   │ • Downsampled  │
│   (Col / Row)   │ • Static assets │ • Segmented LEDs │   decay rates   │   blur pass    │
│ • Padding, gaps │ • Reactive core │ • Dynamic drop   │ • Peak-hold     │ • GLSL Shader  │
│   & z-ordering  │   pulses        │   shadows        │   counters      │   injection    │
│ • Float-coord   │ • Vignette &    │ • Mipmapped art  │ • Attack/decay  │ • Full-screen  │
│   alignment     │   film grain    │   reflections    │   envelopes     │   raymarching  │
└─────────────────┴─────────────────┴──────────────────┴─────────────────┴────────────────┘
                                           │
                                           ▼
             6. TELEMETRY, MEDIA BINDINGS & PLATFORM HARDWARE
     (AudioSnapshot, MediaSnapshot, ALSA loopback, Roon/MPD, Wayland/KMS)
```

---

### Pillar 1: Layout & Spatial Composition Architecture
* **Coordinate Invariants:** Logical $1280 \times 400$ authoring canvas decoupled from high-DPI display density ($1\times, 2\times$).
* **Layout Mechanics:**
  * **Declarative Framers (`ColFramer`, `RowFramer`):** Ratio-driven auto-partitioning (`col_ratios=(1, 2, 1)`, `row_ratios=(4, 1)`) with inter-cell gap percentage (`padpc`) and perimeter insets (`padding`).
  * **Anchored Positioning:** Multi-axis anchors (`align=('centre', 'middle')`, `'left'`, `'top'`, `'right'`, `'bottom'`) with relative fractional scalers (`scalers=(0.5, 1.0)`).
  * **Geometric Constraints:** True 1:1 aspect ratio enforcement (`square=True`) for needle dials, rotary volume controls, and circular shaders.
  * **Visual Layer Stacking:** Integer `z_order` sorting ensuring shadows $\rightarrow$ backings $\rightarrow$ needles $\rightarrow$ glass bezels $\rightarrow$ typography render without overlap artifacts.

---

### Pillar 2: Atmospheric Surfaces & Background Layers
* **Virtual Hardware Surface (`BackgroundStyle`):**
  * **Base Panel:** Solid color, alpha-blended transparency, or underlying brushed aluminum/carbon textures (`texture_path`).
  * **Edge Lighting (`EdgeLightStyle`):** Ambient luminous bezels simulating edge-lit acrylic or OLED front-panel glow with audio coupling.
  * **Procedural Atmospheres:** Volumetric vapor clouds (`CloudStyle`), noise fields, and particulate dust drifts (`StarfieldStyle`).
  * **Vignette & Film Grain (`VignetteStyle`, `NoiseStyle`):** Radial shadows that draw focus inward and analog film noise that breaks up digital color banding.
  * **Audio-Reactive Panel Pulses (`ReactiveGlowStyle`, `PeakAccentStyle`):** Sub-bass center washes and transient flash accents on dynamic musical peaks.
  * **Sub-Frame Scissoring:** Localized background styling scoped to individual sub-containers (e.g. glowing backdrops behind VU meters while the screen background remains pitch black).

---

### Pillar 3: Geometry, Outlines & Component Stylings
* **Vector Outlines (`OutlineStyle`):**
  * Inner and outer borders with customizable stroke width, corner curvature (`radius`), opacity, and additive outer halos (`glow_intensity`, `softness`).
* **SDF Rounded Vector Primitives:**
  * GPU Signed Distance Field rendering for rounded boxes, progress sliders, and line segments with anti-aliased subpixel edges.
* **Skeuomorphic Instrumentation:**
  * Curved analogue dial geometry: tick line lengths, angular arc markers, customizable dB annotations, metallic dome pivots, and drop-shadow needles.
* **Segmented Digital Indicators:**
  * Solid vs. segmented LED columns (`led_h`, `led_gap`) with continuous or discrete amplitude color mapping.
* **Media Surfaces (`MetaImages`, `ArtFrame`):**
  * Square album covers and circular artist portraits featuring mirrored floor reflections (`ReflectionStyle`) and mipmapped bilinear filtering.

---

### Pillar 4: Ballistics, Motion Physics & Temporal Envelopes
* **Mechanical Analogue Physics (`MeterBallistics`):**
  * Moving-average inertia windows (`smoothing_samples`), exponential release timings (`decay_rate`), and peak hold timers (`peak_hold_frames`).
* **Digital Spectrum Dynamics (`FFTBallistics`):**
  * Fast attack envelopes, fluid linear/log decay, and floating peak markers.
* **Time-Domain Smoothing (`Smoother`):**
  * Multi-stage triangular and rectangular smoothing filters applied to raw FFT bins and RMS voltage rails.

---

### Pillar 5: Emissive Lighting, Bloom FX & GLSL Raymarching
* **Three-Layer Optical Model:**
  * Core Shape $\rightarrow$ Additive Edge Highlight $\rightarrow$ Atmospheric Bloom.
* **Five-Stage Compositing Pipeline (`Compositor`):**
  * Emissive HDR pass $\rightarrow$ Downsampled luminance extraction $\rightarrow$ Separable Gaussian ping-pong blur $\rightarrow$ Tone-mapped composite $\rightarrow$ Sharp vector/typography overlay.
* **Hot-Tip Emissive Glow (`BarEffects`):**
  * Peak glow scaling, alpha boost, and thresholding applied to upper signal bands.
* **Custom GLSL Shader Integration (`ShaderFrame`, `GLSLFrame`):**
  * Injecting procedural shaders (`liquidorb`, `supernova`, `warping`, `balatro`, `milkdrop`) as backgrounds or standalone hero visualizers.

---

### Pillar 6: Telemetry, Bindings & Platform Interfaces
* **Hardware Abstraction Layer:** Linux KMS/DRM (`/dev/dri/card*`), Wayland, and macOS OpenGL Core Profile 3.3.
* **Audio Capture Engine:** PyAudio callback writing into an atomic lock-free ring buffer (`AudioRingBuffer`), feeding real-time FFT analyses and RMS energy tracking.
* **Media Endpoints:** Asynchronous metadata polling from Roon or MPD producing immutable state snapshots (`AudioSnapshot`, `MediaSnapshot`).

---

## 2. Decomposing the Architecture: The Definitive Multi-Phase Plan

To reach a pristine, production-ready baseline, the remaining work is divided into **four comprehensive phases**:

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│ Phase 4: Systematic Dataclass API Migration & Design-Surface Validation           │
│ (Refactor components, decompose presets, dogfood all 6 pillars across 5 screens)  │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│ Phase 5: The Master Purge & Architecture Hardening                                │
│ (Eliminate legacy dicts, *args, **kwargs, loose attributes, and tech debt)        │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│ Phase 6: GLSL Shader Pipeline Modernization & Template Engine                     │
│ (ShaderDescriptor, uniform blocks, auto-generating prototyping templates)         │
└─────────────────────────────────────────┬─────────────────────────────────────────┘
                                          │
                                          ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│ Phase 7: Quality Assurance Suite, Three-Tier Docs & Pristine Release Baseline     │
│ (pytest runner, Level 1-3 docs, clean release tag)                                │
└───────────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 4: Systematic Dataclass API Migration & Design-Surface Validation

### Objective
Upgrade the user-facing design surface to use **strictly typed dataclasses and enums** across all six pillars, eliminating untyped parameter passing. Prove the ergonomic power of the new API by implementing five distinct flagship screens covering every pillar.

```
                    PHASE 4 EXECUTION STRUCTURE
                                 │
     ┌───────────────────────────┼───────────────────────────┐
     ▼                           ▼                           ▼
Task 4.1: Component       Task 4.2: Preset            Task 4.3: Screen
Constructors              Decomposition               Dogfooding Suite
(Layout, Atmosphere,      (Modular domain             (5 Archetypes proving
 Geometry, Ballistics)     libraries in presets/)      all 6 pillars)
```

---

### Task 4.1: Modernize Component Signatures across All Pillars
Refactor constructors across visualizers, backgrounds, and layout managers to strictly accept validated configuration dataclasses:

1. **Pillar 1 (Layout):**
   * `Frame(parent, config: Optional[FrameConfig] = None)`
   * `ColFramer(parent, ratios: Optional[Tuple[float, ...]] = None, gap_pc: float = 0.0, config: Optional[FrameConfig] = None)`
   * `RowFramer(parent, ratios: Optional[Tuple[float, ...]] = None, gap_pc: float = 0.0, config: Optional[FrameConfig] = None)`
2. **Pillar 2 & 3 (Atmosphere, Geometry & Outlines):**
   * Standardize `BackgroundStyle(colour, colour_opacity, texture_path, texture_opacity, vignette, noise, ambient_glow, reactive_glow, peak_accent, starfield, cloud, edge_light, shader)`.
   * Standardize `OutlineStyle(colour, width, radius, opacity, glow_intensity, softness, glow_colour)`.
   * Standardize `ReflectionStyle(size, opacity)`.
   * Enforce `MetaImages(parent, config: Optional[FrameConfig] = None, art_type: str = 'album', reflection: Optional[ReflectionStyle] = None)`.
3. **Pillar 3 & 4 (Gauges, Bars & Decoupled Ballistics):**
   * Refactor `VUMeter(parent, channel: Channel, visuals: VUMeterStyle, ballistics: MeterBallistics, config: Optional[FrameConfig] = None)`.
   * Refactor `VUFrame(parent, channel: Channel, visuals: BarStyle, ballistics: MeterBallistics, config: Optional[FrameConfig] = None)`.
   * Refactor `SpectrumFrame(parent, channel: Channel, visuals: SpectrumStyle, bar_visuals: BarStyle, ballistics: FFTBallistics, config: Optional[FrameConfig] = None)`.
4. **Pillar 5 (Emissive Shaders):**
   * `ShaderFrame(parent, shader_name: str, colour_theme: Optional[str] = None, config: Optional[FrameConfig] = None)`.
5. **Pillar 6 (Telemetry & Media):**
   * Standardize `TextFrame`, `MetaData`, and `PlayProgressFrame` to accept `FrameConfig`, binding directly to `MediaSnapshot` properties.

---

### Task 4.2: Decompose Component Presets into Modular Libraries
Separate the monolithic `src/pyvisualiser/styles/presets.py` into dedicated, domain-specific modules within `src/pyvisualiser/presets/` [2]:

* `src/pyvisualiser/presets/vu_analog_presets.py`  
  * `TungstenLuxury`, `VintageStudio`, `ModernBlueBezel`, `DarkAccuphase`, `MinimalistDial`
* `src/pyvisualiser/presets/vu_digital_presets.py`  
  * `MasteringLED`, `SolidBarHorz`, `SplitStereoVertical`, `NeonTipVU`
* `src/pyvisualiser/presets/bar_presets.py`  
  * Reusable LED block and solid bar styles (`SegmentedLEDBar`, `SolidGlowBar`, `ThinNeedleBar`) shared across meters and spectrums.
* `src/pyvisualiser/presets/spectrum_presets.py`  
  * `NeonReflectiveHorizon`, `Studio48Band`, `CompactOctaveBridge`, `DiamondRadial`
* `src/pyvisualiser/presets/outline_presets.py`  
  * `SubtleGlowBorder`, `SharpBezel`, `DeepInsetFrame`, `FloatingCardBorder`
* `src/pyvisualiser/presets/background_presets.py`  
  * `DeepVoidAtmosphere`, `VaporWaveCloud`, `BrushedCarbon`, `OLEDPureBlack`, `AmbientEdgeLit`

---

### Task 4.3: Screen Dogfooding & Ergonomics Verification Suite
To prove the API simplifies screen design, build and validate five distinct reference screens:

#### Screen Archetype 1: `AnalogConsoleHero` (Pillars 1, 2, 3, 4)
* **Goal:** A classic studio preamp layout.
* **Elements:** Dual analogue meters (`VUMeterPresets.TungstenLuxury`), ambient warm edge lighting (`BackgroundPresets.AmbientEdgeLit`), floating metal chassis borders, and a centered metadata stack (`Track`, `Artist`, `SampleRate`).
* **Ergonomic Test:** The entire screen must be declarative, cleanly defined in fewer than 40 lines of Python with zero manual pixel calculations.

#### Screen Archetype 2: `SpectrumHorizonHero` (Pillars 1, 2, 3, 4, 5)
* **Goal:** Wide ultrawide cinematic spectrum analyzer.
* **Elements:** 48-band stereo spectrum with floor reflections (`ReflectionStyle`), floating peak hold markers, hot-tip emissive bloom (`BarEffects`), set against a moving starfield background (`StarfieldStyle`).

#### Screen Archetype 3: `ArtFocusedStreamerHero` (Pillars 1, 2, 3, 6)
* **Goal:** Minimalist modern streamer (NAD M33 / Eversolo benchmark [1]).
* **Elements:** Dominant square album cover with soft glow halo, dynamic segmented progress bar, high-contrast typography, and audio-reactive vignette shadows.

#### Screen Archetype 4: `ShaderImmersionHero` (Pillars 1, 2, 5, 6)
* **Goal:** Modern visualizer running 3D GLSL raymarching.
* **Elements:** Central `liquidorb` or `supernova` shader reacting dynamically to real-time `AudioSnapshot` bass/treble, flanked by high-response vertical digital VU bars and a glowing transport overlay.

#### Screen Archetype 5: `FloatingDesktopWidget` (Pillars 1, 2, 3, 6)
* **Goal:** Compact, floating desktop companion widget ($400 \times 250$).
* **Elements:** Scaled-down components, transparent panel backing, compact needle meter, and single-line scrolling track title.

---

### Task 4.4: Deprecation Warning Instrumentation
* Instrument all legacy parameter access points (`Frame.__init__`, `Bar.__init__`, `VUMeter.__init__`, `BackgroundBase.__init__`).
* Emit explicit `DeprecationWarning`s when dictionaries or loose positional arguments are detected.
* Run all five screens via `python tests/run.py` and verify zero runtime deprecation warnings are logged.

---

## Phase 5: The Master Purge & Architecture Hardening

### Objective
Once the Phase 4 dogfooding suite passes, **delete all technical debt, bridges, and fallback adapters** to lock down the production architecture.

### Tasks
* **Task 5.1: Purge Constructor Fallbacks & Loose Arguments:**
  * Remove `*args` and loose `**kwargs` from `Frame`, `AxisFramer`, `ColFramer`, `RowFramer`, `VUMeter`, `VUFrame`, and `SpectrumFrame`.
  * Make `config: FrameConfig` the mandatory/first-class contract.
* **Task 5.2: Purge Dictionary Unpacking in Styles & Outlines:**
  * Delete all `if isinstance(outline, dict):` and `if isinstance(background, dict):` branches across `components.py` and `backgrounds.py`.
  * Enforce strict `TypeError` instantiation if dictionaries are supplied.
* **Task 5.3: Purge Legacy Platform Snooping:**
  * Disallow UI components from querying `self.platform.vu` or `self.platform.track`.
  * Enforce that `update_screen(audio_snapshot, media_snapshot)` is the only data pipeline into components.
* **Task 5.4: Repository Hygiene:**
  * Delete obsolete, superseded scripts (`tests/screens.py`, `tests/screens2.py`, and stray files in `trials/`).
  * Relocate and freeze unit tests in `tests/unit/`.

---

## Phase 6: GLSL Shader Pipeline Modernization & Template Engine

### Objective
Establish an airtight, non-regex GLSL shader compilation engine and developer prototyping workflow.

### Tasks
* **Task 6.1: Standardized `ShaderDescriptor` & Preamble Injection:**
  * Standardize compile-time header injection with exact uniform mappings matching `AudioSnapshot`:
    * Timing: `u_time`, `u_resolution`
    * Spatial: `u_frame_offset`, `u_frame_size`, `u_palette_colour`
    * Dynamics: `u_volume`, `u_vu_left`, `u_vu_right`, `u_bass`, `u_treble`, `u_bpm`, `u_is_beat`, `u_centroid`, `u_flux`, `u_kurtosis`
  * Replace string replacement hacks with standard GLSL source composition.
* **Task 6.2: Fragment Shader Template Generator:**
  * Implement `ShaderDescriptor.generate_template("assets/shaders/my_shader.frag.glsl")`.
  * Generates clean, ready-to-run shader boilerplate with comments and audio reactivity examples for rapid prototyping.

---

## Phase 7: Quality Assurance Suite, Three-Tier Documentation & Pristine Release Baseline

### Objective
Package the engine into a documented and tested release.

### Tasks
* **Task 7.1: Master Unified Test Runner (`run_tests.py`):**
  * Consolidate all modular test harnesses into a single test suite executable via:
    ```bash
    python run_tests.py
    # or
    pytest tests/
    ```
  * Assert 100% headless pass rate covering coordinates, ballistics, shader compilation, and snapshot calculations.
* **Task 7.2: Three-Tier `docs/API_REFERENCE.md` Overhaul:**
  * **Level 1 (Beginner Tutorial):** Declarative dashboard in 25 lines of Python, layout fundamentals (`ColFramer`, `RowFramer`).
  * **Level 2 (Advanced Guide):** Customizing ballistics, authoring presets, building procedural background atmospheres, injecting custom GLSL shaders.
  * **Level 3 (Full API Specification):** Complete, typed reference signatures for every class, enum, uniform, and mathematical constraint solver.
* **Task 7.3: Baseline Freeze & Tag:**
  * Tag repository release `v2.1.0-pristine`.

---

## Phase 8: Real-Time Interactive Design Tool (HUD)

### Objective
Deliver the real-time visual design tool for tuning profiles and exporting presets.

### Tasks
* **Task 8.1: Dedicated Overhead HUD Pass (`HUDOverlayPass`):**
  * Build a GPU overlay pass isolated from scene geometry with a dedicated, persistent text cache (no VRAM leaks).
* **Task 8.2: Dynamic Parameter Propagation:**
  * Wire keyboard adjustments (`intensity`, `softness`, `threshold`, `warmth`, `energy`) to update the compositor live *and* propagate changes down to active screen components.
* **Task 8.3: Preset Exporter (`S` Key):**
  * Pressing `S` serializes the tuned parameters into formatted Python code (e.g. `VUMeterPresets.CustomTuned = ...`) printed to the console or written to `presets/custom_presets.py`.

---

### Comprehensive Architectural Audit Against the 6 Pillars

Reviewing the plan against the **6 Pillars** (`pyvisualiser`'s complete vision) reveals a few subtle gaps where peripheral features (such as lines, boxes, multi-octave arced displays, particle systems, and event systems) were omitted from the component signature modernization list. 

To ensure a **production-quality v2.1.0 release**, we must expand Phase 4 and Phase 7 to cover *every single rendering primitive and auxiliary frame class* in the package. Otherwise, legacy untyped components will remain orphaned when we execute the Phase 5 "Great Purge".

---

### Gaps Identified & Remediation Steps

1. **Primitive & Auxiliary Visualizers Missing from Signature Modernization:**
   * **`Line` & `Box` (`components.py`):** These foundational primitives are used heavily in analogue meter needles, circular displays (`Diamondiser`), and procedural elements. They must accept styling datclasses (`OutlineStyle` or a dedicated `LineStyle`).
   * **`ArcsOctaves` & `Octaviser` (`spectrum.py`):** Multi-octave radial displays need a clean config contract.
   * **`SamplesFrame` & `OscilogrammeBar` (`oscillogramme.py`):** Time-series oscilloscope frames must map to `FrameConfig`, `OscillogrammeStyle`, and `BarStyle`.
2. **Preset Integration Across All Pillars:**
   * Every pillar requires dedicated preset files to ensure end users can instantiate pre-tuned aesthetics instantly.
3. **End-to-End System Integration Testing (The "System Verification Gate"):**
   * Before tagging v2.1.0, we need a dedicated integration test script that programmatically initializes the `ScreenController` with all refactored hero screens (`H1`–`H9`) and simulates an entire playback lifecycle (audio stream capture loop + Roon metadata change events + profile HUD adjustments) in a headless environment.

---

### Expanded & Hardened Master Plan

The execution plan below is fully comprehensive, ensuring 100% coverage of all 6 design pillars, rigorous system testing, and zero leftover tech debt.

```
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 1 & 2: Foundations & FrameConfig (COMPLETED)                     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: Ballistics Decoupling & Spectrum Calibration (COMPLETED)       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 4: SYSTEMATIC DATACLESS API MIGRATION (COMPLETE PILLAR COVERAGE) │
│ • 4.1 styles.py Harmonisation (TextStyle dataclass, ShaderStyle)       │
│ • 4.2 Core Component Signatures Across All 6 Pillars                   │
│     - Pillar 1: Frame, ColFramer, RowFramer                            │
│     - Pillar 2 & 3: BackgroundBase, Outline, Line, Box, MetaImages     │
│     - Pillar 3 & 4: VUMeter, VUFrame, SpectrumFrame, Diamondiser       │
│     - Pillar 5: ShaderFrame & GLSLFrame                                │
│     - Pillar 6: TextFrame, MetaData, PlayProgressFrame, Oscillogramme  │
│ • 4.3 Modular Domain Preset Libraries (`presets/`)                     │
│ • 4.4 Screen Archetype Dogfooding Suite (`H1`–`H9`, Desktop Heroes)    │
└───────────────────────────────────┬────────────────────────────────    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 5: THE MASTER PURGE & ARCHITECTURE HARDENING                     │
│ • 5.1 Remove dictionary unpacking in Outlines and Backgrounds          │
│ • 5.2 Remove loose *args and **kwargs in Frame and Framers             │
│ • 5.3 Remove platform attribute snooping in components                 │
│ • 5.4 Repository Hygiene (Delete obsolete screens.py, trials/, etc.)   │
└───────────────────────────────────┬────────────────────────────────    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 6: GLSL SHADER PIPELINE & TEMPLATE ENGINE                        │
│ • 6.1 Standardized ShaderDescriptor & AudioSnapshot Uniform Bridge     │
│ • 6.2 Fragment Shader Prototyping Template Generator                   │
└───────────────────────────────────┬────────────────────────────────    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ PHASE 7: QA SUITE, SYSTEM INTEGRATION & THREE-TIER DOCUMENTATION       │
│ • 7.1 Master Unified Test Runner (`run_tests.py` / pytest)             │
│ • 7.2 Headless Full-System Integration Test (Audio + Metadata + Render)│
│ • 7.3 Three-Tier `docs/API_REFERENCE.md` (Tutorial -> Advanced -> Ref) │
│ • 7.4 Baseline Freeze & v2.1.0 Tagging                                 │
└───────────────────────────────────┬────────────────────────────────    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────/
│ PHASE 8: REAL-TIME INTERACTIVE DESIGN TOOL (HUD)                       │
│ • 8.1 Dedicated Zero-Leak HUD Overlay Pass                             │
│ • 8.2 Dynamic Parameter Propagation Engine                             │
│ • 8.3 Single-Key Python Preset Code Serializer (`S` key)               │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Task Breakdown for Production Readiness

### Phase 4 Additions: Complete Component Coverage

#### Sub-task 4.2.7: Primitives & Auxiliary Components Harmonisation (`components.py`, `oscillogramme.py`)
* **Scope:** Modernize `Line`, `Box`, `Oscilogramme`, and `OscilogrammeBar` to accept `FrameConfig` and strict styling dataclasses.
* **Target Files:**
  * `src/pyvisualiser/core/components.py`
  * `src/pyvisualiser/visualisers/oscillogramme.py`
* **Definition of Success:** All drawing primitives operate strictly via typed configuration dataclasses with zero untyped kwargs.

---

### Phase 7 Additions: Rigorous System Integration Testing

#### Sub-task 7.2: Headless Full-System Integration Test (`tests/system/test_integration_lifecycle.py`)
* **Scope:** Build a comprehensive integration test that exercises the entire engine end-to-end without real hardware:
  1. Instantiates `ScreenController` with all refactored Hero Screens (`H1`–`H9`).
  2. Spawns a mock audio provider feeding synthetic multi-octave sine waves into the `AudioRingBuffer`.
  3. Fires asynchronous Roon metadata events (`new_track`, `start`, `stop`).
  4. Steps the main render loop through 300 frames, verifying zero exceptions, stable frame budgeting, and zero VRAM allocation growth.
* **Target Files:** Create `tests/system/test_integration_lifecycle.py`.
* **Definition of Success:** The integration test executes fully and outputs a clean report verifying that audio telemetry, metadata snapshots, and multi-pass shaders synchronize seamlessly.

---

## Final Review & Sign-Off

This expanded plan covers every single corner of `pyvisualiser`, guarantees zero orphaned legacy code upon purge, and introduces rigorous automated integration testing to ensure a commercial, production-quality release.

Does this comprehensive revision give you full confidence? If so, we are ready to lock this plan in and begin executing **Phase 4, Sub-task 4.1 (`styles.py` Harmonisation: `TextStyle` dataclass and `ShaderStyle`)**.