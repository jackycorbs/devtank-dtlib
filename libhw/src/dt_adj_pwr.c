#include <string.h>
#include <stdlib.h>
#include <stdbool.h>
#include <unistd.h>
#include <errno.h>

#include <iio.h>

#include <devtank/log.h>
#include <devtank/dt_adj_pwr.h>
#include <devtank/gpio.h>
#include <devtank/helpers/yaml_helper.h>

struct dt_adj_pwr_t
{
    struct iio_context * context;

    struct iio_channel * voltage_out_ch;
    struct iio_channel * voltage_in_ch;
    struct iio_channel * current_in_ch;

    double               dac_to_raw;
    double               to_dac_divider;
    double               to_dac_offset;
    double               dac_limit;

    double               v_adc_to_raw;
    double               v_adc_scale;
    double               v_adc_offset;
    double               a_adc_to_raw;
    double               a_adc_scale;
    double               a_adc_offset;

    gpio_obj_t*          power_supply_enable_gpio;
    bool                 power_supply_enable_gpio_on;
    gpio_obj_t*          power_out_enable_gpio;
    bool                 power_out_enable_gpio_on;
    gpio_obj_t*          power_led_enable_gpio;
    bool                 power_led_enable_gpio_on;

    double               voltage;
};

static dt_adj_pwr_t dt_adj_pwr = {0};


struct devices_loader_packet_t
{
    dt_adj_pwr_t *adj_pwr;
    bool is_dac;
    struct iio_device *dev;
};


dt_adj_pwr_t* dt_adj_pwr_get(void)
{
    return &dt_adj_pwr;
}


bool dt_adj_pwr_is_setup(dt_adj_pwr_t *adj_pwr)
{
    if (!adj_pwr)
        return false;

    return (adj_pwr->context)?true:false;
}


void dt_adj_pwr_shutdown(dt_adj_pwr_t *adj_pwr)
{
    if (!adj_pwr)
        return;

    dt_adj_pwr_enable_power_out(adj_pwr, false);
    dt_adj_pwr_enable_power_supply(adj_pwr, false);

    if (adj_pwr->context)
    {
        iio_context_destroy(adj_pwr->context);
        adj_pwr->context = NULL;
    }
    adj_pwr->voltage_out_ch = NULL;
    adj_pwr->voltage_in_ch = NULL;
    adj_pwr->current_in_ch = NULL;
    adj_pwr->dac_to_raw = 1;
    adj_pwr->to_dac_divider = 1;
    adj_pwr->to_dac_offset = 0;
    adj_pwr->dac_limit = 1;
    adj_pwr->v_adc_to_raw = 1;
    adj_pwr->v_adc_scale = 1;
    adj_pwr->v_adc_offset = 0;
    adj_pwr->a_adc_scale = 1;
    adj_pwr->a_adc_offset = 0;
    if (adj_pwr->power_supply_enable_gpio)
    {
        gpio_obj_destroy(adj_pwr->power_supply_enable_gpio);
        adj_pwr->power_supply_enable_gpio = NULL;
    }
    if (adj_pwr->power_out_enable_gpio)
    {
        gpio_obj_destroy(adj_pwr->power_out_enable_gpio);
        adj_pwr->power_out_enable_gpio = NULL;
    }
    if (adj_pwr->power_led_enable_gpio)
    {
        gpio_obj_destroy(adj_pwr->power_led_enable_gpio);
        adj_pwr->power_led_enable_gpio = NULL;
    }
}


static bool _devices_loader_cb(dt_yaml_loader_t* loader, const char* key,  const char* value)
{
    struct devices_loader_packet_t * packet = (struct devices_loader_packet_t *)dt_yaml_loader_get_userdata(loader);

    if (!key)
        return false;
    if (!strcmp(key, "dev_name"))
    {
        char syslink[PATH_MAX];
        char realpath[PATH_MAX];

        int r = snprintf(syslink, sizeof(syslink), "/dev/%s", value);
        if (r > 0 && r < PATH_MAX)
        {
            r = readlink(syslink, realpath, sizeof(realpath));
            if (r > 0 && r < (PATH_MAX - 1))
            {
                realpath[r] = 0;
                packet->dev = iio_context_find_device(packet->adj_pwr->context, realpath);
                if (!packet->dev)
                {
                    error_msg("Failed to find IIO device \"%s\" for power control.", value);
                    return false;
                }
            }
            else
            {
                error_msg("Failed to read power control device \"%s\" symlink : %s", value, strerror(errno));
                return false;
            }
        }
        else
        {
            error_msg("Problem writing out path for power control device : %s", value);
            return false;
        }

        info_msg("Found IIO device \"%s\" by name \"%s\"", iio_device_get_name(packet->dev), value);

        return true;
    }
    if (!packet->dev)
    {
        error_msg("Power control IIO device must be set first.");
        return false;
    }

    if (packet->is_dac)
    {
        if (!strcmp(key, "voltage_channel"))
        {
            unsigned index = strtoul(value, NULL, 10);

            packet->adj_pwr->voltage_out_ch = iio_device_get_channel(packet->dev, index);
            if (!packet->adj_pwr->voltage_out_ch)
            {
                error_msg("Failed to get DAC power control channel %u of device which has %u.", index, iio_device_get_channels_count(packet->dev));
                return false;
            }
            info_msg("Found DAC IIO device \"%s\" channel %u \"%s\" for voltage.", iio_device_get_name(packet->dev), index, iio_channel_get_name(packet->adj_pwr->voltage_out_ch));
        }
        else if (!strcmp(key, "dac_limit"))
        {
            packet->adj_pwr->dac_limit = strtod(value, NULL);
            info_msg("DAC out limit is %G", packet->adj_pwr->dac_limit);
        }
        else if (!strcmp(key, "dac_to_raw"))
        {
            packet->adj_pwr->dac_to_raw = strtod(value, NULL);
            info_msg("DAC 1v is %G raw", packet->adj_pwr->dac_to_raw);
        }
        else if (!strcmp(key, "to_dac_divider"))
        {
            packet->adj_pwr->to_dac_divider = strtod(value, NULL);
            info_msg("DAC divider up is %G", packet->adj_pwr->to_dac_divider);
        }
        else if (!strcmp(key, "to_dac_offset"))
        {
            packet->adj_pwr->to_dac_offset = strtod(value, NULL);
            info_msg("DAC offset up is %G", packet->adj_pwr->to_dac_offset);
        }
        else if (!strstr(key, "_comment"))
            warning_msg("Unknown Power control DAC property \"%s\"", key);
    }
    else
    {
        if (!strcmp(key, "voltage_channel"))
        {
            unsigned index = strtoul(value, NULL, 10);

            packet->adj_pwr->voltage_in_ch = iio_device_get_channel(packet->dev, index);
            if (!packet->adj_pwr->voltage_in_ch)
            {
                error_msg("Failed to get ADC power control channel %u of device which has %u.", index, iio_device_get_channels_count(packet->dev));
                return false;
            }
            info_msg("Found ADC IIO device \"%s\" channel %u \"%s\" for voltage.", iio_device_get_name(packet->dev), index, iio_channel_get_name(packet->adj_pwr->voltage_in_ch));
        }
        else if (!strcmp(key, "current_channel"))
        {
            unsigned index = strtoul(value, NULL, 10);

            packet->adj_pwr->current_in_ch = iio_device_get_channel(packet->dev, index);
            if (!packet->adj_pwr->current_in_ch)
            {
                error_msg("Failed to get ADC power control channel %u of device which has %u.", index, iio_device_get_channels_count(packet->dev));
                return false;
            }
            info_msg("Found ADC IIO device \"%s\" channel %u \"%s\" for current.", iio_device_get_name(packet->dev), index, iio_channel_get_name(packet->adj_pwr->current_in_ch));
        }
        else if (!strcmp(key, "a_adc_to_raw"))
        {
            packet->adj_pwr->a_adc_to_raw = strtod(value, NULL);
            info_msg("ADC 1a is %G raw", packet->adj_pwr->a_adc_to_raw);
        }
        else if (!strcmp(key, "v_adc_to_raw"))
        {
            packet->adj_pwr->v_adc_to_raw = strtod(value, NULL);
            info_msg("ADC 1v is %G raw", packet->adj_pwr->v_adc_to_raw);
        }
        else if (!strcmp(key, "v_adc_scale"))
        {
            packet->adj_pwr->v_adc_scale = strtod(value, NULL);
            info_msg("ADC voltage divider is %G", packet->adj_pwr->v_adc_scale);
        }
        else if (!strcmp(key, "v_adc_offset"))
        {
            packet->adj_pwr->v_adc_offset = strtod(value, NULL);
            info_msg("ADC voltage offset is %G", packet->adj_pwr->v_adc_offset);
        }
        else if (!strcmp(key, "a_adc_scale"))
        {
            packet->adj_pwr->a_adc_scale = strtod(value, NULL);
            info_msg("ADC current divider is %G", packet->adj_pwr->a_adc_scale);
        }
        else if (!strcmp(key, "a_adc_offset"))
        {
            packet->adj_pwr->a_adc_offset = strtod(value, NULL);
            info_msg("ADC current offset is %G", packet->adj_pwr->a_adc_offset);
        }
        else if (!strstr(key, "_comment"))
            warning_msg("Unknown Power control ADC property \"%s\"", key);
    }

    return true;
}


enum gpio_loader_type_t
{
    GPIO_SUPPLY_ENABLE,
    GPIO_POWER_OUT_ENABLE,
    GPIO_LED_ENABLE,
};

struct gpoi_loader_packet_t
{
    dt_adj_pwr_t *adj_pwr;
    enum gpio_loader_type_t type;
};


static bool _gpio_loader_cb(dt_yaml_loader_t* loader, const char* key,  const char* value)
{
    struct gpoi_loader_packet_t * packet = (struct gpoi_loader_packet_t *)dt_yaml_loader_get_userdata(loader);

    if (packet->type == GPIO_SUPPLY_ENABLE)
    {
        if (!strcmp(key, "gpio"))
        {
            unsigned pin = strtoul(value, NULL, 10);
            char gpio_path[32];
            snprintf(gpio_path, sizeof(gpio_path), "/sys/class/gpio/gpio%u", pin);
            packet->adj_pwr->power_supply_enable_gpio = gpio_obj_create(gpio_path);
            info_msg("Power supply enable gpio %s", gpio_path);
        }
        else if (!strcmp(key, "turn_on"))
        {
            packet->adj_pwr->power_supply_enable_gpio_on = (strtoul(value, NULL, 10))?true:false;
            info_msg("Power supply enable on is %u", packet->adj_pwr->power_supply_enable_gpio_on);
        }
        else warning_msg("Unknown power supply GPIO property \"%s\"", key);
    }
    else if (packet->type == GPIO_POWER_OUT_ENABLE)
    {
        if (!strcmp(key, "gpio"))
        {
            unsigned pin = strtoul(value, NULL, 10);
            char gpio_path[32];
            snprintf(gpio_path, sizeof(gpio_path), "/sys/class/gpio/gpio%u", pin);
            packet->adj_pwr->power_out_enable_gpio = gpio_obj_create(gpio_path);
            info_msg("Power out enable gpio %s", gpio_path);
        }
        else if (!strcmp(key, "turn_on"))
        {
            packet->adj_pwr->power_out_enable_gpio_on = (strtoul(value, NULL, 10))?true:false;
            info_msg("Power out enable on is %u", packet->adj_pwr->power_out_enable_gpio_on);
        }
        else warning_msg("Unknown power out control GPIO property \"%s\"", key);
    }
    else if (packet->type == GPIO_LED_ENABLE)
    {
        if (!strcmp(key, "gpio"))
        {
            unsigned pin = strtoul(value, NULL, 10);
            char gpio_path[32];
            snprintf(gpio_path, sizeof(gpio_path), "/sys/class/gpio/gpio%u", pin);
            packet->adj_pwr->power_led_enable_gpio = gpio_obj_create(gpio_path);
            info_msg("Power LED enable gpio %s", gpio_path);
        }
        else if (!strcmp(key, "turn_on"))
        {
            packet->adj_pwr->power_led_enable_gpio_on = (strtoul(value, NULL, 10))?true:false;
            info_msg("Power LED enable on is %u", packet->adj_pwr->power_led_enable_gpio_on);
        }
        else warning_msg("Unknown power out control GPIO property \"%s\"", key);
    }

    return true;
}



static bool _dev_map_cb(dt_yaml_loader_t* loader, const char* key)
{
    dt_adj_pwr_t *adj_pwr = dt_yaml_loader_get_userdata(loader);

    if (!key)
    {
        error_msg("Map without key.");
        return false;
    }

    bool r = false;

    if (!strcmp(key, "power_dac"))
    {
        struct devices_loader_packet_t packet = {adj_pwr, true, NULL};
        dt_yaml_loader_set_userdata(loader, &packet);
        r = dt_yaml_loader_do(loader, NULL, NULL, _devices_loader_cb);
    }
    else if (!strcmp(key, "power_adc"))
    {
        struct devices_loader_packet_t packet = {adj_pwr, false, NULL};
        dt_yaml_loader_set_userdata(loader, &packet);
        r = dt_yaml_loader_do(loader, NULL, NULL, _devices_loader_cb);
    }
    else if (!strcmp(key, "power_supply_enable_gpio"))
    {
        struct gpoi_loader_packet_t packet = {adj_pwr, GPIO_SUPPLY_ENABLE};
        dt_yaml_loader_set_userdata(loader, &packet);
        r = dt_yaml_loader_do(loader, NULL, NULL, _gpio_loader_cb);
    }
    else if (!strcmp(key, "power_out_enable_gpio"))
    {
        struct gpoi_loader_packet_t packet = {adj_pwr, GPIO_POWER_OUT_ENABLE};
        dt_yaml_loader_set_userdata(loader, &packet);
        r = dt_yaml_loader_do(loader, NULL, NULL, _gpio_loader_cb);
    }
    else if (!strcmp(key, "power_led_gpio"))
    {
        struct gpoi_loader_packet_t packet = {adj_pwr, GPIO_LED_ENABLE};
        dt_yaml_loader_set_userdata(loader, &packet);
        r = dt_yaml_loader_do(loader, NULL, NULL, _gpio_loader_cb);
    }
    else
    {
        error_msg("Unknown power devivce.");
        return false;
    }

    dt_yaml_loader_set_userdata(loader, adj_pwr);

    return r;
}


static bool _root_map_cb(dt_yaml_loader_t* loader, const char* key)
{
    key = key;
    return dt_yaml_loader_do(loader, _dev_map_cb, NULL, NULL);
}


bool dt_adj_pwr_load_power_control(dt_adj_pwr_t *adj_pwr, const char *filename)
{
    if (adj_pwr->context)
    {
        warning_msg("Already has loaded power control, can't load \"%s\".", filename);
        return false;
    }

    const char* iio_address = getenv("IIO_ADDRESS");

    if (iio_address)
    {
        adj_pwr->context = iio_create_network_context(iio_address);
        if (!adj_pwr->context)
        {
            warning_msg("Failed to open remote IIO power control on \"%s\"", iio_address);
            return false;
        }
    }
    else
    {
        adj_pwr->context = iio_create_local_context();
        if (!adj_pwr->context)
        {
            error_msg("Failed to open local IIO context.");
            return false;
        }
    }

    dt_yaml_loader_t* loader = dt_yaml_loader_open_file(filename, adj_pwr);

    if (!loader)
    {
        warning_msg("Failed to load yaml for power control from %s", filename);
        iio_context_destroy(adj_pwr->context);
        adj_pwr->context = NULL;
        return false;
    }

    bool r = dt_yaml_loader_do(loader, _root_map_cb, NULL, NULL);

    if (!r)
    {
        warning_msg("Failed to load power control from %s", filename);
        dt_adj_pwr_shutdown(adj_pwr);
    }
    else
    {
        info_msg("Loaded power control from %s", filename);
        dt_adj_pwr_enable_power_out(adj_pwr, false); // Should be off anyway, but just in case.
    }

    return r;
}


bool dt_adj_pwr_set_power_out(dt_adj_pwr_t *adj_pwr, double voltage)
{
    if (!adj_pwr || !adj_pwr->voltage_out_ch)
        return false;

    double dac_voltage = (voltage - adj_pwr->to_dac_offset) / adj_pwr->to_dac_divider;

    if (dac_voltage > adj_pwr->dac_limit)
    {
        warning_msg("Voltage DAC to be set to %G for %G out, is beyond %G DAC limit. Clamping.",
                    dac_voltage, voltage, adj_pwr->dac_limit);
        dac_voltage = adj_pwr->dac_limit;
    }

    unsigned v = (unsigned)(dac_voltage * adj_pwr->dac_to_raw);

    int e = iio_channel_attr_write_longlong(adj_pwr->voltage_out_ch, "raw", v);
    if (e < 0)
    {
        error_msg("Setting voltage to %G, iio_channel_attr_write: %i %s", voltage, e, strerror(-e));
        return false;
    }

    info_msg("Voltage out set to %g (%u raw)", voltage, v);
    return true;
}



bool dt_adj_pwr_enable_power_supply(dt_adj_pwr_t *adj_pwr, bool enable)
{
    if (!adj_pwr || !adj_pwr->power_supply_enable_gpio)
        return false;

    bool state = (enable)?adj_pwr->power_supply_enable_gpio_on:!adj_pwr->power_supply_enable_gpio_on;

    info_msg("Enable chip supply.");

    return gpio_obj_write(adj_pwr->power_supply_enable_gpio, state);
}


bool dt_adj_pwr_power_supply_is_enabled(dt_adj_pwr_t *adj_pwr)
{
    if (!adj_pwr || !adj_pwr->power_supply_enable_gpio)
        return false;

    bool state;

    if (!gpio_obj_read(adj_pwr->power_supply_enable_gpio, &state))
    {
        error_msg("Failed to read power supply enable GPIO.");
        return false;
    }

    info_msg("Power supply is enabled : %u", state == adj_pwr->power_supply_enable_gpio_on);

    return state == adj_pwr->power_supply_enable_gpio_on;
}


bool dt_adj_pwr_enable_power_out(dt_adj_pwr_t *adj_pwr, bool enable)
{
    if (!adj_pwr || !adj_pwr->power_out_enable_gpio)
        return false;

    const char* state_name = (enable)?"enabled":"disabled";
    bool state = (enable)?adj_pwr->power_out_enable_gpio_on:!adj_pwr->power_out_enable_gpio_on;

    if (gpio_obj_write(adj_pwr->power_out_enable_gpio, state))
    {
        double voltage = 0;
        if (dt_adj_pwr_get_power_out(adj_pwr, &voltage))
        {
            if (adj_pwr->power_led_enable_gpio)
            {
                state = (state)?adj_pwr->power_led_enable_gpio_on:!adj_pwr->power_led_enable_gpio_on;
                if (!gpio_obj_write(adj_pwr->power_led_enable_gpio, state))
                    warning_msg("Failed to change power out LED.");
            }
            double amps = 0;
            if (dt_adj_pwr_get_power_use(adj_pwr, &amps))
                info_msg("Power at %Gv %Ga out %s.", voltage, amps, state_name);
            else
                warning_msg("Power at %Gv %s but failed to get amps.", voltage, state_name);
        }
        else warning_msg("Power out %s but failed to get voltage.", state_name);
        return true;
    }
    warning_msg("Failed to change power out switch to %s", state_name);
    return false;
}


bool dt_adj_pwr_power_out_is_enabled(dt_adj_pwr_t *adj_pwr)
{
    if (!adj_pwr || !adj_pwr->power_out_enable_gpio)
        return false;

    bool state;

    if (!gpio_obj_read(adj_pwr->power_out_enable_gpio, &state))
    {
        error_msg("Failed to read power supply enable GPIO.");
        return false;
    }

    info_msg("Power relay is enabled : %u", state == adj_pwr->power_out_enable_gpio_on);

    return state == adj_pwr->power_out_enable_gpio_on;
}


bool dt_adj_pwr_get_power_out(dt_adj_pwr_t *adj_pwr, double* voltage)
{
    if (!adj_pwr || !adj_pwr->voltage_in_ch || !voltage)
        return false;

    long long raw;

    int e = iio_channel_attr_read_longlong(adj_pwr->voltage_in_ch, "raw", &raw);
    if (e < 0)
    {
        error_msg("Getting voltage, iio_channel_attr_read: %i %s\n", e, strerror(-e));
        return false;
    }

    *voltage = (raw / adj_pwr->v_adc_to_raw) * adj_pwr->v_adc_scale + adj_pwr->v_adc_offset;

    info_msg("Voltage out read as %Gv (%lld raw)", *voltage, raw);
    return true;
}


bool dt_adj_pwr_get_power_use(dt_adj_pwr_t* adj_pwr, double *amps)
{
    if (!adj_pwr || !adj_pwr->current_in_ch || !amps)
        return false;

    long long raw;

    int e = iio_channel_attr_read_longlong(adj_pwr->current_in_ch, "raw", &raw);
    if (e < 0)
    {
        error_msg("Getting current, iio_channel_attr_read: %i %s\n", e, strerror(-e));
        return false;
    }

    *amps = (raw / adj_pwr->a_adc_to_raw) * adj_pwr->a_adc_scale + adj_pwr->a_adc_offset;

    info_msg("Current amps read as %g (%lld raw)", *amps, raw);
    return true;
}


bool dt_adj_pwr_has_power_control(dt_adj_pwr_t *adj_pwr)
{
    if (!adj_pwr)
        return false;

    if (!adj_pwr->context)
        return false;

    if (!adj_pwr->voltage_out_ch  || !adj_pwr->voltage_in_ch || !adj_pwr->current_in_ch)
    {
        warning_msg("No power out control or power in sensor.");
        return false;
    }

    return true;
}
