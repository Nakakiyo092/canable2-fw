//
// slcan: parse incoming and generate outgoing slcan messages
//

#include <string.h>
#include "stm32g4xx_hal.h"
#include "usbd_cdc_if.h"
#include "can.h"
#include "error.h"
#include "led.h"
#include "nvm.h"
#include "slcan.h"

// Status flags, value is bit position in the status flags
enum slcan_status_flag
{
    STS_CAN_RX_FIFO_FULL = 0, /* Probable message loss. Not mean the buffer is just full. */
    STS_CAN_TX_FIFO_FULL,     /* Probable message loss. Not mean the buffer is just full. */
};

#define SLCAN_RET_OK    ((uint8_t *)"\x0D")
#define SLCAN_RET_ERR   ((uint8_t *)"\x07")
#define SLCAN_RET_LEN   (1)

// Private variables
char *fw_id = "VL2K0 " GIT_VERSION " " GIT_REMOTE "\r";
static enum slcan_timestamp_mode slcan_timestamp_mode = 0;
static uint16_t slcan_last_timestamp = 0;
static uint32_t slcan_last_time_ms = 0;

// Private methods
static uint32_t __std_dlc_code_to_hal_dlc_code(uint8_t dlc_code);
static uint8_t __hal_dlc_code_to_std_dlc_code(uint32_t hal_dlc_code);
static HAL_StatusTypeDef slcan_convert_str_to_number(uint8_t *buf, uint8_t len);
static void slcan_parse_str_open(uint8_t *buf, uint8_t len);
static void slcan_parse_str_listen(uint8_t *buf, uint8_t len);
static void slcan_parse_str_loop(uint8_t *buf, uint8_t len);
static void slcan_parse_str_close(uint8_t *buf, uint8_t len);
static void slcan_parse_str_set_bitrate(uint8_t *buf, uint8_t len);
static void slcan_parse_str_set_data_bitrate(uint8_t *buf, uint8_t len);
static void slcan_parse_str_timestamp(uint8_t *buf, uint8_t len);
static void slcan_parse_str_version(uint8_t *buf, uint8_t len);
static void slcan_parse_str_number(uint8_t *buf, uint8_t len);
static void slcan_parse_str_status_flags(uint8_t *buf, uint8_t len);
static void slcan_parse_str_auto_startup(uint8_t *buf, uint8_t len);

// Parse an incoming CAN frame into an outgoing slcan message
int32_t slcan_parse_frame(uint8_t *buf, FDCAN_RxHeaderTypeDef *frame_header, uint8_t *frame_data)
{
    // Clear buffer
    for (uint8_t j = 0; j < SLCAN_MTU; j++)
        buf[j] = '\0';

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
    // TODO using RxTimestamp will create more accurate timestamp
    if (slcan_timestamp_mode == SLCAN_TIMESTAMP_RX_MILI)
    {
        uint32_t current_time_ms = HAL_GetTick();
        uint32_t time_diff;
        if (slcan_last_time_ms <= current_time_ms)
            time_diff = current_time_ms - slcan_last_time_ms;
        else
            time_diff = UINT32_MAX - slcan_last_time_ms + 1 + current_time_ms;

        slcan_last_timestamp = (slcan_last_timestamp + time_diff % 60000) % 60000;
        slcan_last_time_ms = current_time_ms;

        buf[msg_idx++] = ((slcan_last_timestamp >> 12) & 0xF);
        buf[msg_idx++] = ((slcan_last_timestamp >> 8) & 0xF);
        buf[msg_idx++] = ((slcan_last_timestamp >> 4) & 0xF);
        buf[msg_idx++] = (slcan_last_timestamp & 0xF);
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

// Parse an incoming slcan command from the USB CDC port
void slcan_parse_str(uint8_t *buf, uint8_t len)
{
    // Set default header. All values overridden below as needed.
    FDCAN_TxHeaderTypeDef frame_header =
        {
            .TxFrameType = FDCAN_DATA_FRAME,
            .FDFormat = FDCAN_CLASSIC_CAN,            // default to classic frame
            .IdType = FDCAN_STANDARD_ID,              // default to standard ID
            .BitRateSwitch = FDCAN_BRS_OFF,           // no bitrate switch
            .ErrorStateIndicator = FDCAN_ESI_ACTIVE,  // error active
            .TxEventFifoControl = FDCAN_NO_TX_EVENTS, // don't record tx events
            .MessageMarker = 0,                       // ?
        };
    uint8_t frame_data[64] = {0};

    // Blink blue LED as slcan rx if off bus
    if (can_get_bus_state() == OFF_BUS) led_blink_blue();

    // Reply OK to a blank command
    if (len == 0)
    {
        cdc_transmit(SLCAN_RET_OK, SLCAN_RET_LEN);
        return;
    }

    // Convert an incoming slcan command from ASCII to number (2nd character to end)
    if (slcan_convert_str_to_number(buf, len) != HAL_OK)
    {
        cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }

    // Handle each incoming command
    switch (buf[0])
    {
    // Open channel (normal mode)
    case 'O':
        slcan_parse_str_open(buf, len);
        return;
    // Open channel (silent mode)
    case 'L':
        slcan_parse_str_listen(buf, len);
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
    // Set nominal bitrate
    case 'S':
        slcan_parse_str_set_bitrate(buf, len);
        return;
    // Set data bitrate
    case 'Y':
        slcan_parse_str_set_data_bitrate(buf, len);
        return;
    // Get version number in standard + CANable style
    case 'V':
        slcan_parse_str_version(buf, len);
        return;
    // Get serial number
    case 'N':
        slcan_parse_str_number(buf, len);
        return;
    // Read status flags
    case 'F':
        slcan_parse_str_status_flags(buf, len);
        return;
    // Set timestamp on/off
    case 'Z':
        slcan_parse_str_timestamp(buf, len);
        return;
    // Set auto startup mode
    case 'Q':
        slcan_parse_str_auto_startup(buf, len);
        return;
    // Debug function
    case '?':
        char dbgstr[64] = {0};
        snprintf(dbgstr, 64, "?%02X\r", led_get_cycle_max_time());
        cdc_transmit((uint8_t *)dbgstr, strlen(dbgstr));
        led_clear_cycle_max_time();
        return;

    // Transmit remote frame command
    case 'r':
        frame_header.TxFrameType = FDCAN_REMOTE_FRAME;
        break;
    case 'R':
        frame_header.IdType = FDCAN_EXTENDED_ID;
        frame_header.TxFrameType = FDCAN_REMOTE_FRAME;
        break;

    // Transmit data frame command
    case 'T':
        frame_header.IdType = FDCAN_EXTENDED_ID;
        break;
    case 't':
        break;

    // CANFD transmit - no BRS
    case 'd':
        frame_header.FDFormat = FDCAN_FD_CAN;
        break;
        // frame_header.BitRateSwitch = FDCAN_BRS_ON
    case 'D':
        frame_header.FDFormat = FDCAN_FD_CAN;
        frame_header.IdType = FDCAN_EXTENDED_ID;
        // Transmit CANFD frame
        break;

    // CANFD transmit - with BRS
    case 'b':
        frame_header.FDFormat = FDCAN_FD_CAN;
        frame_header.BitRateSwitch = FDCAN_BRS_ON;
        break;
        // Fallthrough
    case 'B':
        frame_header.FDFormat = FDCAN_FD_CAN;
        frame_header.BitRateSwitch = FDCAN_BRS_ON;
        frame_header.IdType = FDCAN_EXTENDED_ID;
        break;
        // Transmit CANFD frame
        break;

    case 'X':
// TODO: Firmware update
#warning "TODO: Implement firmware update via command"
        break;

    // Invalid command
    default:
        cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }

    // Start parsing at second byte (skip command byte)
    uint8_t parse_loc = 1;

    // Zero out identifier
    frame_header.Identifier = 0;

    // Default to standard ID
    uint8_t id_len = SLCAN_STD_ID_LEN;

    // Update length if message is extended ID
    if (frame_header.IdType == FDCAN_EXTENDED_ID)
        id_len = SLCAN_EXT_ID_LEN;

    // Iterate through ID bytes
    while (parse_loc <= id_len)
    {
        frame_header.Identifier *= 16;
        frame_header.Identifier += buf[parse_loc++];
    }

    // If CAN ID is too large
    if (frame_header.IdType == FDCAN_STANDARD_ID && 0x7FF < frame_header.Identifier)
    {
        cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }
    else if (frame_header.IdType == FDCAN_EXTENDED_ID && 0x1FFFFFFF < frame_header.Identifier)
    {
        cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }    

    // Attempt to parse DLC and check sanity
    uint8_t dlc_code_raw = buf[parse_loc++];

    // If dlc is too long for an FD frame
    if (frame_header.FDFormat == FDCAN_FD_CAN && dlc_code_raw > 0xF)
    {
        cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }
    if (frame_header.FDFormat == FDCAN_CLASSIC_CAN)
    {
        if (frame_header.TxFrameType == FDCAN_DATA_FRAME && dlc_code_raw > 0x8)
        {
            cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
            return;
        }
        else if  (frame_header.TxFrameType == FDCAN_REMOTE_FRAME && dlc_code_raw > 0xF)
        {
            cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
            return;
        }
    }

    // Set TX frame DLC according to HAL
    frame_header.DataLength = __std_dlc_code_to_hal_dlc_code(dlc_code_raw);

    // Calculate number of bytes we expect in the message
    int8_t bytes_in_msg = hal_dlc_code_to_bytes(frame_header.DataLength);

    if ((bytes_in_msg < 0) || (bytes_in_msg > 64))
    {
        cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }

    // Parse data
    // Data frame only. No data bytes for a remote frame.
    if (frame_header.TxFrameType != FDCAN_REMOTE_FRAME)
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
        cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }

    // Transmit the message
    if (can_tx(&frame_header, frame_data) == HAL_OK)
    {
        char repstr[64] = {0};
        if (frame_header.IdType == FDCAN_EXTENDED_ID)
            snprintf(repstr, 64, "Z\r");
        else
            snprintf(repstr, 64, "z\r");
        cdc_transmit((uint8_t *)repstr, strlen(repstr));
    }
    else
    {
        cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
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

// Open channel (normal mode)
void slcan_parse_str_open(uint8_t *buf, uint8_t len)
{
    // Check command length
    if (len != 1)
    {
        cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }

    error_clear();
    // Default to normal mode
    if (can_set_mode(FDCAN_MODE_NORMAL) != HAL_OK)
    {
        cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }
    // Open CAN port
    if (can_enable() != HAL_OK)
    {
        cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }
    cdc_transmit(SLCAN_RET_OK, SLCAN_RET_LEN);
    return;
}

// Open channel (silent mode)
void slcan_parse_str_listen(uint8_t *buf, uint8_t len)
{
    // Check command length
    if (len != 1)
    {
        cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }

    error_clear();
    // Mode silent
    if (can_set_mode(FDCAN_MODE_BUS_MONITORING) != HAL_OK)
    {
        cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }
    // Open CAN port
    if (can_enable() != HAL_OK)
    {
        cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }
    cdc_transmit(SLCAN_RET_OK, SLCAN_RET_LEN);
    return;
}

// Open channel (loopback mode)
void slcan_parse_str_loop(uint8_t *buf, uint8_t len)
{
    // Check command length
    if (len != 1)
    {
        cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }

    error_clear();
    // Mode loopback
    if (buf[0] == '+')
    {
        if (can_set_mode(FDCAN_MODE_EXTERNAL_LOOPBACK) != HAL_OK)
        {
            cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
            return;
        }
    }
    else
    {
        if (can_set_mode(FDCAN_MODE_INTERNAL_LOOPBACK) != HAL_OK)
        {
            cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
            return;
        }
    }
    // Open CAN port
    if (can_enable() != HAL_OK)
    {
        cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }
    cdc_transmit(SLCAN_RET_OK, SLCAN_RET_LEN);
    return;
}

// Close channel
void slcan_parse_str_close(uint8_t *buf, uint8_t len)
{
    // Check command length
    if (len != 1)
    {
        cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }

    if (can_disable() == HAL_OK)
        cdc_transmit(SLCAN_RET_OK, SLCAN_RET_LEN);
    else
        cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
    error_clear();
    return;
}

// Set nominal bitrate
void slcan_parse_str_set_bitrate(uint8_t *buf, uint8_t len)
{
    // Check for valid bitrate
    if (len != 2 || CAN_BITRATE_INVALID <= buf[1])
    {
        cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }

    if (can_set_bitrate(buf[1]) == HAL_OK)
        cdc_transmit(SLCAN_RET_OK, SLCAN_RET_LEN);
    else
        cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
    return;
}

// Set data bitrate
void slcan_parse_str_set_data_bitrate(uint8_t *buf, uint8_t len)
{
    // Check for valid bitrate
    if (len != 2 || CAN_DATA_BITRATE_INVALID <= buf[1])
    {
        cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }

    if (can_set_data_bitrate(buf[1]) == HAL_OK)
        cdc_transmit(SLCAN_RET_OK, SLCAN_RET_LEN);
    else
        cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
    return;
}

// Set timestamp on/off
void slcan_parse_str_timestamp(uint8_t *buf, uint8_t len)
{
    // Set timestamp on/off
    if (can_get_bus_state() == OFF_BUS)
    {
        // Check for valid command
        if (len != 2 || SLCAN_TIMESTAMP_INVALID <= buf[1])
        {
            cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
            return;
        }

        slcan_timestamp_mode = buf[1];
        cdc_transmit(SLCAN_RET_OK, SLCAN_RET_LEN);
        return;
    }
    // This command is only active if the CAN channel is closed.
    else
    {
        cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }
}

// Get version number in standard + CANable style
void slcan_parse_str_version(uint8_t *buf, uint8_t len)
{
    // Check command length
    if (len != 1)
    {
        cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }

    // Report firmware version and remote
    cdc_transmit((uint8_t *)fw_id, strlen(fw_id));
    return;
}

// Get serial number
void slcan_parse_str_number(uint8_t *buf, uint8_t len)
{
    if (len == 1)
    {
        // Report serial number
        uint16_t serial;
        char numstr[64] = {0};
        if (nvm_get_serial_number(&serial) == HAL_OK)
        {
            snprintf(numstr, 64, "N%04X\r", serial);
            cdc_transmit((uint8_t *)numstr, strlen(numstr));
        }
        else
        {
            cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
        }
        return;
    }
    else if (len == 5)
    {
        // Set serial number
        uint16_t serial = ((uint16_t)buf[1] << 12) + ((uint16_t)buf[2] << 8) + ((uint16_t)buf[3] << 4) + buf[4];
        if (nvm_update_serial_number(serial) == HAL_OK)
            cdc_transmit(SLCAN_RET_OK, SLCAN_RET_LEN);
        else
            cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }
    else
    {
        cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }
}

// Read status flags
void slcan_parse_str_status_flags(uint8_t *buf, uint8_t len)
{
    // Check command length
    if (len != 1)
    {
        cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
        return;
    }

    // Return the status flags
    if (can_get_bus_state() == ON_BUS)
    {
        uint8_t status = 0;
        enum error_flag err_reg = error_get_register();

        status = ((err_reg >> ERR_CAN_RXFAIL) & 1) ? (status | (1 << STS_CAN_RX_FIFO_FULL)) : status;
        status = ((err_reg >> ERR_CAN_TXFAIL) & 1) ? (status | (1 << STS_CAN_TX_FIFO_FULL)) : status;
        status = ((err_reg >> ERR_FULLBUF_CANTX) & 1) ? (status | (1 << STS_CAN_TX_FIFO_FULL)) : status;
        status = ((err_reg >> ERR_FULLBUF_USBRX) & 1) ? (status | (1 << STS_CAN_TX_FIFO_FULL)) : status;
        status = ((err_reg >> ERR_FULLBUF_USBTX) & 1) ? (status | (1 << STS_CAN_RX_FIFO_FULL)) : status;

        char stsstr[64] = {0};
        snprintf(stsstr, 64, "F%02X\r", status);
        cdc_transmit((uint8_t *)stsstr, strlen(stsstr));
    }
    // This command is only active if the CAN channel is open.
    else
    {
        cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
    }
    // This command also clear the RED Error LED.
    error_clear();
    return;
}

// Set auto startup mode
void slcan_parse_str_auto_startup(uint8_t *buf, uint8_t len)
{
    // Set auto startup mode
    if (can_get_bus_state() == ON_BUS)
    {
        // Check for valid command
        if (len != 2 || SLCAN_AUTO_STARTUP_INVALID <= buf[1])
        {
            cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
            return;
        }

        if (nvm_update_startup_cfg(buf[1]) != HAL_OK)
        {
            cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
            return;
        }
        cdc_transmit(SLCAN_RET_OK, SLCAN_RET_LEN);
        return;
    }
    // Command works only when CAN channel is open.
    else
    {
        cdc_transmit(SLCAN_RET_ERR, SLCAN_RET_LEN);
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

// Report the current timestamp mode
enum slcan_timestamp_mode slcan_get_timestamp_mode(void)
{
    return slcan_timestamp_mode;
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

