
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk



class new_obj_view(object):
    def __init__(self, context):
        self.context = context
        self.type_name = None
        self.serial_number = None

        builder = context.builder

        self.new_obj_type_lab    = builder.get_object("new_obj_type_lab")
        self.new_obj_serial_lab  = builder.get_object("new_obj_serial_lab")
        self.new_obj_type_list   = builder.get_object("new_obj_type_list")
        self.new_obj_btn         = builder.get_object("new_obj_btn")
        self.new_obj_back_btn    = builder.get_object("new_obj_back_btn")

        self.new_obj_type_list_model = self.new_obj_type_list.get_model()

        if not self.new_obj_type_list_model:
            self.new_obj_type_list_model = Gtk.ListStore(str, object)
            self.new_obj_type_list.set_model(self.new_obj_type_list_model)

            self.new_obj_type_list.append_column(
                Gtk.TreeViewColumn("devices", Gtk.CellRendererText(),
                text=0))

        self.new_obj_btn_id = None
        self.new_obj_back_btn_id = None


    def open(self, type_name, serial_number, db_types, selected=0):
        assert self.new_obj_btn_id is None
        self.new_obj_btn_id = self.new_obj_btn.connect("clicked",
                lambda x: self._new_clicked())
        self.new_obj_back_btn_id = self.new_obj_back_btn.connect("clicked",
                lambda x: self._new_obj_back())

        self.serial_number = serial_number
        self.type_name = type_name

        self.new_obj_type_lab.set_text(type_name)
        self.new_obj_serial_lab.set_text(serial_number)

        self.type_name = type_name

        self.new_obj_type_list_model.clear()

        rows = [(db_type.name, db_type) for db_type in db_types ]

        rows.sort()

        for row in rows:
            self.new_obj_type_list_model.append(row)

        selection = self.new_obj_type_list.get_selection()

        it = self.new_obj_type_list_model.iter_nth_child(None, selected)
        selection.select_iter(it)

        self.context.push_view()
        self.context.change_view("NewObj")


    def close(self):
        if self.new_obj_btn_id:
            self.new_obj_btn.disconnect(self.new_obj_btn_id)
            self.new_obj_btn_id = None

        if self.new_obj_back_btn_id:
            self.new_obj_back_btn.disconnect(self.new_obj_back_btn_id)
            self.new_obj_back_btn_id = None


    def _new_obj_back(self):
        self.close()
        self.context.pop_view()


    def new_do(self, db_type, serial_number):
        self.close()
        self.context.pop_view()


    def _new_clicked(self):
        selection = self.new_obj_type_list.get_selection()

        model, treeiters = selection.get_selected_rows()

        db_type = model[treeiters[0]][1]
        self.new_do(db_type, self.serial_number)
