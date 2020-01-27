#! /bin/sh

echo 37 > /sys/class/gpio/export 
echo 44 > /sys/class/gpio/export 

echo out > /sys/class/gpio/gpio37/direction
echo out > /sys/class/gpio/gpio44/direction

pwr_adc=$(readlink /dev/pwr_adc)

chmod 666 /dev/iio\:device*
chmod 666 /sys/bus/iio/devices/*/*_raw

echo 1 > /sys/bus/iio/devices/$pwr_adc/in_voltage0_scale
echo 1 > /sys/bus/iio/devices/$pwr_adc/in_voltage1_scale
echo 1 > /sys/bus/iio/devices/$pwr_adc/in_voltage2_scale
echo 1 > /sys/bus/iio/devices/$pwr_adc/in_voltage3_scale


