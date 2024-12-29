#ifndef INC_ERROR_H_
#define INC_ERROR_H_

// Error flags, value is bit position in the error register
typedef enum _error_t
{
    ERR_PERIPHINIT = 0, // N/A
    ERR_USBTX_BUSY,     // N/A
    ERR_CAN_TXFAIL,     // Data loss in the driver -> CAN Tx buffer full
    ERR_FULLBUF_CANRX,  // TODO Data loss in the driver -> CAN Rx buffer full
    ERR_FULLBUF_CANTX,  // Data loss in the src -> CAN Tx buffer full
    ERR_FULLBUF_USBRX,  // Data loss in the src -> CAN Tx buffer full
    ERR_FULLBUF_USBTX,  // Data loss in the src -> CAN Rx buffer full
    // TODO Error passive / Bus off / Bus error

    ERR_MAX
} error_t;

// Status flags, value is bit position in the status flags
typedef enum _status_t
{
    STS_CAN_RX_FIFO_FULL = 0, // Message loss. Not mean the buffer is just full.
    STS_CAN_TX_FIFO_FULL,     // Message loss. Not mean the buffer is just full.

} status_t;

// Prototypes
void error_assert(error_t err);
uint32_t error_get_timestamp(error_t err);
uint32_t error_get_last_timestamp(void);
uint8_t error_occurred(error_t err);
uint32_t error_get_register(void);
uint8_t error_get_status_flags();
void error_clear();

#endif /* INC_ERROR_H_ */
