"""SNR Project Main Program.

Creates GUI and initializes case-specific functions.

Author: Jacqueline Williams
Version: August 2016
"""

import snr_gui as gui
import snr_calc as calc
import snr_plot as plt
import math

# To create executable:
# pyinstaller --noconfirm --log-level=ERROR filename.spec

ELEMENT_NAMES = {"H": "Hydrogen", "He": "Helium", "C": "Carbon", "O": "Oxygen", "Ne": "Neon", "N": "Nitrogen",
                 "Mg": "Magnesium", "Si": "Silicon", "Fe": "Iron", "S": "Sulphur"}
ELEMENT_ORDER = ["He", "C", "N", "O", "Ne", "Mg", "Si", "S", "Fe"]
MODEL_DICT = {"lk": "Fractional energy loss", "cf": "Standard", "tw": "Hot low-density media", "wl": "Cloudy ISM"}
ABUNDANCE = {"Solar": {"H": 12, "He": 10.93, "C": 8.52, "O": 8.83, "Ne": 8.08, "N": 7.92, "Mg": 7.58, "Si": 7.55,
                       "Fe": 7.50, "S": 7.33},
             "LMC": {"H": 12, "He": 10.94, "C": 8.04, "N": 7.14, "O": 8.35, "Ne": 7.61, "Na": 7.15, "Mg": 7.47,
                     "Si": 7.81, "S": 6.70, "Cl": 4.76, "Ar": 6.29, "Ca": 5.89, "Sc": 2.64, "Ti": 4.81, "V": 4.08,
                     "Cr": 5.47, "Mn": 5.21, "Fe": 7.23},
             "Ejecta": {"H": 12, "He": 14, "C": 16, "O": 18, "Ne": 16, "N": 16, "Mg": 16, "Si": 16, "Fe": 16, "S": 16},
             "CC": {"H": 12, "He": 11.22, "C": 9.25, "N": 8.62, "O": 9.69, "Ne": 8.92, "Mg": 8.30, "Si": 8.79,
                    "S": 8.54, "Fe": 8.55},
             "Type Ia": {"H": 12, "He": 11.40, "C": 12.60, "N": 7.50, "O": 12.91, "Ne": 11.04, "Mg": 11.55, "Si": 12.75,
                         "S": 12.43, "Fe": 13.12}
             }


def get_model_name(key, snr_em):
    """Get name of model to be shown on emissivity window.

    Args:
        key (str): short string representing model used, see MODEL_DICT keys for possible values and associated models
        snr_em (calc.SNREmissivity): supernova remnant emissivity class instance

    Returns:
        str: name of current emissivity model
    """

    name = MODEL_DICT[key]
    if name == "Standard":
        if snr_em.data["model"] == "chev":
            name = "Standard (s\u200a=\u200a{0:.0f}, n\u200a=\u200a{1})".format(SNR.data["s"], SNR.data["n"])
        else:
            name = "Standard (Sedov)"
    elif name == "Cloudy ISM":
        if SNR.data["t"] < SNR.calc["t_st"]:
            name = "Standard (s\u200a=\u200a{0:.0f}, n\u200a=\u200a{1})".format(SNR.data["s"], SNR.data["n"])
        else:
            name = "{0} (C/\u03C4\u200a=\u200a{1:.0f})".format(name, SNR.data["c_tau"])
    return name


def s_change(update=True):
    """Changes available input parameters when s is changed.

    Args:
        update (bool): true if SuperNovaRemnant instance needs to be updated (generally only False when run during
                       initialization to avoid running update_output multiple times unnecessarily)
    """

    if widgets["s"].value_var.get() == '0':
        # Remove unnecessary parameters m_w and v_w and change available n values
        widgets["m_w"].input.grid_remove()
        widgets["m_w"].label.grid_remove()
        widgets["v_w"].input.grid_remove()
        widgets["v_w"].label.grid_remove()
        widgets["model"].input["lk"].config(state="normal")
        widgets["model"].input["wl"].config(state="normal")
        if 0.1 * SNR.calc["t_c"] <= SNR.calc["t_pds"]:
            widgets["model"].input["tw"].config(state="normal")
        widgets["n"].input.config(values=(0, 2, 4, 6, 7, 8, 9, 10, 12, 14))
        if widgets["n"].get_value() == 1:
            # Reset n value if old value not available
            widgets["n"].value_var.set(0)
    else:
        # Restore previous values for input parameters m_w and v_w and reduce available n values
        widgets["m_w"].input.grid()
        widgets["m_w"].label.grid()
        widgets["v_w"].input.grid()
        widgets["v_w"].label.grid()
        widgets["model"].input["lk"].config(state="disabled")
        widgets["model"].input["tw"].config(state="disabled")
        widgets["model"].input["wl"].config(state="disabled")
        widgets["n"].input.config(values=(0, 1, 2, 7))
        if widgets["n"].get_value() not in (0, 1, 2, 7):
            # Reset n value if old value not available
            widgets["n"].value_var.set(0)
    if update:
        SNR.update_output()


def title_change():
    """Change plot y-label and replot when plot type is changed without updating and recomputing values."""

    plot_type = widgets["plot_type"].get_value()
    SNR.graph.update_title(plot_type)
    SNR.data["plot_type"] = plot_type
    SNR.update_plot(SNR.get_phases())


def enter_pressed(event):
    """Validate input and update output when user presses the enter key.

    Args:
        event: event object passed by tkInter <Return> event
    """

    if hasattr(event.widget, "validate"):
        event.widget.validate()
        # Check if widget is one of the axis limit spinboxes
        if event.widget is not widgets["xmin"].input and event.widget is not widgets["xmax"].input:
            event.widget.callback()
        else:
            # If widget is a spinbox, only update limits rather than running the full update function
            if event.widget is widgets["xmin"].input:
                widget = widgets["xmin"]
            else:
                widget = widgets["xmax"]
            increment_xlimits(widget, 0)


def limit_change():
    """Update plot when preset limits change without running the full update function."""

    SNR.data["range"] = SNR.widgets["range"].get_value()
    SNR.graph.display_plot(SNR.get_limits())


def increment_xlimits(widget, direction=0):
    """Update plot when custom limits change without running the full update function.

    Args:
        widget: widget object that had its value changed
        direction: 0 typed value, +1 for value increased with clicked arrow/arrow keys, -1 for value decreased with
                   clicked arrow/arrow keys
    """

    # Change dropdown value to read custom if not already set
    if SNR.data["range"] != "Custom":
        SNR.data["range"] = "Custom"
        SNR.widgets["range"].value_var.set("Custom")
    old_val = widget.get_value()
    try:
        # Update increment value to appropriate power of 10 or set the increment to 10 if the value is less than 10
        increment = max(10 ** (math.floor(math.log10(old_val))), 10)
        if old_val == increment and increment != 10 and direction == -1:
            # Decrease the increment if the value is being decreased by the user
            increment /= 10
    except ValueError:
        # If old_val = 0, set the increment to 10
        increment = 10
    widget.input.config(increment=increment)
    if direction != 0:
        # Manually change x-limit stored in SNR if arrows are used since widget value updates after this function runs
        maximum = widget.input.cget("to")
        new_val = old_val + direction * widget.input.cget("increment")
        if new_val % increment != 0 and not (round(old_val) == round(maximum) and direction == 1):
            # Change value to a multiple of the increment if the arrows or arrow keys were used to change the value
            # If statement prevents this from happening at the maximum value
            if direction == 1:
                new_val = math.floor(new_val/increment)*increment
            else:
                new_val = math.ceil(new_val/increment)*increment
            widget.value_var.set(new_val - direction * increment)
        if new_val > maximum:
            # Prevents spinbox from going over maximum allowed value
            new_val = maximum
        if not (old_val == 0 and direction == -1) and not (new_val == widgets["xmin"].get_value() or
                                                           new_val == widgets["xmax"].get_value()):
            # Update SNR stored value unless the value will be lower than the minimum value of 0
            SNR.data[widget.identifier] = new_val
            widget.previous = round(new_val)
    else:
        SNR.data[widget.identifier] = old_val
        widget.previous = round(old_val)
    # Redraw plot
    SNR.graph.display_plot(SNR.get_limits())


def model_change(update=True):
    """Update available input parameters when model type is changed and recalculate output.

    Args:
        update (bool): true if SuperNovaRemnant instance needs to be updated (generally only False when run during
                       initialization to avoid running update_output multiple times unnecessarily)
    """

    if widgets["model"].get_value() != "lk":
        widgets["t_lk"].input.grid_remove()
        widgets["t_lk"].label.grid_remove()
        widgets["gamma_0"].input.grid_remove()
        widgets["gamma_0"].label.grid_remove()
        widgets["eps"].input.grid_remove()
        widgets["eps"].label.grid_remove()
    else:
        widgets["t_lk"].input.validate()
        widgets["t_lk"].input.grid()
        widgets["t_lk"].label.grid()
        widgets["gamma_0"].input.grid()
        widgets["gamma_0"].label.grid()
        widgets["eps"].input.grid()
        widgets["eps"].label.grid()

    if widgets["model"].get_value() == "cf":
        widgets["s"].input.config(state="readonly")
    else:
        widgets["s"].input.config(state="disabled")

    if widgets["model"].get_value() == "tw":
        widgets["t_tw"].input.config(state="normal")
        widgets["t_tw"].revert_value()
        widgets["t_tw"].input.grid()
        widgets["t_tw"].label.grid()
    else:
        widgets["t_tw"].input.config(state="disabled")
        widgets["t_tw"].value_var.set("N/A")
        widgets["t_tw"].input.grid_remove()
        widgets["t_tw"].label.grid_remove()

    if widgets["model"].get_value() == "wl":
        widgets["c_tau"].input.grid()
        widgets["c_tau"].label.grid()
    else:
        widgets["c_tau"].input.grid_remove()
        widgets["c_tau"].label.grid_remove()

    if update:
        SNR.update_output()


def scale_change(widget):
    """Trigger change between linear and log scales on the plot axes.

    Args:
        widget: checkbox that triggered the function
    """

    if widget.identifier == "y_scale":
        if widget.get_value() == 1:
            SNR.graph.graph.set_yscale("log")
        else:
            SNR.graph.graph.set_yscale("linear")
            SNR.graph.graph.yaxis.set_major_formatter(SNR.graph.ticker)
    else:
        if widget.get_value() == 1:
            SNR.graph.graph.set_xscale("log")
        else:
            SNR.graph.graph.set_xscale("linear")
            SNR.graph.graph.xaxis.set_major_formatter(SNR.graph.ticker)
    SNR.graph.display_plot(SNR.get_limits())


def update_ratio():
    dropdown = widgets["T_ratio"]
    if dropdown.get_value() == "Default":
        dropdown.input.config(state="readonly")
        dropdown.input.config(values="Custom")
    else:
        dropdown.input.config(state="normal")
        dropdown.input.config(values="Default")
    SNR.update_output()



def abundance_window(abundance_dict, ab_type):
    """Create window to view and adjust element abundances.

    Args:
        abundance_dict (dict): dictionary with default/current element abundances
        ab_type (str): type of abundance window, "ejecta" or "ISM"
    """

    if ab_window_open[ab_type]:
        # Give focus to existing window rather than opening a second window
        ab_window_open[ab_type].root.focus()
    else:
        window = gui.ScrollWindow()
        ab_window_open[ab_type] = window
        window.root.focus()
        window.root.geometry("%dx%d+%d+%d" %(200, 290, APP.root.winfo_x(), APP.root.winfo_y()))
        frame = window.container
        gui.SectionTitle(frame, "Element", size=10)
        if window.os == "Linux":
            title = "log(X/H)+12"
        else:
            title = "log(X/H)\u200a+\a200a12"
        gui.SectionTitle(gui.LayoutFrame(frame, column=1, row=0), title, size=10)
        for element in ELEMENT_ORDER:
            entry = gui.InputEntry(frame, element, ELEMENT_NAMES[element], "{0:.2f}".format(abundance_dict[element]),
                                   condition=lambda value: 0 < value < 100, padding=(0, 0, 5, 0))
            entry.input.bind(
                "<Key>", lambda *args: gui.InputParam.instances[str(window.root)]["ab_type"].value_var.set("Custom"))
        button_frame = gui.LayoutFrame(frame, columnspan=2, padding=(0, 10))
        if ab_type == "ISM":
            types = ("LMC", "Solar")
            default_type = ism_ab_type
            #gui.InputDropdown(gui.LayoutFrame(button_frame, row=0, column=0, padding=(2, 1, 2, 0)), "ab_type", None,
            #                  ism_ab_type, lambda: reset_ab(str(window.root)), ("LMC", "Solar"), width=7)
        else:
            types = ("CC", "Type Ia")
            default_type = ej_ab_type
            #gui.SubmitButton(gui.LayoutFrame(button_frame, row=0, column=0), "Reset",
            #                 lambda: reset_ab(str(window.root), ab_type))
        gui.InputDropdown(gui.LayoutFrame(button_frame, row=0, column=0, padding=(2, 1, 2, 0)), "ab_type", None,
                          default_type, lambda: reset_ab(str(window.root)), types, width=7)
        gui.SubmitButton(gui.LayoutFrame(button_frame, row=0, column=1), "Submit",
                         lambda: ab_window_close(window.root, abundance_dict, ab_type))
        window.root.bind("<1>", lambda event: event.widget.focus_set())
        window.root.bind("<Return>", lambda event: ab_window_close(window.root, abundance_dict, ab_type, event))
        window.root.protocol("WM_DELETE_WINDOW", lambda: ab_window_close(window.root, abundance_dict, ab_type))
        window.root.update()
        window.canvas.config(scrollregion=(0, 0, window.container.winfo_reqwidth(), window.container.winfo_reqheight()))


def reset_ab(root_id):
    """Reset abundance window to defaults.

    Args:
        root_id (str): id of abundance window, used to access input widgets
    """

    elements = gui.InputParam.instances[root_id].copy()
    ab_default = elements.pop("ab_type").get_value()
    for element, widget in elements.items():
        widget.value_var.set("{0:.2f}".format(ABUNDANCE[ab_default][element]))


def ab_window_close(root, ab_dict, ab_type, event=None):
    """Close abundance window and update abundance related variables.

    Args:
        root: tkInter TopLevel window instance for abundance window to be closed
        ab_dict (dict): dictionary of abundance values
        ab_type (str): type of abundance window, either "ejecta" or "ISM"
        event: event returned by tkInter if window was closed using the enter key
    """

    global ism_ab_type, ej_ab_type
    if event and hasattr(event.widget, "validate"):
        event.widget.validate()
    ab_window_open[ab_type] = False
    ab_dict.update(gui.InputParam.get_values(str(root)))
    # Store current ejecta type from dropdown
    if ab_type == "ISM":
        ism_ab_type = ab_dict.pop("ab_type")
    else:
        ej_ab_type = ab_dict.pop("ab_type")
    root.destroy()
    SNR.update_output()


def emissivity_window():
    """Create window to display emissivity data for an SNR with input parameters from the main window."""

    window = gui.ScrollWindow()
    window.root.focus()
    if window.os == "Linux":
        window.root.config(cursor="watch")
    else:
        window.root.config(cursor="wait")
    window.root.geometry("%dx%d+%d+%d" %(880, 650, (ws-880)/2, (hs-700)/2))
    window.root.update()
    window.canvas.grid_remove()
    left_frame = gui.LayoutFrame(window.container, 5)
    right_frame = gui.LayoutFrame(window.container, 5, column=1, row=0)
    root_id = str(window.root)
    SNR_EM = calc.SNREmissivity(SNR, root_id)
    gui.InputParam.instances[root_id] = {}
    widgets = gui.InputParam.instances[root_id]
    gui.SectionTitle(right_frame, "Output Plots:")
    energy_frame = gui.LayoutFrame(right_frame, 0, columnspan=2)
    gui.InputEntry(energy_frame, "energy", "Energy for specific intensity plot (keV):", 1,
                   SNR_EM.update_specific_intensity, gt_zero)
    SNR_EM.plots["Inu"] = plt.OutputPlot(gui.LayoutFrame(right_frame, (0, 5)), (5, 2.6),
                                         "Normalized impact parameter",
                                         "Specific intensity/\nerg cm$^{-2}$ s$^{-1}$ Hz$^{-1}$ sr$^{-1}$")
    range_frame = gui.LayoutFrame(right_frame, (0, 5, 0, 0), columnspan=4)
    gui.InputParam(gui.LayoutFrame(range_frame), None, "Energy range (keV):", None)
    gui.InputEntry(gui.LayoutFrame(range_frame, row=0, column=1), "emin", "", 0.3, SNR_EM.update_luminosity_spectrum,
                   lambda value: 0 < value < widgets["emax"].get_value(), padding=(0, 5))
    #gui.Text(gui.LayoutFrame(range_frame, row=0, column=2), "to", padding=(4, 5, 0, 0))
    gui.InputEntry(gui.LayoutFrame(range_frame, row=0, column=3), "emax", "to", 8, SNR_EM.update_luminosity_spectrum,
                   lambda value: value > widgets["emin"].get_value(), padding=(5, 5))
    SNR_EM.plots["Lnu"] = plt.OutputPlot(gui.LayoutFrame(right_frame), (5, 2.6), "Energy/keV",
                                         "Luminosity/\nerg s$^{-1}$ Hz$^{-1}$")
    gui.SectionTitle(left_frame, "SNR Properties:")
    gui.DisplayValue(left_frame, "Age", "yr", SNR.data["t"])
    gui.DisplayValue(left_frame, "Radius", "pc", SNR.calc["r"])
    gui.InputParam(left_frame, label="Model type:  \u200a{}".format(get_model_name(SNR.data["model"], SNR_EM)),
                   padding=(5, 2))
    if SNR_EM.data["model"] == "chev":
        gui.OutputValue(left_frame, "em", "Emission measure:", "cm\u207B\u00B3", 3, padding=(5, 1, 5, 0))
        em_frame = gui.LayoutFrame(left_frame, columnspan=2)
        gui.OutputValue(gui.LayoutFrame(em_frame, column=0, row=0), "em_f", "(Forward:", "cm\u207B\u00B3,", 3,
                        padding=(5, 0, 0, 0), font="-size 9")
        gui.OutputValue(gui.LayoutFrame(em_frame, column=1, row=0), "em_r", "reverse:", "cm\u207B\u00B3)", 3,
                        padding=(5, 0, 0, 0), font="-size 9")
        gui.OutputValue(left_frame, "Tem", "Emission weighted temperature:", "K", 3, padding=(5, 1, 5, 0))
        Tem_frame = gui.LayoutFrame(left_frame, columnspan=2)
        gui.OutputValue(gui.LayoutFrame(Tem_frame, column=0, row=0), "Tem_f", "(Forward:", "K,", 3, padding=(5, 0, 0, 0),
                        font="-size 9")
        gui.OutputValue(gui.LayoutFrame(Tem_frame, column=1, row=0), "Tem_r", "reverse:", "K)", 3,
                        padding=(5, 0, 0, 0), font="-size 9")
    else:
        gui.OutputValue(left_frame, "em", "Emission measure:", "cm\u207B\u00B3", 3)
        gui.OutputValue(left_frame, "Tem", "Emission weighted temperature:", "K", 3)
    gui.SectionTitle(left_frame, "Radial Profiles:", padding=(0, 10, 0, 0))
    SNR_EM.plots["temp"] = plt.OutputPlot(gui.LayoutFrame(left_frame, (0, 5, 0, 10), columnspan=5), (4.5, 2.3),
                                          "Normalized radius", "Temperature/K")
    SNR_EM.plots["density"] = plt.OutputPlot(gui.LayoutFrame(left_frame, 0, columnspan=5), (4.5, 2.3),
                                             "Normalized radius", "Density/g cm$^{-3}$",
                                             sharex=SNR_EM.plots["temp"].graph)
    if SNR_EM.data["model"] == "chev":
        gui.OutputValue(right_frame, "lum", "Luminosity over energy range:", "erg s\u207B\u00B9", 3,
                        padding=(5, 5, 5, 0))
        lum_frame = gui.LayoutFrame(right_frame, columnspan=2)
        gui.OutputValue(gui.LayoutFrame(lum_frame, column=0, row=0), "lum_f", "(Forward:", "erg s\u207B\u00B9,", 3,
                        padding=(5, 0, 0, 0), font="-size 9")
        gui.OutputValue(gui.LayoutFrame(lum_frame, column=1, row=0), "lum_r", "reverse:", "erg s\u207B\u00B9)", 3,
                        padding=(5, 0, 0, 0), font="-size 9")
    else:
        gui.OutputValue(right_frame, "lum", "Luminosity over energy range:", "erg s\u207B\u00B9", 3, padding=(5, 5))
    SNR_EM.plots["Lnu"].properties = {"function": SNR_EM.luminosity_spectrum, "color": "g"}
    SNR_EM.plots["Inu"].properties = {"function": SNR_EM.specific_intensity, "color": "m"}
    SNR_EM.plots["temp"].properties = {"function": lambda x: SNR_EM.vector_temperature(x) * SNR_EM.data["T_s"], "color": "b"}
    SNR_EM.plots["density"].properties = {"function": lambda x: SNR_EM.vector_density(x) * 4 * SNR_EM.data["n_0"] *
                                                                SNR_EM.data["mu_H"] * calc.M_H, "color": "r"}
    #print(timeit.timeit(SNR_EM.update_output, number=1))
    #profile.runctx("SNR_EM.update_output()", None, locals())
    SNR_EM.update_output()
    window.canvas.grid()
    window.root.bind("<1>", lambda event: event.widget.focus_set())
    window.root.bind("<Return>", enter_pressed)
    window.root.update()
    window.root.config(cursor="")
    window.canvas.config(scrollregion=(0, 0, window.container.winfo_reqwidth(), window.container.winfo_reqheight()))


def gt_zero(value):
    """Checks if value is positive and non-zero."""

    return value > 0

if __name__ == '__main__':
    ab_window_open = {"ISM": False, "Ejecta": False}
    # Set initial ISM abundance type
    ism_ab_type = "LMC"
    ej_ab_type = "Type Ia"
    APP = gui.ScrollWindow("root")
    root_id = "." + APP.container.winfo_parent().split(".")[1]
    gui.InputParam.instances[root_id] = {}
    widgets = gui.InputParam.instances[root_id]
    SNR = calc.SuperNovaRemnant(root_id)
    SNR.data["abundance"] = ABUNDANCE[ism_ab_type].copy()
    SNR.data["ej_abundance"] = ABUNDANCE[ej_ab_type].copy()
    APP.root.wm_title("SNR Modelling Program")
    if APP.os == "Windows":
        ICON = "Crab_Nebula.ico"
        # Uncomment line before using pyinstaller in --onefile mode
        #ICON = sys._MEIPASS+"/Crab_Nebula.ico"
        APP.root.tk.call("wm", "iconbitmap", APP.root._w, "-default", ICON)
    ws = APP.root.winfo_screenwidth()
    hs = APP.root.winfo_screenheight()
    if APP.os == "Linux":
        width = 1000
    else:
        width = 880
    APP.root.geometry("%dx%d+%d+%d" %(width, 650, (ws-width)/2, (hs-700)/2))
    APP.root.bind("<1>", lambda event: event.widget.focus_set())
    APP.input = gui.LayoutFrame(APP.container, 2, row=0, column=0)
    gui.SectionTitle(APP.input, "Input parameters:", 2)
    # Note time isn't restricted to less than t_mrg - this is accounted for in snr_calc.py
    # If time was restricted, users could become confused due to rounding of displayed t_mrg
    gui.InputEntry(APP.input, "t", "Age (yr):", 100, SNR.update_output, gt_zero)
    gui.InputEntry(APP.input, "e_51", "Energy (x 10\u2075\u00B9 erg):", 1.0, SNR.update_output, gt_zero)
    gui.InputEntry(APP.input, "temp_ism", "ISM Temperature (K):", 100, SNR.update_output, gt_zero)
    gui.InputEntry(APP.input, "m_ej", "Ejected mass (Msun):", 1.4, SNR.update_output, gt_zero)
    gui.InputDropdown(APP.input, "n", "Ejecta power-law index, n:", 0, SNR.update_output,
                      (0, 2, 4, 6, 7, 8, 9, 10, 12, 14))
    gui.InputDropdown(APP.input, "s", "Ambient media power-law index, s:", 0, s_change, (0, 2), state="disabled")
    gui.InputEntry(APP.input, "n_0", "ISM number density (cm\u207B\u00B3):", 2.0, SNR.update_output, gt_zero)
    if APP.os == "Linux":
        ratio_label = "Electron to ion temperature ratio Te/Ti:"
    else:
        ratio_label = "Electron to ion temperature ratio T\u2091\u200a/\u200aT\u1d62\u200a:"
    gui.InputDropdown(APP.input, "T_ratio", ratio_label, "Default", update_ratio, "Custom")
    gui.InputEntry(APP.input, "zeta_m", "Cooling adjustment factor:", 1.0, SNR.update_output, gt_zero)
    gui.InputEntry(APP.input, "sigma_v", "ISM turbulence/random speed (km/s):", 7.0, SNR.update_output)
    gui.InputEntry(APP.input, "m_w", "Stellar wind mass loss (Msun/yr):", 1e-7, SNR.update_output, gt_zero)
    gui.InputEntry(APP.input, "v_w", "Wind speed (km/s):", 30, SNR.update_output, gt_zero)
    gui.SubmitButton(APP.input, "Change ISM Abundances", lambda: abundance_window(SNR.data["abundance"], "ISM"),
                     sticky="w", padx=5, pady=(0, 5))
    SNR.buttons["ej_ab"] = gui.SubmitButton(
        APP.input, "Change Ejecta Abundances", lambda: abundance_window(SNR.data["ej_abundance"], "Ejecta"), sticky="w",
        padx=5)
    gui.InputParam(APP.input, label="Model type:")
    MODEL_FRAME = gui.LayoutFrame(APP.input, 0, row=100, column=0, columnspan=2)
    gui.InputRadio(MODEL_FRAME, "model", None, "cf", lambda *args: model_change(),
                   (("cf", "Standard"), ("lk", "Fractional energy loss"), ("tw", "Hot low-density media", "\n"),
                    ("wl", "Cloudy ISM")), padding=(10, 0, 0, 0))
    gui.InputEntry(APP.input, "gamma_0", "Adiabatic index, 1.1 \u2264 \u03B3 \u2264 5/3:", 1.667, SNR.update_output,
                   lambda value: 1.1 <= value <= 5.0 / 3.0)
    gui.InputEntry(APP.input, "eps", "Fractional energy loss, 0 < \u03B5 \u2264 1:", 0.7, SNR.update_output,
                   lambda value: 0 < value <= 1)
    gui.InputDropdown(APP.input, "c_tau", "C/\u03C4", 2, SNR.update_output, (1, 2, 4))
    gui.InputEntry(APP.input, "t_lk", "Fractional energy loss model start\ntime, within ST or PDS phase (yr):", 5000,
                   SNR.update_output, lambda value: (SNR.calc["t_st"] <= value or SNR.calc["t_st"] > SNR.calc["t_pds"])
                                                     and value <= min(SNR.calc["t_mrg"]["PDS"], SNR.calc["t_mcs"]))
    gui.InputEntry(APP.input, "t_tw", "Hot low-density media\nmodel end time (yr):", "4e5", SNR.update_output,
                   lambda value: SNR.calc["t_c"]*0.1 <= value < 1e9)
    SNR.buttons["em"] = gui.SubmitButton(APP.input, "Emissivity", emissivity_window, pady=10)
    APP.plot_frame = gui.LayoutFrame(APP.container, (10, 0), row=0, column=1)
    gui.SectionTitle(APP.plot_frame, "Output:")
    APP.plot_controls = gui.LayoutFrame(APP.plot_frame, 0)
    gui.InputRadio(gui.LayoutFrame(APP.plot_controls, 0), "plot_type", "Plot Type:", "r", lambda *args: title_change(),
                   (("r", "Radius"), ("v", "Velocity")), padding=(10, 0, 0, 0))
    gui.CheckboxGroup(
        gui.LayoutFrame(APP.plot_controls, (80, 0, 0, 0), row=widgets["plot_type"].label.grid_info()["row"], column=1),
        "Log scale:", scale_change, (("x_scale", "x-axis", "0"), ("y_scale", "y-axis", "0")), padding=(10, 0, 0, 0))
    plot_container = gui.LayoutFrame(APP.plot_frame, 0)
    SNR.graph = plt.TimePlot(plot_container, (6.4, 4.4))
    AXIS_FRAME = gui.LayoutFrame(APP.plot_frame, (0, 5), column=0)
    gui.InputDropdown(gui.LayoutFrame(AXIS_FRAME, (0, 0, 15, 0), row=0, column=0), "range", "Plotted Time:", "Current",
                      limit_change, ("Current", "Reverse Shock Lifetime", "ED-ST", "PDS", "MCS"), width=19,
                      font="-size 9")
    gui.InputSpinbox(gui.LayoutFrame(AXIS_FRAME, 0, row=0, column=1), "xmin", "Min:", "0", increment_xlimits,
                     lambda value: value != widgets["xmax"].get_value(), increment=10, from_=0, to=100000000, width=8)
    gui.InputSpinbox(gui.LayoutFrame(AXIS_FRAME, 0, row=0, column=2), "xmax", "Max:", "900", increment_xlimits,
                     lambda value: value != widgets["xmin"].get_value(), increment=100, from_=0, to=100000000, width=8)
    APP.output = gui.LayoutFrame(APP.plot_frame, (0, 10), column=0, columnspan=2)
    APP.output_values = gui.LayoutFrame(APP.output, 0, row=0, column=0)
    APP.output_times = gui.LayoutFrame(APP.output, (20, 0, 0, 0), row=0, column=1)
    gui.SectionTitle(APP.output_values, "Values at specified time:", 4, 11)
    gui.SectionTitle(APP.output_times, "Phase transition times:", 4, 11)
    gui.OutputValue(APP.output_values, "T", "Blast-wave shock electron temperature:", "K")
    gui.OutputValue(APP.output_values, "Tr", "Reverse shock electron temperature:", "K")
    gui.OutputValue(APP.output_values, "r", "Blast-wave shock radius:", "pc")
    gui.OutputValue(APP.output_values, "rr", "Reverse shock radius:", "pc")
    gui.OutputValue(APP.output_values, "v", "Blast-wave shock velocity:", "km/s")
    gui.OutputValue(APP.output_values, "vr", "Reverse shock velocity:", "km/s")
    gui.OutputValue(APP.output_times, "t-ST", "", "yr")
    gui.OutputValue(APP.output_times, "t-WL", "", "yr")
    gui.OutputValue(APP.output_times, "t-PDS", "", "yr")
    gui.OutputValue(APP.output_times, "t-MCS", "", "yr")
    gui.OutputValue(APP.output_times, "t-TW", "", "yr")
    gui.OutputValue(APP.output_times, "t-LK", "", "yr")
    gui.OutputValue(APP.output_times, "t-MRG", "", "yr")
    gui.OutputValue(APP.output_times, "t-s2", "", "", padding=0)

    APP.root.bind("<Return>", enter_pressed)
    SNR.update_output()
    model_change(False)
    s_change(False)
    APP.root.update()
    widgets["t_lk"].value_var.set(round(SNR.calc["t_pds"]))
    APP.canvas.config(scrollregion=(0, 0, APP.container.winfo_reqwidth(), APP.container.winfo_reqheight()))
    APP.root.mainloop()
