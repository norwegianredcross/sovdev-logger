#!/bin/bash
# file: .devcontainer/additions/install-dev-java.sh
#
# Usage: ./install-dev-java.sh [options]
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
SCRIPT_NAME="Java Development Tools"
SCRIPT_DESCRIPTION="Installs OpenJDK 21 and sets up Java development environment"

# Before running installation, we need to add any required repositories or setup
pre_installation_setup() {
    if [ "${UNINSTALL_MODE}" -eq 1 ]; then
        echo "🔧 Preparing for uninstallation..."
    else
        echo "🔧 Performing pre-installation setup..."

        # Check if Java is already installed
        if command -v java >/dev/null 2>&1; then
            echo "✅ Java is already installed (version: $(java -version 2>&1 | head -n 1))"
        fi

        # Check Java environment
        echo "✅ Java environment setup ready"
    fi
}

# Custom Java installation function
install_java() {
    if [ "${UNINSTALL_MODE}" -eq 1 ]; then
        echo "🗑️  Removing Java installation..."
        
        # Remove OpenJDK packages
        sudo apt-get remove -y openjdk-*-jdk openjdk-*-jre default-jdk >/dev/null 2>&1 || true
        
        # Remove JAVA_HOME from bashrc if it exists
        if grep -q "export JAVA_HOME" ~/.bashrc; then
            sed -i '/export JAVA_HOME/d' ~/.bashrc
            sed -i '/# Java environment/d' ~/.bashrc
            echo "✅ Java environment variables removed from ~/.bashrc"
        fi
        return
    fi
    
    # Check if Java is already installed with correct version
    if command -v java >/dev/null 2>&1; then
        local java_version=$(java -version 2>&1 | head -n 1 | grep -o '"[0-9.]*"' | tr -d '"')
        if [[ "$java_version" == 21.* ]]; then
            echo "✅ OpenJDK 21 is already installed"
            
            # Ensure JAVA_HOME is set
            if [ -z "$JAVA_HOME" ]; then
                local java_path=$(readlink -f $(which java) | sed "s:/bin/java::")
                export JAVA_HOME="$java_path"
                
                if ! grep -q "export JAVA_HOME" ~/.bashrc; then
                    echo "" >> ~/.bashrc
                    echo "# Java environment" >> ~/.bashrc
                    echo "export JAVA_HOME=\"$java_path\"" >> ~/.bashrc
                    echo "✅ JAVA_HOME added to ~/.bashrc"
                fi
            fi
            return
        else
            echo "🔄 Different Java version found (${java_version}), installing OpenJDK 21..."
        fi
    fi
    
    echo "📦 Installing OpenJDK (latest available)..."
    
    # Update package lists
    sudo apt-get update -qq
    
    # Install OpenJDK (use default-jdk which provides the latest stable version)
    if sudo DEBIAN_FRONTEND=noninteractive apt-get install -y default-jdk; then
        echo "✅ OpenJDK installed successfully"
    else
        echo "❌ Failed to install OpenJDK"
        return 1
    fi
    
    # Set up JAVA_HOME automatically
    local java_path=$(readlink -f $(which java) | sed "s:/bin/java::")
    export JAVA_HOME="$java_path"
    
    if ! grep -q "export JAVA_HOME" ~/.bashrc; then
        echo "" >> ~/.bashrc
        echo "# Java environment" >> ~/.bashrc
        echo "export JAVA_HOME=\"$java_path\"" >> ~/.bashrc
        echo "✅ JAVA_HOME added to ~/.bashrc"
    fi
    
    # Verify installation
    if command -v java >/dev/null 2>&1 && command -v javac >/dev/null 2>&1; then
        echo "✅ Java is now available: $(java -version 2>&1 | head -n 1)"
        echo "✅ Java compiler available: $(javac -version 2>&1)"
    else
        echo "❌ Java installation failed - not found in PATH"
        return 1
    fi
}

# Define package arrays (remove any empty arrays that aren't needed)
SYSTEM_PACKAGES=(
    "curl"
    "wget"
    "git"
    "build-essential"
    "unzip"
    "maven"
)

NODE_PACKAGES=(
    # No Node.js packages needed for Java development
)

PYTHON_PACKAGES=(
    # No Python packages needed for Java development  
)

PWSH_MODULES=(
    # No PowerShell modules needed for Java development
)

# Define VS Code extensions
declare -A EXTENSIONS
EXTENSIONS["redhat.java"]="Language Support for Java|Fundamental Java language support"
EXTENSIONS["vscjava.vscode-java-pack"]="Extension Pack for Java|Complete Java development toolkit"

# Define verification commands to run after installation
VERIFY_COMMANDS=(
    "command -v java >/dev/null && echo '✅ Java is available' || echo '❌ Java not found'"
    "command -v javac >/dev/null && echo '✅ Java compiler available' || echo '❌ Java compiler not found'"
    "command -v mvn >/dev/null && echo '✅ Maven is available' || echo '❌ Maven not found'"
    "test -n \"\$JAVA_HOME\" && echo '✅ JAVA_HOME is set' || echo '❌ JAVA_HOME not set'"
)

# Post-installation notes
post_installation_message() {
    echo
    echo "🎉 Installation process complete for: $SCRIPT_NAME!"
    echo "Purpose: $SCRIPT_DESCRIPTION"
    echo
    echo "Important Notes:"
    echo "1. OpenJDK has been installed (latest available version)"
    echo "2. Maven has been installed for dependency management"
    echo "3. JAVA_HOME is set and added to ~/.bashrc"
    echo "4. Restart your shell or run 'source ~/.bashrc' to use Java/Maven"
    echo "5. VS Code Java extensions provide full IDE functionality"
    echo
    echo "Quick Start:"
    echo "- Check installation: java -version"
    echo "- Check compiler: javac -version"
    echo "- Check Maven: mvn -version"
    echo "- Create Maven project: mvn archetype:generate"
    echo "- Compile with Maven: mvn compile"
    echo "- Run with Maven: mvn exec:java"
    echo
    echo "Documentation Links:"
    echo "- Java Documentation: https://docs.oracle.com/en/java/"
    echo "- VS Code Java: https://code.visualstudio.com/docs/languages/java"
}

# Post-uninstallation notes
post_uninstallation_message() {
    echo
    echo "🏁 Uninstallation process complete for: $SCRIPT_NAME!"
    echo
    echo "Additional Notes:"
    echo "1. OpenJDK has been removed"
    echo "2. JAVA_HOME has been removed from ~/.bashrc"  
    echo "3. You may need to restart your shell for changes to take effect"
    
    # Check if Java is still accessible
    if command -v java >/dev/null; then
        echo
        echo "⚠️  Warning: Java is still accessible in PATH:"
        echo "- Location: $(which java)"
        echo "- Version: $(java -version 2>&1 | head -n 1)"
        echo "- This may be a different Java installation"
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
    # Custom Java installation first
    install_java
    
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
    # Extension state check removed - extensions are properly handled by process_extensions
    post_uninstallation_message
else
    echo "🔄 Starting installation process for: $SCRIPT_NAME"
    echo "Purpose: $SCRIPT_DESCRIPTION"
    pre_installation_setup
    process_installations
    verify_installations
    # Extension state check removed - extensions are properly handled by process_extensions
    post_installation_message
fi