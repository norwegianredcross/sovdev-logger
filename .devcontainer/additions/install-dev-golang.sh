#!/bin/bash
# file: .devcontainer/additions/install-dev-golang.sh
#
# Usage: ./install-dev-golang.sh [options]
#
# Options:
#   --debug     : Enable debug output for troubleshooting
#   --uninstall : Remove installed components instead of installing them
#   --force     : Force installation/uninstallation even if there are dependencies
#
#------------------------------------------------------------------------------
# CONFIGURATION - Modify this section for each new script
#------------------------------------------------------------------------------

# Script metadata - must be at the very top of the configuration section
SCRIPT_NAME="Go Development Tools"
SCRIPT_DESCRIPTION="Installs Go (latest stable via apt), and sets up Go development environment"

# Before running installation, we need to add any required repositories or setup
pre_installation_setup() {
    if [ "${UNINSTALL_MODE}" -eq 1 ]; then
        echo "🔧 Preparing for uninstallation..."
    else
        echo "🔧 Performing pre-installation setup..."

        # Check if Go is already installed
        if command -v go >/dev/null 2>&1; then
            echo "✅ Go is already installed (version: $(go version))"
        fi

        # Create Go workspace directories
        mkdir -p $HOME/go/{bin,src,pkg}
        echo "✅ Go workspace directories created"
    fi
}

# Custom Go installation function
install_go() {
    if [ "${UNINSTALL_MODE}" -eq 1 ]; then
        echo "🗑️  Removing Go installation..."
        
        # Remove apt packages
        sudo apt-get remove -y golang-go golang-*-go >/dev/null 2>&1 || true
        
        # Remove backports repository
        if [ -f "/etc/apt/sources.list.d/backports.list" ]; then
            sudo rm -f "/etc/apt/sources.list.d/backports.list"
            echo "✅ Backports repository removed"
        fi
        
        # Remove Go environment from bashrc if it exists
        if grep -q "export GOPATH" ~/.bashrc; then
            sed -i '/export GOPATH/d' ~/.bashrc
            sed -i '/# Go environment/d' ~/.bashrc
            sed -i '/export PATH=.*GOPATH/d' ~/.bashrc
            echo "✅ Go environment removed from ~/.bashrc"
        fi
        return
    fi
    
    # Check if Go is already installed
    if command -v go >/dev/null 2>&1; then
        local current_version=$(go version | awk '{print $3}' | sed 's/go//')
        echo "✅ Go is already installed (version: ${current_version})"
        
        # Ensure GOPATH is set
        if [ -z "$GOPATH" ]; then
            export GOPATH="$HOME/go"
            
            if ! grep -q "export GOPATH" ~/.bashrc; then
                echo "" >> ~/.bashrc
                echo "# Go environment" >> ~/.bashrc
                echo "export GOPATH=\$HOME/go" >> ~/.bashrc
                echo "✅ GOPATH added to ~/.bashrc"
            fi
        fi
        return
    fi
    
    echo "📦 Installing latest stable Go via backports..."
    
    # Add Debian backports repository for newer Go versions
    if ! grep -q "bookworm-backports" /etc/apt/sources.list.d/backports.list 2>/dev/null; then
        echo "deb http://deb.debian.org/debian bookworm-backports main" | sudo tee /etc/apt/sources.list.d/backports.list
        echo "✅ Added Debian backports repository"
    fi
    
    # Update package lists
    sudo apt-get update -qq
    
    # Install Go from backports (gets Go 1.23+)
    if sudo DEBIAN_FRONTEND=noninteractive apt-get install -y golang-go -t bookworm-backports; then
        echo "✅ Go installed successfully from backports"
    else
        echo "❌ Failed to install Go from backports"
        return 1
    fi
    
    # Set up Go environment
    export GOPATH="$HOME/go"
    export PATH="$GOPATH/bin:$PATH"
    
    # Add GOPATH to bashrc if not already there
    if ! grep -q "export GOPATH" ~/.bashrc; then
        echo "" >> ~/.bashrc
        echo "# Go environment" >> ~/.bashrc
        echo "export GOPATH=\$HOME/go" >> ~/.bashrc
        echo "export PATH=\"\$GOPATH/bin:\$PATH\"" >> ~/.bashrc
        echo "✅ Go environment added to ~/.bashrc"
    fi
    
    # Verify installation
    if command -v go >/dev/null 2>&1; then
        echo "✅ Go is now available: $(go version)"
    else
        echo "❌ Go installation failed - not found in PATH"
        return 1
    fi
}

# Define package arrays (remove any empty arrays that aren't needed)
SYSTEM_PACKAGES=(
    "curl"
    "wget"
    "git"
    "build-essential"
)

NODE_PACKAGES=(
    # No Node.js packages needed for Go development
)

PYTHON_PACKAGES=(
    # No Python packages needed for Go development  
)

PWSH_MODULES=(
    # No PowerShell modules needed for Go development
)

# Define VS Code extensions
declare -A EXTENSIONS
EXTENSIONS["golang.go"]="Go|Rich Go language support for Visual Studio Code"

# Define verification commands to run after installation
VERIFY_COMMANDS=(
    "command -v go >/dev/null && echo '✅ Go is available' || echo '❌ Go not found'"
    "test -d \$HOME/go && echo '✅ Go workspace exists' || echo '❌ Go workspace not found'"
    "go env GOPATH | grep -q go && echo '✅ GOPATH configured' || echo '❌ GOPATH not configured'"
)

# Post-installation notes
post_installation_message() {
    echo
    echo "🎉 Installation process complete for: $SCRIPT_NAME!"
    echo "Purpose: $SCRIPT_DESCRIPTION"
    echo
    echo "Important Notes:"
    echo "1. Go 1.23+ has been installed via Debian backports repository"
    echo "2. GOPATH is set to \$HOME/go"
    echo "3. Go is available in system PATH (/usr/bin/go)"
    echo "4. VS Code Go extension will install development tools (gopls, goimports) automatically"
    echo "5. Modern Go features (log/slog, generics, etc.) are available"
    echo
    echo "Quick Start:"
    echo "- Check installation: go version"
    echo "- Create a new module: go mod init example.com/mymodule"
    echo "- Install dependencies: go mod tidy"
    echo "- Run code: go run main.go"
    echo "- Build binary: go build"
    echo
    echo "Documentation Links:"
    echo "- Go Documentation: https://golang.org/doc/"
    echo "- Go Modules: https://golang.org/doc/modules/"
    echo "- VS Code Go Extension: https://code.visualstudio.com/docs/languages/go"
}

# Post-uninstallation notes
post_uninstallation_message() {
    echo
    echo "🏁 Uninstallation process complete for: $SCRIPT_NAME!"
    echo
    echo "Additional Notes:"
    echo "1. Go packages have been removed via apt"
    echo "2. Go environment variables have been removed from ~/.bashrc"
    echo "3. Your Go workspace in \$HOME/go has been preserved"
    echo "4. You may need to restart your shell for changes to take effect"
    
    # Check if Go is still accessible
    if command -v go >/dev/null; then
        echo
        echo "⚠️  Warning: Go is still accessible in PATH:"
        echo "- Location: $(which go)"
        echo "- This may be a different Go installation"
    fi
}

#------------------------------------------------------------------------------
# STANDARD SCRIPT LOGIC - Do not modify anything below this line
#------------------------------------------------------------------------------

# Initialize mode flags
DEBUG_MODE=0
UNINSTALL_MODE=0
FORCE_MODE=0

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --debug)
            DEBUG_MODE=1
            shift
            ;;
        --uninstall)
            UNINSTALL_MODE=1
            shift
            ;;
        --force)
            FORCE_MODE=1
            shift
            ;;
        *)
            echo "ERROR: Unknown option: $1" >&2
            echo "Usage: $0 [--debug] [--uninstall] [--force]" >&2
            echo "Description: $SCRIPT_DESCRIPTION"
            exit 1
            ;;
    esac
done

# Export mode flags for core scripts
export DEBUG_MODE
export UNINSTALL_MODE
export FORCE_MODE

# Source all core installation scripts
source "$(dirname "$0")/core-install-apt.sh"
source "$(dirname "$0")/core-install-node.sh"
source "$(dirname "$0")/core-install-extensions.sh"
source "$(dirname "$0")/core-install-pwsh.sh"
source "$(dirname "$0")/core-install-python-packages.sh"

# Function to process installations
process_installations() {
    # Custom Go installation first
    install_go
    
    # Process each type of package if array is not empty
    if [ ${#SYSTEM_PACKAGES[@]} -gt 0 ]; then
        process_system_packages "SYSTEM_PACKAGES"
    fi

    if [ ${#NODE_PACKAGES[@]} -gt 0 ]; then
        process_node_packages "NODE_PACKAGES"
    fi

    if [ ${#PYTHON_PACKAGES[@]} -gt 0 ]; then
        process_python_packages "PYTHON_PACKAGES"
    fi

    if [ ${#PWSH_MODULES[@]} -gt 0 ]; then
        process_pwsh_modules "PWSH_MODULES"
    fi

    if [ ${#EXTENSIONS[@]} -gt 0 ]; then
        process_extensions "EXTENSIONS"
    fi
}

# Function to verify installations
verify_installations() {
    if [ ${#VERIFY_COMMANDS[@]} -gt 0 ]; then
        echo
        echo "🔍 Verifying installations..."
        for cmd in "${VERIFY_COMMANDS[@]}"; do
            if ! eval "$cmd"; then
                echo "❌ Verification failed for: $cmd"
            fi
        done
    fi
}

# Main execution
if [ "${UNINSTALL_MODE}" -eq 1 ]; then
    echo "🔄 Starting uninstallation process for: $SCRIPT_NAME"
    echo "Purpose: $SCRIPT_DESCRIPTION"
    pre_installation_setup
    process_installations
    if [ ${#EXTENSIONS[@]} -gt 0 ]; then
        for ext_id in "${!EXTENSIONS[@]}"; do
            IFS='|' read -r name description _ <<< "${EXTENSIONS[$ext_id]}"
            check_extension_state "$ext_id" "uninstall" "$name"
        done
    fi
    post_uninstallation_message
else
    echo "🔄 Starting installation process for: $SCRIPT_NAME"
    echo "Purpose: $SCRIPT_DESCRIPTION"
    pre_installation_setup
    process_installations
    verify_installations
    if [ ${#EXTENSIONS[@]} -gt 0 ]; then
        for ext_id in "${!EXTENSIONS[@]}"; do
            IFS='|' read -r name description _ <<< "${EXTENSIONS[$ext_id]}"
            check_extension_state "$ext_id" "install" "$name"
        done
    fi
    post_installation_message
fi