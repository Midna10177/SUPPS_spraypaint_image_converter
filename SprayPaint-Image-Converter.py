#!/usr/bin/python3
import argparse
from PIL import Image as image
from PIL import ImagePalette
import re
import os
import itertools
import numpy as np

# Made by rennu

#
#
#This program is intended to convert images to a spraypaint data file for use on the gmod dark rp server "superiorservers"
#the proprietary spraypaint file is represented as a stream of bytes, varying from 0x00 - 0x0F, with each byte representing
#a color in a lookup table (with 0x00 being fully transparent)
#
#Sorry for putting the code on pastebin, i dont really use github
#
# Takes in an image file with -i, and plops a spraypaint data representation of the image into the gmod folder
#
# specify location of hl2.exe with -o "PATH_TO_HL2.EXE" and -i "IMAGETOCONVERT.png.jpg"
#

# Argument Parsing.

parser = argparse.ArgumentParser(
 prog = 'SUPPS spray paint image converter',
 description = '''
  Takes in an image of any format, and converts that stupid proprietary image format that
  the spraypaint addon uses.
  GAMEPATH will have hl2.exe/hl2.sh/hl2_linux stripped from the end if it is there
  created spraypaint file will be put in GAMEPATH+'/garrysmod/data/sup/graffiti/'+inputImageName+'.dat' )

 ''',
 epilog = 'With much gay love, Rennu~')

parser.add_argument( '-i', '--input', help = 'input image', required = True )
parser.add_argument( '-o', '--gamepath', help = 'location of hl2.exe for gmod', required = True )
parser.add_argument( '-p', '--makepreview', help = 'store a preview of the image next to the input image', required = False, action = 'store_true' )
parser.add_argument( '-v', '--verbose', action = 'store_true' ) # for debugging + developers
parser.add_argument( '-g', '--green', action = 'store_true', help = 'if argument passed, use green colors in the color palette') # for debugging + developers

args = parser.parse_args()


# Notes to myself.

'''
STEPS:

 import image

 resize to 256x256 if it isnt already

 convert from original color palette to spraypaint palette with FLOYD-STEINBERG DITHERING

 go through pixels from bottom to top, right to left and convert them to their assigned byte value according to the lookup table

 export array of bytes to a raw byte file in ${STEAMLIBRARY}\steamapps\common\GarrysMod\garrysmod\data\sup\graffiti\IMAGENAME.dat


Notes:

images are:
 256 x 256
 each pixel represented by one byte (00-0F)
 pixel order is top to bottom, right to left

Color code lookup table:
 00 = transparent (special)
 01 = 000000 (black)
 02 = FFFFFF (White)
 03 = FF0000 (RED)
 04 = 00FF00 (GREEN)
 05 = 0000FF (Blue)
 06 = FFFF00 (Yellow)
 07 = FF00FF (Pink)
 08 = 00ffff (cyan?)
 09 = ffcb00 (orange)
 0A = ff8f00 (dark orange)
 0B = ff3700 (near red)
 0C = 9f009f (near purple)
 0D = 5a00e2 (near purple)
 0E = 3700ff (near blue)
 0F = 96ff00 (near green)
'''

# stored as RGB

 #0x0: 'alpha' #im not even gonna worry about alpha pixels right not because im too lazy for that
Lookup_Table = {
 0x1: [0x00,0x00,0x00],
 0x2: [0xFF,0xFF,0xFF],
 0x3: [0xFF,0x00,0x00],
 0x4: [0x00,0xFF,0x00],
 0x5: [0x00,0x00,0xFF],
 0x6: [0xFF,0xFF,0x00],
 0x7: [0xFF,0x00,0xFF],
 0x8: [0x00,0xFF,0xFF],
 0x9: [0xFF,0xCB,0x00],
 0xA: [0xFF,0x8F,0x00],
 0xB: [0xFF,0x37,0x00],
 0xC: [0x9F,0x00,0x9F],
 0xD: [0x5A,0x00,0xE2],
 0xE: [0x37,0x00,0xFF],
 0xF: [0x96,0xFF,0x00]
}

def createFile( fn ):
 open(fn, 'a').close()

def remove_transparency(im, bg_colour=(255, 255, 255)):

    # Only process if image has transparency (http://stackoverflow.com/a/1963146)
    if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):

        # Need to convert to RGBA if LA format due to a bug in PIL (http://stackoverflow.com/a/1963146)
        alpha = im.convert('RGBA').split()[-1]

        # Create a new background image of our matt color.
        # Must be RGBA because paste requires both images have the same format
        # (http://stackoverflow.com/a/8720632  and  http://stackoverflow.com/a/9459208)
        bg = image.new("RGB", im.size, bg_colour + (255,))
        bg.paste(im, mask=alpha)
        return bg

    else:
        return im

def Import_Image( fn ): #Read in filename (fn) and return PIL image data
 Image_Data = image.open( fn )
 Image_Data = remove_transparency(Image_Data)
 return( Image_Data )

def Resize_Image( Image_Data, width, height ): #resize PIL IMAGe data to width, height
 old_size = Image_Data.size #old image size
 new_im = image.new("RGB", ( width, height )) #create new empty image to put black bars around old image to make it square
 factor = min(256/old_size[0], 256/old_size[1]) #get the multiplier to bring it to under 256x256
 new_size = ( int(old_size[0]*factor), int(old_size[1]*factor) ) #apply multiplier
 box = tuple((n - o) // -2 for n, o in zip(new_size, (256,256))) #find the offset center between them (negative 2 because images are flipped at some point)
 #print(box)

 Image_Data = Image_Data.resize( new_size, image.Resampling.LANCZOS )
 new_im.paste(Image_Data, box) # iamge_data into center of black 256x256 canvas
 Image_Data = new_im.rotate(-90) # this rotation is only necessary for the weird byte ordering of the spray paint format
 Image_Data = Image_Data.transpose(image.FLIP_LEFT_RIGHT) # need to flip for the weird spray paint byte ordering format
 return( Image_Data )

def Convert_Colors( Image_Data, palette ): #convert PIL IMAGE data to color palette of palette
 #convert lookup table to an array of integers, usable by PIL
 def getItems( mydict ):
  return [ x for i,x in mydict.items() ]
 mypalette = list(itertools.chain.from_iterable(getItems( palette ) ))
 
 
 #create a new empty image we can apply the palette to so we can quantize our image
 p_img = image.new('P', (32, 32))
 p_img.putpalette( mypalette )
 
 
 #do the actual conversion
 Image_Data = Image_Data.quantize( palette=p_img, dither=image.Dither.FLOYDSTEINBERG )
 
 return( Image_Data )

def PilImage_To_Spraypaint_Data( Image_Data, verbose ): #convert PIL IMAGE data to sprapaint proprietary format
 # max width,height is 256,256
 # each pixel takes up one byte (from 00 - 0F)
 # pixel order is TOP to BOTTOM, RIGHT to LEFT
 palette_data = np.array(Image_Data.convert('RGB'))
 #
 #
 out_data = []
 #
 #
 for x in range(255,-1,-1):
  for y in range(0,256):
   thisPixel = palette_data[x][y]
   found = False
   for index, color in Lookup_Table.items():
    thisPixel = list(thisPixel)
    if color == thisPixel:
     out_data.append( index.to_bytes(1) )
     found = True
     continue
   if not found:
    print('Error,',thisPixel,'at',x,y,'not in lookup table')
    #out_data.append( 0x1.to_bytes(1) )


 #out_data = bytes(out_data)
 out_data = b''.join(out_data)
 return( out_data )

def Save_Spraypaint_Data( Image_Data, PathToFile ):
 open(PathToFile, 'wb').write(Image_Data)


def SanitizeGamePath( gamePath ):
 if gamePath.endswith( 'hl2.exe' ):
  gamePath = re.sub( 'hl2\.exe$', '', gamePath )
 if gamePath.endswith( 'hl2.sh' ):
  gamePath = re.sub( 'hl2\.sh$', '', gamePath )
 if gamePath.endswith( 'hl2_linux' ):
  gamePath = re.sub( 'hl2_linux$', '', gamePath )

 return(os.path.abspath( gamePath ))





def main():
 
 inputImage = args.input
 gamePath = args.gamepath
 verbose = args.verbose
 makepicture = args.makepreview
 
 if verbose:
  if args.green:
   print('using green colors in palette...')
  else:
   print('not using green colors in palette...')
 if not args.green:
  del Lookup_Table[0x4]
  del Lookup_Table[0xF]
 
 if verbose: print( inputImage )
 
 gamePath = SanitizeGamePath( gamePath )
 
 if verbose: print( gamePath )
 
 outDataFile = os.path.join( gamePath, 'garrysmod/data/sup/graffiti',os.path.basename(inputImage)+'.dat' )

 Image_Data = Import_Image( inputImage )
 
 Image_Data = Resize_Image( Image_Data, 256, 256 )
 
 Image_Data = Convert_Colors( Image_Data, Lookup_Table )
 
 
 if makepicture:
  basePath = os.path.dirname( inputImage )
  baseName = os.path.basename( inputImage )
  if not baseName.endswith('.png'): baseName = baseName + '.png'
  previewOut = os.path.join(basePath, 'preview_'+baseName)
  preview_image = Image_Data.rotate(-90).transpose(image.FLIP_LEFT_RIGHT)
  preview_image.save( previewOut )
  del preview_image
  print('Preview image saved to',previewOut)
 
 
 
 Image_Data = PilImage_To_Spraypaint_Data( Image_Data, verbose )
 
 Save_Spraypaint_Data( Image_Data, outDataFile )
 print('Wrote to',outDataFile)

main()
