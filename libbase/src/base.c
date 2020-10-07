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
#include <time.h>
#include <unistd.h>
#include <stdint.h>
#include <sys/syscall.h>
#include <sys/select.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <string.h>
#include <errno.h>
#include <stdlib.h>
#include <locale.h>
#include <sys/ioctl.h>
#include <termios.h>
#include <stdarg.h>
#include <signal.h>

#define DT_REL_PNT
typedef union
{
    struct
    {
        uint64_t offset:62;
        uint64_t is_relative:1;
        uint64_t is_negative:1;
    };
    void * pointer;
} __attribute__((packed)) dt_dyn_rel_ptr_t;

#include "devtank/base.h"
#include "devtank/log.h"

#include "build_config.h"


static bool _library_is_ready = false;


dt_usecs get_current_us(void)
{
    struct timespec ts;

    if (clock_gettime(CLOCK_REALTIME, &ts))
    {
        fatal_error("Failed to get the realtime of the clock.");
        return (uint64_t)-1;
    }

    return (int64_t)(ts.tv_nsec / 1000LL) + (int64_t)(ts.tv_sec * USEC_SECOND);
}

int str_print_time(char* buffer, size_t buffer_size, dt_usecs usecs)
{
    time_t secs     = usecs / USEC_SECOND;
    size_t n = strftime (buffer, buffer_size, "%d/%m %T", localtime(&secs));
    buffer[n] = 0;
    n += dt_snprintf0(buffer + n, buffer_size - n, ".%06u", (unsigned int)((usecs % USEC_SECOND)));
    return n;
}


int str_print_duration(char* buffer, size_t buffer_size, dt_usecs usecs)
{
    int64_t secs     = usecs / USEC_SECOND;
    size_t n = 0;
    if (llabs(secs) > 60)
    {
        int64_t minutes = secs / 60;
        secs %= 60;
        if (llabs(minutes) > 60)
        {
            int64_t hours = minutes / 60;
            minutes %= 60;
            if (llabs(hours) > 24)
            {
                int64_t days = hours / 24;
                hours %= 24;
                n += dt_snprintf0(buffer + n, buffer_size - n, "%"PRIi64"d ", days);
            }
            n += dt_snprintf0(buffer + n, buffer_size - n, "%"PRIi64":", hours);
        }
        n += dt_snprintf0(buffer + n, buffer_size - n, "%"PRIi64":", minutes);
    }
    n += dt_snprintf0(buffer + n, buffer_size - n, "%"PRIi64".%06u", secs, (unsigned int)((usecs % USEC_SECOND)));
    return n;
}


uint32_t get_thread_id(void)
{
    return syscall(SYS_gettid);
}


void get_runtime_version(uint32_t* major, uint32_t* minor, uint32_t* revision)
{
    if (major)
        *major = LIBDEVTANK_VERSION_MAJOR;
    if (minor)
        *minor = LIBDEVTANK_VERSION_MINOR;
    if (revision)
        *revision = LIBDEVTANK_VERSION_REVISION;
}


void dt_get_build_info(const char** build_time, const char** git_commit)
{
    if (build_time)
        *build_time = build_date;
    if (git_commit)
        *git_commit = build_git_commit;

    info_msg("build git commit: \"%s\", build date: \"%s\"", build_git_commit, build_date);
}


int  get_fd_peek(int fd)
{
    int peek = 0;
    if (ioctl(fd, FIONREAD, &peek) < 0)
        return -1;
    return peek;
}


int wait_for_fd(int fd, dt_usecs usecs)
{
    fd_set rfds;
    struct timeval tv;

    FD_ZERO(&rfds);
    FD_SET(fd, &rfds);

    tv.tv_sec = usecs / USEC_SECOND;
    tv.tv_usec = usecs % USEC_SECOND;

    return select(fd + 1, &rfds, NULL, NULL, &tv);
}


bool set_fd_blocking(int fd, bool enable)
{
    int r = fcntl(fd, F_GETFL);
    if (r < 0)
        return false;
    r = fcntl( fd, F_SETFL,
             (enable)?(r | O_NONBLOCK):(r ^ O_NONBLOCK));
    return (r >= 0);
}


bool does_file_exists(const char* filename)
{
    struct stat s;
    return !stat(filename, &s);
}


bool safe_read(int fd, void* data, size_t len, dt_usecs max_usecs)
{
    dt_usecs now = get_current_us();
    size_t read_bytes = 0;
    while(read_bytes < len)
    {
        int r = read(fd, ((uint8_t*)data) + read_bytes, len - read_bytes);
        if (r == -1)
        {
            if (errno == EAGAIN)
                continue;
            warning_msg("Safe read failed : %s", strerror(errno));
            return false;
        }
        else read_bytes += r;
        if (read_bytes != len && (get_current_us() - now) > max_usecs)
        {
            warning_msg("Safe read timed out.");
            return false;
        }
    }
    return true;
}


bool safe_write(int fd, const void* data, size_t len, dt_usecs max_usecs)
{
    dt_usecs now = get_current_us();
    size_t written = 0;
    while(written < len)
    {
        int r = write(fd, ((const uint8_t*)data) + written, len - written);
        if (r == -1)
        {
            if (errno == EAGAIN)
                continue;
            warning_msg("Safe write failed : %s", strerror(errno));
            return false;
        }
        else written += r;
        if (written != len && (get_current_us() - now) > max_usecs)
        {
            warning_msg("Safe write timed out.");
            return false;
        }
    }
    return true;
}


bool fd_sync(int fd)
{
    if (isatty(fd))
    {
        if (!tcdrain(fd))
            return true;
    }
    else if (!syncfs(fd))
        return true;
    warning_msg("Failed to sync fd:%i : %s", fd, strerror(errno));
    return false;
}


unsigned dt_vsnprintf0(char* buffer, size_t len, const char* fmt, va_list ap)
{
    int r = vsnprintf(buffer, len, fmt, ap);
    if (r < 0)
        return 0;
    return (r <= (int)len)?r:(int)len;
}


unsigned dt_snprintf0(char* buffer, size_t len, const char* fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    int r = dt_vsnprintf0(buffer, len, fmt, ap);
    va_end(ap);
    return r;
}


void fatal_signal(int sig)
{
    fatal_error("Fatal Signal Caught : %i \"%s\"", sig, strsignal(sig));
}


void usr_signal(int sig)
{
    bool logging = (sig == SIGUSR1);
    enable_warning_msgs(true);
    enable_info_msgs(logging);
}


void devtank_init()
{
    if (setlocale(LC_ALL, "") == NULL)
        warning_msg("Failed to setup locale");

    signal(SIGTERM, fatal_signal);
    signal(SIGINT,  fatal_signal);
    signal(SIGABRT, fatal_signal);
    signal(SIGILL,  fatal_signal);
    signal(SIGKILL, fatal_signal);
    signal(SIGSEGV, fatal_signal);
    signal(SIGQUIT, fatal_signal);
    signal(SIGUSR1, usr_signal);
    signal(SIGUSR2, usr_signal);

    _library_is_ready = true;
}


bool devtank_ready()
{
    return _library_is_ready;
}


void devtank_shutdown()
{
    _library_is_ready = false;
}


void dt_sleep(dt_usecs usecs)
{
    usleep(usecs);
}


void safe_free(void* p)
{
    if (p)
        free(p);
}


bool   dt_dyn_rel_ptr_is_full(const dt_dyn_rel_ptr_t * rel_p)
{
    if (!rel_p)
        return false;
    return !(rel_p->is_relative);
}


void * dt_dyn_rel_ptr_get(const dt_dyn_rel_ptr_t * rel_p)
{
    if (!rel_p)
        return NULL;
    if (rel_p->is_relative)
    {
        intptr_t ptr = rel_p->offset;

        if (!ptr)
            return NULL;

        if (rel_p->is_negative)
            ptr *= -1;

        return (void*)(((const uint8_t*)rel_p) + ptr);
    }
    return rel_p->pointer;
}


void   dt_dyn_rel_ptr_set(dt_dyn_rel_ptr_t * rel_p, const void * p)
{
    if (!rel_p)
        return;
    rel_p->pointer = (void*)p;
}


void   dt_dyn_rel_ptr_set_rel(dt_dyn_rel_ptr_t * rel_p, const void * p)
{
    if (!rel_p)
        return;

    intptr_t offset = (p)?((intptr_t)p) - ((intptr_t)rel_p):0;

    rel_p->is_relative = 1;
    if (offset < 0)
    {
        rel_p->is_negative = 1;
        offset *= -1;
    }
    rel_p->offset = offset;
}


void   dt_dyn_rel_ptr_free(dt_dyn_rel_ptr_t * rel_p)
{
    if (!rel_p)
        return;
    if (rel_p->is_relative)
        return;
    safe_free(rel_p->pointer);
    rel_p->pointer = NULL;
}


void dt_data_packet_str_set(dt_data_packet_t * packet, const char * str)
{
    if (!packet)
        return;

    packet->ptr = str;
    packet->size = strlen(str)+1;
}


uint64_t dt_hash_64(dt_data_packet_t * datas, unsigned count)
{
    uint64_t hash = 7;
    for (unsigned n = 0; n < count; n++)
    {
        const uint8_t * data = (const uint8_t *)datas[n].ptr;
        if (!data)
            continue;
        const unsigned  size = datas[n].size;
        for (unsigned i = 0; i < size; i++)
            hash = hash*31 + data[i];
    }
    return hash;
}
