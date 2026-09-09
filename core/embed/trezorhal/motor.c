#include "motor.h"

#include "systick.h"

#include "debug_utils.h"
#include "util_macros.h"

#define ExecuteCheck_HAL_OK(func_call) \
  ExecuteCheck_ADV(func_call, HAL_OK, { return false; })

// cc flag tweaks
#pragma GCC diagnostic ignored "-Wunused-function"
#pragma GCC diagnostic ignored "-Wunused-variable"

// do not include this file anywhere else
#include "motor_patterns.h"

// control status
static bool motor_busy = false;
static bool builtin_seq_cpu_play = false;

// motor action list
static MOTOR_ACTION* act_list_index_p = NULL;
static MOTOR_ACTION* act_list_index_p_max = NULL;

#ifndef USE_ROTOR_MOTOR
// only needed for linear motor sequence patterns (seq_* functions)
static MOTOR_ACTION act_list_combine[128] = {0};
#endif

#ifdef USE_ROTOR_MOTOR
// rotor motor PWM state
static volatile bool pwm_phase_on = false;
static volatile uint16_t pwm_cycles_remaining = 0;
static void rotor_start_segment(void);
#endif

// timer related
static TIM_HandleTypeDef TIM7_Handle;

// ===========================================================================
// GPIO Init / Deinit
// ===========================================================================
static void motor_io_init(void) {
  GPIO_InitTypeDef gpio;
  __HAL_RCC_GPIOK_CLK_ENABLE();

#ifdef USE_ROTOR_MOTOR
  // PK2 only (rotor motor)
  gpio.Pin = GPIO_PIN_2;
#else
  // PK2, PK3 (linear motor H-bridge)
  gpio.Pin = (GPIO_PIN_2 | GPIO_PIN_3);
#endif
  gpio.Mode = GPIO_MODE_OUTPUT_PP;
  gpio.Pull = GPIO_PULLDOWN;
  gpio.Speed = GPIO_SPEED_FREQ_LOW;
  gpio.Alternate = 0;
  HAL_GPIO_Init(GPIOK, &gpio);
}

static void motor_io_deinit(void) {
  // dont disable clock, as it may used by other peripherals
  // __HAL_RCC_GPIOK_CLK_DISABLE();
#ifdef USE_ROTOR_MOTOR
  HAL_GPIO_DeInit(GPIOK, GPIO_PIN_2);
#else
  HAL_GPIO_DeInit(GPIOK, (GPIO_PIN_2 | GPIO_PIN_3));
#endif
}

// ===========================================================================
// Timer Init / Deinit  (shared by both motor types)
// ===========================================================================
static bool motor_timer_init(void) {
  // 1000000hz = 1us period
  // 200 000 000hz clock
  // timer max 65535
  // upd_freq = TIM_CLK/(TIM_PSC+1)/(TIM_ARR + 1)
  // TIM_PSC = 199, TIM_ARR = variable  =>  1us resolution

  // tim7
  __HAL_RCC_TIM7_CLK_ENABLE();

  TIM7_Handle.Instance = TIM7;
  TIM7_Handle.Init.Prescaler = 199;
  TIM7_Handle.Init.CounterMode = TIM_COUNTERMODE_UP;
  TIM7_Handle.Init.Period = 0;
  ExecuteCheck_HAL_OK(HAL_TIM_Base_Init(&TIM7_Handle));
  ExecuteCheck_HAL_OK(HAL_TIM_OnePulse_Init(&TIM7_Handle, TIM_OPMODE_SINGLE));

  TIM_MasterConfigTypeDef sMasterConfig = {0};
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  ExecuteCheck_HAL_OK(
      HAL_TIMEx_MasterConfigSynchronization(&TIM7_Handle, &sMasterConfig));

  __HAL_TIM_CLEAR_IT(&TIM7_Handle, TIM_IT_UPDATE);
  __HAL_TIM_ENABLE_IT(&TIM7_Handle, TIM_IT_UPDATE);
  HAL_NVIC_SetPriority(TIM7_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(TIM7_IRQn);

  return true;
}

static void motor_timer_deinit(void) {
  // tim7
  __HAL_RCC_TIM7_CLK_DISABLE();
  __HAL_TIM_DISABLE_IT(&TIM7_Handle, TIM_IT_UPDATE);
  HAL_NVIC_DisableIRQ(TIM7_IRQn);
}

// ===========================================================================
// TIM7 ISR
// ===========================================================================

#ifdef USE_ROTOR_MOTOR

// Start playing the current segment pointed to by act_list_index_p.
// Called from motor_play() and from ISR when a segment finishes.
static void rotor_start_segment(void) {
  if (act_list_index_p >= act_list_index_p_max) {
    motor_reset();
    return;
  }

  pwm_cycles_remaining = act_list_index_p->repeat_count;

  if (act_list_index_p->on_time_us > 0) {
    // PWM segment: start with ON phase
    HAL_GPIO_WritePin(GPIOK, GPIO_PIN_2, GPIO_PIN_SET);
    pwm_phase_on = true;
    __HAL_TIM_SET_AUTORELOAD(&TIM7_Handle, act_list_index_p->on_time_us - 1);
  } else {
    // Pure OFF / pause segment
    HAL_GPIO_WritePin(GPIOK, GPIO_PIN_2, GPIO_PIN_RESET);
    pwm_phase_on = false;
    __HAL_TIM_SET_AUTORELOAD(&TIM7_Handle, act_list_index_p->off_time_us - 1);
  }
  __HAL_TIM_ENABLE(&TIM7_Handle);
}

void TIM7_IRQHandler(void) {
  if (__HAL_TIM_GET_FLAG(&TIM7_Handle, TIM_FLAG_UPDATE) != RESET) {
    if (__HAL_TIM_GET_IT_SOURCE(&TIM7_Handle, TIM_IT_UPDATE) != RESET) {
      __HAL_TIM_CLEAR_IT(&TIM7_Handle, TIM_IT_UPDATE);

      if (pwm_phase_on) {
        // ON phase done -> switch to OFF phase
        HAL_GPIO_WritePin(GPIOK, GPIO_PIN_2, GPIO_PIN_RESET);
        pwm_phase_on = false;
        __HAL_TIM_SET_AUTORELOAD(&TIM7_Handle,
                                 act_list_index_p->off_time_us - 1);
        __HAL_TIM_ENABLE(&TIM7_Handle);
      } else {
        // OFF phase done -> one full PWM cycle completed
        pwm_cycles_remaining--;
        if (pwm_cycles_remaining == 0) {
          // Current segment finished, advance to next
          act_list_index_p++;
          rotor_start_segment();
        } else {
          // Continue PWM cycling
          if (act_list_index_p->on_time_us > 0) {
            HAL_GPIO_WritePin(GPIOK, GPIO_PIN_2, GPIO_PIN_SET);
            pwm_phase_on = true;
            __HAL_TIM_SET_AUTORELOAD(&TIM7_Handle,
                                     act_list_index_p->on_time_us - 1);
          } else {
            // Pure OFF segment, keep waiting
            __HAL_TIM_SET_AUTORELOAD(&TIM7_Handle,
                                     act_list_index_p->off_time_us - 1);
          }
          __HAL_TIM_ENABLE(&TIM7_Handle);
        }
      }
    }
  }
}

#else  // Linear Motor ISR

void TIM7_IRQHandler(void) {
  if (__HAL_TIM_GET_FLAG(&TIM7_Handle, TIM_FLAG_UPDATE) != RESET) {
    if (__HAL_TIM_GET_IT_SOURCE(&TIM7_Handle, TIM_IT_UPDATE) != RESET) {
      __HAL_TIM_CLEAR_IT(&TIM7_Handle, TIM_IT_UPDATE);

      if (act_list_index_p < act_list_index_p_max) {
        motor_ctrl(act_list_index_p);
        __HAL_TIM_SET_AUTORELOAD(&TIM7_Handle,
                                 act_list_index_p->duration_us - 1);
        act_list_index_p++;
        __HAL_TIM_ENABLE(&TIM7_Handle);
      } else {
        motor_reset();
      }
    }
  }
}

#endif  // USE_ROTOR_MOTOR

// ===========================================================================
// Public functions
// ===========================================================================

void motor_init(void) {
  motor_io_init();
  motor_timer_init();
  motor_reset();
}

void motor_deinit(void) {
  motor_reset();
  motor_timer_deinit();
  motor_io_deinit();
}

#ifdef USE_ROTOR_MOTOR

inline void motor_ctrl(MOTOR_ACTION* act) {
  HAL_GPIO_WritePin(GPIOK, GPIO_PIN_2,
                    (act->on_time_us > 0) ? GPIO_PIN_SET : GPIO_PIN_RESET);
}

#else

inline void motor_ctrl(MOTOR_ACTION* act) {
  // as HAL_GPIO_WritePin only cares if PinState == GPIO_PIN_RESET
  // we don't have to filter non zero values
  HAL_GPIO_WritePin(GPIOK, GPIO_PIN_2, (act->state & 0b0000001));
  HAL_GPIO_WritePin(GPIOK, GPIO_PIN_3, (act->state & 0b0000010));
}

#endif  // USE_ROTOR_MOTOR

bool motor_is_busy(void) { return motor_busy; }

// ===========================================================================
// motor_play
// ===========================================================================

#ifdef USE_ROTOR_MOTOR

bool motor_play(MOTOR_ACTION* act_list, size_t act_list_len, bool by_cpu) {
  // sanity check
  if (act_list == NULL || act_list_len == 0) {
    return false;
  }

  if (motor_busy) {
    // already running
    return false;
  }

  motor_busy = true;

  // load action list
  act_list_index_p = act_list;
  act_list_index_p_max = act_list + act_list_len;

  if (by_cpu) {
    // blocking PWM generation
    while (act_list_index_p < act_list_index_p_max) {
      uint16_t repeat = act_list_index_p->repeat_count;
      for (uint16_t i = 0; i < repeat; i++) {
        if (act_list_index_p->on_time_us > 0) {
          HAL_GPIO_WritePin(GPIOK, GPIO_PIN_2, GPIO_PIN_SET);
          dwt_delay_us(act_list_index_p->on_time_us);
        }
        HAL_GPIO_WritePin(GPIOK, GPIO_PIN_2, GPIO_PIN_RESET);
        if (act_list_index_p->off_time_us > 0) {
          dwt_delay_us(act_list_index_p->off_time_us);
        }
      }
      act_list_index_p++;
    }
    motor_reset();
  } else {
    // timer interrupt PWM generation
    __HAL_TIM_DISABLE(&TIM7_Handle);
    rotor_start_segment();
  }

  return true;
}

#else  // Linear Motor

bool motor_play(MOTOR_ACTION* act_list, size_t act_list_len, bool by_cpu) {
  // sanity check
  if (act_list == NULL || act_list_len == 0) {
    return false;
  }

  if (motor_busy) {
    // already running
    return false;
  }

  motor_busy = true;

  // load action list
  act_list_index_p = act_list;
  act_list_index_p_max = act_list + act_list_len;

  if (by_cpu) {
    // block playing
    while (act_list_index_p < act_list_index_p_max) {
      motor_ctrl(act_list_index_p);
      dwt_delay_us(act_list_index_p->duration_us);
      act_list_index_p++;
    }
    motor_reset();
  } else {
    // timer interrupt playing
    __HAL_TIM_DISABLE(&TIM7_Handle);
    __HAL_TIM_SET_AUTORELOAD(&TIM7_Handle, act_list_index_p->duration_us - 1);
    __HAL_TIM_ENABLE(&TIM7_Handle);
  }

  return true;
}

#endif  // USE_ROTOR_MOTOR

void motor_reset(void) {
  motor_ctrl(MAL_relax);
  act_list_index_p = NULL;
  act_list_index_p_max = NULL;
#ifdef USE_ROTOR_MOTOR
  pwm_cycles_remaining = 0;
  pwm_phase_on = false;
#endif
  __HAL_TIM_DISABLE(&TIM7_Handle);
  motor_busy = false;
}

// ===========================================================================
// Debug functions
// ===========================================================================

#ifdef USE_ROTOR_MOTOR

void motor_resonant_finder(uint16_t on_us, uint16_t off_us, uint16_t repeats) {
  MOTOR_ACTION MAL_test[] = {
      {.on_time_us = on_us, .off_time_us = off_us, .repeat_count = repeats},
  };
  motor_play(MAL_test, sizeof(MAL_test) / sizeof(MOTOR_ACTION), false);
}

#else

void motor_resonant_finder(uint16_t dur_f, uint16_t dur_r, uint16_t dur_b) {
  MOTOR_ACTION MAL_single_shot[] = {
      {.state = MOTOR_FORWARD, .duration_us = dur_f},
      {.state = MOTOR_COAST, .duration_us = dur_b},
      {.state = MOTOR_REVERSE, .duration_us = dur_r},
      {.state = MOTOR_COAST, .duration_us = dur_b},
  };
  motor_play(MAL_single_shot, sizeof(MAL_single_shot) / sizeof(MOTOR_ACTION),
             false);
}

#endif  // USE_ROTOR_MOTOR

// ===========================================================================
// Builtin
// ===========================================================================

void motor_set_builtin_play_method(bool by_cpu) {
  builtin_seq_cpu_play = by_cpu;
}

// builtin patterns
void motor_play_whisper(void) {
  motor_play(MAL_Whisper, sizeof(MAL_Whisper) / sizeof(MOTOR_ACTION),
             builtin_seq_cpu_play);
}

void motor_play_light(void) {
  motor_play(MAL_Light, sizeof(MAL_Light) / sizeof(MOTOR_ACTION),
             builtin_seq_cpu_play);
}

void motor_play_medium(void) {
  motor_play(MAL_Medium, sizeof(MAL_Medium) / sizeof(MOTOR_ACTION),
             builtin_seq_cpu_play);
}

void motor_play_heavy(void) {
  motor_play(MAL_Heavy, sizeof(MAL_Heavy) / sizeof(MOTOR_ACTION),
             builtin_seq_cpu_play);
}

// builtin sequences
#ifdef USE_ROTOR_MOTOR

// rotor motor: sequences are pre-defined flat arrays in motor_patterns.h
void motor_play_success(void) {
  motor_play(MAL_Success, sizeof(MAL_Success) / sizeof(MOTOR_ACTION),
             builtin_seq_cpu_play);
}

void motor_play_warning(void) {
  motor_play(MAL_Warning, sizeof(MAL_Warning) / sizeof(MOTOR_ACTION),
             builtin_seq_cpu_play);
}

void motor_play_error(void) {
  motor_play(MAL_Error, sizeof(MAL_Error) / sizeof(MOTOR_ACTION),
             builtin_seq_cpu_play);
}

void motor_play_slide(void) {
  motor_play(MAL_Slide, sizeof(MAL_Slide) / sizeof(MOTOR_ACTION),
             builtin_seq_cpu_play);
}

#else  // Linear Motor

void motor_play_success(void) {
  size_t len = 0;
  seq_Success(act_list_combine, &len);
  motor_play(act_list_combine, len, builtin_seq_cpu_play);
}

void motor_play_warning(void) {
  size_t len = 0;
  seq_Warning(act_list_combine, &len);
  motor_play(act_list_combine, len, builtin_seq_cpu_play);
}

void motor_play_error(void) {
  size_t len = 0;
  seq_Error(act_list_combine, &len);
  motor_play(act_list_combine, len, builtin_seq_cpu_play);
}

void motor_play_slide(void) {
  size_t len = 0;
  seq_Slide(act_list_combine, &len);
  motor_play(act_list_combine, len, builtin_seq_cpu_play);
}

#endif  // USE_ROTOR_MOTOR
