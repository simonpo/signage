# ADR 0001: Plugin System Architecture

**Status:** Proposed
**Date:** 2025-11-29
**Deciders:** Core Team
**Tags:** architecture, plugins, configuration

## Context

The current signage system requires code changes to add new data sources or configure multiple instances of the same type (e.g., multiple football teams). This creates friction for:

1. **End users** who want to customize without modifying Python code
2. **Contributors** who want to add new data sources
3. **Operators** who need flexible scheduling and configuration

### Goals
- Make it easy for individuals to adopt and customize the system
- Enable dynamic configuration without code changes
- Support multiple instances of the same source type
- Maintain backward compatibility with existing CLI-based workflow
- Ensure reliability (timeouts, circuit breakers, error handling)
- Provide good observability for debugging

### Target Scale
- **Primary:** Single user, 5-20 data sources
- **Secondary:** Small community (10-50 users), each with custom configs
- **Not targeting:** Multi-tenant SaaS, thousands of concurrent users

## Decision

We will implement a **YAML-based plugin system** with the following architecture:

### Phase 1: MVP (Weeks 1-2)

**Core Components:**

1. **Plugin Registry** - Decorator-based registration system
   ```python
   @SourceRegistry.register('weather')
   class WeatherSource(BaseSource):
       ...
   ```

2. **Base Source Interface** - Abstract base class with:
   - `fetch_data() -> SignageContent` (abstract, implemented by plugins)
   - `validate_config() -> bool` (abstract, validates plugin-specific config)
   - `execute() -> tuple[SignageContent, SourceMetrics]` (concrete, handles metrics/errors)

3. **YAML Configuration** - Pydantic-validated config schema:
   ```yaml
   sources:
     - id: weather_home
       type: weather
       enabled: true
       schedule: "*/15 * * * *"
       timeout: 30
       config:
         city: Seattle
         api_key: ${OPENWEATHER_API_KEY}
       rendering:
         layout: modern_weather
         background: local
   ```

4. **Backward Compatibility** - Dual mode execution:
   - If `sources.yaml` exists → use plugin system
   - Otherwise → use existing CLI-based system

5. **Migration Tool** - `--migrate` flag to generate `sources.yaml` from current `.env` config

**Architecture Decisions:**

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Outputs per source** | Single only | Simpler metrics, easier testing. Multi-output deferred to Phase 2. |
| **Source dependencies** | Independent (no DAG) | Most signage sources are independent. DAG adds complexity we don't need yet. |
| **Data sharing** | Fully isolated | Avoids shared state bugs. Cache deduplication deferred to future. |
| **Scheduling** | Static cron only | Covers 95% of use cases. Conditional scheduling deferred to Phase 2. |
| **Plugin discovery** | Explicit imports | Simple and obvious. Auto-discovery deferred to Phase 2. |
| **Conditional rendering** | Code-based (`_should_render()`) | Flexible, allows plugin-specific logic. Config-driven conditions deferred. |

### Phase 2: Production Ready (Weeks 3-4)

**Reliability Features:**

1. **Timeouts** - Built-in per-source timeouts (default 30s, configurable)
   - Prevents hanging sources from blocking system
   - Raises `TimeoutError` if exceeded

2. **Circuit Breaker** - Automatic backoff on failures
   - Exponential backoff: 1min, 2min, 4min, 8min (max 30min)
   - Prevents hammering broken APIs
   - Auto-recovery when service comes back

3. **Retry Logic** - Configurable retry with exponential backoff
   ```yaml
   retry:
     enabled: true
     max_attempts: 3
     backoff_seconds: [1, 2, 4]
   ```

4. **Cached Fallback** - Optional stale data fallback
   ```yaml
   fallback:
     use_cached: true
     max_age_hours: 24
   ```

5. **Parallel Execution** - AsyncIO-based concurrent execution
   - Sources run in parallel (faster)
   - One failure doesn't block others
   - Graceful handling of exceptions

6. **Metrics Persistence** - JSON-based metrics storage
   - Survives restarts
   - Enables trend analysis
   - Simple file format (no DB required)

7. **Config Validation** - Pydantic schemas with:
   - Unique ID enforcement
   - Cron expression validation
   - Required field checking
   - Helpful error messages

### Phase 3: Observability (Week 5)

**OpenTelemetry Integration:**

1. **Distributed Tracing** - Full request tracing
   - Source execution → Client call → API request → Rendering
   - Identify bottlenecks and failures

2. **Flexible Export** - Multiple backends:
   - Console (default, simple logging)
   - Jaeger (optional, for power users)
   - Zipkin (optional)
   - File-based (simple JSON traces)

3. **Structured Metrics** - Beyond basic success/failure:
   - Duration percentiles (p50, p95, p99)
   - Data point counts
   - Error categorization

## Consequences

### Positive

1. **Easier Adoption** - No code changes needed for configuration
2. **Multiple Instances** - Can run Arsenal + Man United sources
3. **Better Reliability** - Timeouts and circuit breakers prevent cascading failures
4. **Smooth Migration** - Existing setups continue working
5. **Community Friendly** - Clear plugin examples enable contributions
6. **Observable** - OpenTelemetry provides professional-grade debugging

### Negative

1. **Complexity Increase** - More moving parts than simple CLI args
2. **Learning Curve** - Users need to understand YAML config
3. **Migration Effort** - Users must eventually migrate to `sources.yaml`
4. **Testing Overhead** - More components to test

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing setups | High | Maintain backward compatibility, provide migration tool |
| Config errors hard to debug | Medium | Pydantic validation with clear error messages, `--validate` command |
| AsyncIO complexity | Medium | Keep simple, add tests, document patterns |
| Plugin quality varies | Low | Provide clear examples, testing guidelines |

## Deferred Decisions (Future Roadmap)

These are explicitly **not** included in Phases 1-3, but documented for future consideration:

### Deferred to Phase 4+ (or when requested)

1. **Source Dependencies (DAG)** - `depends_on: [other_source]`
   - **Rationale:** No clear use case yet. Most sources are independent.
   - **When to add:** If users request it for data aggregation workflows

2. **Multi-Output Sources** - `fetch_data() -> list[SignageContent]`
   - **Rationale:** Can be achieved with multiple source configs
   - **When to add:** If it becomes common pattern

3. **Data Sharing/Deduplication** - Shared cache between sources
   - **Rationale:** Premature optimization. API calls are cheap.
   - **When to add:** If rate limits become an issue

4. **Dynamic Scheduling** - Time-of-day conditions, adaptive intervals
   - **Rationale:** Static cron covers most needs
   - **When to add:** If users request sophisticated scheduling

5. **Config-Driven Conditional Rendering** - Declarative render rules
   - **Rationale:** Code-based is more flexible for now
   - **When to add:** If common patterns emerge

6. **Lifecycle Hooks** - `on_startup()`, `on_shutdown()`
   - **Rationale:** YAGNI - no clear use case
   - **When to add:** If plugins need initialization/cleanup

7. **Resource Limits** - Per-source memory/CPU limits
   - **Rationale:** Not a problem at current scale
   - **When to add:** If runaway sources cause issues

8. **Plugin Sandboxing** - Restricted execution environment
   - **Rationale:** Trust model is "vetted plugins only"
   - **When to add:** If opening to untrusted community plugins

9. **Hot Config Reload** - Update config without restart
   - **Rationale:** Restart is acceptable for single-user deployment
   - **When to add:** If running as long-lived service

10. **Multi-Instance Coordination** - Distributed locking
    - **Rationale:** Assume single instance (document limitation)
    - **When to add:** If users run multiple instances

11. **Secrets Manager Integration** - AWS Secrets, Vault
    - **Rationale:** `.env` file is sufficient for self-hosted
    - **When to add:** If deploying to cloud with managed secrets

12. **SLO/Error Budget Tracking** - Formal reliability targets
    - **Rationale:** Health metrics are sufficient for now
    - **When to add:** If running as critical service

## Implementation Plan

### Phase 1: MVP (Target: Week 2)
- [ ] Create `src/plugins/` directory structure
- [ ] Implement `BaseSource` abstract class
- [ ] Implement `SourceRegistry` with decorator
- [ ] Create Pydantic config schemas
- [ ] Implement `ConfigLoader` with validation
- [ ] Migrate weather source as example plugin
- [ ] Migrate tesla source as example plugin
- [ ] Add backward compatibility check
- [ ] Create migration tool (`--migrate`)
- [ ] Write unit tests for base classes
- [ ] Document plugin development

### Phase 2: Production Ready (Target: Week 4)
- [ ] Add timeout decorator
- [ ] Implement circuit breaker logic
- [ ] Add retry with exponential backoff
- [ ] Implement cached fallback
- [ ] Convert to async/await execution
- [ ] Add parallel source execution
- [ ] Persist metrics to JSON file
- [ ] Enhanced config validation (cron, IDs)
- [ ] Integration tests for full pipeline
- [ ] Update Docker configuration

### Phase 3: Observability (Target: Week 5)
- [ ] Add OpenTelemetry SDK dependency
- [ ] Implement tracing setup
- [ ] Add spans to source execution
- [ ] Add spans to client calls
- [ ] Console exporter (default)
- [ ] Jaeger exporter (optional)
- [ ] Configuration for tracing
- [ ] Documentation and examples

## Alternative Approaches Considered

### 1. Keep CLI-only (No YAML)
**Rejected because:** Doesn't solve multiple instances problem, requires code changes for new sources

### 2. JSON Configuration
**Rejected because:** YAML is more human-friendly, better for comments and multi-line strings

### 3. Python-based Config (e.g., `sources.py`)
**Rejected because:** Requires Python knowledge, harder to validate, security concerns

### 4. Database-backed Configuration
**Rejected because:** Overkill for single-user deployment, adds dependency

### 5. Immediate AsyncIO (Phase 1)
**Rejected because:** Adds complexity early. Synchronous execution is simpler to test and debug. Add async in Phase 2 when reliability features require it.

### 6. Third-party Plugin Framework (pluggy, stevedore)
**Rejected because:** Simple decorator registry is sufficient, avoids external dependency

## References

- ROADMAP.md - Project roadmap
- Issue #XX - Plugin system discussion (TBD)
- Docker deployment (PR #21) - Infrastructure foundation
- Existing source implementations: `src/clients/`

## Notes

This ADR represents a significant architectural shift. We're explicitly choosing **incremental adoption** over **big bang migration** to reduce risk and maintain stability for existing users.

The phased approach allows us to:
1. Validate the plugin architecture early (Phase 1)
2. Add reliability incrementally (Phase 2)
3. Enhance observability for power users (Phase 3)
4. Defer complexity we might not need

**Key Principle:** Ship working software, iterate based on actual usage patterns.
