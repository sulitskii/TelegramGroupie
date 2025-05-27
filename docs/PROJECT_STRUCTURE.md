# 📁 Project Structure

## Overview
This document outlines the systematic organization of the TelegramGroupie project, following enterprise-grade architectural patterns with clear separation of concerns.

## 🎯 Root Directory (Minimal & Clean)
The root directory contains only the essential application files:

```
📦 telegram2whatsapp/
├── 📄 main.py              # Flask application (entry point)
├── 📄 interfaces.py        # Core interfaces and abstract base classes
├── 📄 encryption.py        # Encryption utilities and key management
├── 📄 Makefile             # Build automation and development commands
├── 📄 README.md            # Project overview and quick start
├── 📄 SECURITY.md          # Security policies and reporting
└── 📄 .gitignore           # Git ignore patterns
```

**Key Principle:** Only code that represents the core application logic remains at the root level.

## 🏗️ Source Code (`src/`)
Organized production source code:

```
src/
├── core/
│   ├── __init__.py
│   └── service_container.py    # Dependency injection containers
└── implementations/
    ├── __init__.py
    ├── production.py           # Production implementations
    └── test.py                 # Test/mock implementations
```

- **`src/core/`** - Core architectural components (dependency injection, etc.)
- **`src/implementations/`** - Environment-specific implementations 