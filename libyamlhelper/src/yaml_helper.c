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
#include <errno.h>
#include <yaml.h>

#include <devtank/log.h>
#include <devtank/helpers/yaml_helper.h>


struct dt_yaml_loader_t
{
    yaml_parser_t   parser;
    char *          yaml_source_name;
    unsigned        current_line_num;
    void *          userdata;
    FILE *          file;
};


typedef struct
{
    yaml_emitter_t  emitter;
    yaml_document_t document;
    FILE *          file;
} yaml_saver_t;


dt_yaml_loader_t* dt_yaml_loader_open_file(const char* filename, void* userdata)
{
    dt_yaml_loader_t* r = (dt_yaml_loader_t*)malloc(sizeof(dt_yaml_loader_t));
    if (!r)
    {
        error_msg("Failed to allocate memory for dt_yaml_loader_t.");
        return NULL;
    }
    r->file = fopen(filename, "r");
    if (!r->file)
    {
        error_msg("YAML loader failed to open yaml file \"%s\" : %s", filename, strerror(errno));
        free(r);
        return NULL;
    }
    r->yaml_source_name = strdup(filename);
    if (!r->yaml_source_name)
    {
        error_msg("Failed to allocate memory for dt_yaml_loader_t yaml source name.");
        fclose(r->file);
        free(r);
        return NULL;
    }
    r->userdata = userdata;
    r->current_line_num = 0;
    yaml_parser_initialize(&r->parser);
    yaml_parser_set_input_file(&r->parser, r->file);
    return r;
}


void           dt_yaml_loader_destroy(dt_yaml_loader_t* loader)
{
    if (!loader)
        return;
    if (loader->file)
        fclose(loader->file);
    if (loader->yaml_source_name)
        free(loader->yaml_source_name);
    yaml_parser_delete(&loader->parser);
    free(loader);
}


void*          dt_yaml_loader_get_userdata(dt_yaml_loader_t* loader)
{
    return loader->userdata;
}


void           dt_yaml_loader_set_userdata(dt_yaml_loader_t* loader, void* userdata)
{
    loader->userdata = userdata;
}


const char*    dt_yaml_loader_get_filename(dt_yaml_loader_t* loader)
{
    return loader->yaml_source_name;
}


unsigned       dt_yaml_loader_get_line_number(dt_yaml_loader_t* loader)
{
    return loader->current_line_num;
}


bool           dt_yaml_loader_do(dt_yaml_loader_t* loader, dt_yaml_loader_child_cb_t map_child_cb, dt_yaml_loader_child_cb_t array_child_cb, dt_yaml_loader_prop_cb_t prop_cb)
{
    yaml_parser_t* parser = &loader->parser;
    yaml_token_t  token;
    bool valid = true;
    bool done = false;
    char key[32] = {0};

    yaml_token_type_t prev_type = YAML_NO_TOKEN;

    do
    {
        if (!yaml_parser_scan(parser, &token))
            warning_msg("YAML parse error: (%i) \"%s\" line:%zu", parser->error, parser->problem, parser->mark.line + 1);

        loader->current_line_num = token.start_mark.line + 1;

        switch(token.type)
        {
            case YAML_STREAM_END_TOKEN:
                done = true;
                break;
            case YAML_KEY_TOKEN:
            case YAML_VALUE_TOKEN: prev_type = token.type; break;
            case YAML_FLOW_MAPPING_START_TOKEN:
            case YAML_BLOCK_MAPPING_START_TOKEN:
                if (!map_child_cb)
                {
                    warning_msg("Unexpected map in yaml, key \"%s\" in file \"%s\" line:%u", key, loader->yaml_source_name, loader->current_line_num);
                    valid = false;
                }
                else
                {
                    valid = map_child_cb(loader, (key[0])?key:NULL);
                    if (!valid)
                        warning_msg("Yaml map failed, key \"%s\" in file \"%s\" line:%u", key, loader->yaml_source_name, loader->current_line_num);
                }
                break;
            case YAML_FLOW_SEQUENCE_START_TOKEN:
            case YAML_BLOCK_SEQUENCE_START_TOKEN:
                if (!array_child_cb)
                {
                    warning_msg("Unexpected array in yaml, key \"%s\" in file \"%s\" line:%u", key, loader->yaml_source_name, loader->current_line_num);
                    valid = false;
                }
                else
                {
                    valid = array_child_cb(loader, (key[0])?key:NULL);
                    if (!valid)
                        warning_msg("Yaml array failed, key \"%s\" in file \"%s\" line:%u", key, loader->yaml_source_name, loader->current_line_num);
                }
                break;
            case YAML_FLOW_SEQUENCE_END_TOKEN:
            case YAML_FLOW_MAPPING_END_TOKEN:
            case YAML_BLOCK_END_TOKEN:
                done = true;
                key[0] = 0;
                break;
            case YAML_SCALAR_TOKEN:
                    if (prev_type == YAML_KEY_TOKEN)
                    {
                        strncpy(key, (const char*)token.data.scalar.value, sizeof(key)-2);
                        key[sizeof(key)-1] = 0;
                    }
                    else if (prev_type == YAML_VALUE_TOKEN)
                    {
                        if (!prop_cb)
                        {
                            warning_msg("Unexpected scalar in yaml, key \"%s\" in file \"%s\" line:%u", key, loader->yaml_source_name, loader->current_line_num);
                            valid = false;
                        }
                        else
                        {
                            valid = prop_cb(loader, key, (const char*)token.data.scalar.value);
                            if (!valid)
                                warning_msg("Yaml scalar failed, key \"%s\" in file \"%s\" line:%u", key, loader->yaml_source_name, loader->current_line_num);
                        }
                        key[0] = 0;
                    }
                break;
            default: break;
        }

        yaml_token_delete(&token);
    }
    while(valid && !done);

    if (!valid)
        warning_msg("YAML parsing failed : \"%s\"", loader->yaml_source_name);

    return valid;
}


static bool  yaml_saver_init(yaml_saver_t* saver, const char* filename)
{
    saver->file = fopen(filename, "w");
    if (!saver->file)
    {
        error_msg("YAML saver failed to open yaml file \"%s\" : %s", filename, strerror(errno));
        return false;
    }

    memset(&saver->emitter, 0, sizeof(yaml_emitter_t));
    memset(&saver->document, 0, sizeof(yaml_document_t));

    if (!yaml_emitter_initialize(&saver->emitter))
    {
        error_msg("YAML saver failed inialize the libyaml emitter object");
        fclose(saver->file);
        return false;
    }

    yaml_emitter_set_output_file(&saver->emitter, saver->file);
    yaml_emitter_open(&saver->emitter);

    if (!yaml_document_initialize(&saver->document, NULL, NULL, NULL, 0, 0))
    {
        error_msg("YAML saver failed inialize the libyaml emitter object");
        yaml_emitter_delete(&saver->emitter);
        fclose(saver->file);
        return false;
    }

    return true;
}


static void yaml_saver_clear(yaml_saver_t* saver)
{
    yaml_document_delete(&saver->document);
    yaml_emitter_delete(&saver->emitter);
    fclose(saver->file);
}


static int dt_yaml_add_element(yaml_saver_t* saver, dt_yaml_element_t* element);


static bool dy_yaml_add_map_entry(yaml_saver_t* saver, int map_id, dt_yaml_map_entry_t* entry)
{
    int value_id = dt_yaml_add_element(saver, &entry->value);
    if (value_id < 0)
        return false;
    int key_id = yaml_document_add_scalar(&saver->document,
                                NULL,
                                (yaml_char_t *)entry->key,
                                -1,
                                YAML_ANY_SCALAR_STYLE);
    if (key_id < 0)
        return false;
    if (!yaml_document_append_mapping_pair(&saver->document, map_id, key_id, value_id))
        return false;
    return true;
}


static int dt_yaml_add_element(yaml_saver_t* saver, dt_yaml_element_t* element)
{
    switch(element->type)
    {
        case DT_YAML_STRING:
        {
            return yaml_document_add_scalar(&saver->document,
                                            NULL,
                                            (yaml_char_t *)element->s_value,
                                            -1,
                                            YAML_DOUBLE_QUOTED_SCALAR_STYLE);
        }
        case DT_YAML_FLOAT:
        {
            char line[512];
            snprintf(line, sizeof(line), "%g", element->f_value);
            return yaml_document_add_scalar(&saver->document,
                                            NULL,
                                            (yaml_char_t *)line,
                                            -1,
                                            YAML_ANY_SCALAR_STYLE);
        }
        case DT_YAML_INTEGER:
        {
            char line[512];
            snprintf(line, sizeof(line), "%"PRIi64, element->i_value);
            return yaml_document_add_scalar(&saver->document,
                                            NULL,
                                            (yaml_char_t *)line,
                                            -1,
                                            YAML_ANY_SCALAR_STYLE);
        }
        case DT_YAML_HEX:
        {
            char line[512];
            snprintf(line, sizeof(line), "%"PRIx64, element->i_value);
            return yaml_document_add_scalar(&saver->document,
                                            NULL,
                                            (yaml_char_t *)line,
                                            -1,
                                            YAML_ANY_SCALAR_STYLE);
        }
        case DT_YAML_MAP:
        {
            int map_id = yaml_document_add_mapping(&saver->document,
                                                   (yaml_char_t *)YAML_MAP_TAG,
                                                   YAML_ANY_MAPPING_STYLE);
            for(dt_yaml_map_entry_t* entry = element->map_entries; entry->value.type != DT_YAML_NONE; entry++)
                if (!dy_yaml_add_map_entry(saver, map_id, entry))
                    return -1;

            return map_id;
        }
        case DT_YAML_ARRAY:
        {
            int array_id = yaml_document_add_sequence(&saver->document,
                                                      (yaml_char_t *)YAML_SEQ_TAG,
                                                      YAML_ANY_SEQUENCE_STYLE);
            for(dt_yaml_element_t* entry = element->array_entries; entry->type != DT_YAML_NONE; entry++)
            {
                int value_id = dt_yaml_add_element(saver, entry);
                if (value_id < 0)
                    return -1;
                if (!yaml_document_append_sequence_item(&saver->document, array_id, value_id))
                    return -1;
            }
            return array_id;
        }
        case DT_YAML_MAP_CB:
        {
            int map_id = yaml_document_add_mapping(&saver->document,
                                                   (yaml_char_t *)YAML_MAP_TAG,
                                                   YAML_ANY_MAPPING_STYLE);

            dt_yaml_map_entry_t* entry = NULL;

            do
            {
                if (!element->map_entry_callback.get_entry_cb(&entry, element->map_entry_callback.data))
                    return -1;
                if (entry)
                    if (!dy_yaml_add_map_entry(saver, map_id, entry))
                        return -1;
            }
            while(entry);

            return map_id;
        }
        case DT_YAML_ARRAY_CB:
        {
            int array_id = yaml_document_add_sequence(&saver->document,
                                                      (yaml_char_t *)YAML_SEQ_TAG,
                                                      YAML_ANY_SEQUENCE_STYLE);
            dt_yaml_element_t* entry = NULL;

            do
            {
                if (!element->array_entry_callback.get_entry_cb(&entry, element->array_entry_callback.data))
                    return -1;
                if (entry)
                {
                    int value_id = dt_yaml_add_element(saver, entry);
                    if (value_id < 0)
                        return -1;
                    if (!yaml_document_append_sequence_item(&saver->document, array_id, value_id))
                        return -1;
                }
            }
            while(entry);

            return array_id;
        }
        default: break;
    }
    error_msg("No handling of yaml element type: %u", element->type);
    return -1;
}



bool           dt_yaml_save(const char* filename, dt_yaml_element_t* root)
{
    yaml_saver_t saver;

    if (!yaml_saver_init(&saver, filename))
        return false;

    int root_id = dt_yaml_add_element(&saver, root);

    if (root_id >= 0)
    {
        if (!yaml_emitter_dump(&saver.emitter, &saver.document))
            error_msg("Failed to write out yaml file \"%s\" : %s", filename, saver.emitter.problem);
    }
    else error_msg("Failed to serialize given dt_yaml_element_t structure to libyaml.");

    yaml_saver_clear(&saver);

    return (root_id >= 0);
}
