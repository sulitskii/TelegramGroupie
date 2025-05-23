# Telegram Group Bot for Google Cloud Run

This project is a minimal Telegram bot that listens to all group messages and is ready for secure deployment on Google Cloud Run.

## Features
- Listens to all group messages (after disabling privacy mode in @BotFather)
- Secure webhook endpoint with a secret path
- Stub function for message processing (to be implemented)

## Setup

### 1. Prerequisites
- Python 3.11 (recommended; 3.10+ supported, but **not 3.13**)
- pip (Python package installer)
- Docker
- Google Cloud account and project
- Telegram bot token (from @BotFather)

### 2. Installing pip
If you don't have pip installed, you can install it using one of these methods:

#### On macOS:
```sh
# Using Homebrew
brew install python@3.11  # This includes pip
python3.11 -m venv venv
```

#### On Ubuntu/Debian:
```sh
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
python3.11 -m venv venv
```

#### On Windows:
```sh
# Download Python 3.11 from https://www.python.org/downloads/
# Then run:
python -m venv venv
```

Verify pip installation:
```sh
pip --version
# or
pip3 --version
```

### 3. Setting up Virtual Environment
It's recommended to use a virtual environment for development. Here's how to set it up:

```sh
# Create a virtual environment
python3.11 -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate

# Install dependencies in the virtual environment
pip install -r requirements.txt
```

#### Using Virtual Environment in IDE
- **Cursor**:
  1. Open the project folder
  2. Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
  3. Type "Python: Select Interpreter"
  4. Choose the interpreter from your `venv` folder (usually at `./venv/bin/python` on macOS/Linux or `.\venv\Scripts\python.exe` on Windows)

- **VS Code**: 
  1. Open the project folder
  2. Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
  3. Type "Python: Select Interpreter"
  4. Choose the interpreter from your `venv` folder

- **PyCharm**:
  1. Go to Settings/Preferences → Project → Python Interpreter
  2. Click the gear icon → Add
  3. Choose "Existing Environment"
  4. Select the Python interpreter from your `venv` folder

#### Deactivating Virtual Environment
When you're done working:
```sh
deactivate
```

### 4. Environment Variables
Set the following environment variables when deploying:
- `TELEGRAM_TOKEN`: Your Telegram bot token (from @BotFather)
- `WEBHOOK_SECRET`: A random secret string for securing the webhook endpoint
- `GCP_PROJECT_ID`: Your Google Cloud project ID
- `KMS_LOCATION`: Location for KMS key ring (default: 'global')
- `KMS_KEY_RING`: Name of the KMS key ring (default: 'telegram-messages')
- `KMS_KEY_ID`: Name of the KMS key (default: 'message-key')

### 5. Security Setup
1. Enable Cloud KMS API:
```sh
gcloud services enable cloudkms.googleapis.com
```

2. Create a key ring:
```sh
gcloud kms keyrings create telegram-messages --location=global
```

3. Create a symmetric key:
```sh
gcloud kms keys create message-key \
    --keyring=telegram-messages \
    --location=global \
    --purpose=encryption \
    --protection-level=software
```

4. Grant the service account access to use the key:
```sh
gcloud kms keys add-iam-policy-binding message-key \
    --keyring=telegram-messages \
    --location=global \
    --member="serviceAccount:telegram-bot-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudkms.cryptoKeyEncrypterDecrypter"
```

### 6. Firestore Setup
1. Enable Firestore in your Google Cloud project:
```sh
gcloud services enable firestore.googleapis.com
```

2. Create a Firestore database (if not already created):
```sh
gcloud firestore databases create --region=YOUR_REGION
```

3. The application will automatically create the necessary collections and documents in Firestore.

### 7. Local Development
Make sure your virtual environment is activated first:
```sh
# Activate virtual environment if not already activated
source venv/bin/activate  # On macOS/Linux
# or
.\venv\Scripts\activate  # On Windows

# Set environment variables
export TELEGRAM_TOKEN=your-telegram-token
export WEBHOOK_SECRET=your-webhook-secret
export GCP_PROJECT_ID=your-project-id
export KMS_LOCATION=global
export KMS_KEY_RING=telegram-messages
export KMS_KEY_ID=message-key

# Run the application
python main.py
```

### 8. Find Your Google Cloud Project ID
To find your Google Cloud project ID, run:
```sh
gcloud config get-value project
```
This will output your current project ID. If you need to list all projects, use:
```sh
gcloud projects list
```
Replace `YOUR_PROJECT_ID` in the commands below with the value you get from these commands.

### 9. Build and Deploy to Cloud Run
The project includes a `build.sh` script that automates the build and deployment process. Make sure your virtual environment is activated:
```sh
# Activate virtual environment if not already activated
source venv/bin/activate  # On macOS/Linux
# or
.\venv\Scripts\activate  # On Windows

# Run the build script
./build.sh
```

Or manually:
```sh
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/telegram2whatsapp

gcloud run deploy telegram2whatsapp \
  --image gcr.io/YOUR_PROJECT_ID/telegram2whatsapp \
  --platform managed \
  --region YOUR_REGION \
  --allow-unauthenticated \
  --set-env-vars TELEGRAM_TOKEN=your-telegram-token,WEBHOOK_SECRET=your-webhook-secret,GCP_PROJECT_ID=your-project-id,KMS_LOCATION=global,KMS_KEY_RING=telegram-messages,KMS_KEY_ID=message-key \
  --service-account=YOUR_SERVICE_ACCOUNT@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

Note: Make sure your service account has the following roles:
- `roles/datastore.user` (for Firestore access)
- `roles/cloudkms.cryptoKeyEncrypterDecrypter` (for KMS access)
- `roles/cloudrun.invoker` (for Cloud Run access)

### 10. Set the Webhook
After deployment, get your Cloud Run service URL (e.g., `https://telegram2whatsapp-xxxx.a.run.app`).

Set the webhook using:
```sh
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -d "url=https://YOUR_CLOUD_RUN_URL/webhook/YOUR_WEBHOOK_SECRET"
```

### 11. Disable Privacy Mode
- Message @BotFather
- Select your bot → Bot Settings → Group Privacy → Turn OFF

### 12. Security Notes
- Never commit your bot token or secrets to source control.
- Use a strong, random `WEBHOOK_SECRET`.
- Cloud Run provides HTTPS by default.
- You can restrict ingress to only allow traffic from Telegram IPs for extra security (see Google Cloud docs).

## Testing
Make sure your virtual environment is activated:
```sh
# Activate virtual environment if not already activated
source venv/bin/activate  # On macOS/Linux
# or
.\venv\Scripts\activate  # On Windows

# Run tests
pytest tests/
```

The test suite includes:
- Health check endpoint tests
- Webhook endpoint tests
- Message processing tests
- Mocked Telegram API interactions

## Next Steps
- Implement your message processing logic in `process_message()` in `main.py`.

## Version Control
This project uses Git for version control. Here are some common commands:

```sh
# Initialize Git repository (already done)
git init

# Check status of your changes
git status

# Add all changes
git add .

# Commit changes
git commit -m "Your commit message"

# Create a new branch
git checkout -b feature/your-feature-name

# Switch branches
git checkout branch-name

# Push changes to remote repository
git push origin branch-name

# Pull latest changes
git pull origin main
```

### Git Configuration
If you haven't set up Git yet, configure your identity:
```sh
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```