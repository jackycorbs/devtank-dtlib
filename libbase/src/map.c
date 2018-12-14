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

#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>

#define __DT_MAP__

#include "devtank/map.h"

typedef struct dt_map_node_t dt_map_node_t;

struct dt_map_t
{
	dt_map_key_hash_t    key_hash;
	dt_map_key_match_t   key_match;
	dt_map_item_key_t    item_key;
	dt_map_item_delete_t item_delete;

	dt_map_node_t* base[256];
	void *data;
} __attribute__((packed));

struct dt_map_node_t
{
	void*          item;
	dt_map_node_t* next;
} __attribute__((packed));


_Static_assert(sizeof(struct dt_map_static_t) == sizeof(dt_map_t), "Public and private structure definition of dt_map_t are not the same size.");


dt_map_t* dt_map_create(
	dt_map_key_hash_t    key_hash,
	dt_map_key_match_t   key_match,
	dt_map_item_key_t    item_key,
	dt_map_item_delete_t item_delete,
	void               * data)
{
	dt_map_t* map = (dt_map_t*)malloc(sizeof(dt_map_t));
	if (!map) return NULL;

	dt_map_init(map, key_hash, key_match, item_key, item_delete, data);

	return map;
}


void dt_map_init(
	dt_map_t* map,
	dt_map_key_hash_t    key_hash,
	dt_map_key_match_t   key_match,
	dt_map_item_key_t    item_key,
	dt_map_item_delete_t item_delete,
	void               * data)
{
	map->key_hash    = key_hash;
	map->key_match   = key_match;
	map->item_key    = item_key;
	map->item_delete = item_delete;
	map->data = data;

	unsigned i;
	for (i = 0; i < 256; i++)
		map->base[i] = NULL;
}


void dt_map_delete(dt_map_t* map)
{
	dt_map_clear(map);
	free(map);
}


void dt_map_clear(dt_map_t* map)
{
	if (!map) return;

	unsigned i;
	for (i = 0; i < 256; i++)
	{
		dt_map_node_t* node = map->base[i];
		while (node)
		{
			dt_map_node_t* next = node->next;
			if (map->item_delete)
				map->item_delete(node->item, map->data);
			free(node);
			node = next;
		}
		map->base[i] = NULL;
	}
}


static void* dt_map__find(
	const dt_map_t* map, const void* key, uint8_t hash)
{
	if (!map->item_key
		|| !map->key_match)
		return NULL;

	dt_map_node_t* node;
	for (node = map->base[hash]; node; node = node->next)
	{
		const void* nkey = map->item_key(node->item, map->data);
		if (!nkey) continue;
		if (map->key_match(key, nkey, map->data))
			return node->item;
	}

	return NULL;
}

bool dt_map_add(dt_map_t* map, void* item)
{
	if (!map || !item
		|| !map->item_key
		|| !map->key_hash)
		return false;

	const void* key = map->item_key(item, map->data);
	if (!key) return false;

	uint8_t hash = map->key_hash(key, map->data);

	if (dt_map__find(map, key, hash))
		return false;

	dt_map_node_t* node
		= (dt_map_node_t*)malloc(
			sizeof(dt_map_node_t));
	if (!node) return false;

	node->item = item;
	node->next = map->base[hash];
	map->base[hash] = node;
	return true;
}


bool  dt_map_remove(dt_map_t* map, const void* key)
{
	if (!map || !key
		|| !map->key_hash)
		return false;
	uint8_t hash = map->key_hash(key, map->data);
	dt_map_node_t* node, * prev = NULL;
	for (node = map->base[hash]; node; node = node->next)
	{
		const void* nkey = map->item_key(node->item, map->data);
		if (!nkey) continue;
		if (map->key_match(key, nkey, map->data))
		{
			if (prev)
				prev->next = node->next;
			else
				map->base[hash] = node->next;
			if (map->item_delete)
				map->item_delete(node->item, map->data);
			free(node);
			return true;
		}
		prev = node;
	}
	return false;
}


void* dt_map_find(const dt_map_t* map, const void* key)
{
	if (!map || !key
		|| !map->key_hash)
		return NULL;

	uint8_t hash = map->key_hash(key, map->data);
	return dt_map__find(map, key, hash);
}


uint8_t dt_default_short_hash(const void * data, unsigned len)
{
    uint8_t hash = 7;
    for (unsigned i = 0; i < len; i++)
        hash = hash*31 + ((const uint8_t*)data)[i];
    return hash;
}


uint8_t dt_string_short_hash_cb(const void * str, void *data)
{
    (void)data;
    return dt_default_short_hash((const char*)str, strlen((const char*)str));
}


bool    dt_string_match_cb(const void* a, const void* b, void *data)
{
    (void)data;
    const char * s1 = (const char*)a;
    const char * s2 = (const char*)b;
    return (strcmp(s1, s2) == 0);
}
