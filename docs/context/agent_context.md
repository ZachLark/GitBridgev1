# GitBridgev1 Project Context for AI Agents

## Project Overview
GitBridgev1 is a sophisticated bridge between GitHub and Multi-Agent Systems (MAS), implementing the MAS Lite Protocol v2.1. The project facilitates agent collaboration, task management, and consensus-based decision making in software development workflows.

## Core Components
1. **Webhook System**
   - Event processing pipeline
   - Rate limiting and security
   - Task generation from events

2. **Queue Management**
   - Redis-backed event queue
   - Failover mechanisms
   - Performance monitoring

3. **Task Chain**
   - State management
   - Consensus tracking
   - Agent assignment

4. **AI Router**
   - Agent registration
   - Task distribution
   - Performance optimization

## Development Phases
The project follows GitBridge Phases (GBP):
- GBP11-12: Core infrastructure
- GBP13-14: Queue and task management
- GBP15: AI routing and optimization
- GBP16+: Advanced features (planned)

## Technical Stack
- **Language**: Python 3.13.3
- **Key Libraries**: 
  - `hashlib` for SHA256
  - `requests` for API calls
- **Storage**: Redis
- **Protocol**: MAS Lite v2.1

## Development Guidelines
1. **Code Style**
   - Follow pylint rules
   - Max line length: 88
   - Require docstrings
   - Include MAS Lite Protocol references

2. **Testing**
   - Comprehensive test coverage
   - Integration tests for workflows
   - Performance benchmarks

3. **Documentation**
   - Clear component documentation
   - Phase transition markers
   - Implementation status tracking

## Current Status
- Active development in GBP13-15
- Focus on queue system and routing
- Test coverage expansion
- Performance optimization

## Tools Available
1. **Code Analysis**
   - Snapshot generator (v2.1.0)
   - Test coverage reports
   - Performance metrics

2. **Development**
   - Webhook testing suite
   - Queue monitoring
   - Task chain debugger

## Key Files and Directories
- `/scripts/`: Core automation
- `/tests/`: Test suites
- `/docs/`: Documentation
- `/mas_core/`: Core MAS implementation
- `/integrations/`: External integrations

## Best Practices for AI Assistance
1. **Code Changes**
   - Always include necessary imports
   - Add comprehensive docstrings
   - Follow existing patterns
   - Update tests accordingly

2. **Documentation**
   - Mark phase transitions
   - Update relevant docs
   - Include rationale
   - Cross-reference components

3. **Testing**
   - Add test cases
   - Cover edge cases
   - Include performance tests
   - Document test scenarios

4. **Review Process**
   - Check phase compliance
   - Verify test coverage
   - Validate documentation
   - Assess performance impact

## Getting Started
1. Review current phase status:
   ```bash
   python3 scripts/gitbridge_audit_snapshot.py
   ```

2. Check test coverage:
   ```bash
   pytest tests/ --cov
   ```

3. Run development server:
   ```bash
   python3 app.py
   ```

## Communication Protocol
- Use phase markers for transitions
- Reference ticket numbers
- Include implementation status
- Document breaking changes

## Need Help?
- Check `docs/` directory
- Run snapshot tool
- Review test cases
- Examine phase markers 