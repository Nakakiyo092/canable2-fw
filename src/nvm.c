//
// nvm: read and write to non-volatile memory
//

#include "stm32g4xx_hal.h"
#include "can.h"
#include "error.h"
#include "led.h"
#include "nvm.h"
#include "slcan.h"

// Memory status
enum nvm_memory_status
{
    NVM_MEMORY_WRITTEN = 0x0,
    NVM_MEMORY_INVALID,

    NVM_MEMORY_CLEARED = 0xF
};

#define NVM_PAGE_NUMBER_DATA      (63)                          /* Page number of data area (see RM0440-5.3.1) */
#define NVM_ERASE_OK              (0xFFFFFFFF)
#define NVM_ADDR_ORIGIN           (0x0801F800)                  /* Start address of data area in flash */
#define NVM_ADDR_SERIAL_NUMBER    (NVM_ADDR_ORIGIN + 0x000UL)
#define NVM_ADDR_STP_CONFIG       (NVM_ADDR_ORIGIN + 0x008UL)   /* Auto startup configuration */
#define NVM_ADDR_STP_NOM_BITRATE  (NVM_ADDR_ORIGIN + 0x010UL)
#define NVM_ADDR_STP_DATA_BITRATE (NVM_ADDR_ORIGIN + 0x018UL)

#define NVM_EXTRACT_MEM_STS(val)  ((uint8_t)(((val) >> 60) & 0x0F))

// Private variables
static uint64_t nvm_serial_number_raw;
static uint64_t nvm_stp_config_raw;
static uint64_t nvm_stp_nom_bitrate_raw;
static uint64_t nvm_stp_data_bitrate_raw;

// Private methods
static HAL_StatusTypeDef nvm_write_to_flash(uint64_t num_new, uint64_t stp_cfg_new, uint64_t stp_nom_new, uint64_t stp_data_new);

// Read data from non-volatile memory and store it in RAM
void nvm_init(void)
{
    // Read data form flash and store it in private variable (RAM)
    nvm_serial_number_raw = *(uint64_t *)NVM_ADDR_SERIAL_NUMBER;
    nvm_stp_config_raw = *(uint64_t *)NVM_ADDR_STP_CONFIG;
    nvm_stp_nom_bitrate_raw = *(uint64_t *)NVM_ADDR_STP_NOM_BITRATE;
    nvm_stp_data_bitrate_raw = *(uint64_t *)NVM_ADDR_STP_DATA_BITRATE;

    return;
}

// Get serial number
HAL_StatusTypeDef nvm_get_serial_number(uint16_t *num)
{
    if (NVM_EXTRACT_MEM_STS(nvm_serial_number_raw) == NVM_MEMORY_WRITTEN)
    {
        *num = (uint16_t)(nvm_serial_number_raw & 0xFFFF);
        return HAL_OK;
    }
    return HAL_ERROR;
}

// Update serial number
HAL_StatusTypeDef nvm_update_serial_number(uint16_t num)
{
    // Check if the serial number is the same
    if ((uint64_t)num == nvm_serial_number)
    {
        return HAL_OK;
    }

    // Write to the flash
    if (nvm_write_to_flash((uint64_t)num, nvm_stp_config_raw, nvm_stp_nom_bitrate_raw, nvm_stp_data_bitrate_raw) != HAL_OK)
    {
        return HAL_ERROR;
    }

    return HAL_OK;
}

// Apply auto startup configuration
HAL_StatusTypeDef nvm_apply_startup_cfg(void)
{
    // Check if the memory is written
    if (NVM_EXTRACT_MEM_STS(nvm_stp_config_raw) != NVM_MEMORY_WRITTEN)
        return HAL_ERROR;
    if (NVM_EXTRACT_MEM_STS(nvm_stp_nom_bitrate_raw) != NVM_MEMORY_WRITTEN)
        return HAL_ERROR;
    if (NVM_EXTRACT_MEM_STS(nvm_stp_data_bitrate_raw) != NVM_MEMORY_WRITTEN)
        return HAL_ERROR;

    // Read and apply the main configuration
    uint8_t startup_mode = (uint8_t)(nvm_stp_config_raw & 0xF);

    if (startup_mode == SLCAN_AUTO_STARTUP_OFF)
        return HAL_OK;

    if (SLCAN_AUTO_STARTUP_INVALID <= startup_mode)
        return HAL_ERROR;

    uint8_t timestamp_mode = (uint8_t)((nvm_serial_number_raw >> 8) & 0xF);

    if (SLCAN_TIMESTAMP_INVALID <= timestamp_mode)
        return HAL_ERROR;

    slcan_set_timestamp_mode(timestamp_mode);

    // Read and apply bitrate
    struct can_bitrate_cfg bitrate;
    bitrate.prescaler = (uint16_t)((nvm_stp_nom_bitrate_raw) & 0xFF);
    bitrate.time_seg1 = (uint8_t)((nvm_stp_nom_bitrate_raw >> 8) & 0xFF);
    bitrate.time_seg2 = (uint8_t)((nvm_stp_nom_bitrate_raw >> 16) & 0xFF);
    bitrate.sjw = (uint8_t)((nvm_stp_nom_bitrate_raw >> 24) & 0xFF);
    can_set_bitrate_cfg(bitrate);

    bitrate.prescaler = (uint16_t)((nvm_stp_data_bitrate_raw) & 0xFF);
    bitrate.time_seg1 = (uint8_t)((nvm_stp_data_bitrate_raw >> 8) & 0xFF);
    bitrate.time_seg2 = (uint8_t)((nvm_stp_data_bitrate_raw >> 16) & 0xFF);
    bitrate.sjw = (uint8_t)((nvm_stp_data_bitrate_raw >> 24) & 0xFF);
    can_set_data_bitrate_cfg(bitrate);

    // Start the CAN peripheral
    if (startup_mode == SLCAN_AUTO_STARTUP_NORMAL)
    {
        error_clear();

        // Default to normal mode
        if (can_set_mode(FDCAN_MODE_NORMAL) != HAL_OK)
            return HAL_ERROR;

        // Open CAN port
        if (can_enable() != HAL_OK)
            return HAL_ERROR;

        return HAL_OK;
    }
    else if (startup_mode == SLCAN_AUTO_STARTUP_LISTEN)
    {
        error_clear();

        // Mode silent
        if (can_set_mode(FDCAN_MODE_BUS_MONITORING) != HAL_OK)
            return HAL_ERROR;

        // Open CAN port
        if (can_enable() != HAL_OK)
            return HAL_ERROR;

        return HAL_OK;
    }       
    return HAL_ERROR;
}

// Update auto startup configuration
HAL_StatusTypeDef nvm_update_startup_cfg(enum slcan_auto_startup_mode mode)
{
    // Make raw data for startup configuration
    uint64_t startup_cfg = 0;

    if (0xFF < mode) return HAL_ERROR;
    startup_cfg = (startup_cfg & mode)

    if (0xFF < slcan_get_timestamp_mode(void)) return HAL_ERROR;
    startup_cfg = (startup_cfg & (slcan_get_timestamp_mode(void) << 8));

    // Make raw data for nominal bitrate
    uint64_t nom_bitrate = 0;

    if (0xFF < can_get_bitrate_cfg().prescaler) return HAL_ERROR;
    nom_bitrate = (nom_bitrate & can_get_bitrate_cfg().prescaler);
    nom_bitrate = (nom_bitrate & (can_get_bitrate_cfg().time_seg1 << 8));
    nom_bitrate = (nom_bitrate & (can_get_bitrate_cfg().time_seg2 << 16));
    nom_bitrate = (nom_bitrate & (can_get_bitrate_cfg().sjw << 24));


    // Make raw data for data bitrate
    uint64_t data_bitrate = 0;

    if (0xFF < can_get_data_bitrate_cfg().prescaler) return HAL_ERROR;
    data_bitrate = (data_bitrate & can_get_data_bitrate_cfg().prescaler);
    data_bitrate = (data_bitrate & (can_get_data_bitrate_cfg().time_seg1 << 8));
    data_bitrate = (data_bitrate & (can_get_data_bitrate_cfg().time_seg2 << 16));
    data_bitrate = (data_bitrate & (can_get_data_bitrate_cfg().sjw << 24));

    // Check if the configuration is the same
    if (startup_cfg == nvm_stp_config_raw)
        if (nom_bitrate == nvm_stp_nom_bitrate_raw && data_bitrate == nvm_stp_data_bitrate_raw)
            return HAL_OK;

    // Write to the flash
    if (nvm_write_to_flash(nvm_serial_number_raw, startup_cfg, nom_bitrate, data_bitrate) != HAL_OK)
    {
        return HAL_ERROR;
    }
    
    return HAL_OK;
}

// Write data to the data area in flash memory
HAL_StatusTypeDef nvm_write_to_flash(uint64_t num_new, uint64_t stp_cfg_new, uint64_t stp_nom_new, uint64_t stp_data_new)
{
    // Unlock the flash
    HAL_FLASH_Unlock();
    
    // Erase the page
    FLASH_EraseInitTypeDef erase;
    erase.TypeErase = FLASH_TYPEERASE_PAGES;
    erase.Banks = FLASH_BANK_1;
    erase.Page = NVM_PAGE_NUMBER_DATA;
    erase.NbPages = 1;

    uint32_t error = 0;
    HAL_FLASHEx_Erase(&erase, &error);
    if (error != NVM_ERASE_OK)
    {
        HAL_FLASH_Lock();
        return HAL_ERROR;
    }

    // Write serial number to flash
    if (HAL_FLASH_Program(FLASH_TYPEPROGRAM_DOUBLEWORD, NVM_ADDR_SERIAL_NUMBER, num_new) != HAL_OK)
    {
        HAL_FLASH_Lock();
        return HAL_ERROR;
    }

    // Copy to RAM
    nvm_serial_number_raw = num_new;

    // Write startup config to flash
    if (HAL_FLASH_Program(FLASH_TYPEPROGRAM_DOUBLEWORD, NVM_ADDR_STP_CONFIG, stp_cfg_new) != HAL_OK)
    {
        HAL_FLASH_Lock();
        return HAL_ERROR;
    }

    // Copy to RAM
    nvm_stp_config_raw = stp_cfg_new;

    // Write nominal bitrate to flash
    if (HAL_FLASH_Program(FLASH_TYPEPROGRAM_DOUBLEWORD, NVM_ADDR_STP_NOM_BITRATE, stp_nom_new) != HAL_OK)
    {
        HAL_FLASH_Lock();
        return HAL_ERROR;
    }

    // Copy to RAM
    nvm_stp_nom_bitrate_raw = stp_nom_new;

    // Write data bitrate to flash
    if (HAL_FLASH_Program(FLASH_TYPEPROGRAM_DOUBLEWORD, NVM_ADDR_STP_DATA_BITRATE, stp_data_new) != HAL_OK)
    {
        HAL_FLASH_Lock();
        return HAL_ERROR;
    }

    // Copy to RAM
    nvm_stp_data_bitrate_raw = stp_data_new;

    // Lock the flash
    HAL_FLASH_Lock();
    return HAL_OK;
}
