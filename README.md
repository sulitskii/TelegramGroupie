# TelegramGroupie

A smart, cloud-native Flask application for Telegram group management and message bridging, with end-to-end encryption and cloud storage.

## 🔥 **Architecture Overview**

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              TELEGRAMGROUPIE                               │
│                      Smart Telegram Group Management                       │
└────────────────────────────────────────────────────────────────────────────┘
┌─────────────┐    ┌─────────────┐    ┌─────────────────┐    ┌─────────────┐
│  Telegram   │───▶│    Flask    │───▶│   Google Cloud  │───▶│ Destinations│
│   Groups    │    │ Application │    │   Infrastructure│    │   & Bridges │
│  Messages   │    │  (Python)   │    │  (Firestore+KMS)│    │   (Custom)  │
└─────────────┘    └─────────────┘    └─────────────────┘    └─────────────┘
                          │                      │
                          ▼                      ▼
                   ┌─────────────┐    ┌─────────────────┐
                   │   Docker    │    │   Encrypted     │
                   │ Integration │    │   Message       │
                   │   Testing   │    │   Storage       │
                   └─────────────┘    └─────────────────┘
```

## 🚀 **Features**

- **🔐 End-to-End Encryption**: Google Cloud KMS for secure message encryption
- **📱 Telegram Integration**: Captures group messages via webhook
- **☁️ Cloud Storage**: Google Cloud Firestore for scalable data persistence
- **🧪 Mock Testing**: Complete testing infrastructure without external dependencies
- **🐳 Docker Ready**: Full containerization with integration testing
- **⚡ Real-time Processing**: Async message handling with batch processing
- **🔍 Message Retrieval**: REST API for accessing historical messages

## 🛠️ **Technology Stack**

- **Backend**: Python 3.11, Flask 3.0.3
- **Telegram**: python-telegram-bot 21.11.1
- **Cloud**: Google Cloud Firestore, Google Cloud KMS
- **Testing**: pytest, Docker integration tests
- **Security**: Encrypted message storage, webhook secret validation
- **DevOps**: Docker, GitHub Actions CI/CD

## 📦 **Installation**

### **Prerequisites**
- Python 3.11+
- Docker & Docker Compose
- Google Cloud Project (for production)

### **Quick Start**

```bash
# Clone repository
git clone <repository-url>
cd TelegramGroupie

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development

# Run in testing mode (no Google Cloud required)
TESTING=true python main.py
```

## 🧪 **Testing**

### **Local Testing**
```bash
# Run all unit tests
make test

# Run with coverage
make test-coverage

# Run specific test file
python -m pytest tests/test_main.py -v
```

### **Docker Integration Testing**
```bash
# Quick Docker test (30 seconds)
bash scripts/run-basic-docker-test.sh

# Full integration tests with Docker Compose
make docker-test-minimal

# Build and test individually
docker build -t telegramgroupie:test .
docker run -d -p 8081:8080 -e TESTING=true telegramgroupie:test
curl http://localhost:8081/healthz
```

### **Test Architecture**
The project uses a **dual-mode testing approach**:

1. **Production Mode**: Uses real Google Cloud Firestore and KMS
2. **Testing Mode** (`TESTING=true`): Uses mock implementations

Mock implementations provide:
- ✅ **No external dependencies** - runs anywhere
- ✅ **Fast startup** - 1 second vs 30+ seconds
- ✅ **Reliable tests** - no network or authentication issues
- ✅ **Realistic data** - proper encrypted message simulation

## 🔧 **Configuration**

### **Environment Variables**

#### **Production**
```bash
# Required for production
TELEGRAM_TOKEN=your_bot_token
WEBHOOK_SECRET=your_webhook_secret
GCP_PROJECT_ID=your_project_id

# Optional (with defaults)
KMS_LOCATION=global
KMS_KEY_RING=telegram-messages
KMS_KEY_ID=message-key
PORT=8080
```

#### **Testing**
```bash
# Enable testing mode
TESTING=true

# Optional test configuration
GCP_PROJECT_ID=test-project
WEBHOOK_SECRET=test-secret
PORT=8080
```

### **Google Cloud Setup** (Production Only)

1. **Create Google Cloud Project**
2. **Enable APIs**:
   - Cloud Firestore API
   - Cloud KMS API
3. **Create KMS Key Ring and Key**:
   ```bash
   gcloud kms keyrings create telegram-messages --location=global
   gcloud kms keys create message-key \
     --location=global \
     --keyring=telegram-messages \
     --purpose=encryption
   ```
4. **Set up Application Default Credentials**

## 🌐 **API Endpoints**

### **Health Check**
```http
GET /healthz
```

### **Telegram Webhook**
```http
POST /webhook/{secret}
```

### **Message Retrieval**
```http
GET /messages?chat_id={id}&user_id={id}&limit={n}&start_after={token}
```

### **Batch Processing**
```http
POST /messages/batch
Content-Type: application/json

{
  "chat_id": -100123456789,
  "user_id": 123456,
  "batch_size": 500
}
```

## 🏭 **CI/CD Pipeline**

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Code      │───▶│   Build &   │───▶│    Test     │───▶│   Deploy    │
│   Commit    │    │   Install   │    │   Suite     │    │     to      │
│             │    │             │    │             │    │   Cloud     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
 • Git Push         • Python 3.11      • Unit Tests       • Google Cloud
 • PR Creation      • Dependencies      • Integration      • Docker Deploy
 • Branch Update    • Lint & Format     • Docker Tests     • Health Checks
```

### **GitHub Actions Workflow**
- ✅ **Python 3.11** compatibility testing
- ✅ **Dependency** installation and validation
- ✅ **Code quality** checks (flake8, black)
- ✅ **Unit tests** with coverage reporting
- ✅ **Integration tests** with mock implementations
- ✅ **Docker builds** and container testing
- ✅ **Security scanning** and vulnerability checks

## 📁 **Project Structure**

```
TelegramGroupie/
├── 📄 main.py                     # Main Flask application
├── 🔐 encryption.py               # Google Cloud KMS encryption
├── 🧪 mock_firestore.py           # Mock Firestore for testing
├── 🧪 mock_encryption.py          # Mock encryption for testing
├── 📦 requirements.txt            # Production dependencies
├── 📦 requirements-dev.txt        # Development dependencies
├── 🐳 Dockerfile                  # Production container
├── 🐳 Dockerfile.test             # Testing container
├── 🐳 docker-compose.minimal.yml  # Minimal Docker testing
├── 🐳 docker-compose.simple.yml   # Simple Docker testing
├── 🔧 Makefile                    # Build and test commands
├── ⚙️ pytest.ini                  # Test configuration
├── 📚 README.md                   # This file
├── 🔒 SECURITY.md                 # Security guidelines
├── 📋 build.sh                    # Build script
├── tests/                         # Test suite
│   ├── test_main.py              # Flask app tests
│   ├── test_encryption.py        # Encryption tests
│   ├── test_integration.py       # Local integration tests
│   ├── test_integration_docker.py # Docker integration tests
│   ├── test_message_retrieval.py # Message API tests
│   └── test_all.py               # Comprehensive test suite
├── scripts/                       # Utility scripts
│   └── run-basic-docker-test.sh  # Quick Docker test
├── docs/                         # Documentation
│   └── DOCKER_TESTING.md        # Docker testing guide
└── config/                       # Configuration files
    └── local.env                 # Local environment template
```

## 🔐 **Security Considerations**

### **Encryption**
- Messages are encrypted using **Google Cloud KMS** before storage
- Each message has unique encryption keys and initialization vectors
- Decryption only occurs during authorized retrieval

### **Authentication**
- Webhook endpoints protected by secret token validation
- Google Cloud IAM controls access to encryption keys
- No sensitive data in logs or error messages

### **Testing Security**
- Mock implementations maintain same security patterns
- Test data uses realistic encryption structures
- No production credentials in test environments

## 📊 **Performance**

### **Benchmarks**
- **Message Processing**: ~100 messages/second
- **Batch Retrieval**: 500 messages in ~2 seconds
- **Docker Startup**: ~3 seconds in testing mode
- **API Response Time**: <100ms for health checks

### **Scaling**
- Firestore auto-scales for high throughput
- Stateless Flask app supports horizontal scaling
- KMS encryption adds ~10ms overhead per message

## 🧑‍💻 **Development**

### **Code Style**
```bash
# Format code
make format

# Lint code
make lint

# Type checking
make type-check

# All quality checks
make check
```

### **Adding Features**
1. **Write tests first** (TDD approach)
2. **Update mock implementations** for new Google Cloud features
3. **Add Docker tests** for integration scenarios
4. **Update documentation** and diagrams

### **Debugging**
```bash
# Local development with debug
FLASK_DEBUG=true TESTING=true python main.py

# Docker container logs
docker logs <container_name>

# Test debugging
python -m pytest tests/ -v -s --tb=long
```

## 📈 **Monitoring & Observability**

- **Health Checks**: `/healthz` endpoint for load balancer probes
- **Structured Logging**: JSON logs for cloud monitoring
- **Error Tracking**: Exception logging with context
- **Metrics**: Message processing rates and error rates

## 🤝 **Contributing**

1. **Fork** the repository
2. **Create** a feature branch
3. **Write tests** for your changes
4. **Ensure** all tests pass: `make test && make docker-test`
5. **Submit** a pull request

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

## 🚨 **Support**

- **Documentation**: Check `docs/` directory
- **Issues**: Create GitHub issues for bugs
- **Security**: See `SECURITY.md` for reporting vulnerabilities

---

**Built with ❤️ for secure, scalable messaging infrastructure**
