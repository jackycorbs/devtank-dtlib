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
#ifndef __DT_BUFFER__
#define __DT_BUFFER__

#include <stdint.h>
#include <stdbool.h>
#include <stdarg.h>

/**
 * \ingroup base
 * \defgroup Buffer
 * \brief Core buffer functionality.
 * @{
 */

/** \struct dt_buffer_static_t
 *  \brief Reserve the memory required for a dt_buffer object.
 */

struct dt_buffer_static_t
{
    uint8_t data[sizeof(void*) + sizeof(uint32_t)*3]; ///< Bytes for a dt_buffer object.
} __attribute__((packed));

#ifndef DT_BUFFER ///< Used internally so structure can be privately defined differently.
typedef struct dt_buffer_static_t dt_buffer_t; ///< Publically used buffer structure.
#define DT_BUFFER
#endif //DT_BUFFER

/** \brief Prepare a dt_buffer for use.
 * \param buffer buffer object.
 * \param init_size size of the buffer inside dt_buffer to start with.
 */
extern bool           dt_buffer_init(dt_buffer_t* buffer, unsigned init_size);

/** \brief Prepare a dt_buffer for use when contains relative pointer.
 * \param buffer buffer object.
 * \param init_size size of the buffer inside dt_buffer to start with.
 */
extern void           dt_buffer_init_relative(dt_buffer_t* buffer, void* data, unsigned size);

/** \brief Release any memory in dt_buffer and leave it blank. */
extern void           dt_buffer_clear(dt_buffer_t* buffer);

/** \brief Get the size of used memory in the dt_buffer. */
extern unsigned       dt_buffer_get_size(const dt_buffer_t* buffer);

/** \brief Get the total avaiable memory in the dt_buffer. */
extern unsigned       dt_buffer_get_capacity(const dt_buffer_t* buffer);

/** \brief Get pointer to the memory in the dt_buffer. */
extern void*          dt_buffer_get_data(const dt_buffer_t* buffer);

/** \brief Get pointer to the memory at offset in the dt_buffer. */
extern void*          dt_buffer_get_offset_data(const dt_buffer_t* buffer, unsigned offset);

/** \brief Get outset into memory in dt_buffer of address. */
extern bool           dt_buffer_get_offset(dt_buffer_t* buffer, const void* ptr, unsigned * offset);

/** \brief Get if a pointer is to memory in the dt_buffer. */
extern bool           dt_buffer_contains(const dt_buffer_t* buffer, const void * ptr);

/** \brief Set the size of used memory in the dt_buffer */
extern bool           dt_buffer_set_size(dt_buffer_t* buffer, unsigned size);

/** \brief Resize the total avaiable memory in the dt_buffer. */
extern bool           dt_buffer_set_capacity(dt_buffer_t* buffer, unsigned size);

/** \brief Get remaining unused memory in the dt_buffer. */
extern unsigned       dt_buffer_get_unused_capacity(dt_buffer_t* buffer);

/** \brief Set the size and values of the memory in the dt_buffer. */
extern bool           dt_buffer_set_data(dt_buffer_t* buffer, unsigned offset, const void* data, unsigned size);


/** \brief Set the used size of dt_buffer to zero. */
extern bool           dt_buffer_wipe(dt_buffer_t* buffer);

/** \brief Grow used memory in dt_buffer with the values from the passed in memory. */
extern bool           dt_buffer_append(dt_buffer_t* buffer, const void* data, unsigned size);

/** \brief Set the buffer with memory owned elsewhere. */
extern void           dt_buffer_contain(dt_buffer_t* buffer, void* data, unsigned size);

/** \brief Set the buffer to allow/disallow changing capacity. */
extern void           dt_buffer_allow_growth(dt_buffer_t* buffer, bool enable);

/** \brief Get if the buffer allows/disallows changing capacity. */
extern bool           dt_buffer_has_allow_growth(dt_buffer_t* buffer);

/** \brief Append a copy of the given string to buffer and return copy. */
extern char *         dt_buffer_clone_append(dt_buffer_t* buffer, const char* str);

/** \brief Join a copy of the given string to buffer, removing previous null termination. */
extern bool           dt_buffer_clone_join(dt_buffer_t* buffer, const char* str);

/** \brief Append free space of given size and return memory address of in buffer. */
extern void *         dt_buffer_append_space(dt_buffer_t* buffer, unsigned size);

/** \brief Print string to buffer and return copy. */
extern char *         dt_buffer_append_print(dt_buffer_t* buffer, const char * fmt, ...);

/** \brief Print string to buffer and return copy. */
extern char *         dt_buffer_append_vprint(dt_buffer_t* buffer, const char * fmt, va_list va);

/** \brief Append given byte count from given file descriptor to buffer. */
extern void *         dt_buffer_read_fd(dt_buffer_t* buffer, unsigned size, int fd, dt_usecs usecs);

/** \brief Get buffer content as string if it's null terminated. */
extern const char *   dt_buffer_as_string(const dt_buffer_t* buffer, unsigned offset);

/** \brief Copy buffer content if there is enough size. */
extern bool           dt_buffer_get_copy(const dt_buffer_t* buffer, unsigned offset, void * dst, unsigned size);
/**
 * @}
*/

#endif //__DT_BUFFER__
