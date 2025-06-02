# Task Chain Generator

A robust task generation system for the MAS Protocol, featuring concurrent task generation, atomic file operations, and comprehensive monitoring.

## Features

- Interactive and batch task generation
- Atomic file operations with proper locking
- Concurrent task processing
- Resource monitoring and limits
- Performance metrics collection
- Comprehensive test suite
- MAS Protocol v2.1 compliant

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Interactive Mode

```bash
python generate_task_chain.py
```

### Batch Mode

```bash
python generate_task_chain.py --batch config.json
```

Example config.json:
```json
{
    "phase_id": "P7TEST",
    "task_count": 50,
    "descriptions": [
        "Review code changes",
        "Validate architecture"
    ],
    "priority_levels": ["high", "medium"],
    "sections": [
        ["1.1", "1.2"],
        ["2.1", "3.1"]
    ]
}
```

## Performance Monitoring

Run benchmarks:
```bash
python benchmark_task_chain.py
```

View metrics:
```bash
python -c "from task_metrics import MetricsCollector; print(MetricsCollector().get_summary())"
```

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

## Production Deployment

1. Set appropriate resource limits in `generate_task_chain.py`:
   ```python
   with resource_limit(memory_mb=4000, timeout_sec=120):
       # Your task generation code
   ```

2. Configure logging:
   - Set log rotation
   - Configure appropriate log levels
   - Set up monitoring alerts

3. Monitor metrics:
   - Track success rate
   - Monitor memory usage
   - Watch for concurrent write issues
   - Set up alerting for error thresholds

## Best Practices

1. Always use batch mode for large task sets
2. Monitor memory usage for large generations
3. Keep task descriptions concise
4. Regularly check metrics for performance issues
5. Set up automated testing in CI/CD pipeline

## Error Handling

The system handles various error conditions:
- File corruption
- Resource limits
- Concurrent access issues
- Invalid input data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## License

MIT License 