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
#ifndef __DT_LOGGING__
#define __DT_LOGGING__

#include "devtank/base.h"
/**
 * \ingroup base
 * \defgroup logging
 * \brief Core logging functionality.
 * @{
 */
/** \brief printf style error message then abort program */
extern void fatal_error(const char* fmt, ...) PRINTF_FMT_CHECK( 1, 2);

/** \brief printf style error message */
extern void error_msg(const char* fmt, ...) PRINTF_FMT_CHECK( 1, 2);

/** \brief printf style warning message */
extern void warning_msg(const char* fmt, ...) PRINTF_FMT_CHECK( 1, 2);

/** \brief printf style information message */
extern void info_msg(const char* fmt, ...) PRINTF_FMT_CHECK( 1, 2);

/** \brief Change the file descriptor logging is written to. */
extern void set_log_fd(int fd);

/** \brief Get the file descriptor logging is written to. */
extern int  get_log_fd();


/** \brief Change the file descriptor output is written to. */
extern void set_output_fd(int fd);

/** \brief Get the file descriptor output is written to. */
extern int  get_output_fd();

/** \enum log_msg_type_t
 *  \brief Different log types avaiable.
 */
typedef enum
{
    LOG_INFO    = 1, ///< Log information message type
    LOG_WARNING = 2, ///< Log warning message type
    LOG_ERROR   = 3, ///< Log error message type
} log_msg_type_t;

/** \brief Dynamically types vprintf style logged message */
extern void vlog_msg(log_msg_type_t type, const char* fmt, va_list ap);

/** \brief  Dynamically types printf style logged message */
extern void log_msg(log_msg_type_t type, const char* fmt, ...) PRINTF_FMT_CHECK( 2, 3);

/** \brief Log data's bytes with a message.
    \param type Type of message to log
    \param msg Message to be logged, printf formatable.
    \param data Bytes to be appended to log message.
    \param data_size Number of bytes to be appended to log message.
    \param ... Any arguments in printf msg
*/
extern void log_data_msg(log_msg_type_t type, const char* msg, const void* data, size_t data_size, ...) PRINTF_FMT_CHECK(2,5);

/** \brief Log usecs time as local time to info */
extern void log_usecs(const char* comment, dt_usecs usecs);

/** \brief Disable warning messages. */
extern void enable_warning_msgs(bool enable);

/** \brief Disable info  messages. */
extern void enable_info_msgs(bool enable);

/** \brief Is warning messages enabled? */
extern bool warning_msgs_is_enabled();

/** \brief Is info messages enabled? */
extern bool info_msgs_is_enabled();

/** \brief printf style green message to output. */
extern void output_good(const char* fmt, ...) PRINTF_FMT_CHECK( 1, 2);

/** \brief vprintf style green message to output. */
extern void voutput_good(const char* fmt, va_list ap);

/** \brief printf style message to output. */
extern void output_normal(const char* fmt, ...) PRINTF_FMT_CHECK( 1, 2);

/** \brief vprintf style message to output. */
extern void voutput_normal(const char* fmt, va_list ap);

/** \brief printf style red message to output. */
extern void output_bad(const char* fmt, ...) PRINTF_FMT_CHECK( 1, 2);

/** \brief vprintf style red message to output. */
extern void voutput_bad(const char* fmt, va_list ap);

#define output_tested(_pass, _msg, ...)               \
{                                                     \
    if (_pass)                                        \
        output_good(_msg " - PASSED", __VA_ARGS__);   \
    else                                              \
        output_bad(_msg " - FAILED", __VA_ARGS__);    \
}


#define BYTE_BIN_FMT "0b%c%c%c%c%c%c%c%c"  ///< printf format string for printing byte as binary.

#define BYTE_BIN_ARG(_x) \
    (_x & 0x80)?'1':'0', \
    (_x & 0x40)?'1':'0', \
    (_x & 0x20)?'1':'0', \
    (_x & 0x10)?'1':'0', \
    (_x & 0x08)?'1':'0', \
    (_x & 0x04)?'1':'0', \
    (_x & 0x02)?'1':'0', \
    (_x & 0x01)?'1':'0'                    ///< printf argument for printing byte as binary.


#define DT_RETURN_ON_FAIL(_p, _msg, ...) { if (!(_p)) { error_msg(__FILE__ ":"STR(__LINE__)": " _msg); return __VA_ARGS__; } }
#define DT_RETURN_ON_FAIL_ERRNO(_p, _msg, ...) { if (!(_p)) { error_msg(__FILE__ ":"STR(__LINE__)": " _msg" : %s", strerror(errno)); return __VA_ARGS__; } }
#define DT_GOTO_ON_FAIL(_p, _msg, _label) { if (!(_p)) { error_msg(__FILE__ ":"STR(__LINE__)": " _msg); goto _label; } }
#define DT_GOTO_ON_FAIL_ERR(_p, _msg, _err, _label) { if (!(_p)) { error_msg(__FILE__ ":"STR(__LINE__)": " _msg": %s", _err); goto _label; } }
#define DT_RETURN_WARN_ON_FAIL(_p, _msg, ...) { if (!(_p)) { warning_msg(__FILE__ ":"STR(__LINE__)": " _msg); return __VA_ARGS__; } }
#define DT_WARN_ON_FAIL(_p, _msg) { if (!(_p)) warning_msg(__FILE__ ":"STR(__LINE__)": " _msg); }
#define DT_WARN_ON_FAIL_ERRNO(_p, _msg) { if (!(_p)) warning_msg(__FILE__ ":"STR(__LINE__)": " _msg": %s", strerror(errno)); }
#define DT_ERROR_ON_FAIL(_p, _msg, ...) { if (!(_p)) { error_msg(__FILE__ ":"STR(__LINE__)": " _msg); } }
/**
 * @}
*/


#endif //__DT_LOGGING__
