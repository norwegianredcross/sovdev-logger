#!/bin/bash
# file: .devcontainer/dev-setup.sh
# Description: Simple development environment setup and tool selection
# Purpose: Central setup script for devcontainer development tools and templates
#
# Usage: dev-setup [--help] [--version]
#
# Exit Codes:
#   0 - Success or user exit
#   1 - Error in script execution
#   2 - Required directory not found
#   3 - User cancelled operation
#
#------------------------------------------------------------------------------

set -e

# Script metadata
SCRIPT_VERSION="3.0.0"
SCRIPT_NAME="DevContainer Setup"
DEVCONTAINER_DIR=".devcontainer"
ADDITIONS_DIR="$DEVCONTAINER_DIR/additions"
TEMPLATES_DIR="$DEVCONTAINER_DIR/templates"

# Global arrays
declare -a AVAILABLE_TOOLS=()
declare -a TOOL_SCRIPTS=()
declare -a TOOL_DESCRIPTIONS=()
declare -a AVAILABLE_TEMPLATES=()
declare -a TEMPLATE_SCRIPTS=()
declare -a TEMPLATE_DESCRIPTIONS=()

# Whiptail dimensions
DIALOG_HEIGHT=20
DIALOG_WIDTH=80
MENU_HEIGHT=12

#------------------------------------------------------------------------------
# Utility functions
#------------------------------------------------------------------------------

show_help() {
    cat << EOF
$SCRIPT_NAME v$SCRIPT_VERSION

USAGE:
    dev-setup [OPTIONS]

OPTIONS:
    --help          Show this help message
    --version       Show version information

DESCRIPTION:
    Simple setup script for development environment tools and project templates.
    Uses dialog for a clean, user-friendly interface with live descriptions.

EOF
}

show_version() {
    echo "$SCRIPT_NAME v$SCRIPT_VERSION"
}

# Check if dialog is available
check_dialog() {
    if ! command -v dialog >/dev/null 2>&1; then
        echo "❌ Error: dialog is not installed"
        echo ""
        echo "Please install dialog first:"
        echo "  sudo apt-get update"
        echo "  sudo apt-get install dialog"
        echo ""
        exit 2
    fi
}

# Check if we're in a devcontainer project
check_environment() {
    if [[ ! -d "$DEVCONTAINER_DIR" ]]; then
        dialog --title "Error" --msgbox "Not in a devcontainer project.\n\nNo $DEVCONTAINER_DIR directory found.\nPlease run this script from the root of your devcontainer project." $DIALOG_HEIGHT $DIALOG_WIDTH
        clear
        exit 2
    fi
}

#------------------------------------------------------------------------------
# Tool discovery and management
#------------------------------------------------------------------------------

scan_available_tools() {
    AVAILABLE_TOOLS=()
    TOOL_SCRIPTS=()
    TOOL_DESCRIPTIONS=()
    
    if [[ ! -d "$ADDITIONS_DIR" ]]; then
        dialog --title "Error" --msgbox "Tools directory not found: $ADDITIONS_DIR" $DIALOG_HEIGHT $DIALOG_WIDTH
        clear
        return 1
    fi
    
    local found=0
    
    # Scan for install scripts
    for script in "$ADDITIONS_DIR"/install-*.sh; do
        if [[ -f "$script" && ! "$script" =~ _template ]]; then
            local script_name=""
            local script_description=""
            
            # Extract SCRIPT_NAME and SCRIPT_DESCRIPTION from the file
            script_name=$(grep -m 1 '^SCRIPT_NAME=' "$script" 2>/dev/null | sed 's/.*"\(.*\)".*/\1/')
            script_description=$(grep -m 1 '^SCRIPT_DESCRIPTION=' "$script" 2>/dev/null | sed 's/.*"\(.*\)".*/\1/')
            
            if [[ -n "$script_name" ]]; then
                AVAILABLE_TOOLS+=("$script_name")
                TOOL_SCRIPTS+=("$(basename "$script")")
                TOOL_DESCRIPTIONS+=("${script_description:-No description available}")
                ((found++))
            else
                # Fallback to filename if no SCRIPT_NAME found
                local fallback_name=$(basename "$script" .sh)
                fallback_name=${fallback_name#install-}
                fallback_name=$(echo "$fallback_name" | sed 's/-/ /g' | sed 's/\b\w/\u&/g')
                AVAILABLE_TOOLS+=("$fallback_name")
                TOOL_SCRIPTS+=("$(basename "$script")")
                TOOL_DESCRIPTIONS+=("Generated from filename")
                ((found++))
            fi
        fi
    done
    
    if [[ $found -eq 0 ]]; then
        dialog --title "No Tools Found" --msgbox "No development tools found in $ADDITIONS_DIR" $DIALOG_HEIGHT $DIALOG_WIDTH
        clear
        return 1
    fi
    
    return 0
}

scan_available_templates() {
    AVAILABLE_TEMPLATES=()
    TEMPLATE_SCRIPTS=()
    TEMPLATE_DESCRIPTIONS=()
    
    if [[ ! -d "$TEMPLATES_DIR" ]]; then
        dialog --title "Templates" --msgbox "Templates directory not found: $TEMPLATES_DIR\n\nTemplates functionality is not available." $DIALOG_HEIGHT $DIALOG_WIDTH
        clear
        return 1
    fi
    
    local found=0
    
    # Scan for template scripts
    for script in "$TEMPLATES_DIR"/create-*.sh; do
        if [[ -f "$script" ]]; then
            local script_name=""
            local script_description=""
            
            # Extract SCRIPT_NAME and SCRIPT_DESCRIPTION from the file
            script_name=$(grep -m 1 '^SCRIPT_NAME=' "$script" 2>/dev/null | sed 's/.*"\(.*\)".*/\1/')
            script_description=$(grep -m 1 '^SCRIPT_DESCRIPTION=' "$script" 2>/dev/null | sed 's/.*"\(.*\)".*/\1/')
            
            if [[ -n "$script_name" ]]; then
                AVAILABLE_TEMPLATES+=("$script_name")
                TEMPLATE_SCRIPTS+=("$(basename "$script")")
                TEMPLATE_DESCRIPTIONS+=("${script_description:-No description available}")
                ((found++))
            else
                # Fallback to filename if no SCRIPT_NAME found
                local fallback_name=$(basename "$script" .sh)
                fallback_name=${fallback_name#create-}
                fallback_name=$(echo "$fallback_name" | sed 's/-/ /g' | sed 's/\b\w/\u&/g')
                AVAILABLE_TEMPLATES+=("$fallback_name")
                TEMPLATE_SCRIPTS+=("$(basename "$script")")
                TEMPLATE_DESCRIPTIONS+=("Generated from filename")
                ((found++))
            fi
        fi
    done
    
    if [[ $found -eq 0 ]]; then
        dialog --title "No Templates Found" --msgbox "No project templates found in $TEMPLATES_DIR" $DIALOG_HEIGHT $DIALOG_WIDTH
        clear
        return 1
    fi
    
    return 0
}

#------------------------------------------------------------------------------
# Tool installation
#------------------------------------------------------------------------------

install_tools() {
    if ! scan_available_tools; then
        return 1
    fi
    
    while true; do
        # Build simple menu with just tool names
        local menu_options=()
        for i in "${!AVAILABLE_TOOLS[@]}"; do
            menu_options+=("$((i+1))" "${AVAILABLE_TOOLS[$i]}")
        done
        
        # Show clean tool selection menu
        local choice
        choice=$(dialog --clear \
            --title "Development Tools" \
            --menu "Choose a development tool:" \
            $DIALOG_HEIGHT $DIALOG_WIDTH $MENU_HEIGHT \
            "${menu_options[@]}" \
            2>&1 >/dev/tty)
        
        # Check if user cancelled
        if [[ $? -ne 0 ]]; then
            clear
            break
        fi
        
        # Convert choice to array index
        local tool_index=$((choice - 1))
        
        if [[ $tool_index -ge 0 && $tool_index -lt ${#AVAILABLE_TOOLS[@]} ]]; then
            # Show description and ask for confirmation
            show_tool_details_and_confirm "$tool_index"
        fi
    done
}

# New function to show tool details and get user decision
show_tool_details_and_confirm() {
    local tool_index=$1
    local tool_name="${AVAILABLE_TOOLS[$tool_index]}"
    local tool_description="${TOOL_DESCRIPTIONS[$tool_index]}"
    
    # Show tool details with Install/Back options
    local user_choice
    user_choice=$(dialog --clear \
        --title "Tool Details: $tool_name" \
        --menu "$tool_description\n\nWhat would you like to do?" \
        $DIALOG_HEIGHT $DIALOG_WIDTH 4 \
        "1" "Install this tool" \
        "2" "Back to tool list" \
        2>&1 >/dev/tty)
    
    case $user_choice in
        1)
            execute_tool_installation "$tool_index"
            ;;
        2|"")
            # Go back to tool list (do nothing, loop will continue)
            clear
            ;;
    esac
}

execute_tool_installation() {
    local tool_index=$1
    local tool_name="${AVAILABLE_TOOLS[$tool_index]}"
    local script_name="${TOOL_SCRIPTS[$tool_index]}"
    local script_path="$ADDITIONS_DIR/$script_name"
    
    if [[ ! -f "$script_path" ]]; then
        dialog --title "Error" --msgbox "Installation script not found: $script_path" $DIALOG_HEIGHT $DIALOG_WIDTH
        clear
        return 1
    fi
    
    # Clear screen and show installation
    clear
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Installing: $tool_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Make script executable and run it
    chmod +x "$script_path"
    
    if bash "$script_path"; then
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "✅ Successfully installed: $tool_name"
        echo ""
        echo "💡 To make this permanent for your team:"
        echo "   Add this line to your setup documentation:"
        echo "   bash .devcontainer/additions/$script_name"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    else
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "❌ Failed to install: $tool_name"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    fi
    
    echo ""
    read -p "Press Enter to continue..." -r
}

#------------------------------------------------------------------------------
# Template installation
#------------------------------------------------------------------------------

install_templates() {
    if ! scan_available_templates; then
        return 1
    fi
    
    while true; do
        # Build simple menu with just template names
        local menu_options=()
        for i in "${!AVAILABLE_TEMPLATES[@]}"; do
            menu_options+=("$((i+1))" "${AVAILABLE_TEMPLATES[$i]}")
        done
        
        # Show clean template selection menu
        local choice
        choice=$(dialog --clear \
            --title "Project Templates" \
            --menu "Choose a project template:" \
            $DIALOG_HEIGHT $DIALOG_WIDTH $MENU_HEIGHT \
            "${menu_options[@]}" \
            2>&1 >/dev/tty)
        
        # Check if user cancelled
        if [[ $? -ne 0 ]]; then
            clear
            break
        fi
        
        # Convert choice to array index
        local template_index=$((choice - 1))
        
        if [[ $template_index -ge 0 && $template_index -lt ${#AVAILABLE_TEMPLATES[@]} ]]; then
            # Show description and ask for confirmation
            show_template_details_and_confirm "$template_index"
        fi
    done
}

# New function to show template details and get user decision
show_template_details_and_confirm() {
    local template_index=$1
    local template_name="${AVAILABLE_TEMPLATES[$template_index]}"
    local template_description="${TEMPLATE_DESCRIPTIONS[$template_index]}"
    
    # Show template details with Create/Back options
    local user_choice
    user_choice=$(dialog --clear \
        --title "Template Details: $template_name" \
        --menu "$template_description\n\nWhat would you like to do?" \
        $DIALOG_HEIGHT $DIALOG_WIDTH 4 \
        "1" "Create this template" \
        "2" "Back to template list" \
        2>&1 >/dev/tty)
    
    case $user_choice in
        1)
            execute_template_creation "$template_index"
            ;;
        2|"")
            # Go back to template list (do nothing, loop will continue)
            clear
            ;;
    esac
}

execute_template_creation() {
    local template_index=$1
    local template_name="${AVAILABLE_TEMPLATES[$template_index]}"
    local script_name="${TEMPLATE_SCRIPTS[$template_index]}"
    local script_path="$TEMPLATES_DIR/$script_name"
    
    if [[ ! -f "$script_path" ]]; then
        dialog --title "Error" --msgbox "Template script not found: $script_path" $DIALOG_HEIGHT $DIALOG_WIDTH
        clear
        return 1
    fi
    
    # Show creation progress
    {
        echo "10"
        echo "# Preparing template creation..."
        sleep 1
        
        echo "30"
        echo "# Making script executable..."
        chmod +x "$script_path"
        sleep 1
        
        echo "50"
        echo "# Running template creation script..."
        sleep 1
        
        # Execute the template creation script and capture output
        if bash "$script_path" > /tmp/template_output.log 2>&1; then
            echo "100"
            echo "# Template created successfully!"
            sleep 1
            creation_success=true
        else
            echo "100"
            echo "# Template creation failed!"
            sleep 1
            creation_success=false
        fi
    } | dialog --title "Creating: $template_name" --gauge "Initializing..." 8 $DIALOG_WIDTH 0
    
    clear
    
    # Show results
    if [[ "$creation_success" == "true" ]]; then
        dialog --title "Success" \
            --msgbox "✅ Successfully created: $template_name\n\nYour project template has been set up." \
            $DIALOG_HEIGHT $DIALOG_WIDTH
    else
        local error_msg="❌ Failed to create: $template_name\n\n"
        if [[ -f /tmp/template_output.log ]]; then
            error_msg+="Error details:\n$(tail -10 /tmp/template_output.log)"
        fi
        dialog --title "Creation Failed" --msgbox "$error_msg" $DIALOG_HEIGHT $DIALOG_WIDTH
    fi
    
    clear
    
    # Clean up
    rm -f /tmp/template_output.log
}

#------------------------------------------------------------------------------
# Environment information
#------------------------------------------------------------------------------

show_environment_info() {
    local info_text=""
    
    # System info
    info_text+="System Information:\n"
    info_text+="• Container: $(whoami)@$(hostname)\n"
    if [[ -f /etc/os-release ]]; then
        info_text+="• OS: $(grep PRETTY_NAME /etc/os-release | cut -d'"' -f2)\n"
    fi
    info_text+="\n"
    
    # Core tools
    info_text+="Installed Core Tools:\n"
    command -v python3 >/dev/null && info_text+="• Python: $(python3 --version | cut -d' ' -f2)\n"
    command -v node >/dev/null && info_text+="• Node.js: $(node --version | sed 's/v//')\n"
    command -v npm >/dev/null && info_text+="• npm: $(npm --version)\n"
    command -v az >/dev/null && info_text+="• Azure CLI: $(az --version | head -n1 | cut -d' ' -f2)\n"
    command -v pwsh >/dev/null && info_text+="• PowerShell: $(pwsh --version | cut -d' ' -f2)\n"
    info_text+="\n"
    
    # Available tools and templates count
    scan_available_tools >/dev/null 2>&1 && info_text+="Available Tools: ${#AVAILABLE_TOOLS[@]}\n"
    scan_available_templates >/dev/null 2>&1 && info_text+="Available Templates: ${#AVAILABLE_TEMPLATES[@]}\n"
    
    dialog --title "Environment Information" --msgbox "$info_text" $DIALOG_HEIGHT $DIALOG_WIDTH
    clear
}

#------------------------------------------------------------------------------
# Main menu and execution
#------------------------------------------------------------------------------

show_main_menu() {
    while true; do
        local choice
        choice=$(dialog --clear \
            --title "$SCRIPT_NAME v$SCRIPT_VERSION" \
            --menu "Choose an option:" \
            $DIALOG_HEIGHT $DIALOG_WIDTH $MENU_HEIGHT \
            "1" "Install Development Tools" \
            "2" "Create Project Template" \
            "3" "Show Environment Info" \
            "4" "Exit" \
            2>&1 >/dev/tty)
        
        # Check if user cancelled (ESC or Cancel button)
        if [[ $? -ne 0 ]]; then
            if dialog --title "Confirm Exit" --yesno "Are you sure you want to exit?" 8 50; then
                clear
                echo ""
                echo "✅ Thanks for using $SCRIPT_NAME! 🚀"
                exit 0
            fi
            continue
        fi
        
        case $choice in
            1)
                install_tools
                ;;
            2)
                install_templates
                ;;
            3)
                show_environment_info
                ;;
            4)
                clear
                echo ""
                echo "✅ Thanks for using $SCRIPT_NAME! 🚀"
                exit 0
                ;;
            *)
                dialog --title "Error" --msgbox "Invalid selection: $choice" 8 50
                clear
                ;;
        esac
    done
}

#------------------------------------------------------------------------------
# Main execution
#------------------------------------------------------------------------------

main() {
    # Parse command line arguments
    case "${1:-}" in
        --help|-h)
            show_help
            exit 0
            ;;
        --version|-v)
            show_version
            exit 0
            ;;
        "")
            # No arguments - run interactive mode
            ;;
        *)
            echo "❌ Error: Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
    
    # Check requirements and environment
    check_dialog
    check_environment
    
    # Start main menu
    show_main_menu
}

# Trap interrupts for clean exit
trap 'echo ""; echo "ℹ️  Operation cancelled by user"; exit 3' INT TERM

# Execute main function
main "$@"