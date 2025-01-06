#ifndef INC_ERROR_H_
#define INC_ERROR_H_

// Error flags, value is bit position in the error register
typedef enum
{
    ERR_PERIPHINIT = 0,
    ERR_USBTX_BUSY,
    ERR_CAN_TXFAIL,
    ERR_CANRXFIFO_OVERFLOW,
    ERR_FULLBUF_CANTX,
    ERR_FULLBUF_USBRX,
    ERR_FULLBUF_USBTX,

    ERR_MAX
} error_flag_t;

// Prototypes
void error_assert(error_t err);
uint32_t error_get_timestamp(error_t err);
uint32_t error_get_last_timestamp(void);
uint8_t error_occurred(error_t err);
uint32_t error_get_register(void);
void error_clear();

#endif /* INC_ERROR_H_ */
