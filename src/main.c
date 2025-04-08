//
// CANable2 firmware
//

#include "stm32g4xx.h"
#include "stm32g4xx_hal.h"
#include "buffer.h"
#include "can.h"
#include "led.h"
#include "nvm.h"
#include "printf.h"
#include "slcan.h"
#include "system.h"

int main(void)
{
    // Initialize peripherals
    system_init();
    led_init();
    buf_init();
    can_init();
    nvm_init();

    // Power-on blink sequence
    led_blink_sequence(5);

    nvm_apply_startup_cfg();

    while (1)
    {
        led_process();
        can_process();
        buf_process();
    }
}
