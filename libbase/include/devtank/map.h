/*
 * Copyright (c) 2017 DevTank Ltd
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
#ifndef __DT_MAP_H__
#define __DT_MAP_H__

#include <stdbool.h>
#include <stdint.h>

struct dt_map_static_t
{
	uintptr_t data[261];
} __attribute__((packed));

#ifndef __DT_MAP__
typedef struct dt_map_static_t dt_map_t;
#else
typedef struct dt_map_t dt_map_t;
#endif

typedef uint8_t     (*dt_map_key_hash_t)(const void* key, void *data);
typedef bool        (*dt_map_key_match_t)(const void* a, const void* b, void *data);
typedef const void* (*dt_map_item_key_t)(const void* item, void *data);
typedef void        (*dt_map_item_delete_t)(void* item, void *data);

extern dt_map_t* dt_map_create(
	dt_map_key_hash_t    key_hash,
	dt_map_key_match_t   key_match,
	dt_map_item_key_t    item_key,
	dt_map_item_delete_t item_delete,
	void               * data);

extern void dt_map_init(
	dt_map_t* map,
	dt_map_key_hash_t    key_hash,
	dt_map_key_match_t   key_match,
	dt_map_item_key_t    item_key,
	dt_map_item_delete_t item_delete,
	void               * data);

extern void dt_map_delete(dt_map_t* map);
extern void dt_map_clear(dt_map_t* map);

extern bool  dt_map_add(dt_map_t* map, void* item);
extern bool  dt_map_remove(dt_map_t* map, const void* key);

extern void* dt_map_find(const dt_map_t* map, const void* key);

extern uint8_t dt_default_short_hash(const void * data, unsigned len);

extern uint8_t dt_string_short_hash_cb(const void * str, void *data);
extern bool    dt_string_match_cb(const void* a, const void* b, void *data);

#endif
