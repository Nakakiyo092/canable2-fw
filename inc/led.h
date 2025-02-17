#ifndef _LED_H
#define _LED_H

// LED state
enum led_state
{
    LED_ON,
    LED_OFF
};

// GPIO definitions
#define LED_BLUE_Pin GPIO_PIN_15
#define LED_BLUE_Port GPIOA
#define LED_BLUE LED_BLUE_Port , LED_BLUE_Pin

#define LED_GREEN_Pin GPIO_PIN_11   // Original pinout
#define LED_GREEN_Port GPIOB        // Original pinout
//#define LED_GREEN_Pin GPIO_PIN_0    // For Walfront
//#define LED_GREEN_Port GPIOA        // For Walfront
#define LED_GREEN LED_GREEN_Port , LED_GREEN_Pin

// Prototypes
void led_init();
void led_turn_green(enum led_state state);
void led_blink_sequence(uint8_t numblinks);
void led_blink_green(void);
void led_blink_blue(void);
void led_process(void);

#endif
