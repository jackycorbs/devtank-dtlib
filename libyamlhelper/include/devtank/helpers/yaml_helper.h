/*
 * Copyright (c) 2016 DevTank Ltd
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 *
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
 * BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
 * ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 * CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */
#ifndef __YAML_HELPER__
#define __YAML_HELPER__
/**
 * \defgroup YAML_Helper
 * \ingroup C
 * \brief Helper functions to load data structure from YAML or save data structure to YAML.
 * 
 * This gives more structure to of libyaml.
 * The big thing to remember is that libyaml doesn't have intermediate data structures.
 * You load strait from YAML to your data structures. This provides a framework to ease that.
 * 
 * It also adds a framework for saving from you database structure to YAML.
 * 
 * 
 * @{
 */
 
/** \brief YAML loader object, stores current state as YAML is loaded. */
typedef struct dt_yaml_loader_t dt_yaml_loader_t;

/** \brief YAML child object loader callback called for map or array objects. */
typedef bool (*dt_yaml_loader_child_cb_t)(dt_yaml_loader_t* loader, const char* key);

/** \brief YAML map loader callback called for each map element that is not a map or an array. */
typedef bool (*dt_yaml_loader_prop_cb_t)(dt_yaml_loader_t* loader, const char* key, const char* value);

/** \brief Open a YAML file and set the loader with given userdata */
extern dt_yaml_loader_t* dt_yaml_loader_open_file(const char* filename, void* userdata);

/** \brief Destroy YAML loader */
extern void           dt_yaml_loader_destroy(dt_yaml_loader_t* loader);

/** \brief Get current user data of YAML loader */
extern void*          dt_yaml_loader_get_userdata(dt_yaml_loader_t* loader);

/** \brief Set current user data of YAML loader */
extern void           dt_yaml_loader_set_userdata(dt_yaml_loader_t* loader, void* userdata);

/** \brief Get filename the YAML loader was openned with. */
extern const char*    dt_yaml_loader_get_filename(dt_yaml_loader_t* loader);

/** \brief Get current line number the YAML loader is at. */
extern unsigned       dt_yaml_loader_get_line_number(dt_yaml_loader_t* loader);

/** \brief Start the YAML loader processing the YAML of the file it was created with. */
extern bool           dt_yaml_loader_do(dt_yaml_loader_t* loader, dt_yaml_loader_child_cb_t map_child_cb, dt_yaml_loader_child_cb_t array_child_cb, dt_yaml_loader_prop_cb_t prop_cb);



typedef struct dt_yaml_element_t   dt_yaml_element_t;   ///< Abstraction for YAML node to save.
typedef struct dt_yaml_map_entry_t dt_yaml_map_entry_t; ///< Abstraction of map entry of YAML node to save.

/** \brief YAML element to save */
struct dt_yaml_element_t
{
    enum
    {
        DT_YAML_NONE = 0, ///< Invalid elemnt to save.
        DT_YAML_STRING,   ///< String element to save, use s_value
        DT_YAML_FLOAT,    ///< Flaot element to save, use f_value
        DT_YAML_INTEGER,  ///< Integer element to save, use i_value
        DT_YAML_HEX,      ///< Integer element to save, use i_value, but saved as text of hex.
        DT_YAML_MAP,      ///< Map elements array to save, use use map_entries, last value element in array should have type DT_YAML_NONE
        DT_YAML_ARRAY,    ///< Array element to save, use array_entries, last element in array should have type DT_YAML_NONE
        DT_YAML_MAP_CB,   ///< Callback to fetch next map element to save.
        DT_YAML_ARRAY_CB, ///< Callback to fetch next array element to save (dynamic alterative to DT_YAML_ARRAY)
    } type;               ///< Type of element.
    union
    {
        int64_t     i_value; ///< Integer value for element.
        double      f_value; ///< Float value for element.
        const char* s_value; ///< Text value for element.
        dt_yaml_element_t * array_entries; ///< Array of elements, last element having type DT_YAML_NONE.
        dt_yaml_map_entry_t* map_entries;  ///< Array of map entries, last value element having type DT_YAML_NONE.
        struct
        {
            void* data; ///< User data to use with callback
            bool (*get_entry_cb)(dt_yaml_map_entry_t** entry, void *data); ///< Callback to get next map entry.
        } map_entry_callback; ///< Get map entries dynamically.
        struct
        {
            void* data; ///< User data to use with callback
            bool (*get_entry_cb)(dt_yaml_element_t** value, void *data); ///< Callback to get next array element.
        } array_entry_callback; ///< Get elements of array dynamically.
    };
};


/** \brief YAML map element entry to save */
struct dt_yaml_map_entry_t
{
    const char*       key;
    dt_yaml_element_t value;
};


/** \brief Save data structure to YAML file
 * \param filename The path of the file to save out as.
 * \param root root element of YAML to save.
 */
extern bool           dt_yaml_save(const char* filename, dt_yaml_element_t* root);

/**
 * @}
*/

#endif //__YAML_HELPER__
