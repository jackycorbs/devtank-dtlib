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
#include "devtank/base.h"
#include "tests.h"


int main(int argc, char* argv[])
{
    char memory[128] = {0};
    char other[64] = {0};

    dt_dyn_rel_ptr_t * ptr = (dt_dyn_rel_ptr_t*)memory;

    dt_dyn_rel_ptr_set_rel(ptr, memory + 64);

    expect_success (dt_dyn_rel_ptr_get(ptr) == (memory + 64), "check relative pointer");
    expect_fail(dt_dyn_rel_ptr_is_full(ptr), "check relative pointer state");

    dt_dyn_rel_ptr_set(ptr, other);

    expect_success (dt_dyn_rel_ptr_get(ptr) == other, "check relative pointer storing full pointer");
    expect_success (dt_dyn_rel_ptr_is_full(ptr), "check relative pointer state");

    return 0;
}
