{ pkgs }: {
  deps = [
    pkgs.python311Full
    pkgs.ffmpeg-full
    pkgs.nodejs-18_x
    pkgs.libjpeg
    pkgs.zlib
    pkgs.libwebp
    pkgs.freetype
    pkgs.lcms2
    pkgs.openjpeg
    pkgs.libtiff
    pkgs.pkg-config
  ];
}