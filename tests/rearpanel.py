import FreeCAD as App
import Part
import FreeCADGui as Gui

doc = App.newDocument("Dual_PCB_Preamp_Enclosure")

# Dimensions (mm)
panel_w = 435.0        # 435mm Chassis Width
panel_h = 82.0         # 82mm Chassis Height
panel_thk = 3.0        # 3mm Aluminum Panel

pcb_w = 200.0          # 200mm Wide PCB
pcb_l = 80.0           # 80mm Deep PCB
pcb_thk = 1.6          # 1.6mm PCB Thickness
pcb_left_margin = 50.0 # 50mm from left edge (looking from outside Y-face)

hole_clr_dia = 10.0    # Oversized cutout for RCA nose
rca_w = 9.6
rca_h = 11.0
rca_len = 8.9
rca_pitch = 16.0
gap_width = 30.0
center_hole_dia = 3.4

# Vertical spacing for Dual Stack PCBs (Top & Bottom Rows)
z_bottom_pcb = -panel_h / 2.0 + 15.0
z_top_pcb = z_bottom_pcb + 32.0

# PCB X-Position (Calculated from Panel Left Edge)
pcb_x_center = -panel_w / 2.0 + pcb_left_margin + (pcb_w / 2.0)

# Define RCA X-positions (5 Jacks, 30mm Gap, 3 Jacks)
rca_x_positions = []
start_x = pcb_x_center - (((4 * rca_pitch) + gap_width + (2 * rca_pitch)) / 2.0)

for i in range(5):
    rca_x_positions.append(start_x + (i * rca_pitch))

start_x_bank2 = rca_x_positions[-1] + rca_pitch + gap_width
for i in range(3):
    rca_x_positions.append(start_x_bank2 + (i * rca_pitch))

# Safe L-Bracket Positions (Avoid RCA cutouts)
bracket_x_offsets = [
    pcb_x_center - (pcb_w / 2.0) + 10.0,
    (rca_x_positions[4] + rca_x_positions[5]) / 2.0,
    pcb_x_center + (pcb_w / 2.0) - 10.0
]

# 1. VERTICAL REAR PANEL (435mm x 82mm)
panel_raw = Part.makeBox(panel_w, panel_thk, panel_h)
panel_raw.translate(App.Vector(-panel_w / 2.0, -panel_thk, -panel_h / 2.0))

panel_cuts = []

# Cutouts: Dual RCA Rows (Top & Bottom)
for z_pos in [z_bottom_pcb, z_top_pcb]:
    for x in rca_x_positions:
        h = Part.makeCylinder(hole_clr_dia / 2.0, panel_thk + 4)
        h.rotate(App.Vector(0,0,0), App.Vector(1,0,0), 90)
        h.translate(App.Vector(x, 2.0, z_pos))
        panel_cuts.append(h)

# Cutouts: Flush Countersunk Bolt Holes (Entering Y = -panel_thk -> Y = 0)
for z_pos in [z_bottom_pcb, z_top_pcb]:
    for x in bracket_x_offsets:
        # 3.2mm Through hole
        thru = Part.makeCylinder(1.6, panel_thk + 4)
        thru.rotate(App.Vector(0,0,0), App.Vector(1,0,0), 90)
        thru.translate(App.Vector(x, 2.0, z_pos + 4.0))
        
        # 90-degree Countersink (Flush Head on Outside Y = -panel_thk)
        cone = Part.makeCone(3.0, 1.6, 1.8)
        cone.rotate(App.Vector(0,0,0), App.Vector(1,0,0), 90)
        cone.translate(App.Vector(x, -panel_thk + 1.8, z_pos + 4.0))
        
        panel_cuts.extend([thru, cone])

panel = panel_raw
for cut_shape in panel_cuts:
    panel = panel.cut(cut_shape)

# 2. DUAL HORIZONTAL PCBS (200mm x 80mm)
def make_pcb(z_pcb_center):
    pcb_r = Part.makeBox(pcb_w, pcb_l, pcb_thk)
    pcb_r.translate(App.Vector(pcb_x_center - pcb_w / 2.0, 0, z_pcb_center - rca_h / 2.0 - pcb_thk))
    
    for x in bracket_x_offsets:
        h = Part.makeCylinder(1.6, pcb_thk + 4)
        h.translate(App.Vector(x, 10.0, z_pcb_center - rca_h / 2.0 - pcb_thk - 2))
        pcb_r = pcb_r.cut(h)
    return pcb_r

pcb_bottom = make_pcb(z_bottom_pcb)
pcb_top = make_pcb(z_top_pcb)
all_pcbs = pcb_bottom.fuse(pcb_top)

# 3. L-BRACKETS FOR BOTH PCBS
l_brackets = []
for z_pos in [z_bottom_pcb, z_top_pcb]:
    for x in bracket_x_offsets:
        vert_leg = Part.makeBox(8.0, 3.0, 14.0)
        vert_leg.translate(App.Vector(x - 4.0, 0, z_pos - rca_h / 2.0))
        
        horiz_leg = Part.makeBox(8.0, 14.0, 3.0)
        horiz_leg.translate(App.Vector(x - 4.0, 0, z_pos - rca_h / 2.0))
        
        l_brackets.append(vert_leg.fuse(horiz_leg))

all_brackets = l_brackets[0]
for b in l_brackets[1:]:
    all_brackets = all_brackets.fuse(b)

# 4. FLUSH MOUNT M3 BOLTS
def make_countersunk_bolt():
    head = Part.makeCone(3.0, 1.5, 1.8)
    shaft = Part.makeCylinder(1.5, 8.0)
    return head.fuse(shaft.translate(App.Vector(0,0,1.8)))

bolts = []
for z_pos in [z_bottom_pcb, z_top_pcb]:
    for x in bracket_x_offsets:
        # Horizontal Panel Bolt (Passes through rear panel into L-bracket)
        b_panel = make_countersunk_bolt()
        b_panel.rotate(App.Vector(0,0,0), App.Vector(1,0,0), 90)
        b_panel.translate(App.Vector(x, -panel_thk, z_pos + 4.0))
        
        # Vertical PCB Bolt (Passes upward through PCB into L-bracket base)
        b_pcb = Part.makeCylinder(1.5, 8.0)
        b_pcb.translate(App.Vector(x, 10.0, z_pos - rca_h / 2.0 - pcb_thk - 3.0))
        
        bolts.extend([b_panel, b_pcb])

all_bolts = bolts[0]
for b in bolts[1:]:
    all_bolts = all_bolts.fuse(b)

# 5. RCA CONNECTORS (Top Row = Red, Bottom Row = White)
red_rcas = []
white_rcas = []

def make_rca_row(z_pos):
    row = []
    for x in rca_x_positions:
        body = Part.makeBox(rca_w, rca_len, rca_h)
        body.translate(App.Vector(-rca_w / 2.0 + x, 0, z_pos - rca_h / 2.0))
        
        outer = Part.makeCylinder(8.3 / 2.0, 10.0)
        inner = Part.makeCylinder(center_hole_dia / 2.0, 10.0)
        barrel = outer.cut(inner)
        barrel.rotate(App.Vector(0,0,0), App.Vector(1,0,0), -90)
        barrel.translate(App.Vector(x, -10.0, z_pos))
        
        row.append(body.fuse(barrel))
    return row

# Generate rows
bottom_row = make_rca_row(z_bottom_pcb)
top_row = make_rca_row(z_top_pcb)

# Top = Red, Bottom = White
all_red = top_row[0]
for r in top_row[1:]:
    all_red = all_red.fuse(r)

all_white = bottom_row[0]
for w in bottom_row[1:]:
    all_white = all_white.fuse(w)

# 6. RENDER EVERYTHING TO FREECAD VIEW
def add_part(shape, name, color_rgb):
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    obj.ViewObject.ShapeColor = color_rgb

add_part(panel, "Vertical_Rear_Panel_435x82mm", (0.25, 0.25, 0.3)) # Dark Slate Panel
add_part(all_pcbs, "Dual_PCBs_200x80mm", (0.1, 0.45, 0.2))          # Green PCBs
add_part(all_brackets, "L_Brackets", (0.8, 0.7, 0.2))                # Brass L-Brackets
add_part(all_bolts, "M3_Flush_Bolts", (0.15, 0.15, 0.15))           # Black Hardware
add_part(all_red, "Top_RCA_Row_RED", (0.85, 0.1, 0.1))               # Top Row Red (Right)
add_part(all_white, "Bottom_RCA_Row_WHITE", (0.95, 0.95, 0.95))     # Bottom Row White (Left)

doc.recompute()
Gui.SendMsgToActiveView("ViewFit")