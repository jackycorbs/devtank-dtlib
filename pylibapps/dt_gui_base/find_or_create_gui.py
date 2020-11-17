from __future__ import print_function, absolute_import

import sys

from .barcode_scan_gui import double_scan_view
from .new_gui          import new_obj_view


class _create_post_scan(new_obj_view):
    def __init__(self, parent, context):
        self.parent = parent
        new_obj_view.__init__(self, context)

    def new_do(self, obj_type, serial_number):
        new_obj_view.new_do(self, obj_type, serial_number)
        obj = self.parent.create_obj(obj_type, serial_number)
        self.parent.final_with_obj(obj)



class scan_find_or_create(double_scan_view):
    def __init__(self, context, view_name):
        double_scan_view.__init__(self, context, view_name)
        self.new_view = _create_post_scan(self, context)
        self.type_name = None
        self.parent_type_name = None
        self.parent_serial = None

    def get_types(self):
        return []

    def get_next_type(self):
        return None

    def find_by_serial(self, serial_number):
        return None

    def create_obj(self, obj_type, serial_number):
        return None

    def can_create(self):
        return True

    def final_with_obj(self, obj):
        pass

    def open(self, type_name, parent_type_name="", parent_serial=""):
        self.type_name        = type_name
        self.parent_type_name = parent_type_name
        self.parent_serial    = parent_serial
        double_scan_view.open(self, type_name,
                              parent_type_name, parent_serial)

    def barcode_do(self, serial_number):
        double_scan_view.barcode_do(self, serial_number)
        obj = self.find_by_serial(serial_number)
        if obj:
            self.final_with_obj(obj)
        else:
            if self.can_create():
                types = self.get_types()
                if len(types):
                    next_type = self.get_next_type()
                    index = types.index(next_type) if next_type else 0
                    self.new_view.open(self.type_name, serial_number,
                                       types, index)
                    return
                else:
                    double_scan_view.open(self,
                                          self.type_name,
                                          self.parent_type_name,
                                          self.parent_serial)
                    self.set_status(
                        "Instance found and can not create new.")

    def close(self):
        double_scan_view.close(self)
        self.new_view.close()
