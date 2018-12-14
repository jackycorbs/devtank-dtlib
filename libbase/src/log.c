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
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <ctype.h>
#include <time.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include "devtank/base.h"
#include "devtank/log.h"

#define MAX_LOG_LINE 1024
#define LOG_WRITE_MAX_TIME (USEC_SECOND/4)

static bool print_info_msgs = false;
static bool print_warning_msgs = true;

#define KRED  "\x1B[31m"
#define KGRN  "\x1B[32m"
#define KYEL  "\x1B[33m"
#define KBLU  "\x1B[34m"
#define KMAG  "\x1B[35m"
#define KCYN  "\x1B[36m"
#define KWHT  "\x1B[37m"
#define KDFT  "\x1B[39m"

#define ERROR_COLOR   31
#define WARNING_COLOR 33
#define INFO_COLOR    39

#define ERROR_PREFIX "ERROR"
#define WARN_PREFIX  "WARN"
#define INFO_PREFIX  "INFO"


static int log_fd = STDERR_FILENO;
static int out_fd = STDOUT_FILENO;

static __thread char buffer[MAX_LOG_LINE];


static size_t log_line_start(const char* prefix, uint8_t color)
{
    size_t  r = str_print_time(buffer, MAX_LOG_LINE, get_current_us());
    r += dt_snprintf0(&buffer[r], MAX_LOG_LINE-r, " [%"PRIu32"] %s: ", get_thread_id(), prefix);
    if (isatty(log_fd))
        r += dt_snprintf0(&buffer[r], MAX_LOG_LINE-r, "\x1b[%um", color);
    return r;
}


// Log requires own safe write because it can't log on write fails.
static void _log_safe_write(int fd, const void* data, size_t len)
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
            return;
        }
        else written += r;
        if (written != len && (get_current_us() - now) > LOG_WRITE_MAX_TIME)
            return;

    }
}


static void log_line_finish(size_t r)
{
    if (isatty(log_fd))
    {
        if (r >= MAX_LOG_LINE - 1) //Maxxed out, make space for end of color and newline.
            r -= strlen(KDFT) + 2;
        r += dt_snprintf0(buffer + r, MAX_LOG_LINE - r, KDFT"\n");
    }
    else
    {
        if (r >= MAX_LOG_LINE - 1) //Maxxed out, make space for newline.
            r-=2;
        r += dt_snprintf0(buffer + r, MAX_LOG_LINE - r, "\n");
    }
    _log_safe_write(log_fd, buffer, r);
}


static void log_line(const char* prefix, const char* fmt, uint8_t color, va_list ap)
{
    size_t  r = log_line_start(prefix, color);
    r += dt_vsnprintf0(&buffer[r], MAX_LOG_LINE-r, fmt, ap);
    log_line_finish(r);
}


void fatal_error(const char* fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    log_line("ERROR", fmt, ERROR_COLOR, ap);
    va_end(ap);
    fd_sync(log_fd);
    exit(EXIT_FAILURE);
}


void error_msg(const char* fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    log_line(ERROR_PREFIX, fmt, ERROR_COLOR, ap);
    va_end(ap);
}


void warning_msg(const char* fmt, ...)
{
    if (!print_warning_msgs)
        return;
    va_list ap;
    va_start(ap, fmt);
    log_line(WARN_PREFIX, fmt, WARNING_COLOR, ap);
    va_end(ap);
}


void info_msg(const char* fmt, ...)
{
    if (!print_info_msgs)
        return;
    va_list ap;
    va_start(ap, fmt);
    log_line(INFO_PREFIX, fmt, INFO_COLOR, ap);
    va_end(ap);
}


void set_log_fd(int fd)
{
    log_fd = fd;
}

int get_log_fd()
{
    return log_fd;
}

void set_output_fd(int fd)
{
    out_fd = fd;
}

int get_output_fd()
{
    return out_fd;
}


void vlog_msg(log_msg_type_t type, const char* fmt, va_list ap)
{
    if (type == LOG_INFO && !print_info_msgs)
        return;
    const char* prefix;
    uint8_t color;
    switch(type)
    {
        case LOG_WARNING: prefix = WARN_PREFIX; color = WARNING_COLOR; break;
        case LOG_INFO: prefix = INFO_PREFIX; color = INFO_COLOR; break;
        default: prefix = ERROR_PREFIX; color = ERROR_COLOR;
    }
    log_line(prefix, fmt, color, ap);
}


void log_msg(log_msg_type_t type, const char* fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    vlog_msg(type, fmt, ap);
    va_end(ap);
}


void log_data_msg(log_msg_type_t type, const char* msg, const void* data, size_t data_size, ...)
{
    size_t  r;
    const uint8_t * raw = (const uint8_t*)data;

    switch(type)
    {
        case LOG_WARNING: r = log_line_start(WARN_PREFIX,  WARNING_COLOR);
            if (!print_warning_msgs)
                return;
            break;
        case LOG_INFO:    r = log_line_start(INFO_PREFIX,  INFO_COLOR);
            if (!print_info_msgs)
                return;
            break;
        default:          r = log_line_start(ERROR_PREFIX, ERROR_COLOR);
            break;
    }

    if (data_size > MAX_LOG_LINE)
        data_size = MAX_LOG_LINE;

    va_list ap;
    va_start(ap, data_size);
    r+= dt_vsnprintf0(buffer + r, MAX_LOG_LINE - r, msg, ap);
    va_end(ap);

    r += dt_snprintf0(buffer + r, MAX_LOG_LINE - r, ": (%zu) ", data_size);

    for(size_t i = 0; r < MAX_LOG_LINE && i < data_size; ++i)
        r += dt_snprintf0(buffer + r, MAX_LOG_LINE - r, "%02x,", raw[i]);

    if (r < MAX_LOG_LINE)
        buffer[r-1] = ' '; //Trim last comma

    r += dt_snprintf0(buffer + r, MAX_LOG_LINE - r, "\"");
    for(size_t i = 0; r < MAX_LOG_LINE && i < data_size; ++i)
        r += dt_snprintf0(buffer + r, MAX_LOG_LINE - r, "%c", isgraph(raw[i])?raw[i]:'.');

    r += dt_snprintf0(buffer + r, MAX_LOG_LINE - r, "\"");

    log_line_finish(r);
}


void log_usecs(const char* comment, dt_usecs usecs)
{
    if (!print_info_msgs)
        return;
    time_t secs     = usecs / USEC_SECOND;
    size_t  r = log_line_start(INFO_PREFIX, INFO_COLOR);

    r += dt_snprintf0(buffer + r, MAX_LOG_LINE - r, "%s:  ", comment);
    r += strftime(buffer + r,  MAX_LOG_LINE - r, "%X", localtime(&secs));
    r += dt_snprintf0(buffer + r, MAX_LOG_LINE - r, ".%06u (%"PRIi64")", (unsigned int)(usecs % USEC_SECOND), usecs);

    log_line_finish(r);
}


void enable_info_msgs(bool enable)
{
    print_info_msgs = enable;
}


void enable_warning_msgs(bool enable)
{
    print_warning_msgs = enable;
}


bool warning_msgs_is_enabled()
{
    return print_warning_msgs;
}


bool info_msgs_is_enabled()
{
    return print_info_msgs;
}


void output_good(const char* fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    voutput_good(fmt, ap);
    va_end(ap);
}


void output_normal(const char* fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    voutput_normal(fmt, ap);
    va_end(ap);
}


void output_bad(const char* fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    voutput_bad(fmt, ap);
    va_end(ap);
}


void voutput_good(const char* fmt, va_list ap)
{
    size_t r = 0;
    if (isatty(out_fd))
        r += dt_snprintf0(&buffer[r], sizeof(buffer)-r, KGRN);
    r += dt_vsnprintf0(&buffer[r], sizeof(buffer)-r, fmt, ap);
    if (isatty(out_fd))
        r += dt_snprintf0(&buffer[r], sizeof(buffer)-r, KDFT"\n");
    else
        r += dt_snprintf0(&buffer[r], sizeof(buffer)-r, "\n");
    _log_safe_write(out_fd, buffer, r);
}


void voutput_normal(const char* fmt, va_list ap)
{
    size_t r = 0;
    r += dt_vsnprintf0(&buffer[r], sizeof(buffer)-r, fmt, ap);
    r += dt_snprintf0(&buffer[r], sizeof(buffer)-r, "\n");
    _log_safe_write(out_fd, buffer, r);
}


void voutput_bad(const char* fmt, va_list ap)
{
    size_t r = 0;
    if (isatty(out_fd))
        r += dt_snprintf0(&buffer[r], sizeof(buffer)-r, KRED);
    r += dt_vsnprintf0(&buffer[r], sizeof(buffer)-r, fmt, ap);
    if (isatty(out_fd))
        r += dt_snprintf0(&buffer[r], sizeof(buffer)-r, KDFT"\n");
    else
        r += dt_snprintf0(&buffer[r], sizeof(buffer)-r, "\n");
    _log_safe_write(out_fd, buffer, r);
}
