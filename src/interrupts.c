//
// interrupts: handle global system interrupts
//

#include "stm32g4xx_hal.h"
#include "interrupts.h"
#include "can.h"
#include "led.h"
#include "tusb.h"

void NMI_Handler(void)
{
}

void HardFault_Handler(void)
{
  while (1)
  {
  }
}

void MemManage_Handler(void)
{
  while (1)
  {
  }
}

void BusFault_Handler(void)
{
  while (1)
  {
  }
}

void UsageFault_Handler(void)
{
  while (1)
  {
  }
}

void SVC_Handler(void)
{
}
void DebugMon_Handler(void)
{
}

void PendSV_Handler(void)
{
}

// Handle USB interrupts
void USB_LP_IRQHandler(void)
{
  tusb_int_handler(BOARD_TUD_RHPORT, true);
}
// Handle USB interrupts
void USB_HP_IRQHandler(void)
{
  tusb_int_handler(BOARD_TUD_RHPORT, true);
}

// Handle SysTick interrupt
void SysTick_Handler(void)
{
  HAL_IncTick();
  HAL_SYSTICK_IRQHandler();
}

//// Handle CAN interrupts
// void CEC_CAN_IRQHandler(void)
//{
//     HAL_CAN_IRQHandler(can_get_handle());
// }
