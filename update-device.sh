#!/bin/bash
#-------------------------------------------------------------------------
# Author: Gregory P. Smith (@gpshead) <greg@krypto.org>
#
# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#-------------------------------------------------------------------------

# A convenient way to push code changes to a Circuitpython device.
# You may not need the depending on your Linux distro setup.  I'm
# using a minimal Debian install on a compute stick rather than a
# desktop distro configured to auto-mount USB devices.
#
# This assumes you have something like this in your /etc/fstab:
# /dev/sda1       /mnt            vfat    user,noauto     0       0
#
mount /dev/sda1
rsync --checksum --inplace --exclude '*README*' --exclude '*LICENSE' \
      -r *.py asm_thumb third_party /mnt
sync
umount /mnt
