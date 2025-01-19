#ifndef __USBD_CDC_IF_H__
#define __USBD_CDC_IF_H__

#include "usbd_cdc.h"

extern USBD_CDC_ItfTypeDef USBD_Interface_fops_FS;

// Prototypes
void cdc_transmit(uint8_t* buf, uint16_t len);
void cdc_process(void);


#endif
