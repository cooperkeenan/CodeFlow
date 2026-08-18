import sys
from PIL import Image
src, out, x, y, w, h = sys.argv[1], sys.argv[2], *map(int, sys.argv[3:7])
S = 3
im = Image.open(src).crop((x*S, y*S, (x+w)*S, (y+h)*S))
im.save(out)
print(out, im.size)
