#ifndef _CAN_H
#define _CAN_H

// Classic CAN / CANFD nominal bitrates
enum can_bitrate
{
    CAN_BITRATE_10K = 0,
    CAN_BITRATE_20K,
    CAN_BITRATE_50K,
    CAN_BITRATE_100K,
    CAN_BITRATE_125K,
    CAN_BITRATE_250K,
    CAN_BITRATE_500K,
    CAN_BITRATE_750K,
    CAN_BITRATE_1000K,
    CAN_BITRATE_83_3K,

    CAN_BITRATE_INVALID,
};

// CANFD data bitrates
enum can_data_bitrate
{
    CAN_DATA_BITRATE_500K = 0,
    CAN_DATA_BITRATE_1M = 1,
    CAN_DATA_BITRATE_2M = 2,
    CAN_DATA_BITRATE_4M = 4,
    CAN_DATA_BITRATE_5M = 5,

    CAN_DATA_BITRATE_INVALID,
};

// Bus state
enum can_bus_state
{
    OFF_BUS,
    ON_BUS
};

// Structure for CAN/FD bitrate configuration
struct can_bitrate_cfg
{
    uint16_t prescaler;
    uint8_t time_seg1;
    uint8_t time_seg2;
    uint8_t sjw;
};

// Prototypes
void can_init(void);
HAL_StatusTypeDef can_enable(void);
HAL_StatusTypeDef can_disable(void);
HAL_StatusTypeDef can_set_bitrate(enum can_bitrate bitrate);
HAL_StatusTypeDef can_set_data_bitrate(enum can_data_bitrate bitrate);
HAL_StatusTypeDef can_set_bitrate_cfg(struct can_bitrate_cfg bitrate_cfg);
HAL_StatusTypeDef can_set_data_bitrate_cfg(struct can_bitrate_cfg bitrate_cfg);
HAL_StatusTypeDef can_set_mode(uint32_t mode);
void can_set_autoretransmit(uint8_t autoretransmit);
HAL_StatusTypeDef can_tx(FDCAN_TxHeaderTypeDef *tx_msg_header, uint8_t *tx_msg_data);
HAL_StatusTypeDef can_rx(FDCAN_RxHeaderTypeDef *rx_msg_header, uint8_t *rx_msg_data);
void can_process(void);
enum can_bus_state can_get_bus_state(void);
struct can_bitrate_cfg can_get_bitrate_cfg(void);
struct can_bitrate_cfg can_get_data_bitrate_cfg(void);
FDCAN_HandleTypeDef *can_get_handle(void);

#endif // _CAN_H
