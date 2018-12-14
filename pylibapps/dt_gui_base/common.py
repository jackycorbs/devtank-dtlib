from dt_db_base import get_test_doc, get_args_in_src, get_float_prop_digits

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


def get_pass_fail_icon_name(passfail):
    return "dialog-ok" if passfail else "dialog-error"


def _update_desc(prop):
    widget_dict = prop["widget_dict"]
    prop["desc"] = widget_dict["desc"].get_text()


def _update_type(context, prop):
    widget_dict = prop["widget_dict"]
    drop_type = widget_dict["type"]
    drop_type_model = drop_type.get_model()
    index = drop_type.get_active()
    old_type = prop['type']
    new_type = drop_type_model[index][0]
    prop['type'] = new_type
    if new_type != old_type:
        if (old_type == "int" or old_type == "float") and \
           new_type != "int" and new_type != "float":
               for key in ["min", "max", "step", "digits"]:
                   prop.pop(key, None)
                   widget_dict.pop(key, None)
        elif new_type == "int" or new_type == "float":
            prop["min"] = eval(new_type)(_min_min(0))
            prop["max"] = eval(new_type)(_max_max(0))
            prop["step"] = 1

    for key in ["has_default", "default"]:
       widget_dict.pop(key, None)
    _set_property_type_gui(context, prop)
    type_box = widget_dict["type_box"]
    type_box.show_all()


def _update_digits(prop):
    widget_dict = prop["widget_dict"]
    digits_spin = widget_dict["digits"]
    digits = digits_spin.get_value()
    step = 1.0 / pow(10, digits)
    for key in ["step", "max", "min", "default"]:
        spin = widget_dict[key]
        spin.set_digits(digits)
        adjust = spin.get_adjustment()
        adjust.set_step_increment(step)

    default_widget = widget_dict["default"]
    min_spin       = widget_dict["min"]
    max_spin       = widget_dict["max"]
    step_spin      = widget_dict["step"]

    adjust = default_widget.get_adjustment()
    adjust.set_lower(min_spin.get_value())
    adjust.set_upper(max_spin.get_value())
    adjust.set_step_increment(step_spin.get_value())


def _min_min(min_value):
    return min(-10000, abs(min_value) * -10000)


def _max_max(max_value):
    return max(10000, max_value * 10000)


def _update_min(prop):
    widget_dict = prop["widget_dict"]
    min_spin = widget_dict["min"]
    prop_type = eval(prop['type'])
    min_value = min_spin.get_value_as_int() if prop_type is int else min_spin.get_value()
    prop['min'] = min_value
    adjust = min_spin.get_adjustment()
    adjust.set_lower(_min_min(min_value))
    for key in ["max", "default"]:
        spin = widget_dict[key]
        adjust = spin.get_adjustment()
        adjust.set_lower(min_value)


def _update_max(prop):
    widget_dict = prop["widget_dict"]
    max_spin = widget_dict["max"]
    prop_type = eval(prop['type'])
    max_value = max_spin.get_value_as_int() if prop_type is int else max_spin.get_value()
    prop['max'] = max_value
    adjust = max_spin.get_adjustment()
    adjust.set_upper(_max_max(max_value))
    for key in ["min", "default"]:
        spin = widget_dict[key]
        adjust = spin.get_adjustment()
        adjust.set_upper(max_value)


def _update_step(prop):
    widget_dict = prop["widget_dict"]
    step_spin = widget_dict["step"]
    digits_spin = widget_dict["digits"]
    digits = digits_spin.get_value()
    prop_type = eval(prop['type'])
    step_value = step_spin.get_value_as_int() if prop_type is int else step_spin.get_value()
    prop['step'] = step_value
    adjust = step_spin.get_adjustment()
    adjust.set_lower(_min_min(prop['step']))
    adjust.set_upper(_max_max(prop['step']))

    default_widget = widget_dict["default"]
    adjust = default_widget.get_adjustment()
    adjust.set_step_increment(step_value)


def _update_has_default(prop):
    widget_dict = prop["widget_dict"]
    has_default = widget_dict.get("has_default", False)
    has_default = has_default.get_active()
    default_widget = widget_dict["default"]
    if isinstance(default_widget, tuple):
        for widget in default_widget:
            widget.set_sensitive(has_default)
    else:
        default_widget.set_sensitive(has_default)
    if not has_default:
        prop.pop("default", None)


def update_default(prop):
    widget_dict = prop.get("widget_dict", None)
    if not widget_dict:
        return
    has_default = widget_dict.get("has_default", None)
    if has_default and not has_default.get_active():
        prop.pop("default", None)
        return
    default_widget = widget_dict["default"]
    type_name = prop["type"]
    if type_name == "int":
        prop["default"] = default_widget.get_value_as_int()
    elif type_name  == "float":
        prop["default"] = default_widget.get_value()
    elif type_name == "text":
        prop["default"] = default_widget.get_text()
    elif type_name == "bool":
        prop["default"] = default_widget.get_active()
    elif type_name == "file":
        files_drop, new_file_btn = default_widget
        index = files_drop.get_active()
        if index >= 0:
            file_id = files_drop.get_model()[index][1]
            prop["default"] = (file, None, file_id)
        else:
            filename = new_file_btn.get_filename()
            if filename and len(filename):
                prop["default"] = (file, filename, None)
            else:
                prop.pop("default", None)


def _update_resource_file(prop):
    widget_dict = prop["widget_dict"]
    files_drop, new_file_btn = widget_dict["default"]
    index = files_drop.get_active()
    if index >= 0:
        new_file_btn.unselect_all()
        update_default(prop)


def _update_local_file(prop):
    widget_dict = prop["widget_dict"]
    files_drop, new_file_btn = widget_dict["default"]
    filename = new_file_btn.get_filename()
    if len(filename):
        files_drop.set_active(-1)
        update_default(prop)


_types = ["file", "int", "float", "bool", "text"]


def _set_property_type_gui(context, prop):
    widget_dict = prop["widget_dict"]
    all_files = widget_dict["all_files"]
    type_box = widget_dict["type_box"]
    val_type_name = prop['type']

    old_widgets = type_box.get_children()
    for child in old_widgets:
        type_box.remove(child)

    prop_has_default = 'default' in prop and prop['default'] is not None

    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    type_box.add(box)

    has_default = Gtk.CheckButton(label="Default")
    has_default.set_active(prop_has_default)
    box.add(has_default)
    has_default.connect("toggled", lambda x: _update_has_default(prop))
    widget_dict["has_default"] = has_default

    if val_type_name == "float" or val_type_name == "int":

        places = get_float_prop_digits(prop) if val_type_name == "float" else 0

        step = prop['step']
        if not step:
            step = (1.0 / pow(10, places)) if val_type_name == "float" else 1

        if step < 1 and val_type_name == "int":
            step = 1

        prop['step'] = step

        adjust = Gtk.Adjustment(lower=prop['min'],
                                upper=prop['max'],
                                step_incr=step)
        spin = Gtk.SpinButton(digits=places, adjustment=adjust)
        if prop_has_default:
            spin.set_value(prop['default'])
        spin.set_sensitive(prop_has_default)
        box.add(spin)
        adjust.connect("value-changed", lambda x: update_default(prop))
        widget_dict["default"] = spin

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        type_box.add(box)

        if val_type_name == "float":
            adjust = Gtk.Adjustment(value=places, upper=1000, step_incr=1)
            spin = Gtk.SpinButton(adjustment=adjust)
            box.add(Gtk.Label('digits'))
            box.add(spin)
            adjust.connect("value-changed", lambda x: _update_digits(prop))
            widget_dict["digits"] = spin

        adjust = Gtk.Adjustment(value=prop['min'],
                                lower=_min_min(prop['min']),
                                upper=_max_max(prop['max']),
                                step_incr=step)
        spin = Gtk.SpinButton(digits=places, adjustment=adjust)
        box.add(Gtk.Label('Min'))
        box.add(spin)
        adjust.connect("value-changed", lambda x: _update_min(prop))
        widget_dict["min"] = spin

        adjust = Gtk.Adjustment(value=prop['max'],
                                lower=_min_min(prop['min']),
                                upper=_max_max(prop['max']),
                                step_incr=step)
        spin = Gtk.SpinButton(digits=places, adjustment=adjust)
        box.add(Gtk.Label('Max'))
        box.add(spin)
        adjust.connect("value-changed", lambda x: _update_max(prop))
        widget_dict["max"] = spin

        if places:
            lowests = 1.0 / pow(10, places)
            adjust = Gtk.Adjustment(value=step,
                                    lower=lowests,
                                    upper=lowests * 10000,
                                    step_incr=lowests)
        else:
            adjust = Gtk.Adjustment(value=step,
                                    lower=1,
                                    upper=step * 10000,
                                    step_incr=1)
        spin = Gtk.SpinButton(digits=places, adjustment=adjust)
        spin.set_value(step)
        box.add(Gtk.Label('Step'))
        box.add(spin)
        adjust.connect("value-changed", lambda x: _update_step(prop))
        widget_dict["step"] = spin

    elif val_type_name == "text":
        entry = Gtk.Entry()
        if prop_has_default:
            entry.set_text(prop['default'])
        entry.set_sensitive(prop_has_default)
        box.add(entry)
        entry.connect("activate", lambda x: update_default(prop))
        widget_dict["default"] = entry
    elif val_type_name == "bool":
        default_onoff = Gtk.CheckButton("True/False")
        if prop_has_default:
            default_onoff.set_active(prop['default'])
        default_onoff.set_sensitive(prop_has_default)
        box.add(default_onoff)
        default_onoff.connect("toggled", lambda x: update_default(prop))
        widget_dict["default"] = default_onoff
    elif val_type_name == "file":
        files_store = Gtk.ListStore(str, int)
        files_drop = Gtk.ComboBox()
        files_drop.set_model(files_store)
        cell = Gtk.CellRendererText()
        files_drop.pack_start(cell, True)
        files_drop.add_attribute(cell, "text", 0)
        all_file_ids = all_files.keys()
        for file_id in all_file_ids:
            filename = all_files[file_id]
            key = "%i:%s" % (file_id, filename)
            files_store.append([key, file_id])

        box.add(files_drop)
        new_file_btn = Gtk.FileChooserButton()
        box.add(new_file_btn)
        if prop_has_default:
            default_value = prop['default']
            file_id = default_value[2]
            files_drop.set_active(all_file_ids.index(file_id))
        files_drop.set_sensitive(prop_has_default)
        new_file_btn.set_sensitive(prop_has_default)
        files_drop.connect("changed", lambda x: _update_resource_file(prop))
        new_file_btn.connect("file-set", lambda x: _update_local_file(prop))
        widget_dict["default"] = (files_drop, new_file_btn)


def _create_property_gui(context, prop, all_files):

    widget_dict = {"all_files": all_files}
    prop["widget_dict"] = widget_dict

    prop_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    prop_box.set_border_width(10)

    common = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    val_lab = prop['desc']
    common.add(Gtk.Label('Desc'))
    entry = Gtk.Entry()
    entry.set_text(val_lab)
    common.add(entry)
    entry.connect("activate", lambda x: _update_desc(prop))
    widget_dict["desc"] = entry

    type_store = Gtk.ListStore(str)
    type_drop = Gtk.ComboBox()
    type_drop.set_model(type_store)
    cell = Gtk.CellRendererText()
    type_drop.pack_start(cell, True)
    type_drop.add_attribute(cell, "text", 0)
    for type_name in _types:
        type_store.append([type_name])
    val_type_name = prop['type']
    index = _types.index(val_type_name)
    type_drop.set_active(index)
    common.add(Gtk.Label('Type'))
    common.add(type_drop)
    type_drop.connect("changed", lambda x: _update_type(context, prop))
    widget_dict["type"] = type_drop

    prop_has_default = 'default' in prop

    prop_box.add(common)

    type_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    type_box.set_border_width(10)
    prop_box.add(type_box)
    widget_dict["type_box"] = type_box

    _set_property_type_gui(context, prop)

    return prop_box


def populate_test_properties(context, test_props, filename, properties):
    old_props = test_props.get_children()
    for child in old_props:
        test_props.remove(child)

    if len(filename):
        args = get_args_in_src(filename)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        test_props.add(box)

        props_defaults = context.db.get_settings()['defaults']

        all_files = context.db.get_resource_files()

        properties.clear()

        for arg in args:
            is_default = False
            if arg in props_defaults:
                prop = props_defaults[arg]
                is_default = True
            else:
                prop = { 'desc' : arg, 'type': "text"}
            properties[arg] = prop
            prop_gui = _create_property_gui(context, prop, all_files)
            frame = Gtk.Frame(label='args["%s"]' % arg)
            frame.set_border_width(10)
            if is_default:
                default_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                enabled = Gtk.CheckButton(label="Locked Existing Default")
                enabled.set_active(True)
                enabled.connect("toggled", lambda x, y: y.set_sensitive(not x.get_active()), prop_gui)
                prop_gui.set_sensitive(False)
                default_box.add(enabled)
                default_box.add(prop_gui)
                frame.add(default_box)
            else:
                frame.add(prop_gui)
            box.add(frame)

        test_props.show_all()
