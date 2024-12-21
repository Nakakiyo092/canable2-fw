#ifndef _LED_H
#define _LED_H

// GPIO definitions
#define LED_BLUE_Pin GPIO_PIN_15
#define LED_BLUE_Port GPIOA
#define LED_BLUE LED_BLUE_Port , LED_BLUE_Pin

#define LED_GREEN_Pin GPIO_PIN_0
#define LED_GREEN_Port GPIOA
#define LED_GREEN LED_GREEN_Port , LED_GREEN_Pin


// Duration of LED blink
#define LED_DURATION 25

#define LED_ON (0u)
#define LED_OFF (1u)

// Prototypes
void led_init();
void led_blue_blink(uint8_t numblinks);
void led_green_on(void);
void led_green_off(void);
void led_blue_on(void);
void led_process(void);

#endif
