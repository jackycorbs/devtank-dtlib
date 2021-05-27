#! /bin/bash

echo "#! /bin/sh" > $2
echo 'own_dir="$(dirname $(readlink -f $0))"' >> $2
echo 'plat_lib="$own_dir/../lib/$(getconf LONG_BIT)"' >> $2
echo 'if [ ! -e "$plat_lib" ]; then' >> $2
echo '	plat_lib="$own_dir/../lib"' >> $2
echo 'fi' >> $2
printf 'PYTHONPATH="$own_dir/../lib" '  >>  $2
printf 'LD_LIBRARY_PATH="$plat_lib" ' >> $2
printf '"$own_dir"/%s $@' "$(basename $1)" >> $2
chmod +x $2
