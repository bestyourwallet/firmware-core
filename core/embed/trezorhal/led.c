#include "led.h"
#include "stm32h7xx_hal.h"

#define LED_GPIO_PORT GPIOJ
#define LED_GPIO_PIN GPIO_PIN_5
#define LED_GPIO_CLK_EN() __HAL_RCC_GPIOJ_CLK_ENABLE()

uint8_t led_init(void) {
  LED_GPIO_CLK_EN();

  GPIO_InitTypeDef GPIO_InitStruct = {0};
  GPIO_InitStruct.Pin = LED_GPIO_PIN;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;

  HAL_GPIO_Init(LED_GPIO_PORT, &GPIO_InitStruct);

  led_off();
  return 0;
}

uint8_t led_on(void) {
  HAL_GPIO_WritePin(LED_GPIO_PORT, LED_GPIO_PIN, GPIO_PIN_SET);
  return 0;
}

uint8_t led_off(void) {
  HAL_GPIO_WritePin(LED_GPIO_PORT, LED_GPIO_PIN, GPIO_PIN_RESET);
  return 0;
}
