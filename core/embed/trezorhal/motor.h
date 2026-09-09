#ifndef _MOTOR_H_
#define _MOTOR_H_

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include STM32_HAL_H

// ===========================================================================
// Motor type selection
// Uncomment USE_ROTOR_MOTOR for rotor motor (GPIO PK2 software PWM)
// Comment out for linear resonant actuator (PK2 + PK3 H-bridge)
// ===========================================================================
#define USE_ROTOR_MOTOR

#ifdef USE_ROTOR_MOTOR

// Rotor motor action: software PWM via GPIO PK2 driven by TIM7
//
// Each action defines a PWM segment:
//   PWM Period   = on_time_us + off_time_us
//   Duty Cycle   = on_time_us / (on_time_us + off_time_us) * 100%
//   Duration     = (on_time_us + off_time_us) * repeat_count
//
// Set on_time_us = 0 for a pure off/pause segment
// Note: on_time_us and off_time_us must be <= 65535 (TIM7 16-bit max)
//       off_time_us must be > 0

typedef struct __attribute__((__packed__)) {
  uint16_t on_time_us;    // PWM high time per cycle (us), 0 = motor off
  uint16_t off_time_us;   // PWM low time per cycle (us), must > 0
  uint16_t repeat_count;  // number of PWM cycles to repeat
} MOTOR_ACTION;

#else  // Linear Motor

// motor freq 240hz -> 4166.6666us/cycle -> round to 4160us
// #define MOTOR_TO_MAX_CURRENT_US 300
// #define MOTOR_HALF_CYCLE_US 2080

typedef enum {
  MOTOR_COAST = 0b00,
  MOTOR_FORWARD = 0b01,
  MOTOR_REVERSE = 0b10,
  MOTOR_BRAKE = 0b11,
} MOTOR_STATE;

typedef struct __attribute__((__packed__)) {
  MOTOR_STATE state;
  uint16_t duration_us;
} MOTOR_ACTION;

#endif  // USE_ROTOR_MOTOR

// function control
void motor_init(void);
void motor_deinit(void);
void motor_ctrl(MOTOR_ACTION* act);
bool motor_is_busy(void);
bool motor_play(MOTOR_ACTION* act_list, size_t act_list_len, bool by_cpu);
void motor_reset(void);

// debug functions
#ifdef USE_ROTOR_MOTOR
void motor_resonant_finder(uint16_t on_us, uint16_t off_us, uint16_t repeats);
#else
void motor_resonant_finder(uint16_t dur_f, uint16_t dur_r, uint16_t dur_b);
#endif

// builtin
void motor_set_builtin_play_method(bool by_cpu);

// builtin patterns
void motor_play_whisper(void);
void motor_play_light(void);
void motor_play_medium(void);
void motor_play_heavy(void);

// builtin sequences
void motor_play_success(void);
void motor_play_warning(void);
void motor_play_error(void);
void motor_play_slide(void);

#endif  // _MOTOR_H_
