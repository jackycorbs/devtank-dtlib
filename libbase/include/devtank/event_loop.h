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
#ifndef __DT_EVENT_LOOP__
#define __DT_EVENT_LOOP__

#include "devtank/base.h"

typedef struct dt_loop_t dt_loop_t;
typedef struct dt_loop_event_t dt_loop_event_t;

typedef struct
{
    uint8_t on_in;
    uint8_t on_out;
    uint8_t on_err;
    uint8_t on_hup;
} dt_loop_fd_code_t;

#define dt_loop_std_in_code (dt_loop_fd_code_t){.on_in = true, .on_hup = true, .on_err = true}

typedef void     (*dt_loop_destroy_cb)(dt_loop_t * loop);
typedef bool     (*dt_loop_add_fd_cb)(dt_loop_t * loop, int fd, dt_loop_fd_code_t code, dt_loop_event_t * event);
typedef bool     (*dt_loop_remove_fd_cb)(dt_loop_t * loop, int fd);
typedef uint64_t (*dt_loop_add_timer_cb)(dt_loop_t * loop, dt_usecs usecs, dt_loop_event_t * event);
typedef bool     (*dt_loop_remove_timer_cb)(dt_loop_t * loop, uint64_t timer_id);
typedef uint64_t (*dt_loop_add_trigger_cb)(dt_loop_t * loop, dt_loop_event_t * event);
typedef bool     (*dt_loop_remove_trigger_cb)(dt_loop_t * loop, uint64_t trigger_id);
typedef bool     (*dt_loop_fire_trigger_cb)(dt_loop_t * loop, uint64_t trigger_id);

typedef bool     (*dt_loop_wait_cb)(dt_loop_t * loop, dt_usecs usecs, bool stop);

struct dt_loop_t
{
    dt_loop_destroy_cb        destroy;

    dt_loop_add_fd_cb         add_fd;
    dt_loop_remove_fd_cb      remove_fd;

    dt_loop_add_timer_cb      add_timer;
    dt_loop_remove_timer_cb   remove_timer;

    dt_loop_add_trigger_cb    add_trigger;
    dt_loop_remove_trigger_cb remove_trigger;
    dt_loop_fire_trigger_cb   fire_triffer;

    dt_loop_wait_cb           wait;
};

typedef bool (*dt_loop_event_cb)(dt_loop_event_t *event, dt_loop_fd_code_t code);

struct dt_loop_event_t
{
    dt_loop_event_cb cb;
};


inline static void     dt_loop_destroy(dt_loop_t * loop)                                 { if (loop) loop->destroy(loop); }
inline static bool     dt_loop_add_fd(dt_loop_t * loop, int fd, dt_loop_fd_code_t code,
                                      dt_loop_event_t * event)                           { return (loop)?loop->add_fd(loop, fd, code, event):false; }
inline static bool     dt_loop_remove_fd(dt_loop_t * loop, int fd)                       { return (loop)?loop->remove_fd(loop, fd):false; }

inline static uint64_t dt_loop_add_timer(dt_loop_t * loop, dt_usecs usecs,
                                     dt_loop_event_t * event)                            { return (loop)?loop->add_timer(loop, usecs, event):0; }
inline static bool     dt_loop_remove_timer(dt_loop_t * loop, uint64_t timer_id)         { return (loop)?loop->remove_timer(loop, timer_id): false; }

inline static uint64_t dt_loop_add_trigger(dt_loop_t * loop, dt_loop_event_t * event)    { return (loop)?loop->add_trigger(loop, event):0; }
inline static bool     dt_loop_remove_trigger(dt_loop_t * loop, uint64_t trigger_id)     { return (loop)?loop->remove_trigger(loop, trigger_id): false; }
inline static bool     dt_loop_fire_trigger(dt_loop_t * loop, uint64_t trigger_id)       { return (loop)?loop->fire_triffer(loop, trigger_id): false; }

inline static bool     dt_loop_wait(dt_loop_t * loop, dt_usecs usecs, bool stop)         { return (loop)?loop->wait(loop, usecs, stop):false; }


extern dt_loop_t * dt_loop_create_default();


typedef struct dt_file_watch_event_t dt_file_watch_event_t;
typedef bool (*dt_file_watch_event_cb)(dt_file_watch_event_t * event, int fd);

struct dt_file_watch_event_t
{
    dt_file_watch_event_cb cb;
};


typedef struct dt_files_watcher_t dt_files_watcher_t;
typedef struct dt_file_watch_t dt_file_watch_t;

extern dt_files_watcher_t*    dt_loop_open_files_watcher(dt_loop_t * loop, unsigned max_watches);
extern void                   dt_files_watcher_close(dt_files_watcher_t * watcher);

extern dt_file_watch_t *      dt_files_watcher_open_file(dt_files_watcher_t * watcher, const char * filename, dt_file_watch_event_t * event);
extern int                    dt_file_watch_get_fd(dt_file_watch_t * file_watch);

extern void                   dt_file_watch_close(dt_file_watch_t * file_watch);



#endif //__DT_EVENT_LOOP__
