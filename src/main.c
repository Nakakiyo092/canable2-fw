//
// CANable2 firmware
//

#include "stm32g4xx.h"
#include "printf.h"
#include "usb_device.h"
#include "usbd_cdc_if.h"
#include "can.h"
#include "slcan.h"
#include "system.h"
#include "led.h"

int main(void)
{
    // Initialize peripherals
    system_init();
    can_init();
    led_init();
    usb_init();

    // Power-on blink sequence
    led_blue_blink(2);

    while (1)
    {
        led_process();
        can_process();
        cdc_process();
    }
}
