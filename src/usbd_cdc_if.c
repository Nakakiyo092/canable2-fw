#include "usbd_cdc_if.h"
#include "slcan.h"
#include "system.h"
#include "error.h"

// This takes 4k of RAM.
#define NUM_RX_BUFS 8
#define RX_BUF_SIZE CDC_DATA_FS_MAX_PACKET_SIZE // Size of RX buffer item

// CDC transmit buffering
#define TX_LINBUF_SIZE 64 // Set to 64 for max single packet size
#define USBTXQUEUE_LEN 10240 // Number of bytes allocated


// Transmit buffering: circular buffer FIFO
struct usb_tx_buf
{
	uint8_t data[USBTXQUEUE_LEN]; // Data buffer
	uint32_t head; // Head pointer
	uint32_t tail; // Tail pointer
	uint8_t full;
};

// Receive buffering: circular buffer FIFO
struct usb_rx_buf
{
	// Receive buffering: circular buffer FIFO
	uint8_t buf[NUM_RX_BUFS][RX_BUF_SIZE];
	uint32_t msglen[NUM_RX_BUFS];
	uint32_t head;
	uint32_t tail;
	uint8_t full;
};


// Private variables
static struct usb_tx_buf txbuf = {0};
static volatile struct usb_rx_buf rxbuf = {0};
static uint8_t tx_linbuf[TX_LINBUF_SIZE] = {0};
static uint8_t slcan_str[SLCAN_MTU];
static uint8_t slcan_str_index = 0;


// Externs
extern USBD_HandleTypeDef hUsbDeviceFS;


// Private prototypes
static int8_t CDC_Init_FS(void);
static int8_t CDC_DeInit_FS(void);
static int8_t CDC_Control_FS(uint8_t cmd, uint8_t* pbuf, uint16_t length);
static int8_t CDC_Receive_FS(uint8_t* pbuf, uint32_t *Len);
void cdc_process(void);


USBD_CDC_ItfTypeDef USBD_Interface_fops_FS =
{
    CDC_Init_FS,
    CDC_DeInit_FS,
    CDC_Control_FS,
    CDC_Receive_FS
};


// Initializes the CDC media low layer over the FS USB IP
static int8_t CDC_Init_FS(void)
{
    txbuf.head = 0;
    txbuf.tail = 0;
    txbuf.full = 0;
    rxbuf.head = 0;
    rxbuf.tail = 0;
    rxbuf.full = 0;

    USBD_CDC_SetTxBuffer(&hUsbDeviceFS, tx_linbuf, 0);
    USBD_CDC_SetRxBuffer(&hUsbDeviceFS, (uint8_t *)rxbuf.buf[rxbuf.head]);
    return (USBD_OK);
}


// DeInitializes the CDC media low layer
static int8_t CDC_DeInit_FS(void)
{
    return (USBD_OK);
}

/**
  * @brief  Manage the CDC class requests
  * @param  cmd: Command code
  * @param  pbuf: Buffer containing command data (request parameters)
  * @param  length: Number of data to be sent (in bytes)
  * @retval Result of the operation: USBD_OK if all operations are OK else USBD_FAIL
  */
static int8_t CDC_Control_FS(uint8_t cmd, uint8_t* pbuf, uint16_t length)
{
    /* USER CODE BEGIN 5 */
    switch (cmd)
    {
        case CDC_SEND_ENCAPSULATED_COMMAND:

            break;

        case CDC_GET_ENCAPSULATED_RESPONSE:

            break;

        case CDC_SET_COMM_FEATURE:

            break;

        case CDC_GET_COMM_FEATURE:

            break;

        case CDC_CLEAR_COMM_FEATURE:

            break;

  /*******************************************************************************/
  /* Line Coding Structure                                                       */
  /*-----------------------------------------------------------------------------*/
  /* Offset | Field       | Size | Value  | Description                          */
  /* 0      | dwDTERate   |   4  | Number |Data terminal rate, in bits per second*/
  /* 4      | bCharFormat |   1  | Number | Stop bits                            */
  /*                                        0 - 1 Stop bit                       */
  /*                                        1 - 1.5 Stop bits                    */
  /*                                        2 - 2 Stop bits                      */
  /* 5      | bParityType |  1   | Number | Parity                               */
  /*                                        0 - None                             */
  /*                                        1 - Odd                              */
  /*                                        2 - Even                             */
  /*                                        3 - Mark                             */
  /*                                        4 - Space                            */
  /* 6      | bDataBits  |   1   | Number Data bits (5, 6, 7, 8 or 16).          */
  /*******************************************************************************/
        case CDC_SET_LINE_CODING:

            break;

        case CDC_GET_LINE_CODING:
            pbuf[0] = (uint8_t)(115200);
            pbuf[1] = (uint8_t)(115200 >> 8);
            pbuf[2] = (uint8_t)(115200 >> 16);
            pbuf[3] = (uint8_t)(115200 >> 24);
            pbuf[4] = 0; // stop bits (1)
            pbuf[5] = 0; // parity (none)
            pbuf[6] = 8; // number of bits (8)
            break;

        case CDC_SET_CONTROL_LINE_STATE:

            break;

        case CDC_SEND_BREAK:

            break;

        default:

            break;
    }

    return (USBD_OK);
    /* USER CODE END 5 */
}

/**
  * @brief  Data received over USB OUT endpoint are sent over CDC interface
  *         through this function.
  *
  *         @note
  *         This function will block any OUT packet reception on USB endpoint
  *         untill exiting this function. If you exit this function before transfer
  *         is complete on CDC interface (ie. using DMA controller) it will result
  *         in receiving more data while previous ones are still not sent.
  *
  * @param  Buf: Buffer of data to be received
  * @param  Len: Number of data received (in bytes)
  * @retval Result of the operation: USBD_OK if all operations are OK else USBD_FAIL
  */


static int8_t CDC_Receive_FS(uint8_t* Buf, uint32_t *Len)
{
    // Check for overflow!
    if (rxbuf.full)
    {
        error_assert(ERR_FULLBUF_USBRX);

        // Listen again on the same buffer. Old data will be overwritten.
        USBD_CDC_SetRxBuffer(&hUsbDeviceFS, (uint8_t *)rxbuf.buf[rxbuf.head]);
        USBD_CDC_ReceivePacket(&hUsbDeviceFS);
        return HAL_ERROR;
    }
    else
    {
        // Save off length
        rxbuf.msglen[rxbuf.head] = *Len;
        rxbuf.head = (rxbuf.head + 1) % NUM_RX_BUFS;
        if (rxbuf.head == rxbuf.tail) rxbuf.full = 1;

        // Start listening on next buffer. Previous buffer will be processed in main loop.
        USBD_CDC_SetRxBuffer(&hUsbDeviceFS, (uint8_t *)rxbuf.buf[rxbuf.head]);
        USBD_CDC_ReceivePacket(&hUsbDeviceFS);
        return (USBD_OK);
    }
}


// Process incoming and outgoing USB-CDC data
void cdc_process(void)
{
    // Process transmit buffer
    USBD_CDC_HandleTypeDef *hcdc = (USBD_CDC_HandleTypeDef*)hUsbDeviceFS.pClassData;
    if (hcdc->TxState == 0)
    {
        uint16_t linbuf_ctr = 0;
        while (txbuf.tail != txbuf.head || txbuf.full)
        {
            tx_linbuf[linbuf_ctr++] = txbuf.data[txbuf.tail];
            txbuf.tail = (txbuf.tail + 1UL) % USBTXQUEUE_LEN;
            txbuf.full = 0;

            // Take up to the number of bytes to fill the linbuf
            if(linbuf_ctr >= TX_LINBUF_SIZE)
                break;
        }

        if(linbuf_ctr > 0)
        {
            // Set transmit buffer and start TX
            USBD_CDC_SetTxBuffer(&hUsbDeviceFS, tx_linbuf, linbuf_ctr);
            USBD_CDC_TransmitPacket(&hUsbDeviceFS);
        }
    }

    // Process receive buffer
    system_irq_disable();
    if (rxbuf.tail != rxbuf.head || rxbuf.full)
    {
        //  Process one whole buffer
        for (uint32_t i = 0; i < rxbuf.msglen[rxbuf.tail]; i++)
	    {
            if (rxbuf.buf[rxbuf.tail][i] == '\r')
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

                slcan_str[slcan_str_index++] = rxbuf.buf[rxbuf.tail][i];
            }
        }

        // Move on to next buffer
        rxbuf.tail = (rxbuf.tail + 1) % NUM_RX_BUFS;
        rxbuf.full = 0;
    }
    system_irq_enable();

}


// Enqueue data for transmission over USB CDC to host
void cdc_transmit(uint8_t* buf, uint16_t len)
{
    system_irq_disable();
    uint32_t available_space = (USBTXQUEUE_LEN + txbuf.tail - txbuf.head) % USBTXQUEUE_LEN;
    if (!txbuf.full && txbuf.tail == txbuf.head)
    {
        available_space = USBTXQUEUE_LEN;   // The buffer is empty
    }
    if (len > available_space)
    {
        error_assert(ERR_FULLBUF_USBTX);    // The data does not fit in the buffer
    }
    else
    {
        // Copy data
        for (uint32_t i=0; i < len; i++)
        {
            txbuf.data[txbuf.head] = buf[i];

            // Increment the head
            txbuf.head = (txbuf.head + 1UL) % USBTXQUEUE_LEN;
        }
        if (txbuf.head == txbuf.tail) txbuf.full = 1;
    }
    system_irq_enable();
}

