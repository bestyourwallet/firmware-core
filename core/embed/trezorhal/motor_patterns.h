#pragma once

#include "motor.h"

#ifdef USE_ROTOR_MOTOR

// ===========================================================================
// Rotor Motor Patterns (Software PWM on GPIO PK2 via TIM7)
// ===========================================================================
//
// MOTOR_ACTION fields:
//   on_time_us   - PWM high time per cycle (us), max 65535, set 0 for pause
//   off_time_us  - PWM low time per cycle (us), max 65535, must > 0
//   repeat_count - number of PWM cycles to repeat
//
// Derived values:
//   PWM Period   = on_time_us + off_time_us
//   Duty Cycle   = on_time_us / (on_time_us + off_time_us) * 100%
//   Duration     = (on_time_us + off_time_us) * repeat_count
//
// ---------------------------------------------------------------------------
// Helper macros for quick adjustment of frequency, duty cycle, and duration
//
// Example: 60% duty cycle @ 200Hz for 100ms
//   {.on_time_us  = ROTOR_ON(200, 60),
//    .off_time_us = ROTOR_OFF(200, 60),
//    .repeat_count = ROTOR_REPEATS(200, 100)}
// ---------------------------------------------------------------------------

#define ROTOR_PERIOD_US(freq_hz) (1000000 / (freq_hz))
#define ROTOR_ON(freq_hz, duty_pct) \
  (ROTOR_PERIOD_US(freq_hz) * (duty_pct) / 100)
#define ROTOR_OFF(freq_hz, duty_pct) \
  (ROTOR_PERIOD_US(freq_hz) - ROTOR_ON(freq_hz, duty_pct))
#define ROTOR_REPEATS(freq_hz, dur_ms) \
  ((dur_ms)*1000 / ROTOR_PERIOD_US(freq_hz))

// ---- Simple Patterns (4) ----

// Whisper: 40% duty @ 200Hz, 50ms
static MOTOR_ACTION MAL_Whisper[] = {
    {.on_time_us = ROTOR_ON(100, 40),
     .off_time_us = ROTOR_OFF(100, 40),
     .repeat_count = ROTOR_REPEATS(100, 50)},
};

// Light: 55% duty @ 200Hz, 80ms
static MOTOR_ACTION MAL_Light[] = {
    {.on_time_us = ROTOR_ON(200, 55),
     .off_time_us = ROTOR_OFF(200, 55),
     .repeat_count = ROTOR_REPEATS(200, 80)},
};

// Medium: 60% duty @ 200Hz, 100ms
static MOTOR_ACTION MAL_Medium[] = {
    {.on_time_us = ROTOR_ON(200, 60),
     .off_time_us = ROTOR_OFF(200, 60),
     .repeat_count = ROTOR_REPEATS(200, 100)},
};

// Heavy: 80% duty @ 200Hz, 200ms
static MOTOR_ACTION MAL_Heavy[] = {
    {.on_time_us = ROTOR_ON(200, 80),
     .off_time_us = ROTOR_OFF(200, 80),
     .repeat_count = ROTOR_REPEATS(200, 200)},
};

// Relax (Motor OFF)
static MOTOR_ACTION MAL_relax[] = {
    {.on_time_us = 0, .off_time_us = 100, .repeat_count = 1},
};

// ---- Sequence Patterns (4) ----

// Success: Medium(100ms) + Pause(80ms) + Heavy(200ms)
static MOTOR_ACTION MAL_Success[] = {
    {.on_time_us = ROTOR_ON(200, 60),
     .off_time_us = ROTOR_OFF(200, 60),
     .repeat_count = ROTOR_REPEATS(200, 100)},                   // Medium
    {.on_time_us = 0, .off_time_us = 40000, .repeat_count = 2},  // Pause 80ms
    {.on_time_us = ROTOR_ON(200, 80),
     .off_time_us = ROTOR_OFF(200, 80),
     .repeat_count = ROTOR_REPEATS(200, 200)},  // Heavy
};

// Warning: Heavy(100ms) + Pause(80ms) + Medium(100ms)
static MOTOR_ACTION MAL_Warning[] = {
    {.on_time_us = ROTOR_ON(200, 80),
     .off_time_us = ROTOR_OFF(200, 80),
     .repeat_count = ROTOR_REPEATS(200, 100)},                   // Heavy
    {.on_time_us = 0, .off_time_us = 40000, .repeat_count = 2},  // Pause 80ms
    {.on_time_us = ROTOR_ON(200, 60),
     .off_time_us = ROTOR_OFF(200, 60),
     .repeat_count = ROTOR_REPEATS(200, 100)},  // Medium
};

// Error: Med(100ms) + Pause(80ms) + Med(100ms) + Pause(80ms)
//      + Heavy(200ms) + Pause(80ms) + Med(100ms)
static MOTOR_ACTION MAL_Error[] = {
    {.on_time_us = ROTOR_ON(200, 60),
     .off_time_us = ROTOR_OFF(200, 60),
     .repeat_count = ROTOR_REPEATS(200, 100)},                   // Medium
    {.on_time_us = 0, .off_time_us = 40000, .repeat_count = 2},  // Pause 80ms
    {.on_time_us = ROTOR_ON(200, 60),
     .off_time_us = ROTOR_OFF(200, 60),
     .repeat_count = ROTOR_REPEATS(200, 100)},                   // Medium
    {.on_time_us = 0, .off_time_us = 40000, .repeat_count = 2},  // Pause 80ms
    {.on_time_us = ROTOR_ON(200, 80),
     .off_time_us = ROTOR_OFF(200, 80),
     .repeat_count = ROTOR_REPEATS(200, 200)},                   // Heavy
    {.on_time_us = 0, .off_time_us = 40000, .repeat_count = 2},  // Pause 80ms
    {.on_time_us = ROTOR_ON(200, 60),
     .off_time_us = ROTOR_OFF(200, 60),
     .repeat_count = ROTOR_REPEATS(200, 100)},  // Medium
};

// Slide: Whisper(50ms) + Pause(50ms) + Light(80ms) + Pause(50ms)
//      + Medium(100ms) + Pause(50ms) + Heavy(200ms)  (crescendo)
static MOTOR_ACTION MAL_Slide[] = {
    {.on_time_us = ROTOR_ON(200, 20),
     .off_time_us = ROTOR_OFF(200, 20),
     .repeat_count = ROTOR_REPEATS(200, 50)},                    // Whisper
    {.on_time_us = 0, .off_time_us = 50000, .repeat_count = 1},  // Pause 50ms
    {.on_time_us = ROTOR_ON(200, 40),
     .off_time_us = ROTOR_OFF(200, 40),
     .repeat_count = ROTOR_REPEATS(200, 80)},                    // Light
    {.on_time_us = 0, .off_time_us = 50000, .repeat_count = 1},  // Pause 50ms
    {.on_time_us = ROTOR_ON(200, 60),
     .off_time_us = ROTOR_OFF(200, 60),
     .repeat_count = ROTOR_REPEATS(200, 100)},                   // Medium
    {.on_time_us = 0, .off_time_us = 50000, .repeat_count = 1},  // Pause 50ms
    {.on_time_us = ROTOR_ON(200, 80),
     .off_time_us = ROTOR_OFF(200, 80),
     .repeat_count = ROTOR_REPEATS(200, 200)},  // Heavy
};

#else  // Linear Motor Patterns

// ===========================================================================
// Linear Resonant Actuator Patterns (PK2 + PK3 H-bridge)
// ===========================================================================

// simple patterns
// Whisper
static MOTOR_ACTION MAL_Whisper[] = {
    {.state = MOTOR_FORWARD, .duration_us = 1500},  //
    {.state = MOTOR_REVERSE, .duration_us = 1500},  //
    {.state = MOTOR_BRAKE, .duration_us = 10},      //
};
// Light
static MOTOR_ACTION MAL_Light[] = {
    //
    {.state = MOTOR_FORWARD, .duration_us = 1500},  //
    {.state = MOTOR_REVERSE, .duration_us = 800},   //
    {.state = MOTOR_FORWARD, .duration_us = 1500},  //
    {.state = MOTOR_REVERSE, .duration_us = 800},   //
    {.state = MOTOR_COAST, .duration_us = 10},      //
};
// Medium
static MOTOR_ACTION MAL_Medium[] = {
    {.state = MOTOR_FORWARD, .duration_us = 2080},  //
    {.state = MOTOR_REVERSE, .duration_us = 2080},  //
    {.state = MOTOR_FORWARD, .duration_us = 2080},  //
    {.state = MOTOR_REVERSE, .duration_us = 2080},  //
    {.state = MOTOR_BRAKE, .duration_us = 10},      //
};
// Heavy
static MOTOR_ACTION MAL_Heavy[] = {
    {.state = MOTOR_FORWARD, .duration_us = 2080},  //
    {.state = MOTOR_REVERSE, .duration_us = 2080},  //
    {.state = MOTOR_FORWARD, .duration_us = 2080},  //
    {.state = MOTOR_REVERSE, .duration_us = 2080},  //
    {.state = MOTOR_FORWARD, .duration_us = 2080},  //
    {.state = MOTOR_REVERSE, .duration_us = 2080},  //
    {.state = MOTOR_BRAKE, .duration_us = 10},      //
};
// Relax (Coast)
static MOTOR_ACTION MAL_relax[] = {
    {.state = MOTOR_COAST, .duration_us = 50},  //
};

// sequence patterns
static void seq_Success(MOTOR_ACTION* act_list, size_t* act_list_len) {
  *act_list_len = 0;
  MOTOR_ACTION* idx_p = act_list;

  // Medium
  memcpy(idx_p, MAL_Medium, sizeof(MAL_Medium));
  idx_p += sizeof(MAL_Medium) / sizeof(MOTOR_ACTION);

  // interval: 50ms
  *idx_p = (MOTOR_ACTION){.state = MOTOR_COAST, .duration_us = 50000};
  idx_p++;
  // interval: 50ms
  *idx_p = (MOTOR_ACTION){.state = MOTOR_COAST, .duration_us = 50000};
  idx_p++;

  // Heavy
  memcpy(idx_p, MAL_Heavy, sizeof(MAL_Heavy));
  idx_p += sizeof(MAL_Heavy) / sizeof(MOTOR_ACTION);

  *idx_p = (MOTOR_ACTION){.state = MOTOR_COAST, .duration_us = 65535};
  idx_p++;

  *act_list_len = idx_p - act_list;
}

static void seq_Warning(MOTOR_ACTION* act_list, size_t* act_list_len) {
  *act_list_len = 0;
  MOTOR_ACTION* idx_p = act_list;

  // Heavy
  memcpy(idx_p, MAL_Heavy, sizeof(MAL_Heavy));
  idx_p += sizeof(MAL_Heavy) / sizeof(MOTOR_ACTION);

  // interval: 50ms
  *idx_p = (MOTOR_ACTION){.state = MOTOR_COAST, .duration_us = 50000};
  idx_p++;
  // interval: 50ms
  *idx_p = (MOTOR_ACTION){.state = MOTOR_COAST, .duration_us = 50000};
  idx_p++;

  // Medium
  memcpy(idx_p, MAL_Medium, sizeof(MAL_Medium));
  idx_p += sizeof(MAL_Medium) / sizeof(MOTOR_ACTION);

  *idx_p = (MOTOR_ACTION){.state = MOTOR_COAST, .duration_us = 65535};
  idx_p++;

  *act_list_len = idx_p - act_list;
}

static void seq_Error(MOTOR_ACTION* act_list, size_t* act_list_len) {
  *act_list_len = 0;
  MOTOR_ACTION* idx_p = act_list;

  // Medium
  memcpy(idx_p, MAL_Medium, sizeof(MAL_Medium));
  idx_p += sizeof(MAL_Medium) / sizeof(MOTOR_ACTION);

  // interval: 50ms
  *idx_p = (MOTOR_ACTION){.state = MOTOR_COAST, .duration_us = 65535};
  idx_p++;

  // Medium
  memcpy(idx_p, MAL_Medium, sizeof(MAL_Medium));
  idx_p += sizeof(MAL_Medium) / sizeof(MOTOR_ACTION);

  // interval: 50ms
  *idx_p = (MOTOR_ACTION){.state = MOTOR_COAST, .duration_us = 65535};
  idx_p++;

  // Heavy
  memcpy(idx_p, MAL_Heavy, sizeof(MAL_Heavy));
  idx_p += sizeof(MAL_Heavy) / sizeof(MOTOR_ACTION);

  // interval: 50ms
  *idx_p = (MOTOR_ACTION){.state = MOTOR_COAST, .duration_us = 65535};
  idx_p++;

  // Medium
  memcpy(idx_p, MAL_Medium, sizeof(MAL_Medium));
  idx_p += sizeof(MAL_Medium) / sizeof(MOTOR_ACTION);

  *idx_p = (MOTOR_ACTION){.state = MOTOR_COAST, .duration_us = 65535};
  idx_p++;

  *act_list_len = idx_p - act_list;
}

static void seq_Slide(MOTOR_ACTION* act_list, size_t* act_list_len) {
  *act_list_len = 0;
  MOTOR_ACTION* idx_p = act_list;

  // Whisper
  memcpy(idx_p, MAL_Whisper, sizeof(MAL_Whisper));
  idx_p += sizeof(MAL_Whisper) / sizeof(MOTOR_ACTION);

  *idx_p = (MOTOR_ACTION){.state = MOTOR_COAST, .duration_us = 50000};
  idx_p++;
  // Light
  memcpy(idx_p, MAL_Light, sizeof(MAL_Light));
  idx_p += sizeof(MAL_Light) / sizeof(MOTOR_ACTION);

  *idx_p = (MOTOR_ACTION){.state = MOTOR_COAST, .duration_us = 50000};
  idx_p++;
  // Medium
  memcpy(idx_p, MAL_Medium, sizeof(MAL_Medium));
  idx_p += sizeof(MAL_Medium) / sizeof(MOTOR_ACTION);

  *idx_p = (MOTOR_ACTION){.state = MOTOR_COAST, .duration_us = 50000};
  idx_p++;
  // Heavy
  memcpy(idx_p, MAL_Heavy, sizeof(MAL_Heavy));
  idx_p += sizeof(MAL_Heavy) / sizeof(MOTOR_ACTION);

  *idx_p = (MOTOR_ACTION){.state = MOTOR_COAST, .duration_us = 50000};
  idx_p++;

  *act_list_len = idx_p - act_list;
}

#endif  // USE_ROTOR_MOTOR
