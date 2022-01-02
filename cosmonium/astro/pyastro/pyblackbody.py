#
#This file is part of Cosmonium.
#
#Copyright (C) 2018-2019 Laurent Deru.
#
#Cosmonium is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Cosmonium is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with Cosmonium.  If not, see <https://www.gnu.org/licenses/>.
#

# From http://www.tannerhelland.com/4435/convert-temperature-rgb-algorithm-code/
# Start with a temperature, in Kelvin, somewhere between 1000 and 40000.  (Other values may work,
# but I can't make any promises about the quality of the algorithm's estimates above 40000 K.)


from panda3d.core import LColor
from math import log, pow

def temp_to_RGB(kelvin):
    temp = kelvin // 100
    if temp <= 66:
        red = 255

        green = temp
        green = 99.4708025861 * log(green) - 161.1195681661
        
        if temp <= 19:
            blue = 0
        else:
            blue = temp - 10
            blue = 138.5177312231 * log(blue) - 305.0447927307

    else:

        red = temp - 60
        red = 329.698727446 * pow(red, -0.1332047592)
        
        green = temp - 60
        green = 288.1221695283 * pow(green, -0.0755148492 )

        blue = 255

    return LColor(clamp(0, 1, red/255.0), clamp(0, 1, green/255.0), clamp(0, 1, blue/255.0), 1.0)
