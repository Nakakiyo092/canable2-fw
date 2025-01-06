//
// nvm: read and write to non-volatile memory
//

#include "stm32g4xx_hal.h"
#include "nvm.h"

// Definitions
#define NVM_PAGE_NUMBER_DATA      (63)                           /* Page number of data area (see RM0440-5.3.1) */
#define NVM_ERASE_OK              (0xFFFFFFFF)
#define NVM_ADDR_ORIGIN           (0x0801F800)                   /* Start address of data area in flash */
#define NVM_ADDR_SERIAL_NUMBER    (NVM_ADDR_ORIGIN + 0x000UL)

// Private variables
static uint16_t nvm_serial_number = 0;

// Read data from non-volatile memory and store it in RAM
void nvm_init(void)
{
    // read serial number and store it in private variable
    uint64_t serial = *(uint64_t *)NVM_ADDR_SERIAL_NUMBER;
    nvm_serial_number = (uint16_t)serial;

    return;
}

// Get serial number
uint16_t nvm_get_serial_number(void)
{
    return nvm_serial_number;
}

// Update serial number
uint32_t nvm_update_serial_number(uint16_t num)
{
    // Check if the serial number is the same
    if (num == nvm_serial_number)
    {
        return HAL_OK;
    }

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

    // Program the flash
    if (HAL_FLASH_Program(FLASH_TYPEPROGRAM_DOUBLEWORD, NVM_ADDR_SERIAL_NUMBER, (uint32_t)num) != HAL_OK)
    {
        HAL_FLASH_Lock();
        return HAL_ERROR;
    }

    // Lock the flash
    HAL_FLASH_Lock();
    return HAL_OK;
}

