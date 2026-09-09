#include STM32_HAL_H

#if !BOOT_ONLY
#include "fpsensor_platform.h"
#include "gt911.h"
#endif
#include "fingerprint.h"
#include "spi_legacy.h"

void EXTI2_IRQHandler(void) { HAL_GPIO_EXTI_IRQHandler(GPIO_PIN_2); }

void EXTI15_10_IRQHandler(void) {
  // fp sensor irq
  HAL_GPIO_EXTI_IRQHandler(GPIO_PIN_15);
  // spi cs irq
  HAL_GPIO_EXTI_IRQHandler(GPIO_PIN_11);
}

void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin) {
#if !BOOT_ONLY
  // uint8_t irq_status[2];
  // fp sensor irq
  if (GPIO_Pin == GPIO_PIN_15) {
    // TODO: DEV fp
    FP_MODE fp_mode = get_fingerprint_model();
    if (fp_mode == FP_MODE_NORMAL) {
      fingerprint_handle_sensor_interrupt();
      fpsensor_state_set(true);
      fpsensor_irq_disable();
    } else if (fp_mode == FP_MODE_BUTTON) {
      GPIO_PinState fp_int_pin = HAL_GPIO_ReadPin(GPIOA, GPIO_PIN_15);
      if (fp_int_pin == GPIO_PIN_SET) {
        set_fingerprint_button_state(FP_BUTTON_STATE_PRESSED);
      } else {
        set_fingerprint_button_state(FP_BUTTON_STATE_RELEASED);
      }
    }
  }
  // touch panel irq
  else if (GPIO_Pin == GPIO_PIN_2) {
    gt911_read_location();
  }
#endif
  // spi cs irq
  if (GPIO_Pin == GPIO_PIN_11) {
    spi_cs_irq_handler();
  }
}
