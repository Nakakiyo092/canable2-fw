#ifndef _SLCAN_H
#define _SLCAN_H

// Timestamp mode
enum slcan_timestamp_mode
{
    SLCAN_TIMESTAMP_OFF = 0,
    SLCAN_TIMESTAMP_MILI,
    SLCAN_TIMESTAMP_MICRO,

    SLCAN_TIMESTAMP_INVALID
};

// Startup mode
enum slcan_auto_startup_mode
{
    SLCAN_AUTO_STARTUP_OFF = 0,
    SLCAN_AUTO_STARTUP_NORMAL,
    SLCAN_AUTO_STARTUP_LISTEN,

    SLCAN_AUTO_STARTUP_INVALID
};

// Maximum rx buffer len
#define SLCAN_MTU           (1 + 138 + 8 + 1 + 1 + 16) 
                            /* tx z/Z plus frame 138 plus timestamp 8 plus ESI plus \r plus some padding */
#define SLCAN_STD_ID_LEN    (3)
#define SLCAN_EXT_ID_LEN    (8)

// Prototypes
int32_t slcan_parse_rx_frame(uint8_t *buf, FDCAN_RxHeaderTypeDef *frame_header, uint8_t *frame_data);
int32_t slcan_parse_tx_event(uint8_t *buf, FDCAN_TxEventFifoTypeDef *tx_event, uint8_t *frame_data);
void slcan_parse_str(uint8_t *buf, uint8_t len);
void slcan_set_timestamp_mode(enum slcan_timestamp_mode mode);
void slcan_set_report_register(uint16_t reg);
enum slcan_timestamp_mode slcan_get_timestamp_mode(void);
uint16_t slcan_get_report_register(void);

// TODO: move to helper c file
int8_t hal_dlc_code_to_bytes(uint32_t hal_dlc_code);

#endif // _SLCAN_H
