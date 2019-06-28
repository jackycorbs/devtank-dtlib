#ifndef __DT_ADJ_PWR__
#define __DT_ADJ_PWR__

typedef struct dt_adj_pwr_t dt_adj_pwr_t;

/** \brief Query if power control is setup.
  * \param adj_pwr power control interface.
  * \param enable  boolean of it setup or not.
  * */
extern bool dt_adj_pwr_is_setup(dt_adj_pwr_t *adj_pwr);

/** \brief Get power control object.
 * \returns power control object pointer.
 * */
extern dt_adj_pwr_t* dt_adj_pwr_get(void);

/** \brief Query if power control is setup.
  * \param adj_pwr power control interface.
  * \param enable  boolean of it setup or not.
  * */
extern bool dt_adj_pwr_is_setup(dt_adj_pwr_t *adj_pwr);

/** \brief Clear down power control.
  * \param adj_pwr power control interface.
  * */
extern void dt_adj_pwr_shutdown(dt_adj_pwr_t *adj_pwr);

/** \brief Load power control configuration.
  * \param adj_pwr power control interface.
  * \param filename  configuration file to load.
  * */
extern bool dt_adj_pwr_load_power_control(dt_adj_pwr_t *adj_pwr, const char* filename);

/** \brief Turn on the adjustable power supply.
  * \param adj_pwr power control interface.
  * \param enable  boolean of on/off.
  * */
extern bool dt_adj_pwr_enable_power_supply(dt_adj_pwr_t *adj_pwr, bool enable);

/** \brief Is the adjustable power supply on. */
extern bool dt_adj_pwr_power_supply_is_enabled(dt_adj_pwr_t *adj_pwr);

/** \brief Turn on the output of adjustable power supply.
  * \param adj_pwr power control interface.
  * \param enable  boolean of on/off.
  * */
extern bool dt_adj_pwr_enable_power_out(dt_adj_pwr_t *adj_pwr, bool enable);

/** \brief Is the adjustable power output on.
  * \param adj_pwr power control interface.
  * */
extern bool dt_adj_pwr_power_out_is_enabled(dt_adj_pwr_t *adj_pwr);

/** \brief Set the power out on the adj_pwr.
 * \param adj_pwr power control interface.
 * \param voltage Desired voltage.
 * \returns boolean of success.
 * */
extern bool dt_adj_pwr_set_power_out(dt_adj_pwr_t *adj_pwr, double voltage);

/** \brief Get the power on the adj_pwr.
 * \param adj_pwr power control interface.
 * \param voltage point to storage the voltage on the adj_pwr.
 * \returns boolean of success.
 * */
extern bool dt_adj_pwr_get_power_out(dt_adj_pwr_t *adj_pwr, double *voltage);

/** \brief Get the power use on the adj_pwr.
 * \param adj_pwr power control interface.
 * \param amps point to storage the amps on the adj_pwr.
 * \returns boolean of success.
 * */
extern bool dt_adj_pwr_get_power_use(dt_adj_pwr_t* adj_pwr, double *amps);


#endif //__DT_ADJ_PWR__
