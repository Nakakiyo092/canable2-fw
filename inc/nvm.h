#ifndef _NVM_H
#define _NVM_H

// Prototypes
void nvm_init(void);
HAL_StatusTypeDef nvm_get_serial_number(uint16_t *num);
HAL_StatusTypeDef nvm_update_serial_number(uint16_t num);

HAL_StatusTypeDef nvm_apply_startup_cfg(void);
HAL_StatusTypeDef nvm_update_startup_cfg(uint8_t mode);

#endif // _NVM_H
