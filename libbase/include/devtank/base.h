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
#ifndef __DT_BASE__
#define __DT_BASE__

#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <inttypes.h>
#include <limits.h>

/**
 * \defgroup C
 * \brief C libaries
 * @{
 * @}
*/


/**
 * \defgroup base
 * \ingroup C
 * \brief Core functionality.
 * @{
 */

#define LIBDEVTANK_VERSION_REVISION 0 ///< Build version revision
#define LIBDEVTANK_VERSION_MINOR    1 ///< Build version minor number
#define LIBDEVTANK_VERSION_MAJOR    0 ///< Build version major number

#define STR_EXPAND(tok) #tok            ///< Convert macro value to a string.
#define STR(tok) STR_EXPAND(tok)        ///< Convert macro value to a string.

#define ARRAY_SIZE(_array) (sizeof(_array)/sizeof(_array[0])) ///< Get size of an array on local stack.

#define ALIGN_TO(_x, _y) ((_x + _y -1 ) & ~(_y - 1)) ///< Align one number to another, for instance 16 for optimial addressing.
#define ALIGN_16(_x) ALIGN_TO(_x, 16)                ///< Align given number to 16.

#define USEC_SECOND 1000000LL               ///< Amount of microseconds in a second.
#define USEC_MINUTE (USEC_SECOND * 60)      ///< Amount of microseconds in a minute.

#define GET_OFFSET(_type_, _member_)  ((unsigned)(uintptr_t)(&((_type_*)NULL)->_member_))
#define GET_OWNER(_type_, _member_, _member_addr_) ((_type_*)(((uintptr_t)_member_addr_) - GET_OFFSET(_type_, _member_)))


#define INDENT_SPACES 4

typedef int64_t dt_usecs;                 ///< Type used for time, in microseconds.
#define DT_USECS_START  LONG_MIN
#define DT_USECS_END    LONG_MAX

#define DT_USECS_FMT PRIi64               ///< Printf format string for time type.

/** \brief Get the current time (in microseconds) */
extern dt_usecs get_current_us(void);

/** \brief Print time (in microseconds) as a local time string. */
extern int str_print_time(char* buffer, size_t buffer_size, dt_usecs usecs);

/** \brief Print time (in microseconds) as a time string. */
extern int str_print_duration(char* buffer, size_t buffer_size, dt_usecs usecs);

/** \brief Get the id of the current thread executing. */
extern uint32_t get_thread_id(void);

/** \brief Get the version of the libary in use. */
extern void get_runtime_version(uint32_t* major, uint32_t* minor, uint32_t* revision);

/** \brief Get strings of the build time and git commit of the source built. */
extern void dt_get_build_info(const char** build_time, const char** git_commit);

/** \brief Get the number of bytes read to be read.
 * \return byte count on sucess or negative value on error.
 */
extern int  get_fd_peek(int fd);

/** \brief Wait for activity on a file descriptor for a given amount of time (in microseconds).
 * \return possitive on success, zero on timeout, negative on error.
 */
extern int  wait_for_fd(int fd, dt_usecs usecs);


/** \brief Change given file descriptor to blocking
 * \return boolean of success
 */
extern bool set_fd_blocking(int fd, bool enable);


/** \brief Check if the given filename exists.
 * \return boolean of success
 */
extern bool does_file_exists(const char* filename);

/** \brief Read given number of bytes form file descriptor until done or error. */
extern bool safe_read(int fd, void* data, size_t size, dt_usecs max_usecs);

/** \brief Write given number of bytes form file descriptor until done or error. */
extern bool safe_write(int fd, const void* data, size_t size, dt_usecs max_usecs);

/** \brief Commit outstanding buffered write bytes. */
extern bool fd_sync(int fd);


/** \brief Prepare libary for use */
extern void devtank_init();

/** \brief Query if libary is for use */
extern bool devtank_ready();

/** \brief Close down libary after use has finished. */
extern void devtank_shutdown();


/** \brief Release given memory with free, if it's non-NULL. */
extern void safe_free(void* p);

/** \brief Sleep for the given time peroid. */
extern void dt_sleep(dt_usecs usecs);


#ifndef DOXYGEN
#define UNUSED  __attribute__((unused))
#define PRINTF_FMT_CHECK(_fmt_arg, _el_arg)  __attribute__ ((format (printf, _fmt_arg, _el_arg)))
#else
#define UNUSED
#define PRINTF_FMT_CHECK(_fmt_arg, _el_arg)
#endif

/** \brief Version of snprintf where 0 is returned on error so safe have many and not check each. */
extern unsigned dt_snprintf0(char* buffer, size_t len, const char* fmt, ...) PRINTF_FMT_CHECK( 3, 4);

/** \brief Version of vsnprintf where 0 is returned on error so safe have many and not check each. */
extern unsigned dt_vsnprintf0(char* buffer, size_t len, const char* fmt, va_list ap);

#ifndef DT_REL_PNT ///< Used internally so structure can be privately defined differently.
typedef uint64_t dt_dyn_rel_ptr_t;
#define DT_REL_PNT
#endif

extern bool   dt_dyn_rel_ptr_is_full(const dt_dyn_rel_ptr_t * rel_p);
extern void * dt_dyn_rel_ptr_get(const dt_dyn_rel_ptr_t * rel_p);
extern void   dt_dyn_rel_ptr_set(dt_dyn_rel_ptr_t * rel_p, const void * p);
extern void   dt_dyn_rel_ptr_set_rel(dt_dyn_rel_ptr_t * rel_p, const void * p);
extern void   dt_dyn_rel_ptr_free(dt_dyn_rel_ptr_t * rel_p);

#define dt_rel_ptr_set(_rel_p, _p) ((*_rel_p) = (((intptr_t)_p) - ((intptr_t)_rel_p)))
#define dt_rel_ptr_get(_rel_p)     ((*_rel_p)?(((uint8_t*)_rel_p) + (*_rel_p)):NULL)

typedef struct
{
    const void * ptr;
    unsigned     size;
} dt_data_packet_t;


extern void dt_data_packet_str_set(dt_data_packet_t * packet, const char * str);

extern uint64_t dt_hash_64(dt_data_packet_t * datas, unsigned count);


/**
 * @}
*/

#endif //__DT_BASE__
