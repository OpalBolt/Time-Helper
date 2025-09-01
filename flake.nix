{
  # A simple Nix flake for Python dev using nixpkgs and devShells
  description = "Python project dev environment";

  inputs = {
    # Pin nixpkgs to the unstable channel (or use a specific revision)
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs =
    { self, nixpkgs }:
    let
      # Target system (adjust if needed)
      system = "x86_64-linux";
      # Import nixpkgs for this system
      pkgs = import nixpkgs { inherit system; };

      # Choose Python version
      python = pkgs.python3;

      # Python environment with fixed deps
      pythonEnv = python.withPackages (
        ps: with ps; [
          black # formatter
          flake8 # linter
          pytest # test runner
          # Core dependencies from pyproject.toml
          typer # CLI framework
          rich # Terminal formatting
          pydantic # Data validation
          loguru # Modern logging
        ]
      );
      # Build the actual package
      time-helper = python.pkgs.buildPythonApplication {
        pname = "time-helper";
        version = "0.1.0";
        
        src = ./.;
        
        # Use pyproject.toml for build
        pyproject = true;
        build-system = [ python.pkgs.hatchling ];
        
        # Dependencies from pyproject.toml
        dependencies = with python.pkgs; [
          typer
          rich
          pydantic
          loguru
        ];
        
        # Runtime dependencies (timewarrior)
        buildInputs = [ pkgs.timewarrior ];
        
        # Generate shell completions
        nativeBuildInputs = [ pkgs.installShellFiles pkgs.zsh pkgs.fish ];
        
        postInstall = ''
          # Generate completions by entering different shells
          
          # Zsh completion - enter zsh shell and run completion generation
          echo '$out/bin/time-helper --show-completion > time-helper.zsh' | ${pkgs.zsh}/bin/zsh
          installShellCompletion --cmd time-helper --zsh time-helper.zsh
          
          # Bash completion - use current bash environment  
          $out/bin/time-helper --show-completion > time-helper.bash
          installShellCompletion --cmd time-helper --bash time-helper.bash
          
          # Fish completion - enter fish shell and run completion generation
          echo '$out/bin/time-helper --show-completion > time-helper.fish' | ${pkgs.fish}/bin/fish
          installShellCompletion --cmd time-helper --fish time-helper.fish
          
          # Create 'th' alias symlink
          ln -s $out/bin/time-helper $out/bin/th
          
          # Generate completions for the 'th' alias too
          echo '$out/bin/th --show-completion > th.zsh' | ${pkgs.zsh}/bin/zsh
          installShellCompletion --cmd th --zsh th.zsh
          
          echo '$out/bin/th --show-completion > th.bash' | bash
          installShellCompletion --cmd th --bash th.bash
          
          echo '$out/bin/th --show-completion > th.fish' | ${pkgs.fish}/bin/fish
          installShellCompletion --cmd th --fish th.fish
        '';
        
        meta = {
          description = "Automated time tracking export and reporting tool";
          homepage = "https://codeberg.org/OpalBolt/time-helper";
        };
      };

      myShell = pkgs.mkShell {
        name = "python-dev-shell";
        buildInputs = [ 
          pythonEnv 
          pkgs.uv # UV package manager
          pkgs.timewarrior # Time tracking tool
        ];
        shellHook = ''
          echo "Entered dev shell (Python ${python.version})"
          echo "UV is available for package management"
          echo "Timewarrior (timew) is available for time tracking"
          echo "Run 'uv sync' to install dependencies from pyproject.toml"
        '';
      };

    in
    {
      # Export the package so it can be installed system-wide
      packages.${system} = {
        default = time-helper;
        time-helper = time-helper;
      };
      
      devShells.${system}.default = myShell;
    };
}
