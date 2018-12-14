
def _get_scan_widget(context, box):
    if isinstance(box, str) or isinstance(box, unicode):
        return context.builder.get_object(box)
    else:
        return box


class scan_box_base(object):
    def __init__(self, context, box_a, box_b):
        self.context = context
        self.scan_barcodeA_entry = _get_scan_widget(context, box_a)
        self.scan_barcodeB_entry = _get_scan_widget(context, box_b)
        self._scan_A_id = None
        self._scan_B_id = None

    def _change_focus(self):
        self.scan_barcodeA_entry.set_sensitive(False)
        self.scan_barcodeB_entry.set_sensitive(True)
        self.scan_barcodeB_entry.grab_focus()

    def _barscan_act(self):

        serial_numberA = self.scan_barcodeA_entry.get_text()
        serial_numberB = self.scan_barcodeB_entry.get_text()

        if serial_numberA == serial_numberB:
            self.scan_barcodeB_entry.set_sensitive(False)
            self.set_status("")
            self.reset_scan()
            self.barcode_do(serial_numberA)
        else:
            self.set_status("Barcodes don't match.\nPlease scan again.")
            self.reset_scan()

    def set_status(self, msg):
        pass

    def barcode_do(self, serial_number):
        pass

    def open(self):
        self._scan_A_id = self.scan_barcodeA_entry.connect("activate",
            lambda x: self._change_focus())
        self._scan_B_id = self.scan_barcodeB_entry.connect("activate",
            lambda x: self._barscan_act())
        self.reset_scan()

    def close(self):
        if self._scan_A_id:
            self.scan_barcodeA_entry.disconnect(self._scan_A_id)
            self._scan_A_id = None
        if self._scan_B_id:
            self.scan_barcodeB_entry.disconnect(self._scan_B_id)
            self._scan_B_id = None

    def reset_scan(self):
        self.scan_barcodeA_entry.set_text("")
        self.scan_barcodeB_entry.set_text("")
        self.scan_barcodeA_entry.set_sensitive(True)
        self.scan_barcodeB_entry.set_sensitive(False)
        self.scan_barcodeA_entry.grab_focus()



class double_scan_view(scan_box_base):
    def __init__(self, context, view_name):
        scan_box_base.__init__(self,
                               context,
                               "scan_barcodeA_entry",
                               "scan_barcodeB_entry")
        self.type_name = None

        builder = context.builder
        self.window                 = builder.get_object("BarcodeScan")
        
        self.scan_parent_type_lab   = builder.get_object("scan_parent_type_lab")
        self.scan_parent_serial_lab = builder.get_object("scan_parent_serial_lab")
        self.scan_lab               = builder.get_object("scan_lab")
        self.scan_status_lab        = builder.get_object("scan_status_lab")
        self.scan_back_btn          = builder.get_object("scan_back_btn")

        self._show_id = None
        self._back_id = None

        self.view_name = view_name
        context.view_objs[view_name] = self

    def open(self, type_name, parent_type_name="", parent_serial=""):
        assert self._show_id is None
        self._show_id = self.window.connect("show",
            lambda x: self._on_show())

        self._back_id = self.scan_back_btn.connect("clicked",
            lambda x: self.go_back())

        scan_box_base.open(self)

        self.scan_parent_type_lab.set_text(parent_type_name)
        self.scan_parent_serial_lab.set_text(parent_serial)
        self.scan_lab.set_text("Please Scan %s Barcode" % type_name)
        self.scan_status_lab.set_text("")
        self.type_name = type_name
        self.context.push_view()
        self.context.change_view(self.view_name)

    def show_view(self):
        self.context.force_view("BarcodeScan")

    def _on_show(self):
        self.reset_scan()

    def barcode_do(self, serial_number):
        self.close()
        self.context.pop_view()

    def set_status(self, text):
        self.scan_status_lab.set_text(text)

    def close(self):
        if self._show_id:
            self.window.disconnect(self._show_id)
            self._show_id = None
        if self._back_id:
            self.scan_back_btn.disconnect(self._back_id)
            self._back_id = None
        scan_box_base.close(self)

    def go_back(self):
        self.close()
        self.context.pop_view()
