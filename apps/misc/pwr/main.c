#include <stdlib.h>
#include <stdbool.h>
#include <argp.h>

#include "devtank/log.h"
#include "devtank/dt_adj_pwr.h"

static const char* doc = "DT power control tool.";




static struct argp_option options[] = {
    { "verbose",  'v', NULL,   0, "Extra logging.", 1 },
    { "millivolts",  'M', "MILLIVOLTS", 0, "Volts to set power supply to.", 1 },
    { "seconds",  's', "SECONDS",   0, "Number of seconds to keep power supply on.", 1 },
    { 0 }
};

static double volts = 0.0;
static unsigned seconds = 0;


static error_t parse_opt (int key, char *arg, struct argp_state *state)
{
    switch (key)
    {
    case 'v':
        enable_warning_msgs(true);
        enable_info_msgs(true);
        info_msg("Enable info logging.");
        break;
    case 'M':
        {
            unsigned mv = strtoul(arg, NULL, 10);
            volts = mv / 1000.0;
            break; 
        }
    case 's':
        seconds = strtoul(arg, NULL, 10);
        break;
    default:
        break;
    }
    return 0;
}


int main(int argc, char *argv[])
{
    devtank_init();

    struct argp argp = {options, parse_opt, 0, doc, NULL, NULL, NULL};

    argp_parse (&argp, argc, argv, 0, 0, &options);

    dt_adj_pwr_t* adj_pwr = dt_adj_pwr_get();

    if (!dt_adj_pwr_load_power_control(adj_pwr, "hiltop.yaml"))
    {
        dt_adj_pwr_shutdown(adj_pwr);
        devtank_shutdown();
        exit(EXIT_FAILURE);
    }

    if (volts)
    {
        if (dt_adj_pwr_enable_power_supply(adj_pwr, true))
        {
            if (dt_adj_pwr_set_power_out(adj_pwr, volts))
            {
                if (dt_adj_pwr_enable_power_out(adj_pwr, true))
                {
                    printf("Running at %GV for %u seconds\n", volts, seconds);
                }
            }
        }
    }

    while(seconds)
    {
        double temp = 0;
        printf("Press enter to quit.\n");
        wait_for_fd(0, USEC_SECOND);
        if (get_fd_peek(0))
            break;
        seconds--;
        if (dt_adj_pwr_get_power_out(adj_pwr, &temp))
            printf("Voltage is %GV\n", temp);
        if (dt_adj_pwr_get_power_use(adj_pwr, &temp))
            printf("Current is %GA\n", temp);
    }

    dt_adj_pwr_shutdown(adj_pwr);
    devtank_shutdown();
    return EXIT_SUCCESS;
}
