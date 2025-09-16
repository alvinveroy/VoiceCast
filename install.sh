#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Helper Functions ---

echo_info() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

echo_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

echo_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1" >&2
}

# --- Docker Functions ---

check_docker() {
    if ! command -v docker &> /dev/null;
    then
        echo_info "Docker is not installed."
        read -p "Would you like to install it now? (y/n): " install_docker_choice
        if [ "$install_docker_choice" = "y" ]; then
            install_docker
        else
            echo_error "Docker is required to run the application with Docker. Please install it manually and run the script again."
            exit 1
        fi
    else
        echo_info "Docker is already installed."
    fi
}

install_docker() {
    echo_info "Installing Docker..."
    # Detect the OS
    if [[ "$(uname)" == "Linux" ]]; then
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            if [[ "$ID" == "ubuntu" || "$ID" == "debian" ]]; then
                echo_info "Detected Ubuntu/Debian. Installing Docker..."
                sudo apt-get update
                sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
                curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
                sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
                sudo apt-get update
                sudo apt-get install -y docker-ce
                echo_info "Adding current user to the docker group..."
                sudo usermod -aG docker $USER
                echo_success "Docker installed successfully. Please log out and log back in for the group changes to take effect."
                echo_info "Please run the script again after logging back in."
                exit 0
            else
                echo_error "Unsupported Linux distribution. Please install Docker manually."
                exit 1
            fi
        else
            echo_error "Could not detect Linux distribution. Please install Docker manually."
            exit 1
        fi
    elif [[ "$(uname)" == "Darwin" ]]; then
        echo_info "Detected macOS. Please install Docker Desktop for Mac from: https://docs.docker.com/docker-for-mac/install/"
        exit 0
    else
        echo_error "Unsupported OS. Please install Docker manually."
        exit 1
    fi
}

run_docker() {
    echo_info "Pulling the latest Docker image..."
    docker pull ghcr.io/alvinveroy/voicecast:latest

    # 5. Setup .env file
    if [ -f ".env" ]; then
        echo_info ".env file already exists."
    else
        echo_info "Copying .env.example to .env..."
        cp .env.example .env
        echo_success ".env file created. Please configure it with your API keys and settings."
    fi

    echo_info "Creating 'logs' and 'audio' directories..."
    mkdir -p logs
    mkdir -p audio
    echo_success "Directories created."

    echo_info "Running the Docker container..."
    docker run -d \
      --name voicecast-daemon \
      --restart unless-stopped \
      --network host \
      -v "$(pwd)/.env:/app/.env" \
      -v "$(pwd)/logs:/app/logs" \
      -v "$(pwd)/audio:/app/audio" \
      ghcr.io/alvinveroy/voicecast:latest

    echo_success "The VoiceCast TTS Daemon is running in a Docker container."
}

# --- Local Installation Functions ---

install_local() {
    # 1. Check for Python 3.8+
    if ! python3 -c 'import sys; sys.exit(not (sys.version_info.major == 3 and sys.version_info.minor >= 8))'; then
        PY_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))
')
        echo_error "Python version 3.8 or higher is required. You have $PY_VERSION."
        exit 1
    fi
    PY_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))
')
    echo_info "Python version $PY_VERSION found."

    # 2. Check for virtual environment
    VENV_DIR=".venv"
    if [ -d "$VENV_DIR" ]; then
        echo_info "Virtual environment '.venv' already exists."
    else
        echo_info "Creating virtual environment '.venv'..."
        python3 -m venv "$VENV_DIR"
        echo_success "Virtual environment created."
    fi

    # 3. Activate virtual environment and install dependencies
    source "$VENV_DIR/bin/activate"
    echo_info "Virtual environment activated."

    echo_info "Upgrading pip..."
    pip install --upgrade pip

    echo_info "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
    echo_success "All dependencies installed successfully."

    # 4. Create necessary directories
    echo_info "Creating 'logs' and 'audio' directories..."
    mkdir -p logs
    mkdir -p audio
    echo_success "Directories created."

    # 5. Setup .env file
    if [ -f ".env" ]; then
        echo_info ".env file already exists."
    else
        echo_info "Copying .env.example to .env..."
        cp .env.example .env
        echo_success ".env file created. Please configure it with your API keys and settings."
    fi

    # 6. Setup systemd service
    if [ "$(id -u)" -eq 0 ]; then
        echo_info "Running as root, setting up systemd service..."
        read -p "Enter the user to run the service as: " SERVICE_USER
        read -p "Enter the group to run the service as: " SERVICE_GROUP

        SERVICE_FILE="/etc/systemd/system/voicecast.service"
        echo_info "Creating systemd service file at $SERVICE_FILE..."

        cat > "$SERVICE_FILE" <<EOL
[Unit]
Description=VoiceCast TTS Daemon
After=network.target

[Service]
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/.venv/bin/python main.py start
Restart=always

[Install]
WantedBy=multi-user.target
EOL

        echo_info "Reloading systemd daemon..."
        systemctl daemon-reload
        echo_info "Enabling voicecast service to start on boot..."
        systemctl enable voicecast.service
        echo_success "Systemd service created and enabled."
        echo_info "You can start the service with: sudo systemctl start voicecast.service"
        echo_info "You can check the status with: sudo systemctl status voicecast.service"
        echo_info "You can view the logs with: sudo journalctl -u voicecast.service"
    else
        echo_info "Not running as root, skipping systemd service setup."
    fi

    # --- Final Instructions ---
    echo_success "Installation complete!"
    echo_info "To get started, activate the virtual environment with: source .venv/bin/activate"
    echo_info "Then, you can run the application using: python main.py start"
}

# --- Main Script ---

main() {
    echo_info "Welcome to the VoiceCast TTS Daemon installer!"
    echo_info "You can choose to run the application using Docker or locally."
    read -p "How would you like to run the application? (docker/local): " choice

    case "$choice" in
        docker)
            echo_info "You chose to run with Docker."
            check_docker
            run_docker
            ;;
        local)
            echo_info "You chose to run locally."
            install_local
            ;; \
        *)
            echo_error "Invalid choice. Please run the script again and choose either 'docker' or 'local'."
            exit 1
            ;; 
    esac
}

main