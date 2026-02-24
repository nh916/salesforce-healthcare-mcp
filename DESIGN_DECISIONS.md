# Design Decisions & Trade-offs

This document explains the architectural decisions made in this project and the trade-offs involved.

---

## 1. OAuth Approach: Refresh Token vs Full Authorization Flow

### Decision

Use a long-lived `refresh_token` stored in environment variables and mint short-lived access tokens programmatically.

### Why

* Faster to implement
* No interactive browser flow required
* Deterministic and reliable for backend integrations
* Appropriate for server-to-server architecture

### Trade-off

* Requires manual initial OAuth setup
* Less flexible than implementing full Authorization Code + PKCE flow
* Assumes a pre-generated refresh token

### Alternative (More Complete) Approach

Implement the full OAuth authorization flow within the application:

* Authorization Code grant
* Redirect URI handling
* Token exchange endpoint
* Automatic refresh storage

That approach is more production-ready for distributed apps or SaaS products but adds significant complexity that is unnecessary for a scoped integration project.

### Rationale

For this project, the refresh-token approach provides secure, clean authentication without overengineering.

---

## 2. Dedicated `SalesforceClient` Abstraction

### Decision

Encapsulate all Salesforce API logic in a `SalesforceClient`.

### Why

* Centralizes authentication
* Prevents duplicated HTTP logic
* Enables retry-once logic for expired sessions
* Improves testability and modularity

### Trade-off

* Indirection layer vs direct requests

This is the correct long-term architectural choice for maintainability.

---

## 3. Retry-once Token Strategy

Salesforce does not reliably provide expiration metadata for refresh-token flows.

### Decision

Refresh token only when `INVALID_SESSION_ID` is returned.

### Why

* Deterministic
* Avoids speculative expiration logic
* Keeps implementation simple

### Trade-off

* First expired request may fail once before retry

---

## 4. Functional MCP Tools vs Class-based Tool Objects

### Decision

Register plain functions as MCP tools.

### Why

* Clear and explicit tool boundaries
* Simpler introspection for MCP
* Stateless wrappers around a shared client

### Trade-off

* Tools live in a flat structure
* Less object grouping than class-based registration

This keeps the tool layer clean and predictable.

---

## 5. Using Salesforce as the Source of Truth

### Decision

Operate directly on Salesforce `Contact` and `Event` sObjects.

### Why

* Avoids data duplication
* No sync layer needed
* Leverages Salesforce schema and validation

### Trade-off

* Tightly coupled to Salesforce
* No local caching or offline mode

For an integration project, Salesforce should remain authoritative.

---

## 6. Minimal Salesforce Configuration

All business logic exists in the Python codebase.

### Why

* No custom Apex required
* No custom Salesforce metadata configuration
* Highly portable integration
* Easy to deploy to another org with only credentials

### Trade-off

* Less deep customization of Salesforce features
* Operates within standard REST capabilities

This keeps the integration modular and transferable.

---

## 7. Synchronous HTTP Client

### Decision

Use synchronous `httpx.Client`.

### Why

* MCP server operates over stdio
* No concurrency requirement
* Simpler control flow

Async was intentionally avoided to reduce unnecessary complexity.

---

## 8. Boundary Validation with Pydantic

### Decision

Validate all request bodies before sending to Salesforce.

### Why

* Prevent malformed API calls
* Strong typing
* Clear schema documentation

---

# Design Philosophy

The architecture favors:

* Clarity over cleverness
* Determinism over speculation
* Modularity over shortcuts
* Correctness over premature optimization

The result is a clean, extensible integration layer suitable for production evolution without unnecessary complexity for the current scope.
