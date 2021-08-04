from __future__ import print_function, absolute_import

import os
import sys
import copy
import parser

from dt_db_base import get_test_doc

from .group_properties_gui import open_tests_properties
from .new_test_gui import *
from .common import create_list_store
from .edit_test_gui import *


import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


def _on_list_selection_changed(text_obj, tests_group, selection):
    model, treeiters = selection.get_selected_rows()
    text_obj.get_buffer().set_text("")
    for treeiter in treeiters:
        test_obj = model[treeiter][1]
        test_file = test_obj.get_file_to_local()
        doc_text = get_test_doc(test_file)
        text_obj.get_buffer().set_text(doc_text)


def create_seclector_list_store(list_obj, tests_group, text_obj, sort_list):
    store_list = create_list_store(list_obj, sort_list)
    selection = list_obj.get_selection()
    selection.set_mode(Gtk.SelectionMode.MULTIPLE)
    selection.connect("changed", lambda sel : _on_list_selection_changed(text_obj, tests_group, sel))
    return store_list


def _update_test_group(context, right_list_store):
    tests = []
    for treeiter in right_list_store:
        tests += [ treeiter[1] ]
    context.tests_group.tests = tests


def _ok_pressed(context, right_list_store):
    _update_test_group(context, right_list_store)
    open_tests_properties(context)


def _selected_moved(list_obj, is_up):
    list_store = list_obj.get_model()
    selection = list_obj.get_selection()
    treeiters = selection.get_selected_rows()[1]

    count = list_store.iter_n_children(None)

    list_order = [ -1 ] * count

    for treeiter in treeiters:
        index = treeiter[0]
        if is_up and index:
            list_order[index-1] = index
        elif not is_up and index < (count - 1):
            list_order[index+1] = index

    for n in range(0, count):
        if n not in list_order:
            index = list_order.index(-1)
            list_order[index] = n

    list_store.reorder(list_order)


def _on_back(context):
    context.pop_view()

def _show_test_group(tests_group, builder, left_list_store, right_list_store):
    all_tests = tests_group.db.get_all_tests()

    left_list_store.clear()
    for test in all_tests:
        left_list_store.append([test.name, test])

    right_list_store.clear()
    for test in tests_group.tests:
        right_list_store.append([test.name, test])


def _from_left(a_list, b_list):
    a_selection = a_list.get_selection()
    a_list_store = a_list.get_model()
    b_list_store = b_list.get_model()
    treeiters = a_selection.get_selected_rows()[1]
    for treeiter in treeiters:
        entry = a_list_store[treeiter]
        name = entry[0]
        obj = copy.copy(entry[1])
        count=0
        for cur in b_list_store:
            if cur[1].filename == obj.filename:
                count+=1
        if count:
            name = "%s#%02i" % (name, count)
            obj.name = name
        b_list_store.append([name, obj])


def _from_right(a_list, b_list):
    b_selection = b_list.get_selection()
    b_list_store = b_list.get_model()
    treeiters = b_selection.get_selected_rows()[1]
    for treeiter in treeiters:
        b_list_store.remove(b_list_store.get_iter(treeiter))


def _add_test(context, right_list_store):
    _update_test_group(context, right_list_store)
    open_new_test_page(context)


def _edit_test(context, right_list_store):
    left_list = context.builder.get_object("LeftList")
    selection = left_list.get_selection()
    model, treeiters = selection.get_selected_rows()
    for treeiter in treeiters:
        test = model[treeiters][1]
        _update_test_group(context, right_list_store)
        open_edit_test_page(context, test)
        break


def _remove_test(left_list, context):
    selection = left_list.get_selection()
    model, treeiters = selection.get_selected_rows()
    for treeiter in treeiters:
        test = model[treeiters][1]
        test.remove()
        model.remove(model.get_iter(treeiter))


def open_test_group_selector(context):
    context.push_view()
    context.change_view("TestGroupSelector")


def init_test_group_selector(context):
    
    tests_group = context.tests_group
    builder = context.builder

    window = builder.get_object("TestGroupSelector")

    left_list = builder.get_object("LeftList")
    right_list = builder.get_object("RightList")

    from_left_btn = builder.get_object("add_btn")
    from_right_btn = builder.get_object("remove_btn")

    add_test_btn = builder.get_object("add_test_btn")
    edit_test_btn = builder.get_object("edit_test_btn")
    remove_test_btn = builder.get_object("remove_test_btn")

    ok_btn = builder.get_object("ok_btn")
    back_btn = builder.get_object("back_btn")

    up_btn = builder.get_object("order_up_btn")
    down_btn = builder.get_object("order_down_btn")

    left_text =  builder.get_object("LeftText")
    right_text =  builder.get_object("RightText")

    left_list_store = create_seclector_list_store(left_list, tests_group, left_text, True)
    right_list_store = create_seclector_list_store(right_list, tests_group, right_text, False)

    window.connect("show", lambda x: _show_test_group(tests_group, builder, left_list_store, right_list_store))

    from_left_btn.connect("clicked", lambda btn: _from_left(left_list, right_list))
    from_right_btn.connect("clicked", lambda btn: _from_right(left_list, right_list))

    add_test_btn.connect("clicked", lambda btn: _add_test(context, right_list_store))
    edit_test_btn.connect("clicked", lambda btn: _edit_test(context, right_list_store))
    remove_test_btn.connect("clicked", lambda btn: _remove_test(left_list, context))

    up_btn.connect("clicked", lambda btn: _selected_moved(right_list, True))
    down_btn.connect("clicked", lambda btn: _selected_moved(right_list, False))

    back_btn.connect("clicked", lambda btn:_on_back(context))
    ok_btn.connect("clicked", lambda btn: _ok_pressed(context, right_list_store))
