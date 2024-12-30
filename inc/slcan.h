#ifndef _SLCAN_H
#define _SLCAN_H

// Timestamp mode
enum slcan_timestamp_mode
{
    SLCAN_TIMESTAMP_OFF = 0,
    SLCAN_TIMESTAMP_RX_MILI,
    //SLCAN_TIMESTAMP_RX_MICRO,     // Reserved
    //SLCAN_TIMESTAMP_RXTX_MILI,    // TODO
    //SLCAN_TIMESTAMP_RXTX_MICRO,   // Maybe

    SLCAN_TIMESTAMP_INVALID,
};

// Maximum rx buffer len
#define SLCAN_MTU (1 + 8 + 1 + 128 + 4 + 1 + 16) /* cmd 1 plus id 8 plus dlc 1 plus data 128 plus timestamp 4 plus \r plus some padding */
#define SLCAN_STD_ID_LEN 3
#define SLCAN_EXT_ID_LEN 8

// Prototypes
int32_t slcan_parse_frame(uint8_t *buf, FDCAN_RxHeaderTypeDef *frame_header, uint8_t *frame_data);
void slcan_parse_str(uint8_t *buf, uint8_t len);

// TODO: move to helper c file
int8_t hal_dlc_code_to_bytes(uint32_t hal_dlc_code);

#endif // _SLCAN_H
