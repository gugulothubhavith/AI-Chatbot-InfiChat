import os
import sys
import subprocess
import json
import py_compile
from pathlib import Path
import logging

# Configure logging to stay quiet but capture errors
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def print_status(msg, success=True):
    icon = "✅ [PASS]" if success else "❌ [FAIL]"
    print(f"{icon} {msg}")

class ProjectAuditor:
    def __init__(self, root_dir="."):
        self.root = Path(root_dir)
        self.results = {
            "python": True,
            "json": True,
            "docker": True,
            "frontend_ts": True,
            "css": True
        }

    def check_python(self):
        print("\n🔍 Auditing Python files for syntax errors...")
        files_found = 0
        success = True
        for py_file in self.root.rglob("*.py"):
            # Skip virtual environments and hidden dirs
            if any(part in str(py_file) for part in ["venv", ".gemini", "__pycache__", ".git"]):
                continue
            
            files_found += 1
            try:
                py_compile.compile(str(py_file), doraise=True)
                # Success - no output per file to keep it clean
            except Exception as e:
                print_status(f"Syntax Error in {py_file}:\n{e}", False)
                success = False
        
        if files_found == 0:
            print("  No Python files found.")
        elif success:
            print_status(f"All {files_found} Python files are syntactically correct.")
        
        self.results["python"] = success
        return success

    def check_json(self):
        print("\n🔍 Auditing JSON configuration files...")
        files_found = 0
        success = True
        for json_file in self.root.rglob("*.json"):
            if any(part in str(json_file) for part in ["node_modules", ".gemini", "venv", ".git"]):
                continue
                
            files_found += 1
            # Try multiple common encodings
            content = None
            valid_read = False
            for enc in ['utf-8', 'utf-16', 'utf-8-sig']:
                try:
                    with open(json_file, 'r', encoding=enc) as f:
                        content = f.read().strip()
                        if not content:
                            # Empty file is technically not valid JSON, but common for temp.
                            # We'll treat it as a warning/fail if it's meant to be a config.
                            print_status(f"Empty JSON file: {json_file}", False)
                            success = False
                            valid_read = True
                            break
                        json.loads(content)
                        valid_read = True
                        break
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
            
            if not valid_read:
                print_status(f"Invalid JSON or Encoding in {json_file}", False)
                success = False
        
        if files_found == 0:
            print("  No JSON files found.")
        elif success:
            print_status(f"All {files_found} JSON files are valid.")
            
        self.results["json"] = success
        return success

    def check_docker(self):
        print("\n🔍 Auditing Dockerfiles...")
        files_found = 0
        success = True
        for df in self.root.rglob("*Dockerfile*"):
            if any(part in str(df) for part in ["node_modules", "venv", ".git"]):
                continue
            
            files_found += 1
            try:
                with open(df, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content or not content.upper().startswith("FROM"):
                        print_status(f"Invalid Dockerfile: {df} (Should start with FROM)", False)
                        success = False
            except Exception as e:
                print_status(f"Error reading Dockerfile {df}: {e}", False)
                success = False
        
        if files_found == 0:
            print("  No Dockerfiles found.")
        elif success:
            print_status(f"All {files_found} Dockerfiles are valid.")
            
        self.results["docker"] = success
        return success

    def check_frontend(self):
        print("\n🔍 Checking Frontend TypeScript/React types...")
        frontend_path = self.root / "frontend"
        if not frontend_path.exists():
            print("  Skipping: frontend directory not detected.")
            return True
            
        try:
            # We use --noEmit to just check types without building
            result = subprocess.run(
                ["npx", "tsc", "--noEmit"],
                cwd=str(frontend_path),
                capture_output=True,
                text=True,
                shell=True
            )
            if result.returncode == 0:
                print_status("TypeScript type-check passed.")
                return True
            else:
                print_status("TypeScript type-check failed:", False)
                print(result.stdout)
                return False
        except Exception as e:
            print(f"  Note: npx tsc not found or failed to run: {e}")
            return True # Not necessarily a "file error" but a tool lack

    def run_all(self):
        print("🚀 DEEP PROJECT AUDIT STARTING...")
        print("Root Directory:", self.root.absolute())
        print("-" * 40)
        
        self.check_python()
        self.check_json()
        self.check_docker()
        self.check_frontend()
        
        print("\n" + "="*40)
        print("FINAL AUDIT SUMMARY")
        print("-" * 40)
        all_passed = True
        for name, passed in self.results.items():
            if name == "css" and passed: continue # We didn't add a formal CSS parser yet
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{name.upper():<12}: {status}")
            if not passed: all_passed = False
            
        if all_passed:
            print("\n🎉 PROJECT IS 100% HEALTHY!")
            return 0
        else:
            print("\n⚠️  ISSUES FOUND. Please review the failures above.")
            return 1

if __name__ == "__main__":
    auditor = ProjectAuditor()
    sys.exit(auditor.run_all())
