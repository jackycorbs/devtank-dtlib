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
#include <stdlib.h>
#include <string.h>

#include "devtank/log.h"

#define DT_BUFFER
typedef struct
{
    uint8_t* data;
    uint32_t size;
    uint32_t used;
    struct
    {
        uint32_t own:1;
        uint32_t relative:1;
        uint32_t disallow_growth:1;
    };
} __attribute__((packed)) dt_buffer_t;

#include "devtank/buffer.h"

_Static_assert(sizeof(struct dt_buffer_static_t) == sizeof(dt_buffer_t), "Public and private structure definition of dt_buffer_t are not the same size.");


bool           dt_buffer_init(dt_buffer_t* buffer, unsigned init_size)
{
    DT_RETURN_ON_FAIL(buffer, "No buffer given.", false);
    buffer->data = NULL;
    buffer->size = buffer->used = 0;
    buffer->own = true;
    buffer->relative = false;
    buffer->disallow_growth = false;
    if (init_size)
        return dt_buffer_set_capacity(buffer, init_size);
    return true;
}


void           dt_buffer_init_relative(dt_buffer_t* buffer, void* data, unsigned size)
{
    buffer->own = true;
    dt_rel_ptr_set((intptr_t*)&buffer->data, data);
    buffer->used = size;
    buffer->size = size;
    buffer->relative = true;
    buffer->disallow_growth = true;
}


void           dt_buffer_clear(dt_buffer_t* buffer)
{
    DT_RETURN_ON_FAIL(buffer, "No buffer given.", );
    if (!buffer)
        return;
    if (buffer->own)
        safe_free(buffer->data);
    buffer->data = NULL;
    buffer->size = buffer->used = 0;
    buffer->own = true;
    buffer->relative = false;
    buffer->disallow_growth = false;
}


unsigned       dt_buffer_get_size(const dt_buffer_t* buffer)
{
    DT_RETURN_ON_FAIL(buffer, "No buffer given.", 0);
    return buffer->used;
}


unsigned       dt_buffer_get_capacity(const dt_buffer_t* buffer)
{
    DT_RETURN_ON_FAIL(buffer, "No buffer given.", 0);
    return buffer->size;
}


void*       dt_buffer_get_data(const dt_buffer_t* buffer)
{
    DT_RETURN_ON_FAIL(buffer, "No buffer given.", NULL);
    if (buffer->relative)
        return dt_rel_ptr_get((intptr_t*)&buffer->data);
    return buffer->data;
}


void*          dt_buffer_get_offset_data(const dt_buffer_t* buffer, unsigned offset)
{
    uint8_t * mem = dt_buffer_get_data(buffer);
    DT_RETURN_ON_FAIL(mem, "Failed to get buffer memory.", NULL);
    DT_RETURN_ON_FAIL((offset < buffer->used), "Offset outside of memory of buffer.", NULL);
    return mem + offset;
}


bool           dt_buffer_get_offset(dt_buffer_t* buffer, const void* ptr, unsigned * offset)
{
    DT_RETURN_ON_FAIL(buffer, "No buffer given.", false);
    if (!ptr)
        return false;
    uint8_t * mem = dt_buffer_get_data(buffer);
    DT_RETURN_ON_FAIL(mem, "Failed to get buffer memory.", NULL);
    uint8_t * mem_end = mem + buffer->used;
    if (((intptr_t)ptr) >= ((intptr_t)mem) && ((intptr_t)ptr) < ((intptr_t)mem_end))
    {
        if (offset)
            *offset = ((uintptr_t)ptr) - ((uintptr_t)mem);
        return true;
    }
    return false;
}


bool           dt_buffer_contains(const dt_buffer_t* buffer, const void * ptr)
{
    DT_RETURN_ON_FAIL(buffer, "No buffer given.", false);
    if (!ptr)
        return false;
    uint8_t * mem = dt_buffer_get_data(buffer);
    if (!mem)
        return false;
    uint8_t * mem_end = mem + buffer->used;
    return (((intptr_t)ptr) >= ((intptr_t)mem) && ((intptr_t)ptr) < ((intptr_t)mem_end));
}


bool           dt_buffer_set_size(dt_buffer_t* buffer, unsigned size)
{
    DT_RETURN_ON_FAIL(buffer, "No buffer given.", false);
    if (!buffer->own)
        dt_buffer_clear(buffer);

    if (size <= buffer->used)
    {
        buffer->used = size;
        return true;
    }
    else if (size > buffer->size)
    {
        if (buffer->disallow_growth)
        {
            warning_msg("Buffer has requested capacity change %u -> %u (set_size), but isn't allowed.", buffer->size, size);
            return false;
        }

        void* new_data = realloc(buffer->data, size);
        if (!new_data)
        {
            warning_msg("Failed to grow buffer.\n");
            return false;
        }
        buffer->data = new_data;
        buffer->size = size;
        buffer->used = size;
        return true;
    }
    else
    {
        buffer->used = size;
        return true;
    }
}


bool           dt_buffer_set_capacity(dt_buffer_t* buffer, unsigned size)
{
    DT_RETURN_ON_FAIL(buffer, "No buffer given.", false);
    if (!buffer->own)
        dt_buffer_clear(buffer);

    if (buffer->size == size)
        return true;

    if (buffer->disallow_growth)
    {
        warning_msg("Buffer has requested capacity change %u -> %u (set_capacity), but isn't allowed.", buffer->size, size);
        return false;
    }

    void* new_data = realloc(buffer->data, size);
    if (!new_data)
    {
        warning_msg("Failed to change buffer capacity.\n");
        return false;
    }
    buffer->data = new_data;
    buffer->size = size;
    if (buffer->used > size)
        buffer->used = size;
    return true;
}


unsigned       dt_buffer_get_unused_capacity(dt_buffer_t* buffer)
{
    DT_RETURN_ON_FAIL(buffer, "No buffer given.", 0);
    return buffer->size - buffer->used;
}


bool           dt_buffer_set_data(dt_buffer_t* buffer, unsigned offset, const void* data, unsigned size)
{
    DT_RETURN_ON_FAIL(buffer, "No buffer given.", false);
    if (!buffer->own)
    {
        warning_msg("Attempt made to write to buffer that down not own the memory.");
        return false;
    }
    unsigned new_end = offset + size;
    if (buffer->size >= new_end)
    {
        if (buffer->data + offset != data)
            memcpy(buffer->data + offset, data, size);
        buffer->used = new_end;
        return true;
    }
    else
    {
        if (buffer->disallow_growth)
        {
            warning_msg("Buffer has requested capacity change %u -> %u (set_data), but isn't allowed.", buffer->size, new_end);
            return false;
        }

        void* new_data = realloc(buffer->data, new_end);
        if (!new_data)
        {
            error_msg("Failed to grow buffer.\n");
            return false;
        }
        buffer->data = new_data;
        if (offset > buffer->used)
            memset(buffer->data + buffer->used, 0, offset - buffer->used);
        memcpy(buffer->data + offset, data, size);
        buffer->size = new_end;
        buffer->used = new_end;
        return true;
    }
}


bool           dt_buffer_append(dt_buffer_t* buffer, const void* data, unsigned size)
{
    return dt_buffer_set_data(buffer, buffer->used, data, size);
}


bool          dt_buffer_wipe(dt_buffer_t* buffer)
{
    return dt_buffer_set_size(buffer, 0);
}


void           dt_buffer_contain(dt_buffer_t* buffer, void* data, unsigned size)
{
    DT_RETURN_ON_FAIL(buffer, "No buffer given.",);

    dt_buffer_clear(buffer);

    buffer->own = false;
    buffer->data = data;
    buffer->used = size;
    buffer->size = size;
}


void           dt_buffer_allow_growth(dt_buffer_t* buffer, bool enable)
{
    DT_RETURN_ON_FAIL(buffer, "No buffer given.",);
    DT_RETURN_ON_FAIL(!buffer->relative, "No relative buffer can't be set to grow.",);
    buffer->disallow_growth = !enable;
}


bool           dt_buffer_has_allow_growth(dt_buffer_t* buffer)
{
    DT_RETURN_ON_FAIL(buffer, "No buffer given.", false);
    return !buffer->disallow_growth;
}


char *         dt_buffer_clone_append(dt_buffer_t* buffer, const char* str)
{
    DT_RETURN_ON_FAIL(buffer, "No buffer given.", NULL);
    DT_RETURN_ON_FAIL(str, "No string given to append", NULL);

    unsigned len = strlen(str) + 1;

    char * mem = (char*)dt_buffer_append_space(buffer, len);
    if (!mem)
    {
        error_msg("Failed to resize buffer append clone of string.");
        return NULL;
    }

    memcpy(mem, str, len);

    return mem;
}


bool           dt_buffer_clone_join(dt_buffer_t* buffer, const char* str)
{
    DT_RETURN_ON_FAIL(buffer, "No buffer given.", false);
    DT_RETURN_ON_FAIL(str, "No string given to join on", false);

    unsigned len = strlen(str);

    bool appending = (dt_buffer_get_size(buffer) > 0);

    if (!appending)
        len++;

    char * mem = (char*)dt_buffer_append_space(buffer, len);
    if (!mem)
    {
        error_msg("Failed to resize buffer append clone of string.");
        return false;
    }

    if (appending)
        memcpy(mem-1, str, len+1);
    else
        memcpy(mem, str, len);

    return true;
}


void *         dt_buffer_append_space(dt_buffer_t* buffer, unsigned size)
{
    DT_RETURN_ON_FAIL(buffer, "No buffer given.", NULL);
    DT_RETURN_ON_FAIL(size, "No extra space given.", NULL);

    unsigned pos = dt_buffer_get_size(buffer);

    if (!dt_buffer_set_size(buffer, pos + size))
    {
        error_msg("Failed to resize to append extra space.");
        return NULL;
    }

    return ((uint8_t*)dt_buffer_get_data(buffer)) + pos;
}


char *         dt_buffer_append_print(dt_buffer_t* buffer, const char * fmt, ...)
{
    va_list va;
    va_start(va, fmt);
    char * r = dt_buffer_append_vprint(buffer, fmt, va);
    va_end(va);
    return r;
}


char *         dt_buffer_append_vprint(dt_buffer_t* buffer, const char * fmt, va_list va)
{
    va_list va2;

    va_copy(va2, va);

    int required_size = vsnprintf(NULL, 0, fmt, va2) + 1 /*Include null termination.*/;

    va_end(va2);

    DT_RETURN_ON_FAIL(required_size > 0, "Zero size of print to buffer.....", NULL);

    char * r = (char*)dt_buffer_append_space(buffer, required_size);
    DT_RETURN_ON_FAIL(r, "Failed to set buffer to size of complete print.", NULL);

    vsnprintf(r, required_size, fmt, va);

    return r;
}


void *         dt_buffer_read_fd(dt_buffer_t* buffer, unsigned size, int fd, dt_usecs usecs)
{
    DT_RETURN_ON_FAIL(buffer, "No buffer given.", NULL);
    DT_RETURN_ON_FAIL(size, "No extra space given.", NULL);
    DT_RETURN_ON_FAIL(fd >= 0, "File descript given invalid.", NULL);

    unsigned pos = dt_buffer_get_size(buffer);

    void * data = dt_buffer_append_space(buffer, size);
    if (!data)
        return NULL;

    if (!safe_read(fd, data, size, usecs))
    {
        error_msg("Failed to read %u bytes of fd:%i into buffer.", size, fd);
        dt_buffer_set_size(buffer, pos);
        return NULL;
    }
    return data;
}


const char *   dt_buffer_as_string(const dt_buffer_t* buffer, unsigned offset)
{
    const char * str = (const char*)dt_buffer_get_offset_data(buffer, offset);
    DT_RETURN_ON_FAIL(str, "Unable to get buffer content at given offset.", NULL);

    unsigned max_len = buffer->used - offset;

    for(unsigned n = 0; n < max_len; n++)
        if (!str[n])
            return str;

    error_msg("Buffer has no null after offset, so can not return as string.");
    return NULL;
}


bool           dt_buffer_get_copy(const dt_buffer_t* buffer, unsigned offset, void * dst, unsigned size)
{
    const void * mem = dt_buffer_get_offset_data(buffer, offset);
    DT_RETURN_ON_FAIL(mem, "Unable to get buffer content at given offset.", false);

    unsigned max_len = buffer->used - offset;

    DT_RETURN_ON_FAIL(max_len >= size, "Not enough memory in buffer to perform requested copy.", false);

    memcpy(dst, mem, size);
    return true;
}
