#!/usr/bin/env bash
# file: .devcontainer/additions/install-dev-php.sh
#
# Usage: ./install-dev-php.sh [options]
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
SCRIPT_NAME="PHP Development Tools"
SCRIPT_DESCRIPTION="Installs PHP 8.4, Composer, and sets up PHP development environment"

# Before running installation, we need to add any required repositories or setup
pre_installation_setup() {
    if [ "${UNINSTALL_MODE}" -eq 1 ]; then
        echo "🔧 Preparing for uninstallation..."
    else
        echo "🔧 Performing pre-installation setup..."

        # Check if PHP is already installed
        if command -v php >/dev/null 2>&1; then
            echo "✅ PHP is already installed (version: $(php --version | head -n 1))"
        else
            # Install PHP using custom function to avoid core-install-apt.sh hanging
            install_php_custom
        fi
        
        # Check if Composer is available (should be included with PHP installation)
        if command -v composer >/dev/null 2>&1; then
            echo "✅ Composer is already installed (version: $(composer --version | head -n 1))"
        else
            echo "⚠️  Composer not found - this should be included with PHP installation"
            # Install Composer as fallback
            install_composer
        fi
    fi
}

# Custom PHP installation function (uses Laravel's proven installer)
install_php_custom() {
    echo "📦 Installing PHP 8.4 stack using Laravel's official installer..."
    
    # Install PHP stack using Laravel's official installer
    if ! /bin/bash -c "$(curl -fsSL https://php.new/install/linux/8.4)"; then
        echo "❌ Failed to install PHP stack"
        return 1
    fi
    
    # Source the bashrc to update PATH for current session
    if [ -f "/home/vscode/.bashrc" ]; then
        echo "🔄 Updating PATH for current session..."
        # shellcheck source=/dev/null
        source /home/vscode/.bashrc
        
        # Also update PATH for this script execution
        export PATH="/home/vscode/.config/herd-lite/bin:$PATH"
    fi
    
    # Verify installation
    if command -v php >/dev/null 2>&1; then
        echo "✅ PHP is now available: $(php --version | head -n 1)"
    else
        echo "❌ PHP installation failed - not found in PATH"
        return 1
    fi
    
    echo "✅ PHP stack installation completed"
}


# Custom function to install Composer after PHP is installed
install_composer() {
    if [ "${UNINSTALL_MODE}" -eq 1 ]; then
        if [ -f "/usr/local/bin/composer" ]; then
            echo "Removing Composer..."
            sudo rm -f /usr/local/bin/composer
            echo "✅ Composer removed"
        fi
    else
        if ! command -v composer >/dev/null 2>&1; then
            echo "📥 Installing Composer..."
            
            # Download Composer installer using curl (more reliable in containers)
            echo "Downloading Composer installer..."
            if ! curl -sS https://getcomposer.org/installer -o composer-setup.php; then
                echo "❌ Failed to download Composer installer"
                return 1
            fi
            
            # Install to system location
            echo "Installing Composer to /usr/local/bin/composer..."
            if ! sudo php composer-setup.php --install-dir=/usr/local/bin --filename=composer; then
                echo "❌ Failed to install Composer"
                rm -f composer-setup.php 2>/dev/null || true
                return 1
            fi
            
            # Clean up
            echo "Cleaning up installer..."
            rm -f composer-setup.php || true
            
            # Make sure it's executable
            sudo chmod +x /usr/local/bin/composer
            
            # Verify installation
            echo "Verifying Composer installation..."
            if [ -f "/usr/local/bin/composer" ] && command -v composer >/dev/null 2>&1; then
                echo "✅ Composer installed successfully: $(composer --version | head -n 1)"
            else
                echo "❌ Composer installation failed"
                return 1
            fi
        else
            echo "✅ Composer already installed: $(composer --version | head -n 1)"
        fi
    fi
}

# Define package arrays - PHP installed via custom logic above
SYSTEM_PACKAGES=(
    # PHP is installed via custom function, not apt packages
)

NODE_PACKAGES=(
    # No Node.js packages needed for basic PHP development
)

PYTHON_PACKAGES=(
    # No Python packages needed for PHP development
)

PWSH_MODULES=(
    # No PowerShell modules needed for PHP development
)

# Define VS Code extensions
declare -A EXTENSIONS
EXTENSIONS["bmewburn.vscode-intelephense-client"]="PHP Intelephense|Advanced PHP language support with IntelliSense"
EXTENSIONS["xdebug.php-debug"]="PHP Debug|Debug PHP applications using Xdebug"
EXTENSIONS["neilbrayfield.php-docblocker"]="PHP DocBlocker|Automatically generate PHPDoc comments"
EXTENSIONS["ikappas.composer"]="Composer|Composer dependency manager integration"
EXTENSIONS["mehedidracula.php-namespace-resolver"]="PHP Namespace Resolver|Auto-import and resolve PHP namespaces"
EXTENSIONS["humao.rest-client"]="REST Client|Send HTTP requests and view responses directly in VS Code"

# Define verification commands to run after installation
VERIFY_COMMANDS=(
    "command -v php >/dev/null && php --version | head -n 1 || echo '❌ PHP not found'"
    "command -v composer >/dev/null && composer --version | head -n 1 || echo '❌ Composer not found'"
    "php -m | grep -q 'mbstring' && echo '✅ PHP mbstring extension loaded' || echo '❌ PHP mbstring extension missing'"
    "php -m | grep -q 'curl' && echo '✅ PHP curl extension loaded' || echo '❌ PHP curl extension missing'"
    "php -m | grep -q 'sqlite3' && echo '✅ PHP SQLite extension loaded' || echo '❌ PHP SQLite extension missing'"
    "php -m | grep -q 'json' && echo '✅ PHP JSON extension loaded' || echo '❌ PHP JSON extension missing'"
)

# Post-installation notes
post_installation_message() {
    local php_version
    local composer_version

    if command -v php >/dev/null 2>&1; then
        php_version=$(php --version | head -n 1)
    else
        php_version="not installed"
    fi

    if command -v composer >/dev/null 2>&1; then
        composer_version=$(composer --version | head -n 1)
    else
        composer_version="not installed"
    fi

    echo
    echo "🎉 Installation process complete for: $SCRIPT_NAME!"
    echo "Purpose: $SCRIPT_DESCRIPTION"
    echo
    echo "Installed Versions:"
    echo "📋 PHP: $php_version"
    echo "📋 Composer: $composer_version"
    echo
    echo "Important Notes:"
    echo "1. PHP built-in development server: php -S localhost:8000"
    echo "2. Composer for dependency management"
    echo "3. Xdebug support for debugging PHP applications"
    echo "4. SQLite support included for database development"
    echo
    echo "Quick Start Commands:"
    echo "- Create composer.json: composer init"
    echo "- Install dependencies: composer install"
    echo "- Add dependency: composer require vendor/package"
    echo "- Start development server: php -S localhost:8000"
    echo "- Run PHP script: php script.php"
    echo "- Check PHP info: php -m (show modules)"
    echo "- Interactive PHP: php -a"
    echo
    echo "Urbalurba Logging Example:"
    echo "- Navigate to php/examples/demo/ folder"
    echo "- Run setup: ./setup-dev-env.sh"
    echo "- Run example: composer install && php demo.php"
    echo
    echo "Development Workflow:"
    echo "1. Create/open your PHP project"
    echo "2. Install dependencies with Composer"
    echo "3. Start development server: php -S localhost:8000"
    echo "4. Open http://localhost:8000 in your browser"
    echo "5. Edit PHP files - reload browser to see changes"
    echo
    echo "Documentation Links:"
    echo "- PHP Documentation: https://www.php.net/docs.php"
    echo "- Composer Documentation: https://getcomposer.org/doc/"
    echo "- PHP The Right Way: https://phptherightway.com/"

    # Show PATH information
    echo
    echo "Environment Information:"
    echo "📁 PHP binaries location: /home/vscode/.config/herd-lite/bin"
    echo "🔄 PATH has been configured in ~/.bashrc"
    
    # Show next steps at the very end
    echo
    echo "🚀 Next Steps:"
    echo "1. Run: source ~/.bashrc"
    echo "2. Test: php --version"
    echo "3. Test: composer --version"
    echo "4. Navigate to a PHP project and run: php -S localhost:8000"
}

# Post-uninstallation notes
post_uninstallation_message() {
    echo
    echo "🏁 Uninstallation process complete for: $SCRIPT_NAME!"
    echo
    echo "Additional Notes:"
    echo "1. PHP installed via apt package manager"
    echo "2. Composer cache remains in ~/.composer/"
    echo "3. VS Code extensions have been removed"
    echo "4. See PHP documentation for complete removal steps if needed"

    # Check for remaining components
    echo
    echo "Checking for remaining components..."

    if command -v php >/dev/null 2>&1; then
        echo
        echo "⚠️  Warning: PHP is still installed"
        echo "To completely remove PHP:"
        echo "  sudo apt-get purge php8.4*"
        echo "  sudo apt-get autoremove"
    fi

    if command -v composer >/dev/null 2>&1; then
        echo
        echo "⚠️  Warning: Composer is still installed"
        echo "To remove: sudo rm /usr/local/bin/composer"
        echo "Composer cache location: ~/.composer/"
    fi

    # Check for remaining VS Code extensions
    local extensions=(
        "bmewburn.vscode-intelephense-client"
        "xdebug.php-debug"
        "neilbrayfield.php-docblocker"
        "ikappas.composer"
        "mehedidracula.php-namespace-resolver"
        "humao.rest-client"
    )

    local has_extensions=0
    for ext in "${extensions[@]}"; do
        if code --list-extensions | grep -q "$ext"; then
            if [ $has_extensions -eq 0 ]; then
                echo
                echo "⚠️  Note: Some VS Code extensions are still installed:"
                has_extensions=1
            fi
            echo "- $ext"
        fi
    done

    if [ $has_extensions -eq 1 ]; then
        echo "These were not automatically removed during uninstallation."
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
    echo
    echo "🔍 Verifying installations..."
    
    # Check PHP
    if command -v php >/dev/null 2>&1; then
        echo "✅ PHP: $(php --version | head -n 1)"
    else
        echo "❌ PHP not found"
    fi
    
    # Check Composer
    if command -v composer >/dev/null 2>&1; then
        echo "✅ Composer: $(composer --version | head -n 1)"
    else
        echo "❌ Composer not found"
    fi
    
    # Check PHP extensions (only if PHP is available)
    if command -v php >/dev/null 2>&1; then
        if php -m | grep -q 'mbstring'; then
            echo "✅ PHP mbstring extension loaded"
        else
            echo "❌ PHP mbstring extension missing"
        fi
        
        if php -m | grep -q 'curl'; then
            echo "✅ PHP curl extension loaded"
        else
            echo "❌ PHP curl extension missing"
        fi
        
        if php -m | grep -q 'sqlite3'; then
            echo "✅ PHP SQLite extension loaded"
        else
            echo "❌ PHP SQLite extension missing"
        fi
        
        if php -m | grep -q 'json'; then
            echo "✅ PHP JSON extension loaded"
        else
            echo "❌ PHP JSON extension missing"
        fi
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
        # Extensions installed successfully - VS Code will activate them after reload
        echo "✅ All extensions installed - restart VS Code to activate"
    fi
    post_installation_message
fi