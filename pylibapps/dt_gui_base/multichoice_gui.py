import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

_singleton = None


class multichoice_singleton(object):
    def __init__(self, context):
        self.context = context
        self.choice_lab = context.builder.get_object("choice_lab")
        self.choices_box = context.builder.get_object("choices_box")
        self.choice_ok_btn = context.builder.get_object("choice_ok_btn")
        self.choice_ok_btn.connect("clicked", lambda x: self._response_click())
        self.return_cb = None
        self.selected_choice_key = None

    def _response_click(self):
        self.context.pop_view()
        cb = self.choice_map.get(self.selected_choice_key)
        print(f"Multiselected: {self.selected_choice_key}")
        if cb:
            cb()

    def _on_button_toggled(self, _, choice_key):
        self.selected_choice_key = choice_key

    def open(self, msg, choice_map):
        context = self.context
        context.push_view()
        context.change_view("MultiChoice")
        self.choice_lab.set_text(msg)
        self.choice_map = choice_map

        old_kids = self.choices_box.get_children()
        for child in old_kids:
            self.choices_box.remove(child)

        first_choice_btn = None

        for choice_text in choice_map:
            choice_btn = Gtk.RadioButton.new_with_label_from_widget(first_choice_btn, choice_text)
            if not first_choice_btn:
                first_choice_btn = choice_btn
                self.selected_choice_key = choice_text
            choice_btn.connect("toggled", self._on_button_toggled, choice_text)
            self.choices_box.pack_start(choice_btn, False, False, 0)

        self.choices_box.show_all()



def open_multichoice_gui(msg, choice_map):
    _singleton.open(msg, choice_map)


def init_multichoice_gui(context):
    global _singleton
    _singleton = multichoice_singleton(context)
