//
// buffer: manage buffer
//

#include <string.h>
#include "stm32g4xx_hal.h"
#include "buffer.h"
#include "error.h"
#include "slcan.h"
#include "system.h"
#include "tusb.h"

// Cirbuf structure for CAN TX frames
struct buf_can_tx
{
    FDCAN_TxHeaderTypeDef header[BUF_CAN_TXQUEUE_LEN];  // Header buffer
    uint8_t data[BUF_CAN_TXQUEUE_LEN][CAN_MAX_DATALEN]; // Data buffer
    uint16_t head;                              // Head pointer
    uint16_t send;                              // Send pointer
    uint16_t tail;                              // Tail pointer
    uint8_t full;                               // Set this when we are full, clear when the tail moves one.
};

// Public variables
volatile struct buf_cdc_tx buf_cdc_tx = {0};
volatile struct buf_cdc_rx buf_cdc_rx = {0};

// Private variables
static struct buf_can_tx buf_can_tx = {0};
static uint8_t slcan_str[SLCAN_MTU];
static uint8_t slcan_str_index = 0;

// Private prototypes

// Initializes
void buf_init(void)
{
    buf_cdc_rx.head = 0;
    buf_cdc_rx.tail = 0;

    buf_cdc_tx.head = 1;
    buf_cdc_tx.msglen[buf_cdc_tx.head] = 0;
    buf_cdc_tx.tail = 0;
    buf_cdc_tx.msglen[buf_cdc_tx.tail] = 0;

    buf_can_tx.head = 0;
    buf_can_tx.send = 0;
    buf_can_tx.tail = 0;
    buf_can_tx.full = 0;
}

// Process
void buf_process(void)
{
    // Process cdc receive buffer
    if (tud_cdc_n_available(0)) {
        uint8_t buf[64];

        uint32_t count = tud_cdc_n_read(0, buf, sizeof(buf));

        for (uint32_t i = 0; i < count; i++)
	    {
            if (buf[i] == '\r')
            {
                slcan_parse_str(slcan_str, slcan_str_index);
                slcan_str_index = 0;
            }
            else
            {
                // Check for overflow of buffer
                if (slcan_str_index >= SLCAN_MTU)
                {
                    // TODO: Return here and discard this CDC buffer?
                    slcan_str_index = 0;
                }
                slcan_str[slcan_str_index++] = buf[i];
            }
        }
    }


    // Process cdc transmit buffer
    uint32_t new_head = (buf_cdc_tx.head + 1UL) % BUF_CDC_TX_NUM_BUFS;
    if (new_head != buf_cdc_tx.tail)
    {
        if (0 < buf_cdc_tx.msglen[buf_cdc_tx.head])
        {
            buf_cdc_tx.head = new_head;
            buf_cdc_tx.msglen[new_head] = 0;
        }
    }
    uint32_t new_tail = (buf_cdc_tx.tail + 1UL) % BUF_CDC_TX_NUM_BUFS;
    if (new_tail != buf_cdc_tx.head)
    {
        tud_cdc_n_write(0, buf_cdc_tx.data[new_tail], buf_cdc_tx.msglen[new_tail]);
        tud_cdc_n_write_flush(0);
        buf_cdc_tx.tail = new_tail;
    }


    // Process can transmit buffer
    while ((buf_can_tx.send != buf_can_tx.head || buf_can_tx.full) && (HAL_FDCAN_GetTxFifoFreeLevel(can_get_handle()) > 0))
    {
        HAL_StatusTypeDef status;

        // Transmit can frame
        status = HAL_FDCAN_AddMessageToTxFifoQ(can_get_handle(), 
                                               &buf_can_tx.header[buf_can_tx.send], 
                                               buf_can_tx.data[buf_can_tx.send]);

        buf_can_tx.send = (buf_can_tx.send + 1) % BUF_CAN_TXQUEUE_LEN;

        // This drops the packet if it fails (no retry). Failure is unlikely
        // since we check if there is a TX mailbox free.
        if (status != HAL_OK)
        {
            error_assert(ERR_CAN_TXFAIL);
        }
    }
}

// Enqueue data for transmission over USB CDC to host (copy and comit = slow)
void buf_enqueue_cdc(uint8_t* buf, uint16_t len)
{
    if (BUF_CDC_TX_BUF_SIZE - len < buf_cdc_tx.msglen[buf_cdc_tx.head])
    {
        
        error_assert(ERR_FULLBUF_USBTX);    // The data does not fit in the buffer
    }
    else
    {
        // Copy data
        memcpy((uint8_t *)&buf_cdc_tx.data[buf_cdc_tx.head][buf_cdc_tx.msglen[buf_cdc_tx.head]], buf, len);
        buf_cdc_tx.msglen[buf_cdc_tx.head] += len;
    }
}

// Get destination pointer of cdc buffer (Start position of write access)
uint8_t *buf_get_cdc_dest(void)
{
    if (BUF_CDC_TX_BUF_SIZE - SLCAN_MTU < buf_cdc_tx.msglen[buf_cdc_tx.head])
    {
        error_assert(ERR_FULLBUF_USBTX);        // The data will not fit in the buffer
        return NULL;
    }

    return (uint8_t *)&buf_cdc_tx.data[buf_cdc_tx.head][buf_cdc_tx.msglen[buf_cdc_tx.head]];
}

// Send the data bytes in destination area over USB CDC to host
void buf_comit_cdc_dest(uint32_t len)
{
    buf_cdc_tx.msglen[buf_cdc_tx.head] += len;
}

// Get destination pointer of can tx frame header
FDCAN_TxHeaderTypeDef *buf_get_can_dest_header(void)
{
    if (buf_can_tx.full)
    {
        error_assert(ERR_FULLBUF_CANTX);
        return NULL;
    }

    return &buf_can_tx.header[buf_can_tx.head];
}

// Get destination pointer of can tx frame data bytes
uint8_t *buf_get_can_dest_data(void)
{
    if (buf_can_tx.full)
    {
        error_assert(ERR_FULLBUF_CANTX);
        return NULL;
    }

    return buf_can_tx.data[buf_can_tx.head];
}

// Send the message in destination slot on the CAN bus.
HAL_StatusTypeDef buf_comit_can_dest(void)
{
    if (can_is_tx_enabled() == ENABLE)
    {
        // If the queue is full
        if (buf_can_tx.full)
        {
            error_assert(ERR_FULLBUF_CANTX);
            return HAL_ERROR;
        }

        // Increment the head pointer
        buf_can_tx.head = (buf_can_tx.head + 1) % BUF_CAN_TXQUEUE_LEN;
        if (buf_can_tx.head == buf_can_tx.tail) buf_can_tx.full = 1;
    }
    else
    {
        return HAL_ERROR;
    }

    return HAL_OK;
}

// Dequeue data bytes from the can tx buffer (Delete one frame)
uint8_t *buf_dequeue_can_tx_data(void)
{
    uint32_t tmp_tail = buf_can_tx.tail;

    buf_can_tx.tail = (buf_can_tx.tail + 1) % BUF_CAN_TXQUEUE_LEN;
    buf_can_tx.full = 0;

    return buf_can_tx.data[tmp_tail];
}

// Clear can tx buffer
void buf_clear_can_buffer(void)
{
    buf_can_tx.tail = buf_can_tx.head;
    buf_can_tx.send = buf_can_tx.head;
    buf_can_tx.full = 0;
}
