//
// LED: handles blinking of status lights
//

#include "stm32g4xx_hal.h"
#include "led.h"
#include "error.h"

// Duration in ms
#define LED_BLINK_DURATION    (25)

// Private variables
static volatile uint32_t led_blue_laston = 0;
static volatile uint32_t led_green_laston = 0;
static uint32_t led_blue_lastoff = 0;
static uint32_t led_green_lastoff = 0;
static uint8_t led_error_was_indicating = 0;

static uint32_t led_cycle_max_time_us = 0;

// Initialize LED GPIOs
void led_init()
{
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();

    GPIO_InitTypeDef GPIO_InitStruct;
    GPIO_InitStruct.Pin = LED_BLUE_Pin;
    GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
    GPIO_InitStruct.Pull = GPIO_PULLUP;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    GPIO_InitStruct.Alternate = 0;
    HAL_GPIO_Init(LED_BLUE_Port, &GPIO_InitStruct);

    HAL_GPIO_WritePin(LED_BLUE, LED_ON);

    GPIO_InitStruct.Pin = LED_GREEN_Pin;
    GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
    GPIO_InitStruct.Pull = GPIO_PULLUP;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
    GPIO_InitStruct.Alternate = 0;
    HAL_GPIO_Init(LED_GREEN_Port, &GPIO_InitStruct);

    HAL_GPIO_WritePin(LED_GREEN, LED_ON);
}

// Turn green LED on/off
void led_turn_green(enum led_state state)
{
    HAL_GPIO_WritePin(LED_GREEN, state);
}

// Blink two LEDs (blocking)
void led_blink_sequence(uint8_t numblinks)
{
    uint8_t i;
    for (i = 0; i < numblinks; i++)
    {
        HAL_GPIO_WritePin(LED_BLUE, LED_ON);
        HAL_GPIO_WritePin(LED_GREEN, LED_OFF);
        HAL_Delay(100);
        HAL_GPIO_WritePin(LED_BLUE, LED_OFF);
        HAL_GPIO_WritePin(LED_GREEN, LED_ON);
        HAL_Delay(100);
    }
}

// Turn green LED on for a short duration
void led_blink_green(void)
{
    // Make sure the LED has been off for at least LED_BLINK_DURATION before turning on again
    // This prevents a solid status LED on a busy canbus
    if (led_green_laston == 0 && HAL_GetTick() - led_green_lastoff > LED_BLINK_DURATION)
    {
        HAL_GPIO_WritePin(LED_GREEN, LED_ON);
        led_green_laston = HAL_GetTick();
    }
}

// Turn blue LED on for a short duration
void led_blink_blue(void)
{
    // Make sure the LED has been off for at least LED_BLINK_DURATION before turning on again
    // This prevents a solid status LED on a busy canbus
    if (led_blue_laston == 0 && HAL_GetTick() - led_blue_lastoff > LED_BLINK_DURATION)
    {
        HAL_GPIO_WritePin(LED_BLUE, LED_ON);
        led_blue_laston = HAL_GetTick();
    }
}

// Process time-based LED events
void led_process(void)
{

    // If error occurred in the last LED_ERROR_DURATION, override LEDs with constant on
    if (error_get_register())
    {
        HAL_GPIO_WritePin(LED_BLUE, LED_ON);
        HAL_GPIO_WritePin(LED_GREEN, LED_ON);
        led_error_was_indicating = 1;
    }
    // Otherwise, normal LED operation
    else
    {
        // If we were blinking but no longer are blinking, turn the LEDs back off.
        if (led_error_was_indicating)
        {
            HAL_GPIO_WritePin(LED_BLUE, LED_OFF);
            HAL_GPIO_WritePin(LED_GREEN, LED_OFF);
            led_error_was_indicating = 0;
        }

        // If LED has been on for long enough, turn it off
        if (led_blue_laston > 0 && HAL_GetTick() - led_blue_laston > LED_BLINK_DURATION)
        {
            HAL_GPIO_WritePin(LED_BLUE, LED_OFF);
            led_blue_laston = 0;
            led_blue_lastoff = HAL_GetTick();
        }

        // If LED has been on for long enough, turn it off
        if (led_green_laston > 0 && HAL_GetTick() - led_green_laston > LED_BLINK_DURATION)
        {
            // Invert LED
            HAL_GPIO_WritePin(LED_GREEN, LED_OFF);
            led_green_laston = 0;
            led_green_lastoff = HAL_GetTick();
        }
    }
    
    // TODO: Move to somewhere
    // Cycle time for debug function
    static uint32_t last_tick_ms = 0;
    static uint16_t cnt = 0;
    uint32_t curr_tick_ms = HAL_GetTick();
    cnt++;
    if (cnt >= 10000)
    {
        if (led_cycle_max_time_us * 1000 < curr_tick_ms - last_tick_ms)
        {
            led_cycle_max_time_us = (curr_tick_ms - last_tick_ms) / 10;     // * 1000 (ms -> us) / 10000 (cycle)
        }
        last_tick_ms = curr_tick_ms;
        cnt = 0;
    }
}

uint8_t led_get_cycle_max_time(void)
{
    if (0xFF < led_cycle_max_time_us)
        return 0xFF;
    else
        return (uint8_t)led_cycle_max_time_us;
}

void led_clear_cycle_max_time(void)
{
    led_cycle_max_time_us = 0;
}
