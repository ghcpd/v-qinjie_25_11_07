#!/usr/bin/env python3
"""
Automatic test execution script that detects the environment and runs appropriate tests.
Supports Windows, Linux, macOS, and Docker environments.
"""

import os
import sys
import platform
import subprocess
import logging
from pathlib import Path

class EnvironmentDetector:
    def __init__(self):
        self.system = platform.system().lower()
        self.logs_dir = Path("logs")
        self.log_file = self.logs_dir / "test_run.log"
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        self.logs_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def detect_environment(self):
        """Detect the current environment type"""
        # Check if running in Docker
        if self.is_docker():
            return "docker"
        
        # Check operating system
        if self.system == "windows":
            return "windows"
        elif self.system in ["linux", "darwin"]:
            return "unix"
        else:
            return "unknown"
    
    def is_docker(self):
        """Check if running inside Docker container"""
        docker_indicators = [
            Path("/.dockerenv").exists(),
            Path("/proc/1/cgroup").exists() and 
            any("docker" in line for line in open("/proc/1/cgroup", "r").readlines() if Path("/proc/1/cgroup").exists()),
            os.environ.get("DOCKER_CONTAINER") == "true"
        ]
        return any(docker_indicators)
    
    def check_dependencies(self):
        """Check if required dependencies are available"""
        self.logger.info("Checking dependencies...")
        
        # Check Python
        try:
            python_version = sys.version.split()[0]
            self.logger.info(f"Python version: {python_version}")
        except Exception as e:
            self.logger.error(f"Python check failed: {e}")
            return False
        
        # Check required files
        required_files = [
            "input.py",
            "input_secure.py", 
            "test_security.py",
            "requirements.txt"
        ]
        
        missing_files = []
        for file in required_files:
            if not Path(file).exists():
                missing_files.append(file)
        
        if missing_files:
            self.logger.error(f"Missing required files: {missing_files}")
            return False
        
        self.logger.info("All dependencies found")
        return True
    
    def setup_environment(self, env_type):
        """Setup environment based on detected type"""
        self.logger.info(f"Setting up {env_type} environment...")
        
        if env_type == "windows":
            return self.setup_windows()
        elif env_type == "unix":
            return self.setup_unix()
        elif env_type == "docker":
            return self.setup_docker()
        else:
            self.logger.error(f"Unsupported environment: {env_type}")
            return False
    
    def setup_windows(self):
        """Setup Windows environment"""
        try:
            # Check if virtual environment exists
            venv_path = Path(".venv")
            if not venv_path.exists():
                self.logger.info("Creating virtual environment...")
                subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
            
            # Install requirements
            pip_path = venv_path / "Scripts" / "pip.exe"
            if pip_path.exists():
                self.logger.info("Installing requirements...")
                subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], check=True)
            
            return True
        except Exception as e:
            self.logger.error(f"Windows setup failed: {e}")
            return False
    
    def setup_unix(self):
        """Setup Unix (Linux/macOS) environment"""
        try:
            # Run setup script if available
            setup_script = Path("setup.sh")
            if setup_script.exists():
                self.logger.info("Running setup.sh...")
                subprocess.run(["bash", "setup.sh"], check=True)
            else:
                # Manual setup
                venv_path = Path("venv")
                if not venv_path.exists():
                    self.logger.info("Creating virtual environment...")
                    subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
                
                # Install requirements
                pip_path = venv_path / "bin" / "pip"
                if pip_path.exists():
                    self.logger.info("Installing requirements...")
                    subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], check=True)
            
            return True
        except Exception as e:
            self.logger.error(f"Unix setup failed: {e}")
            return False
    
    def setup_docker(self):
        """Setup Docker environment"""
        try:
            # In Docker, dependencies should already be installed
            self.logger.info("Docker environment detected - using pre-installed dependencies")
            
            # Verify pip packages are available
            try:
                import flask
                import requests
                self.logger.info("Required packages verified")
            except ImportError as e:
                self.logger.error(f"Required package missing: {e}")
                return False
            
            return True
        except Exception as e:
            self.logger.error(f"Docker setup failed: {e}")
            return False
    
    def run_tests(self, env_type):
        """Run tests based on environment type"""
        self.logger.info(f"Running tests for {env_type} environment...")
        
        try:
            if env_type == "windows":
                return self.run_windows_tests()
            elif env_type in ["unix", "docker"]:
                return self.run_unix_tests()
            else:
                self.logger.error(f"No test runner for environment: {env_type}")
                return False
        except Exception as e:
            self.logger.error(f"Test execution failed: {e}")
            return False
    
    def run_windows_tests(self):
        """Run tests on Windows"""
        test_script = Path("run_test.bat")
        if test_script.exists():
            self.logger.info("Running run_test.bat...")
            result = subprocess.run(["run_test.bat"], shell=True, capture_output=True, text=True)
            
            # Log output
            if result.stdout:
                self.logger.info(f"Test output:\n{result.stdout}")
            if result.stderr:
                self.logger.error(f"Test errors:\n{result.stderr}")
            
            return result.returncode == 0
        else:
            self.logger.error("run_test.bat not found")
            return False
    
    def run_unix_tests(self):
        """Run tests on Unix systems"""
        test_script = Path("run_test.sh")
        if test_script.exists():
            # Make script executable
            os.chmod(test_script, 0o755)
            
            self.logger.info("Running run_test.sh...")
            result = subprocess.run(["bash", "run_test.sh"], capture_output=True, text=True)
            
            # Log output
            if result.stdout:
                self.logger.info(f"Test output:\n{result.stdout}")
            if result.stderr:
                self.logger.error(f"Test errors:\n{result.stderr}")
            
            return result.returncode == 0
        else:
            self.logger.error("run_test.sh not found")
            return False
    
    def generate_report(self, success, env_type):
        """Generate final test report"""
        report = {
            "timestamp": logging.Formatter().formatTime(logging.LogRecord("", 0, "", 0, "", (), None)),
            "environment": env_type,
            "system": self.system,
            "python_version": sys.version,
            "success": success,
            "log_file": str(self.log_file)
        }
        
        self.logger.info("=== Test Execution Report ===")
        self.logger.info(f"Environment: {env_type}")
        self.logger.info(f"System: {self.system}")
        self.logger.info(f"Python: {sys.version.split()[0]}")
        self.logger.info(f"Success: {success}")
        self.logger.info(f"Log file: {self.log_file}")
        
        return report

def main():
    """Main execution function"""
    detector = EnvironmentDetector()
    
    try:
        detector.logger.info("=== Automatic Test Execution Started ===")
        
        # Detect environment
        env_type = detector.detect_environment()
        detector.logger.info(f"Detected environment: {env_type}")
        
        # Check dependencies
        if not detector.check_dependencies():
            detector.logger.error("Dependency check failed")
            sys.exit(1)
        
        # Setup environment
        if not detector.setup_environment(env_type):
            detector.logger.error("Environment setup failed")
            sys.exit(1)
        
        # Run tests
        success = detector.run_tests(env_type)
        
        # Generate report
        report = detector.generate_report(success, env_type)
        
        if success:
            detector.logger.info("=== All tests completed successfully ===")
            sys.exit(0)
        else:
            detector.logger.error("=== Tests failed ===")
            sys.exit(1)
            
    except KeyboardInterrupt:
        detector.logger.info("Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        detector.logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()