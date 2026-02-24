# Design Decisions & Trade-offs

This document explains the architectural decisions made in this project and the trade-offs involved.

---

## 1. OAuth Approach: Refresh Token vs Full Authorization Flow

### Decision  
Use a long-lived `refresh_token` stored in environment variables and mint short-lived access tokens programmatically.

### Why
- Appropriate for backend/server-to-server architecture  
- No interactive browser flow required  
- Deterministic and reliable  
- Minimal implementation complexity  

### Trade-off
- Requires manual initial OAuth setup  
- Less flexible than full Authorization Code + PKCE flow  
- Assumes pre-generated refresh token  

### Rationale
For a scoped backend integration, the refresh-token approach provides secure authentication without unnecessary complexity. A full OAuth flow would be appropriate for a distributed SaaS application but is intentionally avoided here to prevent overengineering.

---

## 2. Dedicated `SalesforceClient` Abstraction

### Decision  
Encapsulate all Salesforce API logic in a dedicated client.

### Why
- Centralizes authentication
- Eliminates duplicated HTTP logic
- Implements retry-once logic consistently
- Improves testability and modularity

### Trade-off
- Adds a thin abstraction layer

This structure supports long-term maintainability and production evolution.

---

## 3. Retry-once Token Strategy

Salesforce does not reliably expose expiration metadata for refresh-token flows.

### Decision  
Refresh only when `INVALID_SESSION_ID` is returned.

### Why
- Deterministic behavior  
- Avoids speculative expiration logic  
- Simpler and more robust  

### Trade-off
- The first expired request may fail once before retry

---

## 4. Functional MCP Tools vs Class-based Tool Objects

### Decision  
Register plain functions as MCP tools.

### Why
- Clear tool boundaries  
- Stateless wrappers over shared client  
- Cleaner introspection for MCP  

### Trade-off
- Flat structure can grow large as tool count increases  
- Less natural grouping of related operations  
- Harder to attach shared behavior via inheritance  

### Alternative  
Define tool classes (e.g., `ContactTools`, `AppointmentTools`) and register methods.

This would:
- Improve logical grouping
- Support shared validation or pre-processing
- Scale better if tool surface grows significantly

### Rationale  
For the current scope, function-based tools keep the interface simple and transparent. If the tool surface expands substantially, migrating to grouped tool classes would be appropriate.

---

## 5. Minimal Salesforce Configuration

All business logic resides in the Python codebase.

### Why
- No custom Apex  
- No custom Salesforce metadata  
- Easily portable across orgs  
- Deployment requires only credentials  

### Trade-off
- Limited to standard REST API capabilities  

This keeps the integration modular and transferable.

---

## 6. Synchronous HTTP Client

### Decision  
Use synchronous `httpx.Client`.

### Why
- MCP server runs over stdio  
- No concurrency requirements  
- Simpler control flow  

Async was intentionally avoided to reduce unnecessary complexity.

---

## 7. Boundary Validation with Pydantic

### Decision  
Validate all request bodies before sending to Salesforce.

### Why
- Prevent malformed API calls  
- Clear schema contracts  
- Strongly typed integration boundary  

This ensures invalid data fails early and predictably.

---

## 8. Strong Typing, Static Analysis & Code Quality

### Strong Typing

The project uses full Python 3.11 type hints and Pydantic models.

**Benefits:**
- Clear data contracts  
- Reduced runtime surprises  
- Safer refactoring  
- Improved IDE support  
- Predictable, traceable errors

All errors that surface are standard Python errors, making them easy to recognize and debug.

---

### Static Type Checking (MyPy)

MyPy is enforced in CI to detect:
- Missing parameters  
- Incorrect return types  
- Type mismatches  
- Improper optional handling
- It checks for any error that could have been missed or not caught during development

This catches entire classes of issues before runtime.

---

### Deterministic Formatting & Linting

The project enforces:
- `black`
- `isort`
- CI linting workflows  

Clean, consistent formatting:
- Reduces cognitive load  
- Makes diffs smaller  
- Improves readability  
- Simplifies debugging  

Readable code is easier to understand and safer to maintain.

---

### Clear Documentation

Core components include structured Google-style docstrings describing:
- Intent
- Inputs
- Outputs
- Failure behavior  

This improves maintainability and onboarding and makes the system easier for both humans and AI tooling to understand.

---

### Dependency Management with Poetry

Poetry is used for:
- Deterministic dependency resolution  
- Lockfile management  
- Environment isolation  
- Structured dependency grouping  

This prevents dependency drift and improves reproducibility.

---

# Design Philosophy

The architecture prioritizes:

- Clarity over cleverness  
- Determinism over speculation  
- Explicit contracts over implicit behavior  
- Maintainability over shortcuts  

The result is a modular, strongly typed, readable, production-extendable integration layer that avoids unnecessary complexity while remaining robust.
