{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  buildInputs = with pkgs; [
    minikube
    k3s
    kubernetes-helm
    jq
    docker
  ];

  shellHook = ''
    alias kubectl='minikube kubectl'
    . <(minikube completion zsh)
    . <(helm completion zsh)

    # Check if Minikube is running and then configure Docker environment
    if minikube status | grep -q "host: Running"; then
      echo "Configuring Docker environment to use Minikube's Docker daemon..."
      eval $(minikube -p minikube docker-env)
      . <(kubectl completion zsh)
    else
      echo "Minikube is not running. Starting now..."
	  minikube start
	  eval $(minikube -p minikube docker-env)
    fi
  '';
}

