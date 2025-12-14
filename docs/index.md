# PyOCMF

Python library for parsing and validating OCMF (Open Charge Metering Format).

## Installation

```bash
pip install pyocmf
```

## Quick Example

```python
from pyocmf import OCMF

ocmf = OCMF.from_string("OCMF|{...}|{...}")
print(ocmf.payload.RD)  # Access readings
```

## Documentation

See the [API Reference](api.md) for detailed documentation.
