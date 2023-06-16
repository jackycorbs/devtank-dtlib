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

if [ ! -e /dev/pwr_dac ]
then
  echo "No /dev/pwr_dac (udev bug?)"
  of_name=$(grep -al pwr_dac /sys/bus/iio/devices/*/of_node/name)
  if [ -n "$of_name" ]
  then
    iio_name=$(basename $(dirname $(dirname $of_name)))
    iio_index=${iio_name:10}
    iio_major=$(grep iio /proc/devices | awk '{print $1}')
    mknod /dev/$iio_name c $iio_major $iio_index
    ln -s $iio_name /dev/pwr_dac
  fi
fi

