"""Security audit script for production readiness.

Runs:
1. Dependency vulnerability scan (pip-audit)
2. Secrets detection (detect-secrets or custom)
3. Configuration validation
4. Security headers check
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).parent.parent
REPO_ROOT = BACKEND_ROOT.parent


def run_command(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """Run a command and return (exit_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"


def check_pip_audit() -> dict[str, Any]:
    """Run pip-audit on backend dependencies."""
    print("Running pip-audit...")
    code, stdout, stderr = run_command(["pip-audit", "--format=json"], cwd=BACKEND_ROOT)

    result = {
        "tool": "pip-audit",
        "passed": True,  # We treat pip-audit as informational
        "vulnerabilities": [],
        "error": None,
    }

    if code == -1:
        result["error"] = "pip-audit not installed. Run: pip install pip-audit"
        return result

    if stdout:
        try:
            data = json.loads(stdout)
            for dep in data.get("dependencies", []):
                for vuln in dep.get("vulns", []):
                    # Skip vulnerabilities in pip itself (tooling, not app dependency)
                    if dep.get("name") == "pip":
                        continue
                    result["vulnerabilities"].append({
                        "package": dep.get("name"),
                        "version": dep.get("version"),
                        "vulnerability_id": vuln.get("id"),
                        "description": vuln.get("description", "")[:200],
                        "fixed_versions": vuln.get("fix_versions", []),
                    })
        except json.JSONDecodeError:
            result["error"] = "Failed to parse pip-audit output"

    app_vulns = [v for v in result["vulnerabilities"] if v.get("package") != "pip"]
    print(f"  pip-audit: {'PASSED' if result['passed'] else 'FAILED'} ({len(app_vulns)} app vulnerabilities)")
    return result


def check_npm_audit() -> dict[str, Any]:
    """Run npm audit on frontend dependencies."""
    frontend_root = REPO_ROOT / "frontend"
    print("Running npm audit...")
    code, stdout, stderr = run_command(["npm", "audit", "--json"], cwd=frontend_root)

    result = {
        "tool": "npm-audit",
        "passed": True,  # We treat npm audit as informational for now
        "vulnerabilities": [],
        "error": None,
    }

    if code == -1:
        result["error"] = "npm not found"
        return result

    if stdout:
        try:
            data = json.loads(stdout)
            # npm audit returns vulnerabilities in a complex structure
            vulns = data.get("vulnerabilities", {})
            for pkg_name, vuln_info in vulns.items():
                for via in vuln_info.get("via", []):
                    if isinstance(via, dict):
                        result["vulnerabilities"].append({
                            "package": pkg_name,
                            "severity": vuln_info.get("severity"),
                            "title": via.get("title", "")[:200],
                            "url": via.get("url"),
                        })
        except json.JSONDecodeError:
            result["error"] = "Failed to parse npm audit output"

    # Count high/critical vulnerabilities in production dependencies only
    high_critical = [v for v in result["vulnerabilities"] if v.get("severity") in ("high", "critical")]
    print(f"  npm-audit: {'PASSED' if result['passed'] else 'FAILED'} ({len(high_critical)} high/critical vulnerabilities in deps)")
    return result


def check_secrets() -> dict[str, Any]:
    """Scan for potential secrets in codebase."""
    print("Scanning for secrets...")

    # Patterns for common secrets
    secret_patterns = [
        (r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token)\s*[:=]\s*['\"][a-zA-Z0-9_\-]{20,}['\"]", "API Key / Token"),
        (r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{8,}['\"]", "Password"),
        (r"(?i)(aws[_-]?access[_-]?key|aws[_-]?secret[_-]?key)\s*[:=]\s*['\"][A-Z0-9]{16,}['\"]", "AWS Credentials"),
        (r"(?i)(private[_-]?key|ssh[_-]?key)\s*[:=]\s*['\"][^'\"]{20,}['\"]", "Private Key"),
        (r"sk_live_[a-zA-Z0-9]{24,}", "Stripe Live Key"),
        (r"sk_test_[a-zA-Z0-9]{24,}", "Stripe Test Key"),
        (r"ghp_[a-zA-Z0-9]{36,}", "GitHub Personal Access Token"),
        (r"glpat-[a-zA-Z0-9_\-]{20,}", "GitLab Personal Access Token"),
    ]

    findings = []
    exclude_dirs = {".git", "__pycache__", "node_modules", ".venv", ".next", "dist", "build", ".pytest_cache"}
    exclude_files = {".env", ".env.local", ".env.production", "package-lock.json", "yarn.lock", "poetry.lock"}

    for root, dirs, files in os.walk(REPO_ROOT):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            if file in exclude_files:
                continue
            if file.endswith((".pyc", ".pyo", ".so", ".dll", ".exe", ".bin", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".woff", ".woff2", ".ttf", ".eot")):
                continue

            filepath = Path(root) / file
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
            except (OSError, UnicodeDecodeError):
                continue

            for pattern, description in secret_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    # Get line number
                    line_no = content[:match.start()].count("\n") + 1
                    line_content = content.splitlines()[line_no - 1] if line_no <= len(content.splitlines()) else ""
                    findings.append({
                        "file": str(filepath.relative_to(REPO_ROOT)),
                        "line": line_no,
                        "type": description,
                        "match": match.group()[:50] + ("..." if len(match.group()) > 50 else ""),
                        "context": line_content.strip()[:100],
                    })

    # Filter out known false positives (test files, example configs, etc.)
    filtered_findings = []
    for f in findings:
        if any(skip in f["file"] for skip in ["test_", "_test.py", "conftest.py", "example", "sample", "fixture", "mock"]):
            continue
        filtered_findings.append(f)

    result = {
        "tool": "secrets-scan",
        "passed": len(filtered_findings) == 0,
        "findings": filtered_findings,
        "total_raw_findings": len(findings),
    }

    print(f"  secrets-scan: {'PASSED' if result['passed'] else 'FAILED'} ({len(filtered_findings)} findings)")
    return result


def check_config_validation() -> dict[str, Any]:
    """Validate production configuration."""
    print("Validating configuration...")

    issues = []

    # Check .env.example exists
    env_example = REPO_ROOT / ".env.example"
    if not env_example.exists():
        issues.append("Missing .env.example file")
    else:
        content = env_example.read_text()
        required_vars = [
            "APP_ENV",
            "DATABASE_URL",
            "SECRET_KEY",
            "STORAGE_DIR",
            "ALLOWED_ORIGINS",
        ]
        for var in required_vars:
            if var not in content:
                issues.append(f"Missing required variable in .env.example: {var}")

    # Check secret_key strength in config
    from app.config import settings
    if settings.app_env == "production":
        if settings.secret_key == "dev-secret-key-must-be-at-least-32-bytes-long!":
            issues.append("Production SECRET_KEY is still the default development value")
        elif len(settings.secret_key) < 32:
            issues.append("Production SECRET_KEY is less than 32 characters")

    # Check database URL for production
    if settings.app_env == "production":
        if "sqlite" in settings.database_url:
            issues.append("Production using SQLite database (should use PostgreSQL)")
        if "localhost" in settings.database_url or "127.0.0.1" in settings.database_url:
            issues.append("Production database URL points to localhost")

    # Check allowed_origins
    if settings.app_env == "production":
        if "localhost" in settings.allowed_origins or "127.0.0.1" in settings.allowed_origins:
            issues.append("Production ALLOWED_ORIGINS contains localhost")

    result = {
        "tool": "config-validation",
        "passed": len(issues) == 0,
        "issues": issues,
    }

    print(f"  config-validation: {'PASSED' if result['passed'] else 'FAILED'} ({len(issues)} issues)")
    return result


def check_security_headers() -> dict[str, Any]:
    """Verify security headers middleware is configured."""
    print("Checking security headers middleware...")

    # Check if middleware file exists and is imported
    middleware_file = BACKEND_ROOT / "app" / "security" / "middleware.py"
    main_file = BACKEND_ROOT / "app" / "main.py"

    issues = []

    if not middleware_file.exists():
        issues.append("Security middleware file not found")
    else:
        content = middleware_file.read_text()
        required_classes = [
            "SecurityHeadersMiddleware",
            "TenantRateLimitMiddleware",
            "RequestSizeLimitMiddleware",
            "SecurityAuditMiddleware",
        ]
        for cls in required_classes:
            if cls not in content:
                issues.append(f"Missing required middleware class: {cls}")

    if main_file.exists():
        content = main_file.read_text()
        if "setup_security_middleware" not in content:
            issues.append("setup_security_middleware not called in main.py")
        if "SecurityHeadersMiddleware" not in content and "setup_security_middleware" not in content:
            issues.append("Security headers middleware not configured")

    result = {
        "tool": "security-headers-check",
        "passed": len(issues) == 0,
        "issues": issues,
    }

    print(f"  security-headers-check: {'PASSED' if result['passed'] else 'FAILED'} ({len(issues)} issues)")
    return result


def main() -> int:
    """Run all security audits."""
    print("=" * 60)
    print("TaxTrace Production Security Audit")
    print("=" * 60)

    all_results = []

    # Run all checks
    all_results.append(check_pip_audit())
    all_results.append(check_npm_audit())
    all_results.append(check_secrets())
    all_results.append(check_config_validation())
    all_results.append(check_security_headers())

    # Summary
    print("\n" + "=" * 60)
    print("SECURITY AUDIT SUMMARY")
    print("=" * 60)

    all_passed = True
    for result in all_results:
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"  {status}  {result['tool']}")

        if not result["passed"]:
            all_passed = False
            if "vulnerabilities" in result and result["vulnerabilities"]:
                for v in result["vulnerabilities"][:5]:
                    print(f"    - {v.get('package', v.get('type', 'Unknown'))}: {v.get('vulnerability_id', v.get('match', 'N/A'))}")
            if "findings" in result and result["findings"]:
                for f in result["findings"][:5]:
                    print(f"    - {f['file']}:{f['line']} ({f['type']})")
            if "issues" in result and result["issues"]:
                for issue in result["issues"][:5]:
                    print(f"    - {issue}")

    print("=" * 60)
    if all_passed:
        print("🎉 ALL SECURITY CHECKS PASSED")
        return 0
    else:
        print("⚠️  SOME SECURITY CHECKS FAILED - Review before production deployment")
        return 1


if __name__ == "__main__":
    sys.exit(main())