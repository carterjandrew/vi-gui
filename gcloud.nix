{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = let
    gdk = pkgs.google-cloud-sdk.withExtraComponents (with pkgs.google-cloud-sdk.components; [
      gke-gcloud-auth-plugin
    ]);
  in
    [
      gdk
	  pkgs.k3s
    ];

  # Optional shell setup, such as environment variables or a welcome message
  shellHook = ''
    echo "Google Cloud SDK with GKE auth plugin loaded."
  '';
}

