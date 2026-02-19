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
          pytest-cov # coverage plugin
          # Core dependencies from pyproject.toml
          typer # CLI framework
          rich # Terminal formatting
          pydantic # Data validation
          loguru # Modern logging
          pyinstaller # building python package
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
        nativeBuildInputs = [ pkgs.installShellFiles ];

        postInstall = ''
          # Generate completions with explicit shell types
          # This avoids shell detection issues in the Nix build sandbox
          # Set environment variable to disable auto-detection and enable explicit shell arguments
          export _TYPER_COMPLETE_TEST_DISABLE_SHELL_DETECTION=1

          # Zsh completion
          $out/bin/time-helper --show-completion zsh > time-helper.zsh
          installShellCompletion --cmd time-helper --zsh time-helper.zsh

          # Bash completion
          $out/bin/time-helper --show-completion bash > time-helper.bash
          installShellCompletion --cmd time-helper --bash time-helper.bash

          # Fish completion
          $out/bin/time-helper --show-completion fish > time-helper.fish
          installShellCompletion --cmd time-helper --fish time-helper.fish
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
          pkgs.go-task # Task runner
        ];
        shellHook = ''
          echo "Entered dev shell (Python ${python.version})"
          echo "UV is available for package management"
          echo "Timewarrior (timew) is available for time tracking"
          echo "Task runner (task) is available for common development tasks"
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

      apps.${system} = {
        default = {
          type = "app";
          program = "${time-helper}/bin/time-helper";
        };
        time-helper = {
          type = "app";
          program = "${time-helper}/bin/time-helper";
        };
        tests = {
          type = "app";
          program = "${pkgs.writeShellScriptBin "tests" ''
            ${pythonEnv}/bin/pytest "$@"
          ''}/bin/tests";
        };
        lint = {
          type = "app";
          program = "${pkgs.writeShellScriptBin "lint" ''
            ${pythonEnv}/bin/flake8
          ''}/bin/lint";
        };
        format = {
          type = "app";
          program = "${pkgs.writeShellScriptBin "format" ''
            ${pythonEnv}/bin/black .
          ''}/bin/format";
        };
      };
    };
}
