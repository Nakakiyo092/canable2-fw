//
// slcan: parse incoming and generate outgoing slcan messages
//

#include <string.h>
#include "stm32g4xx_hal.h"
#include "usbd_cdc_if.h"
#include "buffer.h"
#include "can.h"
#include "error.h"
#include "led.h"
#include "nvm.h"
#include "slcan.h"

// Status flags, value is bit position in the status flags
enum slcan_status_flag
{
    SLCAN_STS_CAN_RX_FIFO_FULL = 0, /* Message loss. Not mean the buffer is just full. */
    SLCAN_STS_CAN_TX_FIFO_FULL,     /* Message loss. Not mean the buffer is just full. */
    SLCAN_STS_ERROR_WARNING,
    SLCAN_STS_DATA_OVERRUN,
    SLCAN_STS_RESERVED,
    SLCAN_STS_ERROR_PASSIVE,
    SLCAN_STS_ARBITRATION_LOST,     /* Not supported */
    SLCAN_STS_BUS_ERROR
};

// Report flag, value is bit position in the register
enum slcan_report_flag
{
    SLCAN_REPORT_RX = 0,
    SLCAN_REPORT_TX,
    //SLCAN_REPORT_ERROR,
    //SLCAN_REPORT_OVRLOAD,
    SLCAN_REPORT_ESI = 4,
};

// Filter mode
enum slcan_filter_mode
{
    // SLCAN_FILTER_DUAL_MODE = 0,     // Not supported
    // SLCAN_FILTER_SINGLE_MODE,       // Not supported
    SLCAN_FILTER_SIMPLE_ID_MODE = 2,

    SLCAN_FILTER_INVALID
};

#define SLCAN_VERSION   "VL2K1"
#define SLCAN_RET_OK    ((uint8_t *)"\x0D")
#define SLCAN_RET_ERR   ((uint8_t *)"\x07")
#define SLCAN_RET_LEN   (1)

// Private variables
static char *hw_sw_ver = SLCAN_VERSION "\r";
static char *hw_sw_ver_detail = "v: hardware=\"CANable2.0\", software=\"" GIT_VERSION "\", url=\"" GIT_REMOTE "\"\r";
static char *can_info = "I30A0\r";
static char *can_info_detail = "i: protocol=\"ISO-CANFD\", clock_mhz=160, controller=\"STM32G431CB\"\r";
static enum slcan_timestamp_mode slcan_timestamp_mode = 0;
static uint16_t slcan_report_reg = 1;   // Default: no timestamp, no ESI, no Tx, but with Rx
static uint32_t slcan_filter_code = 0x00000000;
static uint32_t slcan_filter_mask = 0xFFFFFFFF;

// Private methods
static int32_t slcan_parse_frame(uint8_t *buf, FDCAN_RxHeaderTypeDef *frame_header, uint8_t *frame_data);
static HAL_StatusTypeDef slcan_convert_str_to_number(uint8_t *buf, uint8_t len);
static void slcan_parse_str_open(uint8_t *buf, uint8_t len);
static void slcan_parse_str_loop(uint8_t *buf, uint8_t len);
static void slcan_parse_str_close(uint8_t *buf, uint8_t len);
static void slcan_parse_str_set_bitrate(uint8_t *buf, uint8_t len);
static void slcan_parse_str_report_mode(uint8_t *buf, uint8_t len);
static void slcan_parse_str_filter_mode(uint8_t *buf, uint8_t len);
static void slcan_parse_str_filter_code(uint8_t *buf, uint8_t len);
static void slcan_parse_str_filter_mask(uint8_t *buf, uint8_t len);
static void slcan_parse_str_version(uint8_t *buf, uint8_t len);
static void slcan_parse_str_can_info(uint8_t *buf, uint8_t len);
static void slcan_parse_str_number(uint8_t *buf, uint8_t len);
static void slcan_parse_str_status(uint8_t *buf, uint8_t len);
static void slcan_parse_str_auto_startup(uint8_t *buf, uint8_t len);
static uint32_t __std_dlc_code_to_hal_dlc_code(uint8_t dlc_code);
static uint8_t __hal_dlc_code_to_std_dlc_code(uint32_t hal_dlc_code);

// Parse a CAN frame into a slcan message
int32_t slcan_parse_frame(uint8_t *buf, FDCAN_RxHeaderTypeDef *frame_header, uint8_t *frame_data)
{
    // Start building the slcan message string at idx 0 in buf[]
    uint8_t msg_idx = 0;

    // Handle classic CAN frames
    if (frame_header->FDFormat == FDCAN_CLASSIC_CAN)
    {
        // Add character for frame type
        if (frame_header->RxFrameType == FDCAN_DATA_FRAME)
        {
            buf[msg_idx] = 't';
        }
        else if (frame_header->RxFrameType == FDCAN_REMOTE_FRAME)
        {
            buf[msg_idx] = 'r';
        }
    }
    // Handle FD CAN frames
    else
    {
        // FD doesn't support remote frames so this must be a data frame

        // Frame with BRS enabled
        if (frame_header->BitRateSwitch == FDCAN_BRS_ON)
        {
            buf[msg_idx] = 'b';
        }
        // Frame with BRS disabled
        else
        {
            buf[msg_idx] = 'd';
        }
    }

    // Assume standard identifier
    uint8_t id_len = SLCAN_STD_ID_LEN;
    uint32_t tmp = frame_header->Identifier;

    // Check if extended
    if (frame_header->IdType == FDCAN_EXTENDED_ID)
    {
        // Convert first char to upper case for extended frame
        buf[msg_idx] -= 32;
        id_len = SLCAN_EXT_ID_LEN;
        tmp = frame_header->Identifier;
    }
    msg_idx++;

    // Add identifier to buffer
    for (uint8_t j = id_len; j > 0; j--)
    {
        // Add nibble to buffer
        buf[j] = (tmp & 0xF);
        tmp = tmp >> 4;
        msg_idx++;
    }

    // Add DLC to buffer
    buf[msg_idx++] = __hal_dlc_code_to_std_dlc_code(frame_header->DataLength);
    int8_t bytes = hal_dlc_code_to_bytes(frame_header->DataLength);

    // Check bytes value
    if (bytes < 0)
        return -1;
    if (bytes > 64)
        return -1;

    // Add data bytes
    // Data frame only. No data bytes for a remote frame.
    if (frame_header->RxFrameType != FDCAN_REMOTE_FRAME)
    {
        for (uint8_t j = 0; j < bytes; j++)
        {
            buf[msg_idx++] = (frame_data[j] >> 4);
            buf[msg_idx++] = (frame_data[j] & 0x0F);
        }
    }

    // Add time stamp
    static uint16_t slcan_last_timestamp_ms = 0;
    static uint32_t slcan_last_timestamp_us = 0;
    static uint32_t slcan_last_time_ms = 0;
    static uint16_t slcan_last_time_us = 0;
    if (slcan_timestamp_mode == SLCAN_TIMESTAMP_MILLI)
    {
        uint32_t current_time_ms = HAL_GetTick();
        uint32_t time_diff_ms;

        time_diff_ms = (uint32_t)(current_time_ms - slcan_last_time_ms);

        slcan_last_timestamp_ms = (uint16_t)(((uint32_t)slcan_last_timestamp_ms + time_diff_ms % 60000) % 60000);
        slcan_last_time_ms = current_time_ms;

        buf[msg_idx++] = ((slcan_last_timestamp_ms >> 12) & 0xF);
        buf[msg_idx++] = ((slcan_last_timestamp_ms >> 8) & 0xF);
        buf[msg_idx++] = ((slcan_last_timestamp_ms >> 4) & 0xF);
        buf[msg_idx++] = (slcan_last_timestamp_ms & 0xF);
    }
    else if (slcan_timestamp_mode == SLCAN_TIMESTAMP_MICRO)
    {
        uint32_t current_time_ms = HAL_GetTick();
        uint16_t current_time_us = frame_header->RxTimestamp; // MAX 0xFFFF
        uint32_t time_diff_ms;
        uint64_t time_diff_us;
        uint64_t n_comp;
        uint32_t t_comp_us = ((uint64_t)UINT16_MAX + 1);                // MAX 0x10000

        if (slcan_last_time_ms <= current_time_ms)
            time_diff_ms = current_time_ms - slcan_last_time_ms;
        else
            time_diff_ms = UINT32_MAX - slcan_last_time_ms + 1 + current_time_ms;

        time_diff_us = (uint64_t)((uint16_t)(current_time_us - slcan_last_time_us));

        // Compensate overflow of micro second counter
        if (t_comp_us != 0)     // Proper bit time only (avoid zero-div)
        {
            n_comp = ((uint64_t)time_diff_ms * 1000 - time_diff_us + t_comp_us / 2);    // MAX 0xFFFFFFFF * 1000, 0xFFFF, 0x10000
            n_comp = n_comp / t_comp_us;                            // MAX 0xFFFF * 1000 + ?
            time_diff_us = time_diff_us + n_comp * t_comp_us;       // MAX 0xFFFF * 1000 * 0x10000
        }

        slcan_last_timestamp_us = (uint32_t)(((uint64_t)slcan_last_timestamp_us + time_diff_us) % 3600000000);
        slcan_last_time_ms = current_time_ms;
        slcan_last_time_us = current_time_us;

        buf[msg_idx++] = ((slcan_last_timestamp_us >> 28) & 0xF);
        buf[msg_idx++] = ((slcan_last_timestamp_us >> 24) & 0xF);
        buf[msg_idx++] = ((slcan_last_timestamp_us >> 20) & 0xF);
        buf[msg_idx++] = ((slcan_last_timestamp_us >> 16) & 0xF);
        buf[msg_idx++] = ((slcan_last_timestamp_us >> 12) & 0xF);
        buf[msg_idx++] = ((slcan_last_timestamp_us >> 8) & 0xF);
        buf[msg_idx++] = ((slcan_last_timestamp_us >> 4) & 0xF);
        buf[msg_idx++] = (slcan_last_timestamp_us & 0xF);
    }
    
    // Add error state indicator
    // FD frame only. No ESI for a classical frame.
    if ((slcan_report_reg >> SLCAN_REPORT_ESI) & 1)
    {
        if (frame_header->FDFormat == FDCAN_FD_CAN)
        {
            if (frame_header->ErrorStateIndicator == FDCAN_ESI_ACTIVE)
                buf[msg_idx++] = 0;
            else
                buf[msg_idx++] = 1;
        }
    }

    // Convert to ASCII (2nd character to end)
    for (uint8_t j = 1; j < msg_idx; j++)
    {
        if (buf[j] < 0xA)
        {
            buf[j] += 0x30;
        }
        else
        {
            buf[j] += 0x37;
        }
    }

    // Add CR for slcan EOL
    buf[msg_idx++] = '\r';

    // Return string length
    return msg_idx;
}

// Parse an incoming CAN frame into an outgoing slcan message
int32_t slcan_parse_rx_frame(uint8_t *buf, FDCAN_RxHeaderTypeDef *frame_header, uint8_t *frame_data)
{
    // Rx reporting not required
    if (((slcan_report_reg >> SLCAN_REPORT_RX) & 1) == 0)
        return 0;

    if (buf == NULL)
        return 0;

    int32_t msg_idx = slcan_parse_frame(buf, frame_header, frame_data);

    // Return string length
    return msg_idx;
}

// Parse an incoming Tx event into an outgoing slcan message
int32_t slcan_parse_tx_event(uint8_t *buf, FDCAN_TxEventFifoTypeDef *tx_event, uint8_t *frame_data)
{
    // Tx reporting not required
    if (((slcan_report_reg >> SLCAN_REPORT_TX) & 1) == 0)
        return 0;

    if (buf == NULL)
        return 0;

    if (tx_event->IdType == FDCAN_STANDARD_ID)
        buf[0] = 'z';
    else
        buf[0] = 'Z';

    FDCAN_RxHeaderTypeDef frame_header;
    frame_header.Identifier = tx_event->Identifier;
    frame_header.IdType = tx_event->IdType;
    frame_header.RxFrameType = tx_event->TxFrameType;
    frame_header.DataLength = tx_event->DataLength;
    frame_header.ErrorStateIndicator = tx_event->ErrorStateIndicator;
    frame_header.BitRateSwitch = tx_event->BitRateSwitch;
    frame_header.FDFormat = tx_event->FDFormat;
    frame_header.RxTimestamp = tx_event->TxTimestamp;
    int32_t msg_idx = slcan_parse_frame(&buf[1], &frame_header, frame_data);

    // Return string length
    return msg_idx + 1;
}

// Parse an incoming slcan command from the USB CDC port
void slcan_parse_str(uint8_t *buf, uint8_t len)
{
    // Blink blue LED as slcan rx if bus closed
    if (can_get_bus_state() == BUS_CLOSED) led_blink_blue();

    // Reply OK to a blank command
    if (len == 0)
    {
        buf_enqueue_cdc(SLCAN_RET_OK, SLCAN_RET_LEN);
        return;
    }

    // Convert an incoming slcan command from ASCII to number (2nd character to end)
    if (slcan_convert_str_to_number(buf, len) != HAL_OK)
    {
        buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }

    // Handle each incoming command
    switch (buf[0])
    {
    // Open channel
    case 'O':
    case 'L':
        slcan_parse_str_open(buf, len);
        return;
    // Open channel (loopback mode)
    case '=':
    case '+':
        slcan_parse_str_loop(buf, len);
        return;
    // Close channel
    case 'C':
        slcan_parse_str_close(buf, len);
        return;
    // Set bitrate
    case 'S':
    case 's':
    case 'Y':
    case 'y':
        slcan_parse_str_set_bitrate(buf, len);
        return;
    // Get version number in standard + detailed style
    case 'V':
    case 'v':
        slcan_parse_str_version(buf, len);
        return;
    // Get CAN controller information
    case 'I':
    case 'i':
        slcan_parse_str_can_info(buf, len);
        return;
    // Get serial number
    case 'N':
        slcan_parse_str_number(buf, len);
        return;
    // Read status flags
    case 'F':
    case 'f':
        slcan_parse_str_status(buf, len);
        return;
    // Set report mode
    case 'Z':
    case 'z':
        slcan_parse_str_report_mode(buf, len);
        return;
    // Set filter mode
    case 'W':
        slcan_parse_str_filter_mode(buf, len);
        return;
    // Set filter code
    case 'M':
        slcan_parse_str_filter_code(buf, len);
        return;
    // Set filter mask
    case 'm':
        slcan_parse_str_filter_mask(buf, len);
        return;
    // Set auto startup mode
    case 'Q':
        slcan_parse_str_auto_startup(buf, len);
        return;
    // Debug function
    case '?':
    {
        //char* dbgstr = (char*)buf_get_cdc_dest();
        //snprintf(dbgstr, SLCAN_MTU - 1, "?%02X-%02X-%01X-%04X%04X-%04X\r",
        //                            (uint8_t)(can_get_cycle_ave_time_ns() >= 255000 ? 255 : can_get_cycle_ave_time_ns() / 1000),
        //                            (uint8_t)(can_get_cycle_max_time_ns() >= 255000 ? 255 : can_get_cycle_max_time_ns() / 1000),
        //                            (uint8_t)(HAL_FDCAN_GetState(can_get_handle())),
        //                            (uint16_t)(HAL_FDCAN_GetError(can_get_handle()) >> 16),
        //                            (uint16_t)(HAL_FDCAN_GetError(can_get_handle()) & 0xFFFF),
        //                            (uint16_t)(error_get_register()));
        //buf_comit_cdc_dest(23);

        uint8_t cycle_ave = (uint8_t)(can_get_cycle_ave_time_ns() >= 255000 ? 255 : can_get_cycle_ave_time_ns() / 1000);
        uint8_t cycle_max = (uint8_t)(can_get_cycle_max_time_ns() >= 255000 ? 255 : can_get_cycle_max_time_ns() / 1000);
        //char *dbgstr = "?XX-XX\r";
        uint8_t dbgstr[7];
        dbgstr[0] = '?';
        dbgstr[1] = cycle_ave >> 4;
        dbgstr[2] = cycle_ave & 0xF;
        for (uint8_t j = 1; j <= 2; j++)
        {
            if (dbgstr[j] < 0xA)
                dbgstr[j] += 0x30;
            else
                dbgstr[j] += 0x37;
        }
        dbgstr[3] = '-';
        dbgstr[4] = cycle_max >> 4;
        dbgstr[5] = cycle_max & 0xF;
        for (uint8_t j = 4; j <= 5; j++)
        {
            if (dbgstr[j] < 0xA)
                dbgstr[j] += 0x30;
            else
                dbgstr[j] += 0x37;
        }
        dbgstr[6] = '\r';
        buf_enqueue_cdc((uint8_t *)dbgstr, 7);

        can_clear_cycle_time();
        return;
    }
    default:
        break;
    }

    // Set default header. All values overridden below as needed.
    FDCAN_TxHeaderTypeDef *frame_header = buf_get_can_dest_header();
    uint8_t *frame_data = buf_get_can_dest_data();

    if (frame_header == NULL || frame_data == NULL)
    {
        buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }

    frame_header->TxFrameType = FDCAN_DATA_FRAME;                // default to data frame
    frame_header->FDFormat = FDCAN_CLASSIC_CAN;                  // default to classic frame
    frame_header->IdType = FDCAN_STANDARD_ID;                    // default to standard ID
    frame_header->BitRateSwitch = FDCAN_BRS_OFF;                 // no bitrate switch
    frame_header->ErrorStateIndicator = FDCAN_ESI_ACTIVE;        // error active
    frame_header->TxEventFifoControl = FDCAN_STORE_TX_EVENTS;    // record tx events
    frame_header->MessageMarker = 0;                             // ?

    // Handle each incoming command (transmit)
    switch (buf[0])
    {
    // Transmit remote frame command
    case 'r':
        frame_header->TxFrameType = FDCAN_REMOTE_FRAME;
        break;
    case 'R':
        frame_header->IdType = FDCAN_EXTENDED_ID;
        frame_header->TxFrameType = FDCAN_REMOTE_FRAME;
        break;

    // Transmit data frame command
    case 'T':
        frame_header->IdType = FDCAN_EXTENDED_ID;
        break;
    case 't':
        break;

    // CANFD transmit - no BRS
    case 'd':
        frame_header->FDFormat = FDCAN_FD_CAN;
        break;
        // frame_header->BitRateSwitch = FDCAN_BRS_ON
    case 'D':
        frame_header->FDFormat = FDCAN_FD_CAN;
        frame_header->IdType = FDCAN_EXTENDED_ID;
        // Transmit CANFD frame
        break;

    // CANFD transmit - with BRS
    case 'b':
        frame_header->FDFormat = FDCAN_FD_CAN;
        frame_header->BitRateSwitch = FDCAN_BRS_ON;
        break;
        // Fallthrough
    case 'B':
        frame_header->FDFormat = FDCAN_FD_CAN;
        frame_header->BitRateSwitch = FDCAN_BRS_ON;
        frame_header->IdType = FDCAN_EXTENDED_ID;
        break;
        // Transmit CANFD frame
        break;

    case 'X':
// TODO: Firmware update
#warning "TODO: Implement firmware update via command"
        break;

    // Invalid command
    default:
        buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }

    // Start parsing at second byte (skip command byte)
    uint8_t parse_loc = 1;

    // Zero out identifier
    frame_header->Identifier = 0;

    // Default to standard ID
    uint8_t id_len = SLCAN_STD_ID_LEN;

    // Update length if message is extended ID
    if (frame_header->IdType == FDCAN_EXTENDED_ID)
        id_len = SLCAN_EXT_ID_LEN;

    // Iterate through ID bytes
    while (parse_loc <= id_len)
    {
        frame_header->Identifier *= 16;
        frame_header->Identifier += buf[parse_loc++];
    }

    // If CAN ID is too large
    if (frame_header->IdType == FDCAN_STANDARD_ID && 0x7FF < frame_header->Identifier)
    {
        buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }
    else if (frame_header->IdType == FDCAN_EXTENDED_ID && 0x1FFFFFFF < frame_header->Identifier)
    {
        buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }    

    // Attempt to parse DLC and check sanity
    uint8_t dlc_code_raw = buf[parse_loc++];

    // If dlc is too long for an FD frame
    if (frame_header->FDFormat == FDCAN_FD_CAN && dlc_code_raw > 0xF)
    {
        buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }
    // If dlc is too long for an classical frame
    if (frame_header->FDFormat == FDCAN_CLASSIC_CAN)
    {
        if (frame_header->TxFrameType == FDCAN_DATA_FRAME && dlc_code_raw > 0x8)
        {
            buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
            return;
        }
        else if  (frame_header->TxFrameType == FDCAN_REMOTE_FRAME && dlc_code_raw > 0xF)
        {
            buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
            return;
        }
    }

    // Set TX frame DLC according to HAL
    frame_header->DataLength = __std_dlc_code_to_hal_dlc_code(dlc_code_raw);

    // Calculate number of bytes we expect in the message
    int8_t bytes_in_msg = hal_dlc_code_to_bytes(frame_header->DataLength);

    if ((bytes_in_msg < 0) || (bytes_in_msg > 64))
    {
        buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }

    // Parse data
    // Data frame only. No data bytes for a remote frame.
    if (frame_header->TxFrameType != FDCAN_REMOTE_FRAME)
    {
        // TODO: Guard against walking off the end of the string!
        for (uint8_t i = 0; i < bytes_in_msg; i++)
        {
            frame_data[i] = (buf[parse_loc] << 4) + buf[parse_loc + 1];
            parse_loc += 2;
        }
    }

    // Check command length
    // parse_loc is always updated after a byte is parsed
    if (len != parse_loc)
    {
        buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }

    // Transmit the message
    if (buf_comit_can_dest() == HAL_OK)
    {
        if (((slcan_report_reg >> SLCAN_REPORT_TX) & 1) == 0)
        {
            // Send ACK (not neccessary if tx event is reported)
            if (frame_header->IdType == FDCAN_EXTENDED_ID)
                buf_enqueue_cdc((uint8_t *)"Z\r", 2);
            else
                buf_enqueue_cdc((uint8_t *)"z\r", 2);
        }
    }
    else
    {
        buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }

    return;
}

// Convert from ASCII to number (2nd character to end)
HAL_StatusTypeDef slcan_convert_str_to_number(uint8_t *buf, uint8_t len)
{
    // Convert from ASCII (2nd character to end)
    for (uint8_t i = 1; i < len; i++)
    {
        // Numbers
        if ('0' <= buf[i] && buf[i] <= '9')
            buf[i] = buf[i] - '0';
        // Lowercase letters
        else if ('a' <= buf[i] && buf[i] <= 'f')
            buf[i] = buf[i] - 'a' + 10;
        // Uppercase letters
        else if ('A' <= buf[i] && buf[i] <= 'F')
            buf[i] = buf[i] - 'A' + 10;
        // Invalid character
        else
            return HAL_ERROR;
    }
    return HAL_OK;
}

// Open channel
void slcan_parse_str_open(uint8_t *buf, uint8_t len)
{
    // Check command length
    if (len != 1)
    {
        buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }

    error_clear();
    can_clear_cycle_time();

    if (buf[0] == 'O')
    {
        // Mode default
        if (can_set_mode(FDCAN_MODE_NORMAL) != HAL_OK)
        {
            buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
            return;
        }
    }
    else if (buf[0] == 'L')
    {
        // Mode silent
        if (can_set_mode(FDCAN_MODE_BUS_MONITORING) != HAL_OK)
        {
            buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
            return;
        }
    }
    // Open CAN port
    if (can_enable() != HAL_OK)
        buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
    else
        buf_enqueue_cdc(SLCAN_RET_OK, SLCAN_RET_LEN);

    return;
}

// Open channel (loopback mode)
void slcan_parse_str_loop(uint8_t *buf, uint8_t len)
{
    // Check command length
    if (len != 1)
    {
        buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }

    error_clear();
    can_clear_cycle_time();

    // Mode loopback
    if (buf[0] == '+')
    {
        if (can_set_mode(FDCAN_MODE_EXTERNAL_LOOPBACK) != HAL_OK)
        {
            buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
            return;
        }
    }
    else
    {
        if (can_set_mode(FDCAN_MODE_INTERNAL_LOOPBACK) != HAL_OK)
        {
            buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
            return;
        }
    }
    // Open CAN port
    if (can_enable() != HAL_OK)
        buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
    else
        buf_enqueue_cdc(SLCAN_RET_OK, SLCAN_RET_LEN);

    return;
}

// Close channel
void slcan_parse_str_close(uint8_t *buf, uint8_t len)
{
    // Check command length
    if (len != 1)
    {
        buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }
    // Close CAN port
    if (can_disable() == HAL_OK)
        buf_enqueue_cdc(SLCAN_RET_OK, SLCAN_RET_LEN);
    else
        buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);

    error_clear();
    can_clear_cycle_time();

    return;
}

// Set nominal bitrate
void slcan_parse_str_set_bitrate(uint8_t *buf, uint8_t len)
{
    if (buf[0] == 'S' || buf[0] == 'Y')
    {
        // Check for valid length
        if (len != 2)
        {
            buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
            return;
        }
        HAL_StatusTypeDef ret;
        if (buf[0] == 'S')
            ret = can_set_bitrate(buf[1]);
        else
            ret = can_set_data_bitrate(buf[1]);

        if (ret == HAL_OK)
            buf_enqueue_cdc(SLCAN_RET_OK, SLCAN_RET_LEN);
        else
            buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
    }
    else if (buf[0] == 's' || buf[0] == 'y')
    {
        // Check for valid length
        if (len != 9)
        {
            buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
            return;
        }

        struct can_bitrate_cfg bitrate_cfg;
        bitrate_cfg.prescaler = ((uint16_t)buf[1] << 4) + buf[2];
        bitrate_cfg.time_seg1 = ((uint16_t)buf[3] << 4) + buf[4];
        bitrate_cfg.time_seg2 = ((uint16_t)buf[5] << 4) + buf[6];
        bitrate_cfg.sjw = ((uint16_t)buf[7] << 4) + buf[8];

        HAL_StatusTypeDef ret;
        if (buf[0] == 's')
            ret = can_set_bitrate_cfg(bitrate_cfg);
        else
            ret = can_set_data_bitrate_cfg(bitrate_cfg);

        if (ret == HAL_OK)
            buf_enqueue_cdc(SLCAN_RET_OK, SLCAN_RET_LEN);
        else
            buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
    }
    return;
}

// Set report mode
void slcan_parse_str_report_mode(uint8_t *buf, uint8_t len)
{
    // Set report mode
    if (can_get_bus_state() == BUS_CLOSED)
    {
        if (buf[0] == 'Z')
        {
            // Check for valid command
            if (len != 2 || SLCAN_TIMESTAMP_INVALID <= buf[1])
            {
                buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
                return;
            }

            slcan_timestamp_mode = buf[1];
            slcan_report_reg = 1;   // Default: no timestamp, no ESI, no Tx, but with Rx
            buf_enqueue_cdc(SLCAN_RET_OK, SLCAN_RET_LEN);
            return;
        }
        else if (buf[0] == 'z')
        {
            // Check for valid command
            if (len != 5 || SLCAN_TIMESTAMP_INVALID <= buf[1])
            {
                buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
                return;
            }

            slcan_timestamp_mode = buf[1];
            slcan_report_reg = (buf[3] << 4) + buf[4];
            buf_enqueue_cdc(SLCAN_RET_OK, SLCAN_RET_LEN);
            return;
        }
    }
    // This command is only active if the CAN channel is closed.
    else
    {
        buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }
}

// Set filter mode
void slcan_parse_str_filter_mode(uint8_t *buf, uint8_t len)
{
    // Set filter mode
    if (can_get_bus_state() == BUS_CLOSED)
    {
        // Check for valid command
        if (len != 2 || SLCAN_FILTER_INVALID <= buf[1])
        {
            buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
            return;
        }

        // Check if the filter mode is supported
        if (buf[1] != SLCAN_FILTER_SIMPLE_ID_MODE)
        {
            buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
            return;
        }

        buf_enqueue_cdc(SLCAN_RET_OK, SLCAN_RET_LEN);
        return;
    }
    // Command can only be sent if CAN232 is initiated but not open.
    else
    {
        buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }
}


// Set filter code
void slcan_parse_str_filter_code(uint8_t *buf, uint8_t len)
{
    // Set filter code
    if (can_get_bus_state() == BUS_CLOSED)
    {
        // Check for valid command
        if (len != 9)
        {
            buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
            return;
        }

        slcan_filter_code = 0;
        for (uint8_t i = 0; i < 8; i++)
        {
            slcan_filter_code = (slcan_filter_code << 4) + buf[1 + i];
        }
        
        FunctionalState state_std = ENABLE;
        FunctionalState state_ext = ENABLE;
        if ((slcan_filter_code >> 31) && !(slcan_filter_mask >> 31))
        {
            state_ext = DISABLE;
        }
        else if (!(slcan_filter_code >> 31) && !(slcan_filter_mask >> 31))
        {
            state_std = DISABLE;
        }

        // Mask definition, SLCAN: 0 -> Enable, STM32: 1 -> Enable
        if (can_set_filter_std(state_std, slcan_filter_code & 0x7FF, (~slcan_filter_mask) & 0x7FF) != HAL_OK)
        {
            buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
            return;
        }
        if (can_set_filter_ext(state_ext, slcan_filter_code & 0x1FFFFFFF, (~slcan_filter_mask) & 0x1FFFFFFF) != HAL_OK)
        {
            buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
            return;
        }
        buf_enqueue_cdc(SLCAN_RET_OK, SLCAN_RET_LEN);
        return;
    }
    // This command is only active if the CAN channel is initiated and not opened.
    else
    {
        buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }
}


// Set filter mask
void slcan_parse_str_filter_mask(uint8_t *buf, uint8_t len)
{
    // Set filter code
    if (can_get_bus_state() == BUS_CLOSED)
    {
        // Check for valid command
        if (len != 9)
        {
            buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
            return;
        }

        slcan_filter_mask = 0;
        for (uint8_t i = 0; i < 8; i++)
        {
            slcan_filter_mask = (slcan_filter_mask << 4) + buf[1 + i];
        }

        FunctionalState state_std = ENABLE;
        FunctionalState state_ext = ENABLE;
        if ((slcan_filter_code >> 31) && !(slcan_filter_mask >> 31))
        {
            state_ext = DISABLE;
        }
        else if (!(slcan_filter_code >> 31) && !(slcan_filter_mask >> 31))
        {
            state_std = DISABLE;
        }

        // Mask definition, SLCAN: 0 -> Enable, STM32: 1 -> Enable
        if (can_set_filter_std(state_std, slcan_filter_code & 0x7FF, (~slcan_filter_mask) & 0x7FF) != HAL_OK)
        {
            buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
            return;
        }
        if (can_set_filter_ext(state_ext, slcan_filter_code & 0x1FFFFFFF, (~slcan_filter_mask) & 0x1FFFFFFF) != HAL_OK)
        {
            buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
            return;
        }
        buf_enqueue_cdc(SLCAN_RET_OK, SLCAN_RET_LEN);
        return;
    }
    // This command is only active if the CAN channel is initiated and not opened.
    else
    {
        buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }
}

// Get version number in standard + detailed style
void slcan_parse_str_version(uint8_t *buf, uint8_t len)
{
    // Check command length
    if (len != 1)
    {
        buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }

    if (buf[0] == 'V')
        buf_enqueue_cdc((uint8_t *)hw_sw_ver, strlen(hw_sw_ver));
    else if (buf[0] == 'v')
        buf_enqueue_cdc((uint8_t *)hw_sw_ver_detail, strlen(hw_sw_ver_detail));

    return;
}

// Get can controller information
void slcan_parse_str_can_info(uint8_t *buf, uint8_t len)
{
    // Check command length
    if (len != 1)
    {
        buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }

    if (buf[0] == 'I')
        buf_enqueue_cdc((uint8_t *)can_info, strlen(can_info));
    else if (buf[0] == 'i')
        buf_enqueue_cdc((uint8_t *)can_info_detail, strlen(can_info_detail));

    return;
}

// Get serial number
void slcan_parse_str_number(uint8_t *buf, uint8_t len)
{
    if (len == 1)
    {
        // Report serial number
        uint16_t serial;
        char* numstr = (char*)buf_get_cdc_dest();
        if (nvm_get_serial_number(&serial) == HAL_OK)
        {
            snprintf(numstr, SLCAN_MTU - 1, "N%04X\r", serial);
            buf_comit_cdc_dest(6);
        }
        else
        {
            buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
        }
        return;
    }
    else if (len == 5)
    {
        // Set serial number
        uint16_t serial = ((uint16_t)buf[1] << 12) + ((uint16_t)buf[2] << 8) + ((uint16_t)buf[3] << 4) + buf[4];
        if (nvm_update_serial_number(serial) == HAL_OK)
            buf_enqueue_cdc(SLCAN_RET_OK, SLCAN_RET_LEN);
        else
            buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }
    else
    {
        buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }
}

// Read status flags
void slcan_parse_str_status(uint8_t *buf, uint8_t len)
{
    // Check command length
    if (len != 1)
    {
        buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }

    // Return the status flags
    if (can_get_bus_state() == BUS_OPENED)
    {
        if (buf[0] == 'F')
        {
            uint8_t status = 0;
            uint32_t err_reg = error_get_register();

            status = ((err_reg >> ERR_CAN_RXFAIL) & 1) ? (status | (1 << SLCAN_STS_DATA_OVERRUN)) : status;
            status = ((err_reg >> ERR_CAN_TXFAIL) & 1) ? (status | (1 << SLCAN_STS_DATA_OVERRUN)) : status;
            status = ((err_reg >> ERR_FULLBUF_CANTX) & 1) ? (status | (1 << SLCAN_STS_CAN_TX_FIFO_FULL)) : status;
            status = ((err_reg >> ERR_FULLBUF_USBRX) & 1) ? (status | (1 << SLCAN_STS_CAN_TX_FIFO_FULL)) : status;
            status = ((err_reg >> ERR_FULLBUF_USBTX) & 1) ? (status | (1 << SLCAN_STS_CAN_RX_FIFO_FULL)) : status;
            status = ((err_reg >> ERR_CAN_BUS_ERR) & 1) ? (status | (1 << SLCAN_STS_BUS_ERROR)) : status;
            status = ((err_reg >> ERR_CAN_WARNING) & 1) ? (status | (1 << SLCAN_STS_ERROR_WARNING)) : status;
            status = ((err_reg >> ERR_CAN_ERR_PASSIVE) & 1) ? (status | (1 << SLCAN_STS_ERROR_PASSIVE)) : status;
            status = ((err_reg >> ERR_CAN_BUS_OFF) & 1) ? (status | (1 << SLCAN_STS_ERROR_WARNING)) : status;

            char* stsstr = (char*)buf_get_cdc_dest();
            snprintf(stsstr, SLCAN_MTU - 1, "F%02X\r", status);
            buf_comit_cdc_dest(4);

            // This command also clear the RED Error LED.
            error_clear();
        }
        else if (buf[0] == 'f')
        {
            char* stsstr = (char*)buf_get_cdc_dest();

            struct can_error_state err = can_get_error_state();

            snprintf(stsstr, SLCAN_MTU - 1, "f: node_sts=%s, last_err_code=%s, err_cnt_tx_rx=[0x%02X, 0x%02X], est_bus_load_percent=%02d\r",
                                        (err.bus_off ? "BUS_OFF" : (err.err_pssv ? "ER_PSSV" : "ER_ACTV")),
                                        (err.last_err_code == FDCAN_PROTOCOL_ERROR_NONE ? "NONE" : 
                                        (err.last_err_code == FDCAN_PROTOCOL_ERROR_STUFF ? "STUF" : 
                                        (err.last_err_code == FDCAN_PROTOCOL_ERROR_FORM ? "FORM" : 
                                        (err.last_err_code == FDCAN_PROTOCOL_ERROR_ACK ? "_ACK" : 
                                        (err.last_err_code == FDCAN_PROTOCOL_ERROR_BIT1 ? "BIT1" : 
                                        (err.last_err_code == FDCAN_PROTOCOL_ERROR_BIT0 ? "BIT0" : 
                                        (err.last_err_code == FDCAN_PROTOCOL_ERROR_CRC ? "_CRC" : "SAME"))))))),
                                        (uint8_t)(err.tec),
                                        (uint8_t)(err.rec),
                                        (uint8_t)(can_get_bus_load_ppm() >= 990000 ? 99 : (can_get_bus_load_ppm() / 50000) * 5));
                                        //(uint8_t)(HAL_FDCAN_GetState(can_get_handle())),
                                        //(uint16_t)(HAL_FDCAN_GetError(can_get_handle()) >> 16),
                                        //(uint16_t)(HAL_FDCAN_GetError(can_get_handle()) & 0xFFFF),
                                        //(uint8_t)((sts.BusOff << 2) + (sts.ErrorPassive << 1) + sts.Warning),

            buf_comit_cdc_dest(93);
        }
    }
    // This command is only active if the CAN channel is open.
    else
    {
        buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
    }
    return;
}

// Set auto startup mode
void slcan_parse_str_auto_startup(uint8_t *buf, uint8_t len)
{
    // Set auto startup mode
    if (can_get_bus_state() == BUS_OPENED)
    {
        // Check for valid command
        if (len != 2 || SLCAN_AUTO_STARTUP_INVALID <= buf[1])
        {
            buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
            return;
        }

        if (nvm_update_startup_cfg(buf[1]) != HAL_OK)
            buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
        else
            buf_enqueue_cdc(SLCAN_RET_OK, SLCAN_RET_LEN);
            
        return;
    }
    // Command works only when CAN channel is open.
    else
    {
        buf_enqueue_cdc(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }
}

// Set the timestamp mode
void slcan_set_timestamp_mode(enum slcan_timestamp_mode mode)
{
    if (mode < SLCAN_TIMESTAMP_INVALID)
        slcan_timestamp_mode = mode;
    return;
}

// Set the report setting register
void slcan_set_report_register(uint16_t reg)
{
    slcan_report_reg = reg;
    return;
}

// Report the current timestamp mode
enum slcan_timestamp_mode slcan_get_timestamp_mode(void)
{
    return slcan_timestamp_mode;
}

// Report the current report setting register value
uint16_t slcan_get_report_register(void)
{
    return slcan_report_reg;
}

// Convert a FDCAN_data_length_code to number of bytes in a message
int8_t hal_dlc_code_to_bytes(uint32_t hal_dlc_code)
{
    switch (hal_dlc_code)
    {
    case FDCAN_DLC_BYTES_0:
        return 0;
    case FDCAN_DLC_BYTES_1:
        return 1;
    case FDCAN_DLC_BYTES_2:
        return 2;
    case FDCAN_DLC_BYTES_3:
        return 3;
    case FDCAN_DLC_BYTES_4:
        return 4;
    case FDCAN_DLC_BYTES_5:
        return 5;
    case FDCAN_DLC_BYTES_6:
        return 6;
    case FDCAN_DLC_BYTES_7:
        return 7;
    case FDCAN_DLC_BYTES_8:
        return 8;
    case FDCAN_DLC_BYTES_12:
        return 12;
    case FDCAN_DLC_BYTES_16:
        return 16;
    case FDCAN_DLC_BYTES_20:
        return 20;
    case FDCAN_DLC_BYTES_24:
        return 24;
    case FDCAN_DLC_BYTES_32:
        return 32;
    case FDCAN_DLC_BYTES_48:
        return 48;
    case FDCAN_DLC_BYTES_64:
        return 64;
    default:
        return -1;
    }
}

// Convert a standard 0-F CANFD length code to a FDCAN_data_length_code
// TODO: make this a macro
static uint32_t __std_dlc_code_to_hal_dlc_code(uint8_t dlc_code)
{
    return (uint32_t)dlc_code << 16;
}

// Convert a FDCAN_data_length_code to a standard 0-F CANFD length code
// TODO: make this a macro
static uint8_t __hal_dlc_code_to_std_dlc_code(uint32_t hal_dlc_code)
{
    return hal_dlc_code >> 16;
}

