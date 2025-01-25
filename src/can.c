//
// can: initializes and provides methods to interact with the CAN peripheral
//

#include "stm32g4xx_hal.h"
#include "usbd_cdc_if.h"
#include "can.h"
#include "error.h"
#include "led.h"
#include "slcan.h"
#include "system.h"

// CAN transmit buffering
#define TXQUEUE_LEN 64     // Number of buffers allocated
#define TXQUEUE_DATALEN 64 // CAN DLC length of data buffers. Must be 64 for canfd.

// Cirbuf structure for CAN TX frames
struct can_tx_buf
{
    uint8_t data[TXQUEUE_LEN][TXQUEUE_DATALEN]; // Data buffer
    FDCAN_TxHeaderTypeDef header[TXQUEUE_LEN];  // Header buffer
    uint16_t head;                              // Head pointer
    uint16_t tail;                              // Tail pointer
    uint8_t full;                               // Set this when we are full, clear when the tail moves one.
};

// Private variables
static FDCAN_HandleTypeDef can_handle;
static FDCAN_FilterTypeDef can_std_filter;
static FDCAN_FilterTypeDef can_ext_filter;
static FDCAN_FilterTypeDef can_std_pass_all;
static FDCAN_FilterTypeDef can_ext_pass_all;
static uint8_t can_rx_err_cnt_prev = 0;
static uint8_t can_tx_err_cnt_prev = 0;
static enum can_bus_state can_bus_state;
static uint32_t can_mode = FDCAN_MODE_NORMAL;
static uint8_t can_autoretransmit = ENABLE;
static struct can_tx_buf can_tx_queue = {0};
static struct can_bitrate_cfg can_bitrate_nominal, can_bitrate_data = {0};

// Private methods
uint8_t can_is_msg_accepted(void);
uint8_t can_is_msg_stack(void);
uint8_t can_is_msg_received(void);

// Initialize CAN peripheral settings, but don't actually start the peripheral
void can_init(void)
{
    // Initialize GPIO for CAN transceiver
    GPIO_InitTypeDef GPIO_InitStruct;
    __HAL_RCC_FDCAN_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_GPIOA_CLK_ENABLE();

    GPIO_InitStruct.Pin = GPIO_PIN_13;
    GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
    GPIO_InitStruct.Pull = GPIO_PULLDOWN;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);
    HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, 1); // CAN IO power

    // PB8     ------> CAN_RX
    // PB9     ------> CAN_TX
    GPIO_InitStruct.Pin = GPIO_PIN_8 | GPIO_PIN_9;
    GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
    GPIO_InitStruct.Alternate = GPIO_AF9_FDCAN1;
    HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

    // Initialize default CAN filter configuration
    can_std_filter.IdType = FDCAN_STANDARD_ID;
    can_std_filter.FilterIndex = 0;
    can_std_filter.FilterType = FDCAN_FILTER_MASK;
    can_std_filter.FilterConfig = FDCAN_FILTER_TO_RXFIFO0;
    can_std_filter.FilterID1 = 0x7FF;
    can_std_filter.FilterID2 = 0x000;

    can_ext_filter.IdType = FDCAN_EXTENDED_ID;
    can_ext_filter.FilterIndex = 0;
    can_ext_filter.FilterType = FDCAN_FILTER_MASK;
    can_ext_filter.FilterConfig = FDCAN_FILTER_TO_RXFIFO0;
    can_ext_filter.FilterID1 = 0x1FFFFFFF;
    can_ext_filter.FilterID2 = 0x00000000;

    can_std_pass_all.IdType = FDCAN_STANDARD_ID;
    can_std_pass_all.FilterIndex = 1;
    can_std_pass_all.FilterType = FDCAN_FILTER_MASK;
    can_std_pass_all.FilterConfig = FDCAN_FILTER_TO_RXFIFO1;
    can_std_pass_all.FilterID1 = 0x7FF;
    can_std_pass_all.FilterID2 = 0x000;

    can_ext_pass_all.IdType = FDCAN_EXTENDED_ID;
    can_ext_pass_all.FilterIndex = 1;
    can_ext_pass_all.FilterType = FDCAN_FILTER_MASK;
    can_ext_pass_all.FilterConfig = FDCAN_FILTER_TO_RXFIFO1;
    can_ext_pass_all.FilterID1 = 0x1FFFFFFF;
    can_ext_pass_all.FilterID2 = 0x00000000;

    // Reset the queue
    memset(&can_tx_queue, 0, sizeof(can_tx_queue));

    // default to 125 kbit/s & 2Mbit/s
    can_set_bitrate(CAN_BITRATE_125K);
    can_set_data_bitrate(CAN_DATA_BITRATE_2M);
    can_handle.Instance = FDCAN1;
    can_bus_state = OFF_BUS;
}

// Start the CAN peripheral
HAL_StatusTypeDef can_enable(void)
{
    if (can_bus_state == OFF_BUS)
    {
        // Reset error counter
        __HAL_RCC_FDCAN_FORCE_RESET();
        __HAL_RCC_FDCAN_RELEASE_RESET();

        can_handle.Init.ClockDivider = FDCAN_CLOCK_DIV1; // 144Mhz
        can_handle.Init.FrameFormat = FDCAN_FRAME_FD_BRS;

        can_handle.Init.Mode = can_mode;
        can_handle.Init.AutoRetransmission = can_autoretransmit;
        can_handle.Init.TransmitPause = DISABLE;     // emz
        can_handle.Init.ProtocolException = DISABLE; // emz

        can_handle.Init.NominalPrescaler = can_bitrate_nominal.prescaler;
        can_handle.Init.NominalSyncJumpWidth = can_bitrate_nominal.sjw;
        can_handle.Init.NominalTimeSeg1 = can_bitrate_nominal.time_seg1;
        can_handle.Init.NominalTimeSeg2 = can_bitrate_nominal.time_seg2;

        // FD only
        can_handle.Init.DataPrescaler = can_bitrate_data.prescaler;
        can_handle.Init.DataSyncJumpWidth = can_bitrate_data.sjw;
        can_handle.Init.DataTimeSeg1 = can_bitrate_data.time_seg1;
        can_handle.Init.DataTimeSeg2 = can_bitrate_data.time_seg2;

        can_handle.Init.StdFiltersNbr = 2;
        can_handle.Init.ExtFiltersNbr = 2;
        can_handle.Init.TxFifoQueueMode = FDCAN_TX_FIFO_OPERATION;

        if (HAL_FDCAN_Init(&can_handle) != HAL_OK) return HAL_ERROR;

        // This is a must for high data bit rates, especially for isolated transceivers
        uint32_t offset = can_handle.Init.DataPrescaler * can_handle.Init.DataTimeSeg1;
        if (offset <= 0x7F)
        {
            if (HAL_FDCAN_ConfigTxDelayCompensation(&can_handle, offset, 0) != HAL_OK) return HAL_ERROR;
            if (HAL_FDCAN_EnableTxDelayCompensation(&can_handle) != HAL_OK) return HAL_ERROR;
        }
        else
        {
            // bitrate ~ 1Mbps when offset = 0x7F, compensation would not be must
            HAL_FDCAN_DisableTxDelayCompensation(&can_handle);
        }

        if (HAL_FDCAN_ConfigFilter(&can_handle, &can_std_filter) != HAL_OK) return HAL_ERROR;
        if (HAL_FDCAN_ConfigFilter(&can_handle, &can_ext_filter) != HAL_OK) return HAL_ERROR;
        if (HAL_FDCAN_ConfigFilter(&can_handle, &can_std_pass_all) != HAL_OK) return HAL_ERROR;
        if (HAL_FDCAN_ConfigFilter(&can_handle, &can_ext_pass_all) != HAL_OK) return HAL_ERROR;
        HAL_FDCAN_ConfigGlobalFilter(&can_handle, FDCAN_REJECT, FDCAN_REJECT, FDCAN_FILTER_REMOTE, FDCAN_FILTER_REMOTE);

        if (HAL_FDCAN_Start(&can_handle) != HAL_OK) return HAL_ERROR;

        can_bus_state = ON_BUS;

        // Clear the tx buffer
        can_tx_queue.tail = can_tx_queue.head;
        can_tx_queue.full = 0;

        led_turn_green(LED_OFF);

        return HAL_OK;
    }
    return HAL_ERROR;
}

// Disable the CAN peripheral and go off-bus
HAL_StatusTypeDef can_disable(void)
{
    if (can_bus_state == ON_BUS)
    {
        HAL_FDCAN_Stop(&can_handle);
        HAL_FDCAN_DeInit(&can_handle);

        // Reset error counter
        __HAL_RCC_FDCAN_FORCE_RESET();
        __HAL_RCC_FDCAN_RELEASE_RESET();

        can_bus_state = OFF_BUS;

        // Clear the tx buffer
        can_tx_queue.tail = can_tx_queue.head;
        can_tx_queue.full = 0;

        led_turn_green(LED_ON);

        return HAL_OK;
    }
    return HAL_ERROR;
}

// Set the data bitrate of the CAN peripheral
HAL_StatusTypeDef can_set_data_bitrate(enum can_data_bitrate bitrate)
{
    if (can_bus_state == ON_BUS)
    {
        // cannot set bitrate while on bus
        return HAL_ERROR;
    }

    // Set default bitrate 2M
    can_bitrate_data.prescaler = 2;
    can_bitrate_data.sjw = 8;
    can_bitrate_data.time_seg1 = 30;
    can_bitrate_data.time_seg2 = 9;

    switch (bitrate)
    {
    case CAN_DATA_BITRATE_500K:
        can_bitrate_data.prescaler = 8;
        break;
    case CAN_DATA_BITRATE_1M:
        can_bitrate_data.prescaler = 4;
        break;
    case CAN_DATA_BITRATE_2M:
        break;
    case CAN_DATA_BITRATE_4M:
        can_bitrate_data.prescaler = 1;
        break;
    case CAN_DATA_BITRATE_5M:
        can_bitrate_data.prescaler = 1;
        can_bitrate_data.sjw = 6;
        can_bitrate_data.time_seg1 = 24;
        can_bitrate_data.time_seg2 = 7;
        break;
    case CAN_DATA_BITRATE_8M:
        can_bitrate_data.prescaler = 1;
        can_bitrate_data.sjw = 3;
        can_bitrate_data.time_seg1 = 14;
        can_bitrate_data.time_seg2 = 5;
        break;
    default:
        return HAL_ERROR;
    }

    return HAL_OK;
}

// Set the nominal bitrate of the CAN peripheral
HAL_StatusTypeDef can_set_bitrate(enum can_bitrate bitrate)
{
    if (can_bus_state == ON_BUS)
    {
        // cannot set bitrate while on bus
        return HAL_ERROR;
    }

    // Set default bitrate 125k
    can_bitrate_nominal.prescaler = 16;
    can_bitrate_nominal.sjw = 8;
    can_bitrate_nominal.time_seg1 = 70;
    can_bitrate_nominal.time_seg2 = 9;

    switch (bitrate)
    {
    case CAN_BITRATE_10K:
        can_bitrate_nominal.prescaler = 200;
        break;
    case CAN_BITRATE_20K:
        can_bitrate_nominal.prescaler = 100;
        break;
    case CAN_BITRATE_50K:
        can_bitrate_nominal.prescaler = 40;
        break;
    case CAN_BITRATE_100K:
        can_bitrate_nominal.prescaler = 20;
        break;
    case CAN_BITRATE_125K:
        break;
    case CAN_BITRATE_250K:
        can_bitrate_nominal.prescaler = 8;
        break;
    case CAN_BITRATE_500K:
        can_bitrate_nominal.prescaler = 4;
        break;
    case CAN_BITRATE_800K:
        can_bitrate_nominal.prescaler = 2;
        can_bitrate_nominal.sjw = 10;
        can_bitrate_nominal.time_seg1 = 88;
        can_bitrate_nominal.time_seg2 = 11;
        break;
    case CAN_BITRATE_1000K:
        can_bitrate_nominal.prescaler = 2;
        break;
    default:
        return HAL_ERROR;
    }

    return HAL_OK;
}

// Set the data bitrate configuration of the CAN peripheral
HAL_StatusTypeDef can_set_data_bitrate_cfg(struct can_bitrate_cfg bitrate_cfg)
{
    if (can_bus_state == ON_BUS)
    {
        // cannot set bitrate while on bus
        return HAL_ERROR;
    }

    if (!IS_FDCAN_DATA_PRESCALER(bitrate_cfg.prescaler)) return HAL_ERROR;
    if (!IS_FDCAN_DATA_TSEG1(bitrate_cfg.time_seg1)) return HAL_ERROR;
    if (!IS_FDCAN_DATA_TSEG2(bitrate_cfg.time_seg2)) return HAL_ERROR;
    if (!IS_FDCAN_DATA_SJW(bitrate_cfg.sjw)) return HAL_ERROR;

    can_bitrate_data = bitrate_cfg;

    return HAL_OK;
}

// Set the nominal bitrate configuration of the CAN peripheral
HAL_StatusTypeDef can_set_bitrate_cfg(struct can_bitrate_cfg bitrate_cfg)
{
    if (can_bus_state == ON_BUS)
    {
        // cannot set bitrate while on bus
        return HAL_ERROR;
    }

    if (!IS_FDCAN_NOMINAL_PRESCALER(bitrate_cfg.prescaler)) return HAL_ERROR;
    if (!IS_FDCAN_NOMINAL_TSEG1(bitrate_cfg.time_seg1)) return HAL_ERROR;
    if (!IS_FDCAN_NOMINAL_TSEG2(bitrate_cfg.time_seg2)) return HAL_ERROR;
    if (!IS_FDCAN_NOMINAL_SJW(bitrate_cfg.sjw)) return HAL_ERROR;

    can_bitrate_nominal = bitrate_cfg;

    return HAL_OK;
}

// Set CAN peripheral to the specific mode
// normal: FDCAN_MODE_NORMAL
// silent: FDCAN_MODE_BUS_MONITORING
// loopback: FDCAN_MODE_INTERNAL_LOOPBACK
// external: FDCAN_MODE_EXTERNAL_LOOPBACK
HAL_StatusTypeDef can_set_mode(uint32_t mode)
{
    if (can_bus_state == ON_BUS)
    {
        // cannot set silent mode while on bus
        return HAL_ERROR;
    }
    can_mode = mode;

    return HAL_OK;
}

// Set filter for standard CAN ID
HAL_StatusTypeDef can_set_filter_std(FunctionalState state, uint32_t code, uint32_t mask)
{
    HAL_StatusTypeDef ret = HAL_OK;
    
    if (can_bus_state == ON_BUS) return HAL_ERROR;
    if (state == ENABLE)
        can_std_filter.FilterConfig = FDCAN_FILTER_TO_RXFIFO0;
    else if (state == DISABLE)
        can_std_filter.FilterConfig = FDCAN_FILTER_DISABLE;
    else
        ret = HAL_ERROR;

    if (code > 0x7FF)
        ret = HAL_ERROR;
    else
        can_std_filter.FilterID1 = code;

    if (mask > 0x7FF)
        ret = HAL_ERROR;
    else
        can_std_filter.FilterID2 = mask;
    
    return ret;
}

// Set filter for extended CAN ID
HAL_StatusTypeDef can_set_filter_ext(FunctionalState state, uint32_t code, uint32_t mask)
{
    HAL_StatusTypeDef ret = HAL_OK;
    
    if (can_bus_state == ON_BUS) return HAL_ERROR;
    if (state == ENABLE)
        can_ext_filter.FilterConfig = FDCAN_FILTER_TO_RXFIFO0;
    else if (state == DISABLE)
        can_ext_filter.FilterConfig = FDCAN_FILTER_DISABLE;
    else
        ret = HAL_ERROR;

    if (code > 0x1FFFFFFF)
        ret = HAL_ERROR;
    else
        can_ext_filter.FilterID1 = code;

    if (mask > 0x1FFFFFFF)
        ret = HAL_ERROR;
    else
        can_ext_filter.FilterID2 = mask;
    
    return ret;
}

// Get filter state for standard CAN ID
FunctionalState can_is_filter_std_enabled(void)
{
    if (can_std_filter.FilterConfig == FDCAN_FILTER_DISABLE)
        return DISABLE;
    else
        return ENABLE;
}

// Get filter state for extended CAN ID
FunctionalState can_is_filter_ext_enabled(void)
{
    if (can_ext_filter.FilterConfig == FDCAN_FILTER_DISABLE)
        return DISABLE;
    else
        return ENABLE;
}

// Get filter for standard CAN ID
uint32_t can_get_filter_std_code(void)
{
    return can_std_filter.FilterID1 & 0x7FF;
}

// Get filter for standard CAN ID
uint32_t can_get_filter_std_mask(void)
{
    return can_std_filter.FilterID2 & 0x7FF;
}

// Get filter for extended CAN ID
uint32_t can_get_filter_ext_code(void)
{
    return can_ext_filter.FilterID1 & 0x1FFFFFFF;
}

// Get filter for extended CAN ID
uint32_t can_get_filter_ext_mask(void)
{
    return can_ext_filter.FilterID2 & 0x1FFFFFFF;
}

// Set CAN peripheral to autoretransmit mode
void can_set_autoretransmit(uint8_t autoretransmit)
{
    if (can_bus_state == ON_BUS)
    {
        // Cannot set autoretransmission while on bus
        return;
    }
    if (autoretransmit)
    {
        can_autoretransmit = ENABLE;
    }
    else
    {
        can_autoretransmit = DISABLE;
    }
}

// Send a message on the CAN bus. Called from USB ISR.
HAL_StatusTypeDef can_tx(FDCAN_TxHeaderTypeDef *tx_msg_header, uint8_t *tx_msg_data)
{
    if (can_bus_state == ON_BUS && can_handle.Init.Mode != FDCAN_MODE_BUS_MONITORING)
    {
        // If the queue is full
        if (can_tx_queue.full)
        {
            error_assert(ERR_FULLBUF_CANTX);
            return HAL_ERROR;
        }

        // Convert length to bytes
        uint32_t len = hal_dlc_code_to_bytes(tx_msg_header->DataLength);

        // Don't overrun buffer element max length
        if (len > TXQUEUE_DATALEN)
            return HAL_ERROR;

        // Save the header to the circular buffer
        can_tx_queue.header[can_tx_queue.head] = *tx_msg_header;

        // Copy the data to the circular buffer
        for (uint8_t i = 0; i < len; i++)
        {
            can_tx_queue.data[can_tx_queue.head][i] = tx_msg_data[i];
        }

        // Increment the head pointer
        can_tx_queue.head = (can_tx_queue.head + 1) % TXQUEUE_LEN;
        if (can_tx_queue.head == can_tx_queue.tail) can_tx_queue.full = 1;
    }
    else
    {
        return HAL_ERROR;
    }

    return HAL_OK;
}

// Receive message from the CAN bus (blocking)
HAL_StatusTypeDef can_rx(FDCAN_RxHeaderTypeDef *rx_msg_header, uint8_t *rx_msg_data)
{
    HAL_StatusTypeDef status;
    status = HAL_FDCAN_GetRxMessage(&can_handle, FDCAN_RX_FIFO0, rx_msg_header, rx_msg_data);

    return status;
}

// Process data from CAN tx/rx circular buffers
void can_process(void)
{
    while ((can_tx_queue.tail != can_tx_queue.head || can_tx_queue.full) && (HAL_FDCAN_GetTxFifoFreeLevel(&can_handle) > 0))
    {
        HAL_StatusTypeDef status;

        // Transmit can frame
        status = HAL_FDCAN_AddMessageToTxFifoQ(&can_handle, &can_tx_queue.header[can_tx_queue.tail], can_tx_queue.data[can_tx_queue.tail]);
        can_tx_queue.tail = (can_tx_queue.tail + 1) % TXQUEUE_LEN;
        can_tx_queue.full = 0;

        // This drops the packet if it fails (no retry). Failure is unlikely
        // since we check if there is a TX mailbox free.
        if (status != HAL_OK)
        {
            error_assert(ERR_CAN_TXFAIL);
        }

        led_blink_green();
    }

    // Check if multiple message is stored in buffer.
    // This is unlikely since we loop cycle in less than several microseconds,
    // which is far less than a transmission time of a CAN frame.
    if (can_is_msg_stack())
    {
        // An error should be asserted because we do not have an overflow notification from the HAL driver.
        error_assert(ERR_CAN_RXFAIL);
    }

    // Message has been received, pull it from the buffer
    if (can_is_msg_accepted())
    {
        // Storage for status and received message buffer
        FDCAN_RxHeaderTypeDef rx_msg_header;
        uint8_t rx_msg_data[64] = {0};
        uint8_t msg_buf[SLCAN_MTU];

        // If message received from bus, parse the frame
        if (can_rx(&rx_msg_header, rx_msg_data) == HAL_OK)
        {
            int32_t msg_len = slcan_parse_frame((uint8_t *)&msg_buf, &rx_msg_header, rx_msg_data);

            // Transmit message via USB-CDC
            if (msg_len > 0)
            {
                cdc_transmit(msg_buf, msg_len);
            }
        }
    }

    if (can_is_msg_received())
    {
        led_blink_blue();
    }

    // Check for bus errors
    FDCAN_ProtocolStatusTypeDef sts;
    FDCAN_ErrorCountersTypeDef cnt;
    HAL_FDCAN_GetProtocolStatus(&can_handle, &sts);
    HAL_FDCAN_GetErrorCounters(&can_handle, &cnt);

    uint8_t rx_err_cnt = (uint8_t)(cnt.RxErrorPassive ? 128 : cnt.RxErrorCnt);
    if (rx_err_cnt > can_rx_err_cnt_prev || cnt.TxErrorCnt > can_tx_err_cnt_prev) error_assert(ERR_CAN_BUS_ERR);
    if (sts.Warning) error_assert(ERR_CAN_WARNING);
    if (sts.ErrorPassive) error_assert(ERR_CAN_ERR_PASSIVE);
    if (sts.BusOff) error_assert(ERR_CAN_BUS_OFF);

    can_rx_err_cnt_prev = rx_err_cnt;
    can_tx_err_cnt_prev = cnt.TxErrorCnt;

    if (can_bus_state == OFF_BUS)
    {
        led_turn_green(LED_ON);
    }
}

// Check if a CAN message has been accepted and is waiting in the FIFO
uint8_t can_is_msg_accepted(void)
{
    if (can_bus_state == OFF_BUS)
    {
        return 0;
    }

    return (HAL_FDCAN_GetRxFifoFillLevel(&can_handle, FDCAN_RX_FIFO0) > 0);
}

// Check if multiple CAN messages stack in the FIFO
uint8_t can_is_msg_stack(void)
{
    if (can_bus_state == OFF_BUS)
    {
        return 0;
    }

    return (HAL_FDCAN_GetRxFifoFillLevel(&can_handle, FDCAN_RX_FIFO0) >= 2);
}

// Check if a CAN message has been received and is waiting in the FIFO
// This functon also deletes one message from the FIFO
uint8_t can_is_msg_received(void)
{
    if (can_bus_state == OFF_BUS)
    {
        return 0;
    }

    uint8_t result = (HAL_FDCAN_GetRxFifoFillLevel(&can_handle, FDCAN_RX_FIFO1) > 0);

    FDCAN_RxHeaderTypeDef rx_msg_header;
    uint8_t rx_msg_data[TXQUEUE_DATALEN];

    HAL_FDCAN_GetRxMessage(&can_handle, FDCAN_RX_FIFO1, &rx_msg_header, rx_msg_data);

    return result;
}

// Get the data bitrate configuration of the CAN peripheral
struct can_bitrate_cfg can_get_data_bitrate_cfg(void)
{
    return can_bitrate_data;
}

// Get the nominal bitrate configuration of the CAN peripheral
struct can_bitrate_cfg can_get_bitrate_cfg(void)
{
    return can_bitrate_nominal;
}

// Return reference to CAN handle
FDCAN_HandleTypeDef *can_get_handle(void)
{
    return &can_handle;
}

// Return bus status
enum can_bus_state can_get_bus_state(void)
{
    return can_bus_state;
}
