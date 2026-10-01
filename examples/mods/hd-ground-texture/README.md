# Example: a high-resolution ground texture

`data/texture/필드바닥/prt_흙02.bmp` replaces the dirt of Prontera's fields
(the client's own path, Korean and all). The file can be any size; the
client squeezes every ground texture to 256x256 when it builds the map's
texture atlas, and Graphics+ ("High-resolution ground") rebuilds the atlas
at up to four times that when a map has larger textures, so they keep their
detail.

To make your own: find the texture's name (Settings -> Tools, or the map's
.gnd), and ship a larger file under the same path. Keep it seamless -- it
tiles -- and close to the original's colour, or the hand-painted edges
around it won't match.

The texture is [Ground104](https://ambientcg.com/view?id=Ground104) from
ambientCG, CC0 1.0 (public domain), resized to 1024x1024 and tinted to the
original's average colour.
