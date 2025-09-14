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

# --- Main Script ---

# 1. Check for Python 3.8+
if ! python3 -c 'import sys; sys.exit(not (sys.version_info.major == 3 and sys.version_info.minor >= 8))'; then
    PY_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
    echo_error "Python version 3.8 or higher is required. You have $PY_VERSION."
    exit 1
fi
PY_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
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
