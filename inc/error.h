#ifndef INC_ERROR_H_
#define INC_ERROR_H_


// Error flags, value is bit position in the error register
typedef enum _error_t
{
    ERR_PERIPHINIT = 0,     // N/A
    ERR_USBTX_BUSY,         // N/A
    ERR_CAN_TXFAIL,         // Data loss in the driver -> Data overrun
    ERR_CANRXFIFO_OVERFLOW, // N/A
    ERR_FULLBUF_CANTX,      // Data loss in the src -> CAN Tx buffer full
    ERR_FULLBUF_USBRX,      // Data loss in the src -> CAN Tx buffer full
    ERR_FULLBUF_USBTX,      // Data loss in the src -> CAN Rx buffer full

    ERR_MAX
} error_t;


// Prototypes
void error_assert(error_t err);
uint32_t error_timestamp(error_t err);
uint32_t error_last_timestamp(void);
uint8_t error_occurred(error_t err);
uint32_t error_reg(void);
void error_clear();


#endif /* INC_ERROR_H_ */
