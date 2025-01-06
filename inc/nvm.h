#ifndef _NVM_H
#define _NVM_H

// Prototypes
void nvm_init(void);
uint16_t nvm_get_serial_number(void);
HAL_StatusTypeDef nvm_update_serial_number(uint16_t num);

#endif // _NVM_H
