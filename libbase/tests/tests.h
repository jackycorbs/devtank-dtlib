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
#ifndef __TESTS__
#define __TESTS__

#include "devtank/log.h"
#include <stdarg.h>

static inline void expect_fail(bool r, const char *test_name, ...)
{
    char buffer[512];

    va_list ap;
    va_start(ap, test_name);
    vsnprintf(buffer, sizeof(buffer), test_name, ap);
    va_end(ap);

    if (r)
    {
        output_bad(  "Success when fail expected    : %s", buffer);
        exit(EXIT_FAILURE);
    }
    else output_good("Fail when fail expected       : %s", buffer);
}


static inline void expect_success(bool r, const char *test_name, ...)
{
    char buffer[512];

    va_list ap;
    va_start(ap, test_name);
    vsnprintf(buffer, sizeof(buffer), test_name, ap);
    va_end(ap);

    if (!r)
    {
        output_bad(  "Fail when success expected    : %s", buffer);
        exit(EXIT_FAILURE);
    }
    else output_good("Success when success expected : %s", buffer);
}


#endif //__TESTS__
