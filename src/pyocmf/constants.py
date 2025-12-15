"""Constants used throughout the pyocmf library."""

# OCMF format constants
OCMF_HEADER = "OCMF"
"""The header identifier for OCMF strings."""

OCMF_SEPARATOR = "|"
"""The separator between OCMF sections (header, payload, signature)."""

OCMF_PREFIX = f"{OCMF_HEADER}{OCMF_SEPARATOR}"
"""The prefix that all OCMF strings start with ('OCMF|')."""
