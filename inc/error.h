#ifndef INC_ERROR_H_
#define INC_ERROR_H_

// Error flags, value is bit position in the error register
enum error_flag
{
    //ERR_PERIPHINIT = 0,
    //ERR_USBTX_BUSY,
    ERR_CAN_RXFAIL = 0,
    ERR_CAN_TXFAIL,
    //ERR_CANRXFIFO_OVERFLOW,
    ERR_FULLBUF_CANTX,
    ERR_FULLBUF_USBRX,
    ERR_FULLBUF_USBTX,
    ERR_CAN_BUS_ERR,
    ERR_CAN_WARNING,
    ERR_CAN_ERR_PASSIVE,
    ERR_CAN_BUS_OFF,

    ERR_MAX
};

// Prototypes
void error_assert(enum error_flag err);
uint32_t error_get_timestamp(enum error_flag err);
uint32_t error_get_last_timestamp(void);
uint8_t error_occurred(enum error_flag err);
uint32_t error_get_register(void);
void error_clear();

#endif /* INC_ERROR_H_ */
