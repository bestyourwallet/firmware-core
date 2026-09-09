#ifndef FPSENSOR_PLATFORM_H
#define FPSENSOR_PLATFORM_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C"
{
#endif

    int fpsensor_init(void);
    int fp_spi_init(void);
    int fp_gpio_init(void);
    void fpsensor_state_set(bool state);
    int fpsensor_detect(void);
    void fpsensor_irq_enable(void);
    void fpsensor_irq_disable(void);

    int fingerprint_template_download(uint16_t id);
    int fingerprint_template_upload_from_storage(void);
    int fingerprint_template_delete_from_storage(uint16_t id);
    int fingerprint_template_delete_all_from_storage(void);

#ifdef __cplusplus
}
#endif

#endif
