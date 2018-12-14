/*
 * Copyright (c) 2018 DevTank Ltd
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
#include <unistd.h>
#include <stdlib.h>
#include "devtank/event_loop.h"
#include "tests.h"

static bool     in_called    = false;
static bool     out_called   = false;

static dt_usecs event_time = 0;

static unsigned triggered_count = 0;


static int in_fd = -1;


static bool in_cb(dt_loop_event_t *event, dt_loop_fd_code_t code)
{
    if (code.on_in)
    {
        int byte_num = get_fd_peek(in_fd);
        in_called = true;

        char bytes[byte_num];

        expect_success(safe_read(in_fd, bytes, byte_num, USEC_SECOND), "read pipe.");
    }
    return true;
}

static bool out_cb(dt_loop_event_t *event, dt_loop_fd_code_t code)
{
    if (code.on_out)
        out_called = true;
    return true;
}


static bool time_cb(dt_loop_event_t *event, dt_loop_fd_code_t code)
{
    if (code.on_in)
        event_time = get_current_us();
    return true;
}


static bool trigger_cb(dt_loop_event_t *event, dt_loop_fd_code_t code)
{
    if (code.on_in)
        triggered_count++;
    return true;
}


int main(int argc, char* argv[])
{
    dt_loop_t * loop = dt_loop_create_default();
    expect_success(loop, "create event loop.");

    int fds[2];

    expect_success(!pipe(fds), "create pipes.");

    in_fd = fds[0];

    dt_loop_event_t in_event = {.cb = in_cb };
    dt_loop_event_t out_event = {.cb = out_cb };

    expect_success(dt_loop_add_fd(loop, fds[0], (dt_loop_fd_code_t){.on_in = true}, &in_event), "add in pipe");
    expect_success(dt_loop_add_fd(loop, fds[1], (dt_loop_fd_code_t){.on_out = true}, &out_event), "add out pipe");

    dprintf(fds[1], "here\n");

    expect_success(dt_loop_wait(loop, USEC_SECOND / 4, false), "wait on loop");

    expect_success(in_called, "check in was called.");
    expect_success(out_called, "check out was called.");

    expect_success(dt_loop_remove_fd(loop, fds[0]), "remove in pipe");
    expect_success(dt_loop_remove_fd(loop, fds[1]), "remove out pipe");

    close(fds[1]);
    close(fds[0]);

    dt_loop_event_t time_event = {.cb = time_cb };

    dt_usecs start_time = get_current_us();
    uint64_t timer_id = dt_loop_add_timer(loop, USEC_SECOND / 4, &time_event);
    expect_success(timer_id, "timer added.");

    expect_success(dt_loop_wait(loop, USEC_SECOND / 2, true), "wait on loop");

    dt_usecs delta_time = event_time - start_time;

    output_normal("useconds delta for 0.25 of a second : %"PRIi64, delta_time);

    expect_success(delta_time > (USEC_SECOND / 4) &&
                   delta_time < ((USEC_SECOND / 4) + (USEC_SECOND / 40)),
                    "time event check");

    expect_success(dt_loop_remove_timer(loop, timer_id), "remove timer.");

    dt_loop_event_t trigger_event = {.cb = trigger_cb };

    uint64_t trigger_id = dt_loop_add_trigger(loop, &trigger_event);

    expect_success(trigger_id, "add trigger to loop.");
    expect_success(dt_loop_fire_trigger(loop, trigger_id), "fire trigger.");
    expect_success(dt_loop_fire_trigger(loop, trigger_id), "fire trigger.");

    expect_success(dt_loop_wait(loop, USEC_SECOND / 2, true), "wait on loop");
    expect_success(dt_loop_wait(loop, USEC_SECOND / 2, true), "wait on loop");

    expect_success(dt_loop_remove_trigger(loop, trigger_id), "remove trigger from loop.");
    expect_success(triggered_count == 2, "triggered count check.");

    dt_loop_destroy(loop);

    return EXIT_SUCCESS;
}
