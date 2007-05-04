#!/bin/sh
#
# Script to create tarballs of Slovník cizích slov
#
# Copyright (c) 2006 - 2007 Michal Čihař
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

# URL where to download source files
url='http://slovnik-cizich-slov.abz.cz/export.php'
dir="stardict-czech-`date +%Y%m%d`"

rm -rf $dir
mkdir $dir
cd $dir
wget -q $url
if [ ! -f export.php ] ; then
    echo "No file!"
    exit 1
fi
mv export.php slovnik.txt
recode iso-8859-2..utf-8 slovnik.txt
python ../cizislova2stardict.py
dictzip *.dict
rm slovnik.txt
cd ..
tar cfj $dir.tar.bz2 $dir
rm -rf $dir