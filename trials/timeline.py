import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Set up figure and style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
fig, ax = plt.subplots(figsize=(14, 8), dpi=300)

# Colors
color_hw = '#2b5c8f'       # Blue
color_sw = '#1e824c'       # Green
color_mech = '#d9534f'     # Red/Coral
color_sys = '#8e44ad'      # Purple
color_bg = '#f8f9fa'

fig.patch.set_facecolor(color_bg)
ax.set_facecolor(color_bg)

# Timeline phases (Weeks 1 to 16)
weeks = list(range(1, 17))

# Data definition for tasks [Task Name, Stream, Start Week, Duration, Color]
tasks = [
    # CYCLE 1 (Weeks 1 - 8)
    ("HW Arch & Schematics", "HW", 1, 2.5, color_hw),
    ("PCB Layout v1 & Fab", "HW", 3.5, 2.5, color_hw),
    ("Board Assembly & Test", "HW", 6, 1.5, color_hw),
    
    ("SW Arch & MVC Setup", "SW", 1, 2, color_sw),
    ("Core Python/OpenGL UI", "SW", 3, 3, color_sw),
    ("Desktop/RPi Porting", "SW", 6, 1.5, color_sw),
    
    ("Mech Concepts & Specs", "Mech", 1, 2, color_mech),
    ("FreeCAD Enclosure v1", "Mech", 3, 2.5, color_mech),
    ("3D Router Milling v1", "Mech", 5.5, 2, color_mech),
    
    ("CYCLE 1 INTEGRATION & TEST", "System", 7.5, 1, color_sys),
    
    # CYCLE 2 (Weeks 9 - 16)
    ("HW Optimization & Noise Fixes", "HW", 9, 2.5, color_hw),
    ("PCB Layout v2 (Final Fab)", "HW", 11.5, 2.5, color_hw),
    ("Final Board Populating", "HW", 14, 1.5, color_hw),
    
    ("Advanced Features & HAL Tuning", "SW", 9, 3, color_sw),
    ("Non-Functional Optimization", "SW", 12, 2.5, color_sw),
    ("SW Freeze & Release", "SW", 14.5, 1, color_sw),
    
    ("Refined Panels & Shielding", "Mech", 9, 2.5, color_mech),
    ("Chassis CNC Milling & Anodize", "Mech", 11.5, 2.5, color_mech),
    ("Ergonomic & Thermal Fit Check", "Mech", 14, 1.5, color_mech),
    
    ("FINAL SYSTEM VALIDATION", "System", 15.5, 1, color_sys)
]

# Y-positions for streams
stream_y = {
    "HW": 4,
    "SW": 3,
    "Mech": 2,
    "System": 1
}

# Draw timeline bars
for task, stream, start, duration, color in tasks:
    y = stream_y[stream]
    # Draw rounded bar
    rect = patches.FancyBboxPatch(
        (start, y - 0.25), duration, 0.5,
        boxstyle="round,pad=0.02,rounding_size=0.1",
        linewidth=1, edgecolor='none', facecolor=color, alpha=0.85
    )
    ax.add_patch(rect)
    # Task Label
    ax.text(start + duration/2, y, task, color='white', weight='bold',
            fontsize=7.5, ha='center', va='center', wrap=True)

# Cycle background shading / vertical boundaries
# Cycle 1 Block
rect_c1 = patches.Rectangle((0.8, 0.3), 7.9, 4.4, linewidth=1.5,
                            edgecolor='#333333', facecolor='#e9ecef', alpha=0.3, linestyle='--')
ax.add_patch(rect_c1)
ax.text(4.75, 4.9, "CYCLE 1: Proof of Concept & Baseline Subsystems", 
        fontsize=11, weight='bold', color='#212529', ha='center')

# Cycle 2 Block
rect_c2 = patches.Rectangle((8.8, 0.3), 7.9, 4.4, linewidth=1.5,
                            edgecolor='#333333', facecolor='#e9ecef', alpha=0.3, linestyle='--')
ax.add_patch(rect_c2)
ax.text(12.75, 4.9, "CYCLE 2: Alpha Refinement & Final Integration", 
        fontsize=11, weight='bold', color='#212529', ha='center')

# Stream Labels on Y axis
ax.set_yticks([1, 2, 3, 4])
ax.set_yticklabels(["System Integration", "Mechanical", "Software", "Hardware"], fontsize=10, weight='bold')

# X axis formatting
ax.set_xlim(0.5, 17)
ax.set_xticks(range(1, 17))
ax.set_xticklabels([f"Wk {i}" for i in range(1, 17)], fontsize=9)
ax.set_xlabel("Project Timeline (Weeks / Milestones)", fontsize=11, weight='bold', labelpad=10)

# Title & Annotations
plt.title("Preamplifier Dual-Cycle Synchronized Development Roadmap", fontsize=14, weight='bold', pad=25)

# Feedback Loop Arrows
ax.annotate("", xy=(8.9, 4.2), xytext=(8.3, 1.3),
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=-0.3", color='#c0392b', lw=2))
ax.text(8.6, 2.7, "Cycle 1 Feedback\n& Lessons Learned", color='#c0392b', fontsize=8, weight='bold', ha='center', rotation=90)

plt.tight_layout()
plt.show()