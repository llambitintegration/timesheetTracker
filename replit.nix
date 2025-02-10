{pkgs}: {
  deps = [
    pkgs.openssl
    pkgs.postgresql
    pkgs.libxcrypt
    pkgs.glibcLocales
  ];
}
