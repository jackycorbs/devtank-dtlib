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
#include "tests.h"
#include "devtank/buffer.h"


int main(int argc, char* argv[])
{
    dt_buffer_t static_buffer;
    expect_success(dt_buffer_init(&static_buffer, 0),  "init buffer test with 0");
    expect_success(dt_buffer_get_size(&static_buffer) == 0, "init buffer test with 0 has 0 size.");
    expect_success(dt_buffer_get_capacity(&static_buffer) == 0, "init buffer test with 0 has 0 capacity.");
    dt_buffer_clear(&static_buffer);
    expect_success(dt_buffer_init(&static_buffer, 32),  "init buffer test with 32");
    expect_success((dt_buffer_get_size(&static_buffer) == 0), "init buffer size test");
    expect_success((dt_buffer_get_capacity(&static_buffer) == 32), "capacity size test");
    dt_buffer_clear(&static_buffer);

    dt_buffer_set_data(&static_buffer, 0, (uint8_t[]){0xFF}, 1);
    expect_success((dt_buffer_get_size(&static_buffer) == 1), "used size test");
    dt_buffer_set_data(&static_buffer, 4, (uint8_t[]){0xFF}, 1);
    expect_success((dt_buffer_get_size(&static_buffer) == 5), "used size test 2");
    dt_buffer_set_data(&static_buffer, 0, (uint8_t*)"hello", 6);
    expect_success(!strcmp((char*)dt_buffer_get_data(&static_buffer),"hello"), "used content test");

    dt_buffer_set_capacity(&static_buffer, 64);
    expect_success((dt_buffer_get_capacity(&static_buffer) == 64), "capcity change size test");
    expect_success((dt_buffer_get_size(&static_buffer) == 6), "used size test 3");

    dt_buffer_set_size(&static_buffer, 4);
    expect_success(!strncmp((char*)dt_buffer_get_data(&static_buffer),"hell", 4), "used content test 2");
    expect_success((dt_buffer_get_size(&static_buffer) == 4), "used size test 4");

    uint32_t t=0x1234;

    dt_buffer_append(&static_buffer, (uint8_t*)&t, sizeof(t));
    expect_success((dt_buffer_get_size(&static_buffer) == 8), "used size test 8");
    expect_success(!strncmp((char*)dt_buffer_get_data(&static_buffer),"hell", 4), "append test value 1.");
    expect_success((*(uint32_t*)(&(((uint8_t*)dt_buffer_get_data(&static_buffer))[4]))) == t, "append test value 2.");
    dt_buffer_clear(&static_buffer);

    expect_success(dt_buffer_init(&static_buffer, 0),  "init buffer test with 0");

    uint8_t zeroes[256] = {0};
    dt_buffer_append(&static_buffer, zeroes, sizeof(zeroes));
    expect_success((dt_buffer_get_size(&static_buffer) == 256), "used size test 256");
    dt_buffer_append(&static_buffer, zeroes, sizeof(zeroes));
    expect_success((dt_buffer_get_size(&static_buffer) == 512), "used size test 512");
    dt_buffer_append(&static_buffer, zeroes, sizeof(zeroes));
    expect_success((dt_buffer_get_size(&static_buffer) == 768), "used size test 768");
    dt_buffer_append(&static_buffer, zeroes, sizeof(zeroes));
    expect_success((dt_buffer_get_size(&static_buffer) == 1024), "used size test 1024");
    dt_buffer_clear(&static_buffer);

    expect_success(dt_buffer_has_allow_growth(&static_buffer), "check buffer knows it can grow.");
    dt_buffer_allow_growth(&static_buffer, false);
    expect_fail(dt_buffer_append(&static_buffer, zeroes, sizeof(zeroes)), "adding to fixed buffer.");
    dt_buffer_allow_growth(&static_buffer, true);
    dt_buffer_set_capacity(&static_buffer, 1024);
    const char * hello = dt_buffer_clone_append(&static_buffer, "hello");
    expect_success(hello, "appended string to buffer.");
    expect_success(strcmp(hello, "hello") == 0, "string added to buffer corrected.");

    uint8_t * ptr = (uint8_t*)dt_buffer_append_space(&static_buffer, 4);
    expect_success(ptr, "appended empty space to buffer.");
    expect_success((uintptr_t)(hello + strlen(hello) + 1) == (uintptr_t)ptr, "appended empty space where expected.");

    expect_success(dt_buffer_set_size(&static_buffer, dt_buffer_get_size(&static_buffer) - 4), "shrink buffer.");

    expect_success(dt_buffer_clone_join(&static_buffer, " there"), "join append test.");
    expect_success(strcmp(dt_buffer_as_string(&static_buffer, 0), "hello there") == 0, "string joint to buffer corrected.");
    dt_buffer_clear(&static_buffer);

    dt_buffer_contain(&static_buffer, zeroes, sizeof(zeroes));

    expect_success(dt_buffer_contains(&static_buffer, zeroes), "check buffer wrapped address start.");
    expect_success(dt_buffer_contains(&static_buffer, zeroes + sizeof(zeroes) -1), "check buffer wrapped address end.");
    expect_fail(dt_buffer_contains(&static_buffer, zeroes + sizeof(zeroes)), "check buffer doesn't wrapped beyond address end.");
    expect_fail(dt_buffer_contains(&static_buffer, zeroes - 1), "check buffer doesn't wrapped before address start.");

    dt_buffer_clear(&static_buffer);

    uint8_t mem[sizeof(dt_buffer_t) + sizeof(uint32_t)];

    dt_buffer_t * rel_buffer = (dt_buffer_t*)mem;

    dt_buffer_init_relative(rel_buffer, mem + sizeof(dt_buffer_t), 4);
    expect_success(dt_buffer_get_size(rel_buffer) == 4, "check buffer size when relative pointer.");
    ptr = (uint8_t*)dt_buffer_get_offset_data(rel_buffer, 1);
    expect_success(ptr == (mem + sizeof(dt_buffer_t) + 1), "check buffer offset data from relative pointer.");
    unsigned offset;
    expect_success(dt_buffer_get_offset(rel_buffer, ptr, &offset), "query offset in buffer.");
    expect_success(offset == 1, "check offset returned in buffer.");

    return EXIT_SUCCESS;
}
