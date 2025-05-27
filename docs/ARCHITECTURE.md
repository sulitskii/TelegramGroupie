# System Architecture

## 🏗️ **High-Level Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TELEGRAMGROUPIE                               │
│                      Smart Group Management Platform                       │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────────────────────┐
                    │           TELEGRAM API              │
                    │     (Webhook Integration)           │
                    └─────────────────┬───────────────────┘
                                      │ HTTPS POST
                                      │ /webhook/{secret}
                                      ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                         FLASK APPLICATION                           │
    │                    (Dependency Injection)                           │
    │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │
    │  │   Webhook       │  │   Message       │  │   API Endpoints     │ │
    │  │   Handler       │  │   Processing    │  │   (/messages)       │ │
    │  │                 │  │                 │  │                     │ │
    │  └─────────────────┘  └─────────────────┘  └─────────────────────┘ │
    └─────────────────────────────┬───────────────────────────────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                    ▼             ▼             ▼
    ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
    │   GOOGLE CLOUD      │ │   GOOGLE CLOUD      │ │    WHATSAPP         │
    │     FIRESTORE       │ │        KMS          │ │   BUSINESS API      │
    │                     │ │                     │ │                     │
    │ • Message Storage   │ │ • Encryption Keys   │ │ • Message Delivery  │
    │ • Metadata          │ │ • Secure Encryption │ │ • Group Management  │
    │ • Search/Query      │ │ • Key Management    │ │ • Status Updates    │
    └─────────────────────┘ └─────────────────────┘ └─────────────────────┘
```

## 🔄 **Message Flow Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              MESSAGE FLOW                                  │
└─────────────────────────────────────────────────────────────────────────────┘

1. TELEGRAM MESSAGE RECEIVED
   ┌─────────────┐
   │ User sends  │ ──┐
   │ message to  │   │
   │ Telegram    │   │
   │ group       │   │
   └─────────────┘   │
                     │ Webhook POST
                     ▼
2. WEBHOOK PROCESSING        ┌─────────────────────────────────┐
   ┌─────────────┐          │         FLASK APP               │
   │ Validate    │ ───────▶ │                                 │
   │ webhook     │          │ ┌─────────────────────────────┐ │
   │ secret      │          │ │    process_message()        │ │
   └─────────────┘          │ │                             │ │
                            │ │ • Extract message data      │ │
                            │ │ • Get user info             │ │
                            │ │ • Get chat info             │ │
                            │ └─────────────────────────────┘ │
                            └─────────────────┬───────────────┘
                                              │
3. ENCRYPTION                                 ▼
   ┌─────────────┐          ┌─────────────────────────────────┐
   │ Google      │ ◀────────│      encryption.encrypt()      │
   │ Cloud KMS   │          │                                 │
   │             │          │ • Generate unique DEK          │
   │ • DEK       │ ────────▶│ • Encrypt message text          │
   │ • Envelope  │          │ • Return encrypted data:        │
   │   Encryption│          │   - ciphertext                  │
   │             │          │   - encrypted_data_key          │
   │             │          │   - initialization_vector       │
   │             │          │   - salt                        │
   └─────────────┘          └─────────────────┬───────────────┘
                                              │
4. STORAGE                                    ▼
   ┌─────────────┐          ┌─────────────────────────────────┐
   │ Google      │ ◀────────│      db.collection().add()     │
   │ Cloud       │          │                                 │
   │ Firestore   │          │ Document Structure:             │
   │             │          │ {                               │
   │ Collection: │          │   message_id: 12345,            │
   │ "messages"  │          │   chat_id: -100123456789,       │
   │             │          │   user_id: 987654321,           │
   │             │          │   encrypted_text: {             │
   │             │          │     ciphertext: "...",          │
   │             │          │     encrypted_data_key: "...",  │
   │             │          │     iv: "...",                  │
   │             │          │     salt: "..."                 │
   │             │          │   },                            │
   │             │          │   timestamp: "2024-01-01T...",  │
   │             │          │   type: "telegram"              │
   │             │          │ }                               │
   └─────────────┘          └─────────────────────────────────┘

5. WHATSAPP DELIVERY (Future Implementation)
   ┌─────────────┐          ┌─────────────────────────────────┐
   │ WhatsApp    │ ◀────────│     Send to WhatsApp Groups     │
   │ Business    │          │                                 │
   │ API         │          │ • Decrypt message               │
   │             │          │ • Format for WhatsApp           │
   │             │          │ • Send to target groups         │
   │             │          │ • Handle delivery status        │
   └─────────────┘          └─────────────────────────────────┘
```

## 🧪 **Dependency Injection Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DEPENDENCY INJECTION SYSTEM                        │
└─────────────────────────────────────────────────────────────────────────────┘

APPLICATION FACTORY PATTERN
┌─────────────────────┐      ┌─────────────────────┐      ┌─────────────────────┐
│      INTERFACES     │      │   SERVICE CONTAINER │      │  IMPLEMENTATIONS    │
│                     │      │                     │      │                     │
│ ┌─────────────────┐ │      │ ┌─────────────────┐ │      │ ┌─────────────────┐ │
│ │ DatabaseClient  │ │◀────▶│ │  Environment    │ │────▶ │ │ Production/     │ │
│ │ EncryptionSvc   │ │      │ │  Detection      │ │      │ │ Test Impls      │ │
│ │ TelegramBot     │ │      │ │                 │ │      │ │                 │ │
│ │ MessageHandler  │ │      │ │ • APP_ENV       │ │      │ │ • Production:   │ │
│ └─────────────────┘ │      │ │ • FLASK_ENV     │ │      │ │   Real GCP      │ │
└─────────────────────┘      │ │ • pytest       │ │      │ │ • Test:         │ │
                             │ │   detection     │ │      │ │   Mocks         │ │
                             │ └─────────────────┘ │      │ └─────────────────┘ │
                             └─────────────────────┘      └─────────────────────┘

ENVIRONMENT DETECTION LOGIC
┌─────────────────────────────────────────────────────────────────────────────┐
│ def create_service_container(environment: str = None) -> ServiceContainer:   │
│     if environment is None:                                                 │
│         if os.environ.get("APP_ENV") == "test":                             │
│             environment = "test"                                            │
│         elif os.environ.get("FLASK_ENV") == "testing":                      │
│             environment = "test"                                            │
│         elif "pytest" in os.environ.get("_", ""):                          │
│             environment = "test"                                            │
│         else:                                                               │
│             environment = "production"                                      │
│                                                                             │
│     return (TestServiceContainer() if environment == "test"                │
│             else ProductionServiceContainer())                             │
└─────────────────────────────────────────────────────────────────────────────┘

PRODUCTION ENVIRONMENT                   TEST ENVIRONMENT
┌─────────────────────┐                 ┌─────────────────────┐
│    REAL SERVICES    │                 │   MOCK SERVICES     │
│                     │                 │                     │
│ ┌─────────────────┐ │                 │ ┌─────────────────┐ │
│ │ Google Cloud    │ │                 │ │ In-Memory       │ │
│ │ Firestore       │ │                 │ │ Database        │ │
│ │ • Real database │ │ ────REPLACED──▶ │ │ • Dict storage  │ │
│ │ • Network calls │ │     WITH        │ │ • No network    │ │
│ │ • Authentication│ │                 │ │ • Fast startup  │ │
│ │ • GCP billing   │ │                 │ │ • Test data     │ │
│ └─────────────────┘ │                 │ └─────────────────┘ │
│                     │                 │                     │
│ ┌─────────────────┐ │                 │ ┌─────────────────┐ │
│ │ Google Cloud    │ │                 │ │ Mock Encryption │ │
│ │ KMS             │ │                 │ │ • Base64 encode │ │
│ │ • HSM encryption│ │ ────REPLACED──▶ │ │ • No GCP calls  │ │
│ │ • Key management│ │     WITH        │ │ • Deterministic │ │
│ │ • IAM policies  │ │                 │ │ • Test-friendly │ │
│ └─────────────────┘ │                 │ └─────────────────┘ │
│                     │                 │                     │
│ ┌─────────────────┐ │                 │ ┌─────────────────┐ │
│ │ Telegram Bot    │ │                 │ │ Mock Telegram   │ │
│ │ • Real bot API  │ │                 │ │ Bot             │ │
│ │ • Rate limits   │ │ ────REPLACED──▶ │ │ • Log messages  │ │
│ │ • Network deps  │ │     WITH        │ │ • No-op methods │ │
│ │ • Token required│ │                 │ │ • Offline tests │ │
│ └─────────────────┘ │                 │ └─────────────────┘ │
└─────────────────────┘                 └─────────────────────┘

KEY BENEFITS:
✅ Identical application logic in all environments
✅ No conditional branches based on environment flags  
✅ Clean separation of concerns
✅ Easy testing with injected mocks
✅ Production code contains zero testing logic
```

## 🐳 **Docker Testing Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DOCKER TEST ENVIRONMENT                           │
└─────────────────────────────────────────────────────────────────────────────┘

CONTAINER ORCHESTRATION
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│    TEST RUNNER      │────▶│    APPLICATION      │────▶│   TEST RESULTS      │
│                     │     │     CONTAINER       │     │                     │
│ ┌─────────────────┐ │     │ ┌─────────────────┐ │     │ ┌─────────────────┐ │
│ │ pytest          │ │     │ │ Flask App       │ │     │ │ JUnit XML       │ │
│ │ HTTP requests   │ │     │ │ Test services   │ │     │ │ HTML reports    │ │
│ │ Integration     │ │     │ │ APP_ENV=test    │ │     │ │ Coverage data   │ │
│ │ tests           │ │     │ │ Port 8080       │ │     │ │ Logs            │ │
│ └─────────────────┘ │     │ └─────────────────┘ │     │ └─────────────────┘ │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
           │                           │                           │
           └───────────────────────────┼───────────────────────────┘
                                       │
                            ┌─────────────────────┐
                            │   DOCKER NETWORK    │
                            │    test-network     │
                            │                     │
                            │ • Container-to-     │
                            │   container comms   │
                            │ • Isolated testing  │
                            │ • No external deps  │
                            └─────────────────────┘

TEST EXECUTION FLOW:
1. docker-compose up --build
2. Build application container with APP_ENV=test
3. Start test runner container
4. Test runner makes HTTP requests to app container
5. Application responds using injected mock services
6. Test results written to shared volume
7. Containers shut down automatically
```

## 🏭 **CI/CD Pipeline Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CI/CD PIPELINE                                │
└─────────────────────────────────────────────────────────────────────────────┘

GITHUB ACTIONS WORKFLOW
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   TRIGGER   │───▶│    BUILD    │───▶│    TEST     │───▶│   DEPLOY    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼

┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ • git push  │    │ • Python    │    │ • Unit      │    │ • Google    │
│ • PR create │    │   3.11      │    │   tests     │    │   Cloud     │
│ • scheduled │    │ • pip       │    │ • Integration │   │   Run       │
│   runs      │    │   install   │    │   tests     │    │ • Container │
│             │    │ • lint      │    │ • Docker    │    │   Registry  │
│             │    │ • format    │    │   tests     │    │ • Health    │
│             │    │ • deps      │    │ • Coverage  │    │   checks    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘

PARALLEL TEST MATRIX:
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TEST EXECUTION                                   │
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │   Unit      │  │ Integration │  │   Docker    │  │   E2E       │       │
│  │   Tests     │  │   Tests     │  │   Tests     │  │   Tests     │       │
│  │             │  │             │  │             │  │             │       │
│  │ • Fast      │  │ • Mock      │  │ • Container │  │ • Full      │       │
│  │ • Isolated  │  │   services  │  │   testing   │  │   pipeline  │       │
│  │ • Coverage  │  │ • HTTP API  │  │ • Network   │  │ • Real      │       │
│  │ • 32 tests  │  │ • Real flow │  │   isolation │  │   deploy    │       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🔐 **Security Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            SECURITY LAYERS                                 │
└─────────────────────────────────────────────────────────────────────────────┘

TRANSPORT SECURITY
┌─────────────────────────────────────────────────────────────────────────────┐
│ HTTPS/TLS 1.3 (Telegram ←→ Flask ←→ Google Cloud)                         │
└─────────────────────────────────────────────────────────────────────────────┘

APPLICATION SECURITY
┌─────────────────────────────────────────────────────────────────────────────┐
│ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│ │   WEBHOOK       │  │   ENDPOINT      │  │       INPUT                 │ │
│ │   VALIDATION    │  │   SECURITY      │  │    VALIDATION               │ │
│ │                 │  │                 │  │                             │ │
│ │ • Secret token  │  │ • Rate limiting │  │ • Message size limits       │ │
│ │ • Path hiding   │  │ • CORS policy   │  │ • Content sanitization      │ │
│ │ • IP filtering  │  │ • Auth required │  │ • SQL injection prevention  │ │
│ └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘

DATA SECURITY
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ENCRYPTION AT REST                                │
│                                                                             │
│ ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐ │
│ │  PLAINTEXT      │  KMS    │   ENCRYPTED     │ Firestore │   STORAGE     │ │
│ │   MESSAGE       │ ──────▶ │   MESSAGE       │ ──────▶  │   LAYER       │ │
│ │                 │ Encrypt │                 │ Store    │               │ │
│ │ "Hello World"   │         │ {               │          │ Collection:   │ │
│ │                 │         │   ciphertext,   │          │ "messages"    │ │
│ │                 │         │   encrypted_key,│          │               │ │
│ │                 │         │   iv,           │          │ + Firestore   │ │
│ │                 │         │   salt          │          │   encryption  │ │
│ │                 │         │ }               │          │ + Disk        │ │
│ │                 │         │                 │          │   encryption  │ │
│ └─────────────────┘         └─────────────────┘          └─────────────────┘ │
│                                                                             │
│ DECRYPTION FLOW (Reverse)                                                   │
│ Storage → Firestore → Envelope Decryption → KMS → Plaintext                │
└─────────────────────────────────────────────────────────────────────────────┘

ACCESS CONTROL
┌─────────────────────────────────────────────────────────────────────────────┐
│ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│ │  GOOGLE CLOUD   │  │   SERVICE       │  │      PRINCIPLE OF           │ │
│ │     IAM         │  │   ACCOUNTS      │  │    LEAST PRIVILEGE          │ │
│ │                 │  │                 │  │                             │ │
│ │ • Role-based    │  │ • Firestore     │  │ • Minimal permissions       │ │
│ │   access        │  │   read/write    │  │ • No admin access           │ │
│ │ • Resource      │  │ • KMS encrypt/  │  │ • Audit logging             │ │
│ │   scoping       │  │   decrypt only  │  │ • Regular rotation          │ │
│ └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 📊 **Data Model Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             DATA MODEL                                     │
└─────────────────────────────────────────────────────────────────────────────┘

FIRESTORE COLLECTION: "messages"
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DOCUMENT                                      │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ document_id: "auto-generated-uuid"                                     │ │
│ │ {                                                                       │ │
│ │   message_id: 12345,              // Telegram message ID               │ │
│ │   chat_id: -100123456789,         // Telegram chat ID (negative)       │ │
│ │   chat_title: "Test Group",       // Human-readable chat name          │ │
│ │   user_id: 987654321,             // Telegram user ID                  │ │
│ │   username: "john_doe",           // Telegram username                  │ │
│ │   encrypted_text: {               // Encrypted message content          │ │
│ │     ciphertext: "base64...",      // AES-256 encrypted text             │ │
│ │     encrypted_data_key: "...",    // KMS-encrypted DEK                  │ │
│ │     iv: "hex...",                 // Initialization vector              │ │
│ │     salt: "hex..."                // Salt for key derivation            │ │
│ │   },                                                                    │ │
│ │   timestamp: "2024-01-01T12:00:00Z", // ISO 8601 timestamp             │ │
│ │   type: "telegram",               // Message source type                │ │
│ │   metadata: {                     // Optional metadata                  │ │
│ │     reply_to_message_id: 12344,   // If replying to another message     │ │
│ │     forwarded_from: "channel",    // If forwarded                       │ │
│ │     has_media: false,             // If contains media                  │ │
│ │     message_type: "text"          // text, photo, video, etc.           │ │
│ │   }                                                                     │ │
│ │ }                                                                       │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘

INDEXING STRATEGY
┌─────────────────────────────────────────────────────────────────────────────┐
│ PRIMARY INDEXES (Automatic)                                                │
│ • document_id (unique)                                                      │
│                                                                             │
│ COMPOSITE INDEXES (firestore.indexes.json)                                 │
│ • [chat_id, timestamp] - For chat message retrieval                        │
│ • [user_id, timestamp] - For user message retrieval                        │
│ • [chat_id, user_id, timestamp] - For filtered queries                     │
│ • [type, timestamp] - For message type filtering                           │
└─────────────────────────────────────────────────────────────────────────────┘

QUERY PATTERNS
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. GET RECENT MESSAGES FROM CHAT                                           │
│    db.collection('messages')                                               │
│      .where('chat_id', '==', -100123456789)                               │
│      .orderBy('timestamp', 'desc')                                         │
│      .limit(100)                                                           │
│                                                                             │
│ 2. GET USER MESSAGES ACROSS CHATS                                          │
│    db.collection('messages')                                               │
│      .where('user_id', '==', 987654321)                                    │
│      .orderBy('timestamp', 'desc')                                         │
│      .limit(50)                                                            │
│                                                                             │
│ 3. PAGINATED RETRIEVAL                                                     │
│    db.collection('messages')                                               │
│      .where('chat_id', '==', -100123456789)                               │
│      .orderBy('timestamp', 'desc')                                         │
│      .startAfter(last_document)                                            │
│      .limit(100)                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🚀 **Deployment Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRODUCTION DEPLOYMENT                            │
└─────────────────────────────────────────────────────────────────────────────┘

GOOGLE CLOUD RUN
┌─────────────────────────────────────────────────────────────────────────────┐
│ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│ │    TRAFFIC      │  │   CONTAINER     │  │         SCALING             │ │
│ │  MANAGEMENT     │  │   INSTANCES     │  │                             │ │
│ │                 │  │                 │  │                             │ │
│ │ • Load          │  │ • Flask app     │  │ • 0-1000 instances          │ │
│ │   balancing     │  │ • Python 3.11   │  │ • Auto-scaling based on     │ │
│ │ • TLS           │  │ • Docker        │  │   CPU/memory/requests       │ │
│ │   termination   │  │   container     │  │ • Cold start: ~2 seconds    │ │
│ │ • Health        │  │ • Memory: 512MB │  │ • Warm instances for        │ │
│ │   checks        │  │ • CPU: 1 vCPU   │  │   better performance        │ │
│ └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘

REGIONAL AVAILABILITY
┌─────────────────────────────────────────────────────────────────────────────┐
│ PRIMARY: us-central1 (Iowa)                                                │
│ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│ │  CLOUD RUN      │  │   FIRESTORE     │  │         KMS                 │ │
│ │   SERVICE       │  │   DATABASE      │  │                             │ │
│ │                 │  │                 │  │                             │ │
│ │ • Multi-zone    │  │ • Multi-region  │  │ • Global key management     │ │
│ │   deployment    │  │   replication   │  │ • Hardware security         │ │
│ │ • 99.95% SLA    │  │ • 99.999% SLA   │  │   modules (HSM)             │ │
│ │ • Automatic     │  │ • Consistent    │  │ • Automatic key rotation    │ │
│ │   failover      │  │   backups       │  │ • Audit logging             │ │
│ └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘

MONITORING & OBSERVABILITY
┌─────────────────────────────────────────────────────────────────────────────┐
│ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│ │   CLOUD         │  │   ERROR         │  │       ALERTING              │ │
│ │  MONITORING     │  │  REPORTING      │  │                             │ │
│ │                 │  │                 │  │                             │ │
│ │ • Request       │  │ • Exception     │  │ • PagerDuty integration     │ │
│ │   metrics       │  │   tracking      │  │ • Slack notifications       │ │
│ │ • Latency       │  │ • Stack traces  │  │ • Email alerts              │ │
│ │ • Error rates   │  │ • User context  │  │ • Escalation policies       │ │
│ │ • Custom        │  │ • Performance   │  │ • Incident management       │ │
│ │   dashboards    │  │   insights      │  │ • SLO/SLI monitoring        │ │
│ └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🔄 **API Architecture**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API DESIGN                                    │
└─────────────────────────────────────────────────────────────────────────────┘

REST ENDPOINTS
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│ GET /healthz                           │ Health check endpoint              │
│ ├─ Returns: {"status": "ok"}           │ Used by load balancers             │
│ └─ Response time: <10ms                │ No authentication required         │
│                                        │                                    │
│ POST /webhook/{secret}                 │ Telegram webhook receiver          │
│ ├─ Auth: Secret token in URL           │ Processes incoming messages        │
│ ├─ Body: Telegram Update JSON          │ Validates webhook signature        │
│ └─ Returns: {"status": "ok"}           │ Triggers message processing         │
│                                        │                                    │
│ GET /messages                          │ Message retrieval endpoint         │
│ ├─ Query params:                       │ Supports filtering and pagination  │
│ │  • chat_id (optional)               │ Returns decrypted messages          │
│ │  • user_id (optional)               │ Includes metadata                   │
│ │  • limit (default: 100)             │                                    │
│ │  • start_after (pagination)         │                                    │
│ └─ Returns: {messages: [...], token}   │                                    │
│                                        │                                    │
│ POST /messages/batch                   │ Batch message processing            │
│ ├─ Body: {chat_id, user_id, batch_size}│ Bulk operations support            │
│ └─ Returns: {messages: [...], count}   │ Optimized for large datasets       │
│                                        │                                    │
└─────────────────────────────────────────────────────────────────────────────┘

ERROR HANDLING
┌─────────────────────────────────────────────────────────────────────────────┐
│ HTTP STATUS CODES                                                           │
│ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│ │      2xx        │  │      4xx        │  │           5xx               │ │
│ │    SUCCESS      │  │   CLIENT ERROR  │  │       SERVER ERROR          │ │
│ │                 │  │                 │  │                             │ │
│ │ • 200 OK        │  │ • 400 Bad       │  │ • 500 Internal Server       │ │
│ │ • 201 Created   │  │   Request       │  │   Error                     │ │
│ │                 │  │ • 401 Unauthorized│ │ • 502 Bad Gateway           │ │
│ │                 │  │ • 404 Not Found │  │ • 503 Service               │ │
│ │                 │  │ • 405 Method    │  │   Unavailable               │ │
│ │                 │  │   Not Allowed   │  │ • 504 Gateway Timeout       │ │
│ └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
│                                                                             │
│ ERROR RESPONSE FORMAT                                                       │
│ {                                                                           │
│   "error": "Human readable error message",                                 │
│   "code": "ERROR_CODE_CONSTANT",                                           │
│   "details": {                                                             │
│     "field": "specific_field_with_error",                                  │
│     "value": "invalid_value_provided"                                      │
│   },                                                                       │
│   "timestamp": "2024-01-01T12:00:00Z",                                     │
│   "request_id": "uuid-for-tracking"                                        │
│ }                                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

This comprehensive architecture documentation provides a detailed view of the system design, covering all major components, data flows, security considerations, and deployment strategies. The diagrams use ASCII art for universal compatibility and easy maintenance in version control.

The architecture is built on solid dependency injection principles, ensuring clean separation between environments while maintaining identical application behavior across all deployments.

┌─────────────────────────────────────────────────────────────────────────────┐
│                            TELEGRAMGROUPIE                                  │
│                      Smart Group Management Platform                        │
└─────────────────────────────────────────────────────────────────────────────┘
