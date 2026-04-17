#!/usr/bin/env python
# -*- coding: utf-8 -*-
import clr
import System
from System.Runtime.InteropServices import Marshal
from AlibreScript.API import *
import math
import time
def printTraceBack():
    import traceback
    return
def show_error(msg, title='Error', include_trace=False):
    try:
        from System.Windows.Forms import MessageBox
        MessageBox.Show(str(msg), str(title), System.Windows.Forms.MessageBoxButtons.OK, System.Windows.Forms.MessageBoxIcon.Error)
    except:
        pass
    if include_trace:
        printTraceBack()
def show_info(msg, title='Info'):
    try:
        from System.Windows.Forms import MessageBox
        MessageBox.Show(str(msg), str(title), System.Windows.Forms.MessageBoxButtons.OK, System.Windows.Forms.MessageBoxIcon.Information)
    except:
        pass
def safe_try(fn):
    """Decorator-like wrapper for event handlers to avoid crashing the UI."""
    def _inner(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as ex:
            show_error('Unexpected error: %s' % ex, 'Unexpected Error', include_trace=True)
            return None
    return _inner
alibre = None
root = None
MyPart = None
try:
    alibre = Marshal.GetActiveObject("AlibreX.AutomationHook")
    root = alibre.Root
except Exception as ex:
    show_error('Could not connect to Alibre Automation. Details: %s' % ex, 'Alibre Connection Error', include_trace=True)
try:
    if root is not None:
        MyPart = Part(root.TopmostSession)
    else:
        MyPart = None
except Exception as ex:
    show_error('Could not get current Part session. Open a part and try again.\nDetails: %s' % ex, 'Part Error', include_trace=True)
    MyPart = None
try:
    clr.AddReference('System.Windows.Forms')
    clr.AddReference('System.Drawing')
except Exception as ex:
    show_error('Failed to load Windows Forms assemblies. Details: %s' % ex, 'Reference Load Error', include_trace=True)
from System.Windows.Forms import (
    ListBox, SelectionMode, Padding, AutoScaleMode,
    Timer, Button, ToolTip,
    DockStyle, Cursors, FlatStyle,
    Form, Label, CheckBox, NumericUpDown,
    MessageBox, Panel, TableLayoutPanel,
    FlowLayoutPanel, FlowDirection, RadioButton
)
from System.Drawing import Color, Size, SizeF, Font, FontStyle, SystemFonts
def involute_function(angle):
    """Calculate involute function: tan(angle) - angle"""
    return math.tan(angle) - angle
def generate_external_tooth_profile(z, m, alpha_deg, profile_shift=0.0, undercut_auto_suppress=False, num_points=[10,10,5,5]):
    """
    Generate the profile of one tooth consisting of 6 parts.
    Parameters:
    -----------
    z : int
        Number of teeth
    m : float
        Module (mm)
    alpha_deg : float
        Pressure angle in degrees
    profile_shift : float
        Profile shifting value (default: 0.0)
    undercut_auto_suppress : bool
        Automatic undercut suppression (default: False)
    num_points : list of int
        Number of points per curve segment, order is following : [involute,trochoid,addendum,deddundum] (default: [20, 20, 20, 20])
    Returns:
    --------
    dict containing the 6 profile parts:
        'trochoid_1': [(x1, y1), (x2, y2), ...] - First trochoid curve
        'involute_1': [(x1, y1), (x2, y2), ...] - First involute curve  
        'upper_arc': [(x1, y1), (x2, y2), ...] - Upper addendum arc
        'involute_2': [(x1, y1), (x2, y2), ...] - Second involute curve
        'trochoid_2': [(x1, y1), (x2, y2), ...] - Second trochoid curve
        'lower_arc': [(x1, y1), (x2, y2), ...] - Lower dedendum arc
    """
    alpha = math.radians(alpha_deg)
    pitch_radius = m * z / 2.0
    base_radius = pitch_radius * math.cos(alpha)
    if undercut_auto_suppress:
        if base_radius > pitch_radius - m:
            profile_shift = base_radius - (pitch_radius - m)
    pitch_radius += profile_shift
    addendum_radius = pitch_radius + m
    dedendum_radius = max(pitch_radius - 1.25 * m, 0.01)
    if base_radius > pitch_radius:
        raise ValueError("Base radius is larger than pitch radius, resulting in invalid gear geometry.")
    else:
        offset_angle = math.acos(base_radius / pitch_radius)
    phi = involute_function(offset_angle)
    angular_tooth_width = math.pi / z
    addendum_involute_angle = math.acos(base_radius / addendum_radius)
    max_involute_angle = addendum_involute_angle + involute_function(addendum_involute_angle)
    if base_radius < dedendum_radius:
        deddendum_involute_angle = math.acos(base_radius / dedendum_radius)
    else : 
        deddendum_involute_angle = 0
    min_involute_angle = deddendum_involute_angle + involute_function(deddendum_involute_angle)
    tooth_angle = -angular_tooth_width - 2 * phi
    involute_1 = []
    involute_2 = []
    for i in range(num_points[0]):
        t = float(i) / (num_points[0] - 1)
        theta = t * (max_involute_angle - min_involute_angle) + min_involute_angle
        x_inv = base_radius * (math.cos(theta) + theta * math.sin(theta))
        y_inv = base_radius * (math.sin(theta) - theta * math.cos(theta))
        cos_tooth = math.cos(tooth_angle)
        sin_tooth = math.sin(tooth_angle)
        x1 = x_inv * cos_tooth - y_inv * sin_tooth
        y1 = x_inv * sin_tooth + y_inv * cos_tooth
        involute_2.append((x1, y1))
        involute_1.append((x_inv, -y_inv))
    trochoid_1 = []
    trochoid_2 = []
    if base_radius > dedendum_radius:
        t_trochoid = base_radius - dedendum_radius
        b_trochoid = math.sqrt(base_radius**4 / (base_radius - t_trochoid)**2 - base_radius**2)
        h_trochoid = b_trochoid * (1 - t_trochoid / base_radius)
        alpha_trochoid = math.atan(h_trochoid / base_radius)
        offset_trochoid_angle = alpha_trochoid + involute_function(alpha_trochoid)
        beta_trochoid = math.atan(b_trochoid / base_radius) - offset_trochoid_angle
        for i in range(num_points[1]):
            t = float(i) / (num_points[1] - 1)
            theta_tro = t * offset_trochoid_angle
            x_tro = (base_radius * (math.cos(theta_tro) + theta_tro * math.sin(theta_tro)) - 
                    t_trochoid * math.cos(theta_tro))
            y_tro = (base_radius * (math.sin(theta_tro) - theta_tro * math.cos(theta_tro)) - 
                    t_trochoid * math.sin(theta_tro))
            cos_beta = math.cos(beta_trochoid)
            sin_beta = math.sin(beta_trochoid)
            x_tro_rot = x_tro * cos_beta - y_tro * sin_beta
            y_tro_rot = x_tro * sin_beta + y_tro * cos_beta
            trochoid_1.append((x_tro_rot, y_tro_rot))
            cos_tooth = math.cos(tooth_angle)
            sin_tooth = math.sin(tooth_angle)
            x2 = x_tro_rot * cos_tooth - (-y_tro_rot) * sin_tooth
            y2 = x_tro_rot * sin_tooth + (-y_tro_rot) * cos_tooth
            trochoid_2.append((x2, y2))
        trochoid_1.reverse()
        trochoid_2.reverse()
    upper_arc = []
    addendum_involute_angle_val = math.acos(base_radius / addendum_radius)
    involute_at_addendum = involute_function(addendum_involute_angle_val)
    start_angle_upper = -involute_at_addendum
    end_angle_upper = tooth_angle + involute_at_addendum
    for i in range(num_points[2]):
        t = float(i) / (num_points[2] - 1)
        theta_arc = start_angle_upper + t * (end_angle_upper - start_angle_upper)
        x_arc = addendum_radius * math.cos(theta_arc)
        y_arc = addendum_radius * math.sin(theta_arc)
        upper_arc.append((x_arc, y_arc))
    lower_arc = []
    if base_radius > dedendum_radius:
        start_angle_lower = tooth_angle - beta_trochoid
        end_angle_lower = -angular_tooth_width * 2 + beta_trochoid
    else: 
        start_angle_lower = tooth_angle + involute_function(deddendum_involute_angle)
        end_angle_lower = -angular_tooth_width * 2 - involute_function(deddendum_involute_angle)
    for i in range(num_points[3]):
        t = float(i) / (num_points[3] - 1)
        theta_arc = start_angle_lower + t * (end_angle_lower - start_angle_lower)
        x_arc = dedendum_radius * math.cos(theta_arc)
        y_arc = dedendum_radius * math.sin(theta_arc)
        lower_arc.append((x_arc, y_arc))
    return {
        'trochoid_1': trochoid_1,
        'involute_1': involute_1,
        'upper_arc': upper_arc,
        'involute_2': involute_2,
        'trochoid_2': trochoid_2,
        'lower_arc': lower_arc,
        'parameters': {
            'z': z,
            'm': m,
            'alpha_deg': alpha_deg,
            'profile_shift': profile_shift,
            'pitch_radius': pitch_radius,
            'base_radius': base_radius,
            'addendum_radius': addendum_radius,
            'dedendum_radius': dedendum_radius
        }
    }
def generate_internal_tooth_profile(z, m, alpha_deg, thickness, profile_shift=0.0, undercut_auto_suppress=False, num_points=[10,5,5,10]):
    """
    Generate the profile of one tooth consisting of 6 parts.
    Parameters:
    -----------
    z : int
        Number of teeth
    m : float
        Module (mm)
    alpha_deg : float
        Pressure angle in degrees
    thickness : float
        External thickness (mm)
    profile_shift : float
        Profile shifting value (default: 0.0)
    undercut_auto_suppress : bool
        Automatic undercut suppression (default: False)
    num_points : list of int
        Number of points per curve segment, order is following : [involute,addendum,deddundum,external] (default: [20, 20, 20, 20])
    Returns:
    --------
    dict containing the 6 profile parts:
        'involute_1': [(x1, y1), (x2, y2), ...] - First involute curve  
        'upper_arc': [(x1, y1), (x2, y2), ...] - Upper addendum arc
        'involute_2': [(x1, y1), (x2, y2), ...] - Second involute curve
        'lower_arc': [(x1, y1), (x2, y2), ...] - Lower dedendum arc
        'external_arc': [(x1, y1), (x2, y2), ...] - External arc
    """
    alpha = math.radians(alpha_deg)
    pitch_radius = m * z / 2.0
    base_radius = pitch_radius * math.cos(alpha)
    if undercut_auto_suppress:
        if base_radius > pitch_radius - m:
            profile_shift = base_radius - (pitch_radius - m)
    pitch_radius += profile_shift
    addendum_radius = pitch_radius - m
    dedendum_radius = max(pitch_radius + 1.25 * m, 0.01)
    if base_radius > pitch_radius:
        raise ValueError("Base radius is larger than pitch radius, resulting in invalid gear geometry.")
    else:
        offset_angle = math.acos(base_radius / pitch_radius)
    phi = involute_function(offset_angle)
    angular_tooth_width = math.pi / z
    dedendum_involute_angle = math.acos(base_radius / dedendum_radius)
    if base_radius < addendum_radius:
        addendum_involute_angle = math.acos(base_radius / addendum_radius)
    else : 
        addendum_involute_angle = 0
    max_involute_angle = dedendum_involute_angle + involute_function(dedendum_involute_angle)
    min_involute_angle = addendum_involute_angle + involute_function(addendum_involute_angle)
    tooth_angle = -angular_tooth_width - 2 * phi
    involute_1 = []
    involute_2 = []
    for i in range(num_points[0]):
        t = float(i) / (num_points[0] - 1)
        theta = t * (max_involute_angle - min_involute_angle) + min_involute_angle
        x_inv = base_radius * (math.cos(theta) + theta * math.sin(theta))
        y_inv = base_radius * (math.sin(theta) - theta * math.cos(theta))
        cos_tooth = math.cos(tooth_angle)
        sin_tooth = math.sin(tooth_angle)
        x1 = x_inv * cos_tooth - y_inv * sin_tooth
        y1 = x_inv * sin_tooth + y_inv * cos_tooth
        involute_2.append((x1, y1))
        involute_1.append((x_inv, -y_inv))
    upper_arc = []
    involute_at_dedendum = involute_function(dedendum_involute_angle)
    start_angle_upper = -involute_at_dedendum
    end_angle_upper = tooth_angle + involute_at_dedendum
    for i in range(num_points[1]):
        t = float(i) / (num_points[1] - 1)
        theta_arc = start_angle_upper + t * (end_angle_upper - start_angle_upper)
        x_arc = dedendum_radius * math.cos(theta_arc)
        y_arc = dedendum_radius * math.sin(theta_arc)
        upper_arc.append((x_arc, y_arc))
    lower_arc_1 = []
    lower_arc_2 = []
    start_angle_lower = tooth_angle + involute_function(addendum_involute_angle)
    end_angle_lower = -angular_tooth_width * 2 - involute_function(addendum_involute_angle)
    angular_width_lower = end_angle_lower - start_angle_lower
    half_num_points_lower = num_points[2]//2
    for i in range(half_num_points_lower):
        t = float(i) / (half_num_points_lower - 1)
        theta_arc = start_angle_lower + t * angular_width_lower/2
        x_arc = max(addendum_radius,base_radius) * math.cos(theta_arc)
        y_arc = max(addendum_radius,base_radius) * math.sin(theta_arc)
        lower_arc_1.append((x_arc, y_arc))
    for i in range(half_num_points_lower):
        t = float(i) / (half_num_points_lower - 1)
        theta_arc = -involute_function(addendum_involute_angle) - t * angular_width_lower/2
        x_arc = max(addendum_radius,base_radius) * math.cos(theta_arc)
        y_arc = max(addendum_radius,base_radius) * math.sin(theta_arc)
        lower_arc_2.append((x_arc, y_arc))
    external_arc = []
    start_angle_external = -involute_function(addendum_involute_angle)  - angular_width_lower/2
    end_angle_external = start_angle_lower + angular_width_lower/2
    for i in range(num_points[3]):
        t = i / (num_points[3] - 1)
        theta_arc = start_angle_external + t * (end_angle_external - start_angle_external)
        x_arc = (dedendum_radius+thickness) * math.cos(theta_arc)
        y_arc = (dedendum_radius+thickness) * math.sin(theta_arc)
        external_arc.append((x_arc, y_arc))
    return {
        'involute_1': involute_1,
        'upper_arc': upper_arc,
        'involute_2': involute_2,
        'lower_arc_1': lower_arc_1,
        'lower_arc_2': lower_arc_2,
        'external_arc': external_arc,
        'parameters': {
            'z': z,
            'm': m,
            'alpha_deg': alpha_deg,
            'profile_shift': profile_shift,
            'pitch_radius': pitch_radius,
            'base_radius': base_radius,
            'addendum_radius': addendum_radius,
            'dedendum_radius': dedendum_radius
        }
    }
def alibre_arc(sketch, arc, reverse = False):
    if reverse:
        start_pt = arc[0]
        end_pt = arc[-1]
    else:
        start_pt = arc[-1]
        end_pt = arc[0]
    center_x, center_y = 0.0, 0.0
    lower_arc = sketch.AddArcCenterStartEnd(center_x, center_y, start_pt[0], start_pt[1], end_pt[0], end_pt[1], False)
    print("  Created lower dedendum arc from (" + str(round(start_pt[0], 3)) + ", " + 
            str(round(start_pt[1], 3)) + ") to (" + str(round(end_pt[0], 3)) + ", " + 
            str(round(end_pt[1], 3)) + ")")
    return lower_arc
def alibre_spline(sketch, points):
    if len(points) > 0:
        spline_points = []
        for x, y in points:
            spline_points.append(x)
            spline_points.append(y)
        spline = sketch.AddBspline(spline_points, False)
    else: 
        spline = None
    return spline
def create_external_gear_in_alibre(z, m, alpha_deg, profile_shift=0.0,
                         undercut_auto_suppress=False,sketch=None):
    """
    Create a complete spur gear in Alibre CAD
    Parameters:
    -----------
    z : int - Number of teeth
    m : float - Module (mm)
    alpha_deg : float - Pressure angle (degrees)
    profile_shift : float - Profile shift coefficient
    undercut_auto_suppress : bool - Auto suppress undercut
    num_points : int - Points per curve (higher = smoother)
    Returns:
    --------
    Success status and created objects
    """
    try:
        print("Generating gear profile: z=" + str(z) + ", m=" + str(m) + ", alpha=" + str(alpha_deg) + "°")
        tooth_profile = generate_external_tooth_profile(
                z=z, m=m, alpha_deg=alpha_deg, 
                profile_shift=profile_shift,
                undercut_auto_suppress=undercut_auto_suppress
        )
        params = tooth_profile['parameters']
        print("Generated profile with pitch radius: " + str(round(params['pitch_radius'], 2)) + "mm")
        if len(tooth_profile['trochoid_1']) == 0:
            trochoid_start = tooth_profile['involute_1'][0]
        else:
            trochoid_start = tooth_profile['trochoid_1'][-1]
        center_to_trochoid = sketch.AddLine(0, 0, trochoid_start[0], trochoid_start[1], False)
        trochoid_1_spline = alibre_spline(sketch, tooth_profile['trochoid_1'])
        involute_1_spline = alibre_spline(sketch, tooth_profile['involute_1'])
        upper_arc = alibre_arc(sketch, tooth_profile['upper_arc'])
        involute_2_spline = alibre_spline(sketch, tooth_profile['involute_2'])
        trochoid_2_spline = alibre_spline(sketch, tooth_profile['trochoid_2'])
        lower_arc = alibre_arc(sketch, tooth_profile['lower_arc'])
        arc_end = tooth_profile['lower_arc'][-1]
        arc_to_center = sketch.AddLine(arc_end[0], arc_end[1], 0, 0, False)
        print("  Created return line from dedendum arc to center: (" + 
                str(round(arc_end[0], 3)) + ", " + str(round(arc_end[1], 3)) + ") -> (0,0)")
        print("Sketch completed successfully")
        return tooth_profile['parameters']
    except NameError as e:
        print("Error: Alibre API functions not available. This script must be run within Alibre CAD.")
        print("Make sure you have an active part open before running this script.")
        return False, None
    except Exception as e:
        print("Error creating gear: " + str(e))
        return False, None
def create_internal_gear_in_alibre(z, m, alpha_deg, profile_shift=0.0,
                            thickness=10.0,
                            undercut_auto_suppress=False,sketch=None):
    """
    Create a complete internal spur gear in Alibre CAD
    Parameters:
    - z : int - Number of teeth
    - m : float - Module (mm)
    - alpha_deg : float - Pressure angle (degrees)
    - profile_shift : float - Profile shift coefficient
    - thickness : float - External thickness (mm)
    - undercut_auto_suppress : bool - Auto suppress undercut
    - num_points : int - Points per curve (higher = smoother)
    """
    try:
        print("Generating gear profile: z=" + str(z) + ", m=" + str(m) + ", alpha=" + str(alpha_deg) + "°")
        tooth_profile = generate_internal_tooth_profile(
                z=z, m=m, alpha_deg=alpha_deg, 
                thickness=thickness,
                profile_shift=profile_shift,
                undercut_auto_suppress=undercut_auto_suppress
        )
        params = tooth_profile['parameters']
        print("Generated profile with pitch radius: " + str(round(params['pitch_radius'], 2)) + "mm")
        external_start = tooth_profile['external_arc'][-1]
        lower_arc_1_start = tooth_profile['lower_arc_1'][-1]
        involute_to_external = sketch.AddLine(lower_arc_1_start[0], lower_arc_1_start[1], external_start[0], external_start[1], False)
        external_arc = alibre_arc(sketch, tooth_profile['external_arc'])
        external_end = tooth_profile['external_arc'][0]
        lower_arc_2_end = tooth_profile['lower_arc_2'][-1]
        external_to_lower = sketch.AddLine(external_end[0], external_end[1], lower_arc_2_end[0], lower_arc_2_end[1], False)
        lower_arc_1 = alibre_arc(sketch, tooth_profile['lower_arc_1'])
        lower_arc_2 = alibre_arc(sketch, tooth_profile['lower_arc_2'],reverse=True)
        involute_2_spline = alibre_spline(sketch, tooth_profile['involute_2'])
        upper_arc = alibre_arc(sketch, tooth_profile['upper_arc'])
        involute_1_spline = alibre_spline(sketch, tooth_profile['involute_1'])
        print("Sketch completed successfully")
        return tooth_profile['parameters']
    except NameError as e:
        print("Error: Alibre API functions not available. This script must be run within Alibre CAD.")
        print("Make sure you have an active part open before running this script.")
        return False, None
    except Exception as e:
        print("Error creating gear: " + str(e))
        return False, None
def create_gear_with_plane(z, m, alpha_deg, plane, profile_shift=0.0, thickness=10.0, internal=False):
    """Create gear on specified plane - matches original code structure"""
    name = "gear1"
    sketch = MyPart.AddSketch(name, plane)
    if internal:
        parameters = create_internal_gear_in_alibre(
            z=z, m=m, alpha_deg=alpha_deg,
            profile_shift=profile_shift,
            thickness=thickness,
            undercut_auto_suppress=False,
            sketch=sketch
        )
    else:
        parameters = create_external_gear_in_alibre(
            z=z, m=m, alpha_deg=alpha_deg,
            profile_shift=profile_shift,
            undercut_auto_suppress=False,
            sketch=sketch
        )
    try:
        sketch_name = sketch.Name
        param_pitch_name = sketch_name + "_pitch_radius"
        param_teeth_name = sketch_name + "_z"
        try:
            p2 = MyPart.AddParameter(param_pitch_name, ParameterTypes.Distance, float(parameters['pitch_radius']))
        except:
            pass
        try:
            p1 = MyPart.AddParameter(param_teeth_name, ParameterTypes.Count, int(parameters['z']))
        except:
            pass
        MyPart.Regenerate()
    except Exception as param_ex:
        print("Warning: Could not add parameters: %s" % param_ex)
    return parameters
def get_professional_colors():
    return {
        'background': Color.FromArgb(250, 250, 250),
        'accent': Color.FromArgb(0, 122, 204),
        'accent_light': Color.FromArgb(230, 244, 255),
        'border': Color.FromArgb(204, 204, 204),
        'text': Color.FromArgb(64, 64, 64),
        'button_bg': Color.FromArgb(240, 240, 240)
    }
def scale_size(base_size, scale_factor=1.0):
    return int(base_size)
def create_professional_button(text, is_primary=False):
    colors = get_professional_colors()
    btn = Button()
    btn.Text = text
    btn.FlatStyle = FlatStyle.Flat
    btn.Font = Font(SystemFonts.DefaultFont.FontFamily, 9, FontStyle.Regular)
    btn.UseVisualStyleBackColor = False
    if is_primary:
        btn.BackColor = colors['accent']
        btn.ForeColor = Color.White
        btn.FlatAppearance.BorderColor = colors['accent']
    else:
        btn.BackColor = colors['button_bg']
        btn.ForeColor = colors['text']
        btn.FlatAppearance.BorderColor = colors['border']
    btn.FlatAppearance.BorderSize = 1
    btn.Cursor = Cursors.Hand
    return btn
def create_professional_label(text, is_header=False):
    colors = get_professional_colors()
    lbl = Label()
    lbl.Text = text
    lbl.ForeColor = colors['text']
    lbl.AutoSize = True
    lbl.TextAlign = System.Drawing.ContentAlignment.TopLeft
    lbl.Font = Font(SystemFonts.DefaultFont.FontFamily, 10 if is_header else 9,
                    FontStyle.Bold if is_header else FontStyle.Regular)
    return lbl
def create_professional_checkbox(text):
    colors = get_professional_colors()
    chk = CheckBox()
    chk.Text = text
    chk.ForeColor = colors['text']
    chk.Font = Font(SystemFonts.DefaultFont.FontFamily, 9)
    chk.UseVisualStyleBackColor = True
    chk.AutoSize = True
    chk.TextAlign = System.Drawing.ContentAlignment.MiddleLeft
    return chk
def create_professional_numericupdown():
    colors = get_professional_colors()
    num = NumericUpDown()
    num.BackColor = Color.White
    num.ForeColor = colors['text']
    num.Font = Font(SystemFonts.DefaultFont.FontFamily, scale_size(9))
    num.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle
    num.Margin = Padding(2)
    return num
def create_professional_radiobutton(text):
    colors = get_professional_colors()
    rb = RadioButton()
    rb.Text = text
    rb.AutoSize = True
    rb.Font = Font(SystemFonts.DefaultFont.FontFamily, 9)
    rb.ForeColor = colors['text']
    rb.Margin = Padding(0, 0, 16, 0)
    return rb
class SelectionListBox(ListBox):
    def __new__(cls):
        instance = ListBox.__new__(cls)
        try:
            instance.AutoScaleDimensions = SizeF(96, 96)
            instance.AutoScaleMode = AutoScaleMode.Dpi
            instance.IntegralHeight = 1
            instance.SelectionMode = SelectionMode.MultiExtended
            instance.BackColor = Color.White
            instance.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle
            instance.Font = Font(SystemFonts.DefaultFont.FontFamily, 9)
            import AlibreScript
            Root = AlibreScript.API.Global.Root
            instance.Root = Root
            instance.top_sess = instance.Root.TopmostSession
            instance.myTimer = Timer()
            instance.myTimer.Tick += instance.TimerEventProcessor
            instance.myTimer.Interval = 100
            instance.Enter += instance.onEnter_Selection
            instance.Leave += instance.onLeave_Selection
            instance.HandleDestroyed += instance.onHandleDestroyed
            instance.PreviousSelection = instance.Root.NewObjectCollector()
        except Exception as ex:
            show_error('Selection list init failed: %s' % ex, include_trace=True)
        return instance
    @safe_try
    def onEnter_Selection(self, sender, e):
        colors = get_professional_colors()
        sender.BackColor = colors['accent_light']
        sender.myTimer.Start()
    @safe_try
    def onLeave_Selection(self, sender, e):
        try:
            sender.myTimer.Stop()
        finally:
            sender.BackColor = Color.White
    @safe_try
    def onHandleDestroyed(self, sender, e):
        try:
            sender.myTimer.Stop()
        finally:
            pass
    @safe_try
    def TimerEventProcessor(self, sender, e):
        try:
            self.myTimer.Stop()
            if self.top_sess is None:
                return
            try:
                if self.PreviousSelection is None:
                    self.PreviousSelection = self.Root.NewObjectCollector()
            except:
                return
            NewSelections = getattr(self.top_sess, 'SelectedObjects', None)
            if NewSelections is None:
                return
            try:
                count = int(NewSelections.Count)
            except:
                return
            for a in range(0, count):
                item = NewSelections.Item(a)
                tgt = getattr(item, 'Target', None)
                tname = ''
                try:
                    tname = str(tgt.GetType().Name)
                except:
                    try:
                        tname = str(tgt.Type)
                    except:
                        tname = ''
                if tgt is not None and 'PLANE' in tname.upper():
                    try:
                        obj_name = str(tgt.Name)
                    except:
                        obj_name = str(getattr(item, 'DisplayName', 'Plane'))
                    if self.Items.Count == 0 or obj_name != self.Items[0]:
                        self.Items.Clear()
                        try:
                            self.PreviousSelection.Clear()
                        except:
                            try:
                                self.PreviousSelection = self.Root.NewObjectCollector()
                            except:
                                pass
                        self.Items.Add(obj_name)
                        try:
                            self.PreviousSelection.Add(item)
                        except:
                            pass
                    break
        finally:
            try:
                self.myTimer.Start()
            except:
                pass
def show_gear_form():
    if MyPart is None:
        show_error('No active Part session was found. Open a part and run the script again.', 'No Part Session')
        return None
    colors = get_professional_colors()
    form = Form()
    form.Text = 'Alibre Gear Generator Enhanced'
    form.AutoSize = False
    form.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen
    form.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedDialog
    form.MaximizeBox = False
    form.MinimizeBox = False
    form.ShowInTaskbar = False
    form.ShowIcon = False
    form.TopMost = True
    form.BackColor = colors['background']
    form.Font = Font(SystemFonts.DefaultFont.FontFamily, 9)
    form.Padding = Padding(12)
    main_panel = Panel()
    main_panel.Dock = DockStyle.Fill
    main_panel.BackColor = colors['background']
    main_panel.Padding = Padding(8)
    main_panel.AutoSize = True
    main_panel.AutoSizeMode = System.Windows.Forms.AutoSizeMode.GrowAndShrink
    form.Controls.Add(main_panel)
    table = TableLayoutPanel()
    table.ColumnCount = 1
    table.RowCount = 0
    table.Dock = DockStyle.Fill
    table.AutoSize = True
    table.AutoSizeMode = System.Windows.Forms.AutoSizeMode.GrowAndShrink
    table.Padding = Padding(0)
    table.Margin = Padding(0)
    table.ColumnStyles.Add(System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 100.0))
    main_panel.Controls.Add(table)
    control_spacing = 8
    section_spacing = 16
    def add_control_row(ctrl, extra_margin_bottom=None, fixed_height=None):
        table.RowCount += 1
        if fixed_height is not None:
            table.RowStyles.Add(System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, fixed_height))
            ctrl.Height = fixed_height
        else:
            table.RowStyles.Add(System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.AutoSize))
        mb = control_spacing if extra_margin_bottom is None else extra_margin_bottom
        ctrl.Margin = Padding(0, 0, 0, mb)
        ctrl.Dock = DockStyle.Fill
        table.Controls.Add(ctrl, 0, table.RowCount - 1)
    add_control_row(create_professional_label("py-gear", True), extra_margin_bottom=section_spacing)
    add_control_row(create_professional_label("Gear Parameters", True), extra_margin_bottom=6)
    add_control_row(create_professional_label("Number of Teeth:"))
    num_teeth = create_professional_numericupdown()
    num_teeth.Value = 20
    num_teeth.Minimum = 6
    num_teeth.Maximum = 200
    num_teeth.DecimalPlaces = 0
    num_teeth.Height = 28
    add_control_row(num_teeth)
    add_control_row(create_professional_label("Module (mm):"))
    num_module = create_professional_numericupdown()
    num_module.Value = 2.0
    num_module.Minimum = 0.1
    num_module.Maximum = 100.0
    num_module.DecimalPlaces = 2
    num_module.Height = 28
    add_control_row(num_module)
    add_control_row(create_professional_label("Pressure Angle (degrees):"))
    num_pressure = create_professional_numericupdown()
    num_pressure.Value = 20.0
    num_pressure.Minimum = 10.0
    num_pressure.Maximum = 30.0
    num_pressure.DecimalPlaces = 1
    num_pressure.Height = 28
    add_control_row(num_pressure)
    add_control_row(create_professional_label("Profile Shift (mm):"))
    num_profile_shift = create_professional_numericupdown()
    num_profile_shift.Value = 0.0
    num_profile_shift.Minimum = -10.0
    num_profile_shift.Maximum = 10.0
    num_profile_shift.DecimalPlaces = 2
    num_profile_shift.Height = 28
    add_control_row(num_profile_shift)
    add_control_row(create_professional_label("Thickness (mm) - for internal gears:"))
    num_thickness = create_professional_numericupdown()
    num_thickness.Value = 10.0
    num_thickness.Minimum = 1.0
    num_thickness.Maximum = 100.0
    num_thickness.DecimalPlaces = 2
    num_thickness.Height = 28
    add_control_row(num_thickness, extra_margin_bottom=section_spacing)
    add_control_row(create_professional_label("Gear Type", True), extra_margin_bottom=6)
    gear_type_flow = FlowLayoutPanel()
    gear_type_flow.FlowDirection = FlowDirection.LeftToRight
    gear_type_flow.WrapContents = True
    gear_type_flow.AutoSize = True
    rb_external = create_professional_radiobutton("External Gear")
    rb_internal = create_professional_radiobutton("Internal Gear")
    rb_external.Checked = True
    gear_type_flow.Controls.Add(rb_external)
    gear_type_flow.Controls.Add(rb_internal)
    add_control_row(gear_type_flow, extra_margin_bottom=section_spacing)
    add_control_row(create_professional_label("Plane Selection", True), extra_margin_bottom=6)
    add_control_row(create_professional_label("Select a plane where the gear will be created:"))
    sel_target = SelectionListBox()
    sel_target.IntegralHeight = False
    sel_target.Height = 90
    add_control_row(sel_target, fixed_height=90, extra_margin_bottom=section_spacing)
    chk_optimal = create_professional_checkbox("Optimal profile shift")
    add_control_row(chk_optimal)
    chk_stay_open = create_professional_checkbox("Stay open after creating")
    add_control_row(chk_stay_open, extra_margin_bottom=8)
    gear_counter = [1]
    def close_form_safely():
        try:
            if hasattr(sel_target, 'myTimer') and sel_target.myTimer is not None:
                sel_target.myTimer.Stop()
                sel_target.myTimer.Dispose()
        except:
            pass
        try:
            form.Close()
            form.Dispose()
        except:
            pass
    def reset_tool_state():
        """Clear selection only, preserve control values for next gear creation"""
        try:
            try:
                sel_target.Items.Clear()
            except:
                pass
            try:
                if getattr(sel_target, 'Root', None) is not None:
                    sel_target.PreviousSelection = sel_target.Root.NewObjectCollector()
                else:
                    sel_target.PreviousSelection = None
            except:
                sel_target.PreviousSelection = None
            try:
                sel_target.myTimer.Stop()
                sel_target.myTimer.Start()
            except:
                pass
            try:
                sel_target.Focus()
                form.Activate()
            except:
                pass
        except Exception as reset_ex:
            print('Reset warning: %s' % reset_ex)
    @safe_try
    def create_gear_click(sender, e):
        try:
            number_of_teeth = int(num_teeth.Value)
            module = float(num_module.Value)
            pressure_angle = float(num_pressure.Value)
            profile_shift = float(num_profile_shift.Value)
            thickness = float(num_thickness.Value)
            is_internal = rb_internal.Checked
            optimal_profile_shift = chk_optimal.Checked
            if sel_target.Items.Count == 0 or sel_target.PreviousSelection is None:
                show_info("Please select a plane", "Input Required")
                return
            selected_item = sel_target.PreviousSelection.Item(0)
            target = getattr(selected_item, 'Target', None)
            if target is None:
                show_error('Could not resolve the selected plane.', 'Selection Error')
                return
            target_type = str(target.GetType().Name).upper()
            if 'PLANE' not in target_type:
                show_error('Please select a valid plane. Selected type: %s' % target_type, 'Invalid Selection')
                return
            try:
                plane_name = str(target.Name)
                proper_plane = MyPart.GetPlane(plane_name)
            except Exception as plane_ex:
                show_error('Could not get plane object: %s' % plane_ex, 'Plane Access Error')
                return
            gear_type = "Internal" if is_internal else "External"
            unique_name = "Gear%d_%s_%dT_M%g" % (gear_counter[0], gear_type, number_of_teeth, module)
            try:
                original_create = create_gear_with_plane
                def create_gear_with_unique_name(z, m, alpha_deg, plane, profile_shift=0.0, thickness=10.0, internal=False):
                    """Create gear with unique name"""
                    sketch = MyPart.AddSketch(unique_name, plane)
                    if internal:
                        parameters = create_internal_gear_in_alibre(
                            z=z, m=m, alpha_deg=alpha_deg,
                            profile_shift=profile_shift,
                            thickness=thickness,
                            undercut_auto_suppress=optimal_profile_shift,
                            sketch=sketch
                        )
                    else:
                        parameters = create_external_gear_in_alibre(
                            z=z, m=m, alpha_deg=alpha_deg,
                            profile_shift=profile_shift,
                            undercut_auto_suppress=optimal_profile_shift,
                            sketch=sketch
                        )
                    try:
                        sketch_name = sketch.Name
                        param_pitch_name = sketch_name + "_pitch_radius"
                        param_teeth_name = sketch_name + "_z"
                        try:
                            p2 = MyPart.AddParameter(param_pitch_name, ParameterTypes.Distance, float(parameters['pitch_radius']))
                        except:
                            pass
                        try:
                            p1 = MyPart.AddParameter(param_teeth_name, ParameterTypes.Count, int(parameters['z']))
                        except:
                            pass
                        MyPart.Regenerate()
                    except Exception as param_ex:
                        print("Warning: Could not add parameters: %s" % param_ex)
                    return parameters
                result = create_gear_with_unique_name(
                    z=number_of_teeth,
                    m=module,
                    alpha_deg=pressure_angle,
                    plane=proper_plane,
                    profile_shift=profile_shift,
                    thickness=thickness,
                    internal=is_internal
                )
                gear_counter[0] += 1
                #show_info("Gear '%s' created successfully!" % unique_name, "Success")
                if not chk_stay_open.Checked:
                    close_form_safely()
                else:
                    reset_tool_state()
            except Exception as create_ex:
                show_error("Failed to create gear: %s" % create_ex, "Create Gear Error", include_trace=True)
        except Exception as ex:
            show_error("Failed to create gear: %s" % ex, "Create Gear Error", include_trace=True)
    def cancel_click(sender, e):
        close_form_safely()
    btn_create = create_professional_button("Create Gear", True)
    btn_create.Dock = DockStyle.Fill
    add_control_row(btn_create, extra_margin_bottom=8, fixed_height=50)
    btn_close = create_professional_button("Close", False)
    btn_close.Dock = DockStyle.Fill
    add_control_row(btn_close, extra_margin_bottom=0, fixed_height=40)
    btn_create.Click += create_gear_click
    btn_close.Click += safe_try(cancel_click)
    tooltip = ToolTip()
    tooltip.SetToolTip(sel_target, "Click here, then select a plane in the Alibre workspace")
    tooltip.SetToolTip(num_teeth, "Number of teeth on the gear (6-200)")
    tooltip.SetToolTip(num_module, "Module defines the tooth size")
    tooltip.SetToolTip(num_pressure, "Pressure angle affects tooth shape")
    tooltip.SetToolTip(num_profile_shift, "Profile shift for gear modifications")
    tooltip.SetToolTip(rb_external, "Standard external spur gear")
    tooltip.SetToolTip(rb_internal, "Internal ring gear")
    tooltip.SetToolTip(chk_optimal, "Automatically calculate optimal profile shift")
    tooltip.SetToolTip(chk_stay_open, "Leave this window open after creating the gear")
    table.PerformLayout()
    main_panel.PerformLayout()
    try:
        pref = table.PreferredSize
        total_hpad = form.Padding.Left + form.Padding.Right + main_panel.Padding.Left + main_panel.Padding.Right
        total_vpad = form.Padding.Top + form.Padding.Bottom + main_panel.Padding.Top + main_panel.Padding.Bottom
        min_width = 420
        width = max(min_width, pref.Width + total_hpad)
        height = pref.Height + total_vpad
        height = min(height, 2400)
        form.ClientSize = Size(int(width), int(height))
        form.MinimumSize = Size(min_width, 400)
    except Exception as ex:
        print('Form sizing warning: %s' % ex)
    try:
        form.Show()
    except Exception as ex:
        show_error('Failed to display form: %s' % ex, include_trace=True)
        return None
    return form
try:
    gear_form = show_gear_form()
except Exception as ex:
    show_error('Fatal error while creating the gear generator UI: %s' % ex, include_trace=True)