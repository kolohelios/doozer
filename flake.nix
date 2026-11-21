{
  description = "Doozer — evidence-based knowledge maintenance experiments";

  inputs = {
    kolohelios-nix.url = "https://flakehub.com/f/kolohelios/kolohelios-nix/*.tar.gz";
    nixpkgs.follows = "kolohelios-nix/nixpkgs";
    shaka.url = "https://flakehub.com/f/kolohelios/shaka/*.tar.gz";
  };

  outputs =
    {
      self,
      nixpkgs,
      kolohelios-nix,
      shaka,
      ...
    }:
    let
      forEachSystem = nixpkgs.lib.genAttrs kolohelios-nix.lib.supportedSystems;
    in
    {
      devShells = forEachSystem (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.mkShell {
            packages = [
              shaka.packages.${system}.default
              pkgs.jujutsu
              pkgs.gh
              pkgs.just
              pkgs.typos
              pkgs.actionlint
              pkgs.shellcheck
              pkgs.vale
              pkgs.taplo
            ];
          };
        }
      );

      checks = forEachSystem (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          nix-format = pkgs.runCommand "doozer-nix-format" { nativeBuildInputs = [ pkgs.nixfmt ]; } ''
            nixfmt --check ${./flake.nix}
            touch "$out"
          '';
          documentation = pkgs.runCommand "doozer-documentation" { } ''
            cd ${self}
            test -s docs/PRD.md
            test -s docs/EDD.md
            test -s LICENSE-MIT
            test -s LICENSE-APACHE
            grep -q 'OPENROUTER_API_KEY=' .env.example
            touch "$out"
          '';
        }
      );

      formatter = kolohelios-nix.formatter;
    };
}
