#!/bin/bash
#
# PDF Generation Helper Script
# 
# This script makes it easy to generate PDF reports from anywhere in the project.
# It handles all the directory navigation and virtual environment activation.
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory (project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PDF_GEN_DIR="$SCRIPT_DIR/pdf_generator"

# Function to print colored output
print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "  $1"
}

# Print usage information
usage() {
    print_header "PDF Generation Helper"
    echo ""
    echo "Usage:"
    echo "  $0 [basic|ai]"
    echo ""
    echo "Options:"
    echo "  basic     Generate basic PDF without AI (faster, no API key needed)"
    echo "  ai        Generate AI-powered PDF with narratives (requires API key)"
    echo "  test      Test API key configuration"
    echo ""
    echo "Examples:"
    echo "  $0              # Interactive mode - prompts for choice"
    echo "  $0 basic        # Generate basic PDF"
    echo "  $0 ai           # Generate AI-powered PDF"
    echo "  $0 test         # Test API key"
    echo ""
}

# Check if pdf_generator directory exists
check_directory() {
    if [ ! -d "$PDF_GEN_DIR" ]; then
        print_error "pdf_generator directory not found at: $PDF_GEN_DIR"
        print_info "Make sure you're running this from the project root."
        exit 1
    fi
    print_success "Found pdf_generator directory"
}

# Check if virtual environment exists
check_venv() {
    if [ ! -d "$PDF_GEN_DIR/venv" ]; then
        print_warning "Virtual environment not found"
        print_info "Setting up virtual environment..."
        cd "$PDF_GEN_DIR" || exit 1
        
        if [ -f "setup_venv.sh" ]; then
            bash setup_venv.sh
        else
            print_error "setup_venv.sh not found"
            print_info "Please run: cd pdf_generator && ./setup_venv.sh"
            exit 1
        fi
        
        cd "$SCRIPT_DIR" || exit 1
    fi
    print_success "Virtual environment ready"
}

# Generate basic PDF
generate_basic() {
    print_header "Generating Basic PDF"
    print_info "Using sample data without AI enhancement"
    echo ""
    
    cd "$PDF_GEN_DIR" || exit 1
    source venv/bin/activate
    
    python generate_sample.py
    exit_code=$?
    
    deactivate
    cd "$SCRIPT_DIR" || exit 1
    
    echo ""
    if [ $exit_code -eq 0 ]; then
        print_success "PDF generated successfully!"
        print_info "Location: $SCRIPT_DIR/output/nairobi_report_sample.pdf"
    else
        print_error "PDF generation failed with exit code: $exit_code"
        exit $exit_code
    fi
}

# Generate AI-powered PDF
generate_ai() {
    print_header "Generating AI-Powered PDF"
    print_info "Using AI to generate narratives and advisories"
    echo ""
    
    # Check for API key
    if [ ! -f "$PDF_GEN_DIR/.env" ]; then
        print_warning "No .env file found"
        print_info "Creating .env file..."
        echo "OPENAI_API_KEY=" > "$PDF_GEN_DIR/.env"
        echo ""
        print_info "Please edit pdf_generator/.env and add your API key:"
        print_info "  OPENAI_API_KEY=sk-your-key-here"
        print_info ""
        print_info "Get an API key from: https://platform.openai.com/api-keys"
        print_info "See pdf_generator/docs/API_KEY_SETUP.md for detailed instructions"
        exit 1
    fi
    
    cd "$PDF_GEN_DIR" || exit 1
    source venv/bin/activate
    
    python generate_ai_sample.py
    exit_code=$?
    
    deactivate
    cd "$SCRIPT_DIR" || exit 1
    
    echo ""
    if [ $exit_code -eq 0 ]; then
        print_success "PDF generated successfully!"
        print_info "PDF location: $SCRIPT_DIR/output/ai_generated_report.pdf"
        print_info "JSON location: $SCRIPT_DIR/output/complete_report.json"
    else
        print_error "PDF generation failed with exit code: $exit_code"
        print_info "See pdf_generator/docs/API_KEY_SETUP.md for troubleshooting"
        exit $exit_code
    fi
}

# Test API key
test_api_key() {
    print_header "Testing API Key"
    echo ""
    
    cd "$PDF_GEN_DIR" || exit 1
    source venv/bin/activate
    
    python test_api_key.py
    exit_code=$?
    
    deactivate
    cd "$SCRIPT_DIR" || exit 1
    
    exit $exit_code
}

# Interactive mode
interactive_mode() {
    print_header "PDF Generation - Interactive Mode"
    echo ""
    echo "What would you like to do?"
    echo ""
    echo "  1) Generate basic PDF (no AI, faster)"
    echo "  2) Generate AI-powered PDF (requires API key)"
    echo "  3) Test API key configuration"
    echo "  4) Show help"
    echo "  5) Exit"
    echo ""
    read -p "Enter your choice (1-5): " choice
    echo ""
    
    case $choice in
        1)
            generate_basic
            ;;
        2)
            generate_ai
            ;;
        3)
            test_api_key
            ;;
        4)
            usage
            ;;
        5)
            print_info "Goodbye!"
            exit 0
            ;;
        *)
            print_error "Invalid choice: $choice"
            exit 1
            ;;
    esac
}

# Main script
main() {
    # Check prerequisites
    check_directory
    check_venv
    echo ""
    
    # Parse command line arguments
    if [ $# -eq 0 ]; then
        # No arguments - run interactive mode
        interactive_mode
    else
        case "$1" in
            basic)
                generate_basic
                ;;
            ai)
                generate_ai
                ;;
            test)
                test_api_key
                ;;
            -h|--help|help)
                usage
                ;;
            *)
                print_error "Unknown option: $1"
                echo ""
                usage
                exit 1
                ;;
        esac
    fi
}

# Run main function
main "$@"
