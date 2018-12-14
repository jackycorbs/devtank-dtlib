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
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <fcntl.h>
#include <errno.h>
#include <string.h>

#include <sys/epoll.h>
#include <sys/timerfd.h>
#include <sys/eventfd.h>
#include <sys/inotify.h>

#include "devtank/log.h"
#include "devtank/buffer.h"
#include "devtank/event_loop.h"


#define VIRTUAL_FILE_TIMEOUT (USEC_SECOND / 10)


typedef struct
{
    dt_loop_t   base;
    int         efd;
    unsigned    count;
    dt_buffer_t slots;
    unsigned    slots_count;
} _epoll_event_loop_t;


typedef enum
{
    _EVENT_SLOT_FREE,
    _EVENT_SLOT_FD,
    _EVENT_SLOT_TIMER,
    _EVENT_SLOT_TRIGGER
} _event_slot_type_t;



typedef struct
{
    _event_slot_type_t type;
    int                fd;
    dt_loop_event_t * event;
} __attribute__((packed)) _event_slot_t;



static bool _epoll_event_loop_add(_epoll_event_loop_t * loop, int fd, dt_loop_fd_code_t code, dt_loop_event_t * dt_event, _event_slot_type_t type)
{
    struct epoll_event event = {0};

    _event_slot_t* slots = (_event_slot_t*)dt_buffer_get_data(&loop->slots);

    bool free_found = false;

    for(unsigned n = 0; n < loop->slots_count; n++)
    {
        _event_slot_t * slot = &slots[n];
        if (slot->type == _EVENT_SLOT_FREE)
        {
            event.data.u32 = n;
            slot->type  = type;
            slot->fd    = fd;
            slot->event = dt_event;
            free_found = true;
        }
    }

    event.events = 0;

    if (!free_found)
    {
        _event_slot_t slot = {.type = type, .fd = fd, .event = dt_event};
        event.data.u32 = loop->slots_count;
        DT_RETURN_ON_FAIL(dt_buffer_append(&loop->slots, &slot, sizeof(slot)),
                          "Failed to add event to buffer.", false);
        loop->slots_count++;
    }

    if (code.on_in)
        event.events |= EPOLLIN;
    if (code.on_out)
        event.events |= EPOLLOUT;
    if (code.on_err)
        event.events |= EPOLLERR;
    if (code.on_hup)
        event.events |= EPOLLHUP | EPOLLRDHUP;

    if (!epoll_ctl(loop->efd, EPOLL_CTL_ADD, fd, &event))
    {
        loop->count++;
        return true;
    }
    return false;
}


static void _epoll_event_loop_destroy(_epoll_event_loop_t * loop)
{
    DT_RETURN_ON_FAIL(loop, "No event loop given",);
    if (loop->efd > 0)
        close(loop->efd);
    dt_buffer_clear(&loop->slots);
    free(loop);
}


static bool _epoll_event_loop_add_fd(_epoll_event_loop_t * loop, int fd, dt_loop_fd_code_t code, dt_loop_event_t * dt_event)
{
    DT_RETURN_ON_FAIL(dt_event, "No event given for fd in event loop.", false);

    if (_epoll_event_loop_add(loop, fd, code, dt_event, _EVENT_SLOT_FD))
    {
        info_msg("Added fd:%i to event loop.", fd);
        return true;
    }
    error_msg("Failed to add fd:%i to event loop.", fd);
    return false;
}


static bool _epoll_event_loop_remove_fd(_epoll_event_loop_t * loop, int fd)
{
    _event_slot_t* slots = (_event_slot_t*)dt_buffer_get_data(&loop->slots);

    for(unsigned n = 0; n < loop->slots_count; n++)
    {
        _event_slot_t * slot = &slots[n];
        if (slot->fd == fd)
        {
            slot->type = _EVENT_SLOT_FREE;
            break;
        }
    }

    if (epoll_ctl(loop->efd, EPOLL_CTL_DEL, fd, NULL))
    {
        warning_msg("Failed to remove from event loop.... : %s", strerror(errno));
        return false;
    }
    loop->count--;
    return true;
}


static uint64_t _epoll_event_loop_add_timer(_epoll_event_loop_t * loop, dt_usecs usecs, dt_loop_event_t * dt_event)
{
    DT_RETURN_ON_FAIL(dt_event, "No event given for fd in event loop.", false);

    int fd = timerfd_create(CLOCK_MONOTONIC, TFD_CLOEXEC);

    if (fd < 0)
    {
        error_msg("Failed to create timer file descriptor : %s", strerror(errno));
        return 0;
    }

    struct itimerspec timerspec = {0};

    timerspec.it_value.tv_sec  = usecs / USEC_SECOND;
    timerspec.it_value.tv_nsec = (usecs % USEC_SECOND) * 1000;
    timerspec.it_interval      = timerspec.it_value;

    if (timerfd_settime(fd, 0, &timerspec, NULL))
    {
        error_msg("Failed set time of timer file descriptor: %s", strerror(errno));
        close(fd);
        return 0;
    }

    if (!_epoll_event_loop_add(loop, fd, dt_loop_std_in_code, dt_event, _EVENT_SLOT_TIMER))
    {
        close(fd);
        return 0;
    }

    info_msg("Added timer event %i to event loop.", fd);

    return (uint64_t)fd;
}


static bool     _epoll_event_loop_remove_timer(_epoll_event_loop_t * loop, uint64_t timer_id)
{
    int fd = (int)timer_id;
    DT_RETURN_ON_FAIL(_epoll_event_loop_remove_fd(loop, fd), "Failed to remove from event loop.", false);
    close(fd);
    return true;
}


static uint64_t _epoll_event_add_trigger_cb(_epoll_event_loop_t * loop, dt_loop_event_t * event)
{
    DT_RETURN_ON_FAIL(event, "No event for trigger given.", 0);
    int fd = eventfd(0, EFD_SEMAPHORE);
    if (fd < 0)
    {
        error_msg("Failed to create event file descriptor : %s", strerror(errno));
        return 0;
    }

    if (!_epoll_event_loop_add(loop, fd, dt_loop_std_in_code, event, _EVENT_SLOT_TRIGGER))
    {
        close(fd);
        return 0;
    }

    info_msg("Added trigger event %i to event loop.", fd);

    return (uint64_t)fd;
}


static bool     _epoll_event_remove_trigger_cb(_epoll_event_loop_t * loop, uint64_t trigger_id)
{
    int fd = (int)trigger_id;
    DT_RETURN_ON_FAIL(_epoll_event_loop_remove_fd(loop, fd), "Failed to remove trigger from event loop.", false);
    close(fd);
    return true;
}


static bool     _epoll_event_fire_trigger_cb(__attribute__((unused)) _epoll_event_loop_t * loop, uint64_t trigger_id)
{
    int fd = (int)trigger_id;
    uint64_t instance = 1;
    if (!safe_write(fd, &instance, sizeof(instance), VIRTUAL_FILE_TIMEOUT))
    {
        error_msg("Failed to fire trigger %i", fd);
        return false;
    }
    return true;
}


static bool _epoll_event_loop_wait(_epoll_event_loop_t * loop, dt_usecs usecs, bool stop)
{
    if (!loop->count)
    {
        if (!stop)
            dt_sleep(usecs);
        return true;
    }

    struct epoll_event events[loop->count];

    dt_usecs now = get_current_us();
    dt_usecs start_time = now;

    do
    {
        int n = epoll_wait (loop->efd, events, loop->count, (usecs - (start_time - now))/ 1000);

        if (n < 0)
        {
            if (errno != EINTR)
                error_msg("Error on epoll : %s", strerror(errno));
            return false;
        }

        for (int i = 0; i < n; i++)
        {
            struct epoll_event * event = &events[i];

            _event_slot_t * slots = (_event_slot_t*)dt_buffer_get_data(&loop->slots);
            _event_slot_t * slot = &slots[event->data.u32];

            switch(slot->type)
            {
                case _EVENT_SLOT_FD: break;
                case _EVENT_SLOT_TIMER:
                case _EVENT_SLOT_TRIGGER:
                {
                    uint64_t instances = 0;
                    if (!safe_read(slot->fd, &instances, sizeof(instances), VIRTUAL_FILE_TIMEOUT))
                        error_msg("Failed to read timer or trigger file descriptor.");
                    break;
                }
                default:
                    error_msg("Slot used in event loop is invalid.");
            }

            dt_loop_fd_code_t code = {.on_in = (event->events & EPOLLIN),
                                      .on_out = (event->events & EPOLLOUT),
                                      .on_err = (event->events & EPOLLERR),
                                      .on_hup = (event->events & EPOLLHUP) || (event->events & EPOLLRDHUP)};

            if (!slot->event->cb(slot->event, code))
            {
                info_msg("Early exit of loop.");
                return false;
            }
        }

        if (stop)
            break;

        now = get_current_us();
    }
    while(now < (start_time + usecs));

    return true;
}



dt_loop_t * dt_loop_create_default()
{
    _epoll_event_loop_t * r = malloc(sizeof(_epoll_event_loop_t));
    DT_RETURN_ON_FAIL(r, "Allocation for default event loop failed.", NULL);

    memset(r, 0, sizeof(_epoll_event_loop_t));

    r->base.destroy      = (dt_loop_destroy_cb)_epoll_event_loop_destroy;

    r->base.add_fd       = (dt_loop_add_fd_cb)_epoll_event_loop_add_fd;
    r->base.remove_fd    = (dt_loop_remove_fd_cb)_epoll_event_loop_remove_fd;

    r->base.add_timer    = (dt_loop_add_timer_cb)_epoll_event_loop_add_timer;
    r->base.remove_timer = (dt_loop_remove_timer_cb)_epoll_event_loop_remove_timer;

    r->base.add_trigger    = (dt_loop_add_trigger_cb)_epoll_event_add_trigger_cb;
    r->base.remove_trigger = (dt_loop_remove_trigger_cb)_epoll_event_remove_trigger_cb;
    r->base.fire_triffer   = (dt_loop_fire_trigger_cb)_epoll_event_fire_trigger_cb;

    r->base.wait         = (dt_loop_wait_cb)_epoll_event_loop_wait;
    r->count = 0;

    if (!dt_buffer_init(&r->slots, 1024))
    {
        error_msg("Failed create buffer for event loop.");
        _epoll_event_loop_destroy(r);
        return NULL;
    }

    r->efd = epoll_create1(0);
    if (r->efd < 0)
    {
        error_msg("Failed to create epoll for event loop : %s", strerror(errno));
        _epoll_event_loop_destroy(r);
        return NULL;
    }
    return (dt_loop_t*)r;
}


struct dt_file_watch_t
{
    dt_loop_event_t         base;
    dt_files_watcher_t *    watcher;
    dt_file_watch_event_t * event;
    int                     file_fd;
    int                     file_wd;
    uint64_t                file_timer_id;
};



struct dt_files_watcher_t
{
    dt_loop_event_t      event;
    int                  inotify_fd;
    dt_loop_t          * loop;
    unsigned             max_watches;
    dt_file_watch_t      watches[1];
};


static bool dt_loop_open_files_watcher_event_cb(dt_files_watcher_t * watcher, dt_loop_fd_code_t code)
{
    if (code.on_in)
    {
        int bytes = get_fd_peek(watcher->inotify_fd);
        if (bytes > 0)
        {
            char buffer[bytes];
            DT_RETURN_ON_FAIL(safe_read(watcher->inotify_fd, buffer, bytes, USEC_SECOND / 4),
                              "Failed to read inotify.", true);
            int pos = 0;
            while (pos < bytes)
            {
                struct inotify_event *event = (struct inotify_event*)(buffer + pos);

                for(unsigned n = 0; n < watcher->max_watches; n++)
                {
                    dt_file_watch_t * watch = &watcher->watches[n];
                    if (watch->event && watch->file_wd == event->wd)
                        watch->event->cb(watch->event, watch->file_fd);
                }

                pos = pos + sizeof(struct inotify_event) + event->len;
            }
        }
    }

    return true;
}


static bool _dt_file_watch_event_cb(dt_file_watch_t * watch, dt_loop_fd_code_t code)
{
    if (code.on_in)
        if (get_fd_peek(watch->file_fd) > 0)
            watch->event->cb(watch->event, watch->file_fd);

    return true;
}



dt_files_watcher_t*    dt_loop_open_files_watcher(dt_loop_t * loop, unsigned max_watches)
{
    DT_RETURN_ON_FAIL(loop, "No event loop given", 0);
    DT_RETURN_ON_FAIL(max_watches, "Can't have file watcher of max watches 0.", 0);

    int fd = inotify_init1(IN_CLOEXEC);
    DT_RETURN_ON_FAIL(fd > 0, "Event loop failed to create watcher.", 0);

    unsigned size = sizeof(dt_files_watcher_t) + (sizeof(dt_file_watch_t) * max_watches);

    dt_files_watcher_t * r = (dt_files_watcher_t*)malloc(size);
    if (!r)
    {
        error_msg("Failed to allocate new dt_files_watcher_t.");
        close(fd);
        return NULL;
    }

    memset(r, 0, size);

    r->max_watches = max_watches;
    r->event.cb = (dt_loop_event_cb)dt_loop_open_files_watcher_event_cb;

    if (!dt_loop_add_fd(loop, fd, dt_loop_std_in_code, &r->event))
    {
        error_msg("Failed to setup new dt_files_watcher_t.");
        close(fd);
        free(r);
        return NULL;
    }

    for(unsigned n = 0; n < max_watches; n++)
    {
        r->watches[n].event = NULL;
        r->watches[n].watcher = r;
        r->watches[n].base.cb = (dt_loop_event_cb)_dt_file_watch_event_cb;
    }

    r->inotify_fd = fd;
    r->loop = loop;
    return r;
}


void                   dt_files_watcher_close(dt_files_watcher_t * watcher)
{
    DT_RETURN_ON_FAIL(watcher, "No files watcher given", );
    DT_WARN_ON_FAIL(dt_loop_remove_fd(watcher->loop, watcher->inotify_fd),
                    "Failed to unwatch closing watcher.");
    close(watcher->inotify_fd);
    free(watcher);
}


dt_file_watch_t *      dt_files_watcher_open_file(dt_files_watcher_t * watcher, const char * filename, dt_file_watch_event_t * event)
{
    DT_RETURN_ON_FAIL(watcher, "No files watcher given", NULL);
    DT_RETURN_ON_FAIL(filename, "No file name for watcher to watch given.", NULL);
    DT_RETURN_ON_FAIL(event, "No event on file watch to called.", NULL);

    dt_file_watch_t * r = NULL;

    for(unsigned n = 0; n < watcher->max_watches; n++)
        if (!watcher->watches[n].event)
            r = &watcher->watches[n];

    DT_RETURN_ON_FAIL(r, "Watcher has no spare slot to watch more.", NULL);

    r->file_fd = open(filename, O_RDONLY);
    if (r->file_fd < 0)
    {
        error_msg("Failed to open file \"%s\" for watching : %s", filename, strerror(errno));
        return NULL;
    }

    r->file_timer_id = dt_loop_add_timer(watcher->loop, USEC_SECOND / 10, &r->base);
    if (!r->file_timer_id)
    {
        close(r->file_fd);
        error_msg("Failed set timer for watching file \"%s\"", filename);
        return NULL;
    }

    r->file_wd = inotify_add_watch(watcher->inotify_fd, filename, IN_MODIFY);
    if (r->file_wd < 0)
    {
        error_msg("Failed to create watch for file \"%s\" : %s", filename, strerror(errno));
        dt_loop_remove_timer(watcher->loop, r->file_timer_id);
        close(r->file_fd);
        return NULL;
    }

    info_msg("Watcher watching \"%s\"", filename);
    r->event = event;
    return r;
}


int                    dt_file_watch_get_fd(dt_file_watch_t * file_watch)
{
    DT_RETURN_ON_FAIL(file_watch, "No file watch given", 0);
    return file_watch->file_fd;
}


void                   dt_file_watch_close(dt_file_watch_t * file_watch)
{
    DT_RETURN_ON_FAIL(file_watch, "No file watch given", );
    DT_RETURN_ON_FAIL(file_watch->event, "File watch already not active.", );

    dt_files_watcher_t * watcher = file_watch->watcher;

    DT_WARN_ON_FAIL_ERRNO(!inotify_rm_watch(watcher->inotify_fd, file_watch->file_wd), "Failed to remove watch from inotify.");
    DT_WARN_ON_FAIL(dt_loop_remove_timer(watcher->loop, file_watch->file_timer_id), "Failed to remove watch timer.");

    if (get_fd_peek(file_watch->file_fd) > 0)
        file_watch->event->cb(file_watch->event, file_watch->file_fd);

    close(file_watch->file_fd);
    file_watch->event = NULL;
}
