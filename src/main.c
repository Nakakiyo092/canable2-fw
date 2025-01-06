//
// CANable2 firmware
//

#include "stm32g4xx.h"
#include "printf.h"
#include "usb_device.h"
#include "usbd_cdc_if.h"
#include "can.h"
#include "led.h"
#include "nvm.h"
#include "slcan.h"
#include "system.h"

int main(void)
{
    // Initialize peripherals
    system_init();
    led_init();
    can_init();
    nvm_init();
    usb_init();

    // Power-on blink sequence
    led_blink_sequence(5);

    while (1)
    {
        led_process();
        can_process();
        cdc_process();
    }
}
