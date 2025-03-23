{
  description = "DuckAI";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";

    systems.url = "github:nix-systems/default";
  };

  outputs =
    {
      self,
      systems,
      nixpkgs,
    }:
    let
      eachSystem = nixpkgs.lib.genAttrs (import systems);
    in
    {
      devShells = eachSystem (
        system:
        let
          pkgs = import nixpkgs {
            inherit system;
            config.allowUnfree = true;
          };
        in
        {
          default = pkgs.mkShell {
            shellHook = ''
              if [ ! -d venv ]; then
                python3 -m venv venv
              fi

              source venv/bin/activate
            '';

            packages = with pkgs; [
              python3
            ];
          };
        }
      );
    };
}
