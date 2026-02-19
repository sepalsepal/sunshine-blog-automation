# config/version.py
# 🔒 PD 승인 없이 수정 금지

SYSTEM_VERSION = "v2.2"
SPEC_VERSION = "v1.1"

def get_version_info() -> dict:
    return {
        "system_version": SYSTEM_VERSION,
        "spec_version": SPEC_VERSION,
        "combined": f"SYS:{SYSTEM_VERSION}/SPEC:{SPEC_VERSION}"
    }
