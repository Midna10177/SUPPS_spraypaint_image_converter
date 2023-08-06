# SUPPS_spraypaint_image_converter
lets you process an image into the proprietary data format that the SUPPS.gg spraypaint addon uses for its saved spraypaint files

example:
./SprayPaint-Image-Converter.py -o /home/renny/.steam/steam/steamapps/common/GarrysMod/hl2.sh -vp -i /home/renny/Pictures/rainbow_vertical.png -g

help text:

usage: SUPPS spray paint image converter [-h] -i INPUT -o GAMEPATH [-p] [-v]
                                         [-g]

Takes in an image of any format, and converts that stupid proprietary image
format that the spraypaint addon uses. GAMEPATH will have
hl2.exe/hl2.sh/hl2_linux stripped from the end if it is there created
spraypaint file will be put in
GAMEPATH+'/garrysmod/data/sup/graffiti/'+inputImageName+'.dat' )

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        input image
  -o GAMEPATH, --gamepath GAMEPATH
                        location of hl2.exe for gmod
  -p, --makepreview     store a preview of the image next to the input image
  -v, --verbose
  -g, --green           if argument passed, use green colors in the color
                        palette

With much gay love, Rennu~
