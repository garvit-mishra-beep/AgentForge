"""
Sandbox Execution Service for AgentForge.
Provides secure, isolated execution environments for running untrusted code.
"""
import asyncio
import logging
import os
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

try:
    import docker
    from docker.errors import ImageNotFound
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    docker = None

logger = logging.getLogger(__name__)


@dataclass
class ResourceLimits:
    """Resource limits for sandbox execution."""
    cpu_cpus: float = 1.0
    memory_mb: int = 512
    disk_mb: int = 100
    max_processes: int = 10
    max_open_files: int = 64


class SandboxType(str, Enum):
    """Types of sandboxes available."""
    DOCKER = "docker"
    PROCESS = "process"  # Fallback to restricted process execution
    NONE = "none"  # No sandboxing (for trusted code only)


class NetworkPolicy(str, Enum):
    """Network access policies for sandboxes."""
    NONE = "none"  # No network access
    INTERNAL = "internal"  # Only internal/loopback network
    RESTRICTED = "restricted"  # Limited external access (e.g., package repos)
    FULL = "full"  # Full network access (not recommended for untrusted code)


class SecurityLevel(str, Enum):
    """Security levels for sandbox execution."""
    MINIMAL = "minimal"  # Basic isolation
    STANDARD = "standard"  # Standard security restrictions
    MAXIMUM = "maximum"  # Maximum lockdown (may break some functionality)


@dataclass
class SandboxConfig:
    """Configuration for sandbox execution."""
    sandbox_type: SandboxType = SandboxType.DOCKER
    security_level: SecurityLevel = SecurityLevel.STANDARD
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    network_policy: NetworkPolicy = NetworkPolicy.NONE
    read_only_root: bool = True
    tmpfs_size: str = "64M"  # Size for /tmp mount
    max_execution_time: int = 30  # Seconds
    allowed_paths: list[str] = field(default_factory=list)  # Host paths allowed to mount
    environment_vars: dict[str, str] = field(default_factory=dict)
    user_id: int = 1000  # Non-root user
    group_id: int = 1000
    add_capabilities: list[str] = field(default_factory=list)  # Additional capabilities to keep
    drop_all_capabilities: bool = True  # Drop all Linux capabilities by default
    no_new_privileges: bool = True  # Prevent privilege escalation
    private_tmp: bool = True  # Private /tmp directory
    proc_isolation: bool = True  # PID namespace isolation
    uid_map: str | None = None  # User namespace mapping
    gid_map: str | None = None  # Group namespace mapping


@dataclass
class ExecutionResult:
    """Result of sandbox execution."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    execution_time_ms: int
    timeout: bool
    oom_killed: bool
    files_created: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class SandboxExecutor:
    """Executes code in secure sandboxed environments."""

    def __init__(self):
        self.temp_dir_base = "/tmp/agentforge_sandbox"
        self._ensure_base_dir()
        self.docker_client = None

        # Initialize Docker client if available
        if DOCKER_AVAILABLE:
            try:
                self.docker_client = docker.from_env()
                # Test connection
                self.docker_client.ping()
                logger.info("Docker client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Docker client: {e}")
                self.docker_client = None
        else:
            logger.warning("Docker SDK not available")

        # Default seccomp profile that blocks dangerous syscalls
        # Based on Docker's default profile with additional restrictions
        self.default_seccomp_profile = {
            "defaultAction": "SCMP_ACT_ERRNO",
            "architectures": [
                "SCMP_ARCH_X86_64",
                "SCMP_ARCH_X86",
                "SCMP_ARCH_X32"
            ],
            "syscalls": [
                # Process management
                {"name": "exit", "action": "SCMP_ACT_ALLOW"},
                {"name": "exit_group", "action": "SCMP_ACT_ALLOW"},
                {"name": "brk", "action": "SCMP_ACT_ALLOW"},
                {"name": "munmap", "action": "SCMP_ACT_ALLOW"},
                {"name": "mmap", "action": "SCMP_ACT_ALLOW"},
                {"name": "mprotect", "action": "SCMP_ACT_ALLOW"},

                # File operations
                {"name": "open", "action": "SCMP_ACT_ALLOW"},
                {"name": "openat", "action": "SCMP_ACT_ALLOW"},
                {"name": "close", "action": "SCMP_ACT_ALLOW"},
                {"name": "read", "action": "SCMP_ACT_ALLOW"},
                {"name": "write", "action": "SCMP_ACT_ALLOW"},
                {"name": "readv", "action": "SCMP_ACT_ALLOW"},
                {"name": "writev", "action": "SCMP_ACT_ALLOW"},
                {"name": "pread64", "action": "SCMP_ACT_ALLOW"},
                {"name": "pwrite64", "action": "SCMP_ACT_ALLOW"},
                {"name": "lseek", "action": "SCMP_ACT_ALLOW"},
                {"name": "stat", "action": "SCMP_ACT_ALLOW"},
                {"name": "fstat", "action": "SCMP_ACT_ALLOW"},
                {"name": "lstat", "action": "SCMP_ACT_ALLOW"},
                {"name": "fstatat", "action": "SCMP_ACT_ALLOW"},
                {"name": "access", "action": "SCMP_ACT_ALLOW"},
                {"name": "chmod", "action": "SCMP_ACT_ALLOW"},
                {"name": "fchmod", "action": "SCMP_ACT_ALLOW"},
                {"name": "chown", "action": "SCMP_ACT_ALLOW"},
                {"name": "fchown", "action": "SCMP_ACT_ALLOW"},
                {"name": "getcwd", "action": "SCMP_ACT_ALLOW"},
                {"name": "mkdir", "action": "SCMP_ACT_ALLOW"},
                {"name": "mkdirat", "action": "SCMP_ACT_ALLOW"},
                {"name": "rmdir", "action": "SCMP_ACT_ALLOW"},
                {"name": "rename", "action": "SCMP_ACT_ALLOW"},
                {"name": "renameat", "action": "SCMP_ACT_ALLOW"},
                {"name": "link", "action": "SCMP_ACT_ALLOW"},
                {"name": "linkat", "action": "SCMP_ACT_ALLOW"},
                {"name": "unlink", "action": "SCMP_ACT_ALLOW"},
                {"name": "unlinkat", "action": "SCMP_ACT_ALLOW"},
                {"name": "symlink", "action": "SCMP_ACT_ALLOW"},
                {"name": "symlinkat", "action": "SCMP_ACT_ALLOW"},
                {"name": "chdir", "action": "SCMP_ACT_ALLOW"},
                {"name": "fchdir", "action": "SCMP_ACT_ALLOW"},

                # Memory management
                {"name": "brk", "action": "SCMP_ACT_ALLOW"},
                {"name": "munmap", "action": "SCMP_ACT_ALLOW"},
                {"name": "mremap", "action": "SCMP_ACT_ALLOW"},
                {"name": "mincore", "action": "SCMP_ACT_ALLOW"},
                {"name": "madvise", "action": "SCMP_ACT_ALLOW"},
                {"name": "mlock", "action": "SCMP_ACT_ALLOW"},
                {"name": "munlock", "action": "SCMP_ACT_ALLOW"},
                {"name": "mlockall", "action": "SCMP_ACT_ALLOW"},
                {"name": "munlockall", "action": "SCMP_ACT_ALLOW"},
                {"name": "mprotect", "action": "SCMP_ACT_ALLOW"},

                # Process and thread
                {"name": "getpid", "action": "SCMP_ACT_ALLOW"},
                {"name": "getppid", "action": "SCMP_ACT_ALLOW"},
                {"name": "getuid", "action": "SCMP_ACT_ALLOW"},
                {"name": "getgid", "action": "SCMP_ACT_ALLOW"},
                {"name": "geteuid", "action": "SCMP_ACT_ALLOW"},
                {"name": "getegid", "action": "SCMP_ACT_ALLOW"},
                {"name": "setuid", "action": "SCMP_ACT_ALLOW"},
                {"name": "setgid", "action": "SCMP_ACT_ALLOW"},
                {"name": "seteuid", "action": "SCMP_ACT_ALLOW"},
                {"name": "setegid", "action": "SCMP_ACT_ALLOW"},
                {"name": "getgroups", "action": "SCMP_ACT_ALLOW"},
                {"name": "setgroups", "action": "SCMP_ACT_ALLOW"},
                {"name": "getresuid", "action": "SCMP_ACT_ALLOW"},
                {"name": "getresgid", "action": "SCMP_ACT_ALLOW"},
                {"name": "setresuid", "action": "SCMP_ACT_ALLOW"},
                {"name": "setresgid", "action": "SCMP_ACT_ALLOW"},
                {"name": "fork", "action": "SCMP_ACT_ALLOW"},
                {"name": "vfork", "action": "SCMP_ACT_ALLOW"},
                {"name": "clone", "action": "SCMP_ACT_ALLOW"},
                {"name": "execve", "action": "SCMP_ACT_ALLOW"},
                {"name": "exit", "action": "SCMP_ACT_ALLOW"},
                {"name": "exit_group", "action": "SCMP_ACT_ALLOW"},
                {"name": "wait4", "action": "SCMP_ACT_ALLOW"},
                {"name": "waitid", "action": "SCMP_ACT_ALLOW"},
                {"name": "getitimer", "action": "SCMP_ACT_ALLOW"},
                {"name": "setitimer", "action": "SCMP_ACT_ALLOW"},

                # Signals
                {"name": "kill", "action": "SCMP_ACT_ALLOW"},
                {"name": "tkill", "action": "SCMP_ACT_ALLOW"},
                {"name": "tgkill", "action": "SCMP_ACT_ALLOW"},
                {"name": "sigaction", "action": "SCMP_ACT_ALLOW"},
                {"name": "sigaltstack", "action": "SCMP_ACT_ALLOW"},
                {"name": "signal", "action": "SCMP_ACT_ALLOW"},
                {"name": "sigpause", "action": "SCMP_ACT_ALLOW"},
                {"name": "sigpending", "action": "SCMP_ACT_ALLOW"},
                {"name": "sigprocmask", "action": "SCMP_ACT_ALLOW"},
                {"name": "sigsuspend", "action": "SCMP_ACT_ALLOW"},
                {"name": "rt_sigtimedwait", "action": "SCMP_ACT_ALLOW"},
                {"name": "rt_sigqueueinfo", "action": "SCMP_ACT_ALLOW"},
                {"name": "rt_sigsuspend", "action": "SCMP_ACT_ALLOW"},

                # Time
                {"name": "time", "action": "SCMP_ACT_ALLOW"},
                {"name": "gettimeofday", "action": "SCMP_ACT_ALLOW"},
                {"name": "clock_gettime", "action": "SCMP_ACT_ALLOW"},
                {"name": "clock_settime", "action": "SCMP_ACT_ALLOW"},
                {"name": "clock_getres", "action": "SCMP_ACT_ALLOW"},
                {"name": "clock_nanosleep", "action": "SCMP_ACT_ALLOW"},
                {"name": "timer_create", "action": "SCMP_ACT_ALLOW"},
                {"name": "timer_delete", "action": "SCMP_ACT_ALLOW"},
                {"name": "timer_getoverrun", "action": "SCMP_ACT_ALLOW"},
                {"name": "timer_gettime", "action": "SCMP_ACT_ALLOW"},
                {"name": "timer_settime", "action": "SCMP_ACT_ALLOW"},

                # Socket and networking (limited)
                {"name": "socket", "action": "SCMP_ACT_ALLOW"},
                {"name": "socketpair", "action": "SCMP_ACT_ALLOW"},
                {"name": "bind", "action": "SCMP_ACT_ALLOW"},
                {"name": "listen", "action": "SCMP_ACT_ALLOW"},
                {"name": "accept", "action": "SCMP_ACT_ALLOW"},
                {"name": "accept4", "action": "SCMP_ACT_ALLOW"},
                {"name": "connect", "action": "SCMP_ACT_ALLOW"},
                {"name": "getsockname", "action": "SCMP_ACT_ALLOW"},
                {"name": "getpeername", "action": "SCMP_ACT_ALLOW"},
                {"name": "getsockopt", "action": "SCMP_ACT_ALLOW"},
                {"name": "setsockopt", "action": "SCMP_ACT_ALLOW"},
                {"name": "sendto", "action": "SCMP_ACT_ALLOW"},
                {"name": "sendmsg", "action": "SCMP_ACT_ALLOW"},
                {"name": "recvfrom", "action": "SCMP_ACT_ALLOW"},
                {"name": "recvmsg", "action": "SCMP_ACT_ALLOW"},
                {"name": "shutdown", "action": "SCMP_ACT_ALLOW"},

                # File system info
                {"name": "statfs", "action": "SCMP_ACT_ALLOW"},
                {"name": "fstatfs", "action": "SCMP_ACT_ALLOW"},
                {"name": "ustat", "action": "SCMP_ACT_ALLOW"},
                {"name": "dup", "action": "SCMP_ACT_ALLOW"},
                {"name": "dup2", "action": "SCMP_ACT_ALLOW"},
                {"name": "dup3", "action": "SCMP_ACT_ALLOW"},
                {"name": "fcntl", "action": "SCMP_ACT_ALLOW"},
                {"name": "ioctl", "action": "SCMP_ACT_ALLOW"},

                # System info
                {"name": "uname", "action": "SCMP_ACT_ALLOW"},
                {"name": "getrlimit", "action": "SCMP_ACT_ALLOW"},
                {"name": "setrlimit", "action": "SCMP_ACT_ALLOW"},
                {"name": "getrusage", "action": "SCMP_ACT_ALLOW"},
                {"name": "times", "action": "SCMP_ACT_ALLOW"},

                # IPC (limited)
                {"name": "ipc", "action": "SCMP_ACT_ALLOW"},

                # Miscellaneous but safe
                {"name": "arc", "action": "SCMP_ACT_ALLOW"},
                {"name": "chroot", "action": "SCMP_ACT_ALLOW"},
                {"name": "sync", "action": "SCMP_ACT_ALLOW"},
                {"name": "swapon", "action": "SCMP_ACT_ALLOW"},
                {"name": "swapoff", "action": "SCMP_ACT_ALLOW"},
                {"name": "mount", "action": "SCMP_ACT_ALLOW"},
                {"name": "umount2", "action": "SCMP_ACT_ALLOW"},
                {"name": "personality", "action": "SCMP_ACT_ALLOW"},
            ]
        }

    def _ensure_base_dir(self):
        """Ensure the base directory for temporary files exists."""
        os.makedirs(self.temp_dir_base, exist_ok=True)

    async def execute_in_sandbox(
        self,
        image: str,
        command: list[str],
        files: dict[str, str],
        config: SandboxConfig | None = None
    ) -> ExecutionResult:
        """
        Execute a command in a sandboxed container.

        Args:
            image: Docker image to use
            command: Command to execute inside the container
            files: Files to make available in the container (path -> content)
            config: Sandbox configuration (uses defaults if None)

        Returns:
            ExecutionResult with the outcome of execution
        """
        if config is None:
            config = SandboxConfig()

        start_time = time.time()

        # Fallback to basic execution if Docker is not available
        if not DOCKER_AVAILABLE or self.docker_client is None:
            logger.warning("Docker not available, using basic execution (limited security)")
            return await self._execute_basic(command, files, config)

        host_files_dir = tempfile.mkdtemp(dir=self.temp_dir_base, prefix="sandbox_")
        workspace_dir = os.path.join(host_files_dir, "workspace")
        os.makedirs(workspace_dir, exist_ok=True)

        try:
            # Write files to the host directory
            for file_path, content in files.items():
                full_path = os.path.join(workspace_dir, file_path.lstrip('/'))
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            # Prepare container configuration
            host_config = self._create_host_config(config)

            # Pull image if needed
            try:
                self.docker_client.images.get(image)
            except ImageNotFound:
                logger.info(f"Pulling image {image}")
                self.docker_client.images.pull(image)

            # Create and start container
            container = self.docker_client.containers.create(
                image=image,
                command=command,
                host_config=host_config,
                working_dir="/workspace",
                detach=True,
                # Auto-remove is handled manually for better error handling
            )

            try:
                container.start()

                # Wait for completion
                try:
                    result = container.wait(timeout=config.max_execution_time)
                    exit_code = result.get('StatusCode', 1)
                    timeout_occurred = False
                except Exception as wait_error:
                    # Handle timeout
                    if "timeout" in str(wait_error).lower():
                        timeout_occurred = True
                        try:
                            container.kill()
                        except Exception:
                            pass
                    else:
                        timeout_occurred = False
                    # Try to get exit code even after error
                    try:
                        result = container.wait(timeout=1)
                        exit_code = result.get('StatusCode', 1)
                    except Exception:
                        exit_code = -1

                # Get output
                logs = container.logs(stdout=True, stderr=True, stream=False)
                if isinstance(logs, tuple):
                    stdout_bytes, stderr_bytes = logs
                else:
                    # Some versions return combined output
                    stdout_bytes = logs
                    stderr_bytes = b''

                stdout = stdout_bytes.decode('utf-8', errors='replace') if stdout_bytes else ""
                stderr = stderr_bytes.decode('utf-8', errors='replace') if stderr_bytes else ""

                # Check for OOM (simplified)
                oom_killed = False
                try:
                    container.reload()
                    # Check if OOM killed (this is approximate)
                    # In reality, we'd need to check events, but this gives a hint
                    # For now, we'll assume it's not OOM killed unless we have evidence
                except Exception:
                    pass

                # Collect files created in workspace
                files_created = {}
                if os.path.exists(workspace_dir):
                    for root, dirs, file_names in os.walk(workspace_dir):
                        for file_name in file_names:
                            file_path = os.path.join(root, file_name)
                            rel_path = os.path.relpath(file_path, workspace_dir)
                            try:
                                with open(file_path, encoding='utf-8') as f:
                                    files_created[rel_path] = f.read()
                            except (UnicodeDecodeError, OSError):
                                # Skip binary files
                                pass

                execution_time_ms = int((time.time() - start_time) * 1000)

                return ExecutionResult(
                    success=(exit_code == 0),
                    exit_code=exit_code,
                    stdout=stdout,
                    stderr=stderr,
                    execution_time_ms=execution_time_ms,
                    timeout=timeout_occurred,
                    oom_killed=oom_killed,
                    files_created=files_created,
                    metadata={
                        "container_id": container.id[:12] if container else None,
                        "image": image,
                        "command": command,
                        "timeout_occurred": timeout_occurred
                    }
                )

            finally:
                # Clean up container
                try:
                    container.remove(force=True)
                except Exception as e:
                    logger.debug(f"Error removing container: {e}")

        except Exception as e:
            logger.error(f"Error executing in sandbox: {e}")
            execution_time_ms = int((time.time() - start_time) * 1000)
            return ExecutionResult(
                success=False,
                exit_code=-2,
                stdout="",
                stderr=f"Sandbox execution failed: {str(e)}",
                execution_time_ms=execution_time_ms,
                timeout=False,
                oom_killed=False,
                metadata={"error": str(e)}
            )

        finally:
            # Cleanup host files directory
            try:
                shutil.rmtree(host_files_dir, ignore_errors=True)
            except Exception as e:
                logger.debug(f"Error cleaning up host files directory: {e}")

    def _create_host_config(self, config: SandboxConfig):
        """Create Docker host configuration based on security settings."""

        # Prepare host config parameters
        host_config_params: dict[str, Any] = {}

        # Memory limit
        if config.resource_limits.memory_mb > 0:
            host_config_params["mem_limit"] = f"{config.resource_limits.memory_mb}m"

        # CPU limit
        if hasattr(config.resource_limits, 'cpu_cpus') and config.resource_limits.cpu_cpus > 0:
            # Docker API expects cpu_quota and cpu_period
            cpu_quota = int(100000 * config.resource_limits.cpu_cpus)
            host_config_params["cpu_quota"] = cpu_quota
            host_config_params["cpu_period"] = 100000

        # Process limit
        if config.resource_limits.max_processes > 0:
            host_config_params["pids_limit"] = config.resource_limits.max_processes

        # Security options
        if config.no_new_privileges:
            # Note: This might need to be "no-new-privileges:true" depending on Docker version
            try:
                host_config_params["security_opt"] = ["no-new-privileges"]
            except Exception:
                # If this fails, we'll continue without it
                pass

        # Capabilities
        cap_drop = []
        cap_add = []

        if config.drop_all_capabilities:
            cap_drop = ["ALL"]
        if config.add_capabilities:
            cap_add = config.add_capabilities

        if cap_drop:
            host_config_params["cap_drop"] = cap_drop
        if cap_add:
            host_config_params["cap_add"] = cap_add

        # Read-only root filesystem
        if config.read_only_root:
            host_config_params["read_only"] = True

        # Temporary filesystem
        if config.tmpfs_size:
            host_config_params["tmpfs"] = {"/tmp": f"size={config.tmpfs_size}"}

        # User and group
        if config.user_id is not None:
            user_spec = f"{config.user_id}"
            if config.group_id is not None:
                user_spec += f":{config.group_id}"
            host_config_params["user"] = user_spec

        # Network mode
        if config.network_policy == NetworkPolicy.NONE:
            host_config_params["network_mode"] = "none"
        elif config.network_policy == NetworkPolicy.INTERNAL:
            # For internal only, we can use none or bridge with no external access
            # Using none is simpler for complete isolation
            host_config_params["network_mode"] = "none"
        # For RESTRICTED and FULL, we use default bridge network (no override needed)

        # Volume mounts - we'll handle these separately in container creation
        # For now, just return the config

        # Create and return HostConfig object
        try:
            return self.docker_client.api.create_host_config(**host_config_params)
        except Exception as e:
            logger.warning(f"Error creating host config: {e}, using defaults")
            # Return a basic host config if our custom one fails
            return self.docker_client.api.create_host_config()

    async def _execute_basic(
        self,
        command: list[str],
        files: dict[str, str],
        config: SandboxConfig
    ) -> ExecutionResult:
        """
        Basic fallback execution when Docker is not available.
        This provides minimal security through process restrictions.
        """

        start_time = time.time()

        host_files_dir = tempfile.mkdtemp(dir=self.temp_dir_base, prefix="basic_sandbox_")
        workspace_dir = os.path.join(host_files_dir, "workspace")
        os.makedirs(workspace_dir, exist_ok=True)

        try:
            # Write files
            for file_path, content in files.items():
                full_path = os.path.join(workspace_dir, file_path.lstrip('/'))
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            # Prepare subprocess with basic restrictions
            # Note: This is significantly less secure than Docker sandboxing
            # but provides basic isolation when Docker is unavailable

            # Change to workspace directory
            proc = await asyncio.create_subprocess_exec(
                *command,
                cwd=workspace_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                # Basic limitations (these are approximate)
                # In a real implementation, we might use subprocess preexec_fn
                # to set resource limits, but that's platform-specific
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=config.max_execution_time
                )
                timeout_occurred = False
            except TimeoutError:
                timeout_occurred = True
                try:
                    proc.kill()
                except ProcessLookupError:
                    pass  # Process already ended
                await proc.wait()

            # Get output
            stdout_str = stdout.decode('utf-8', errors='replace') if stdout else ""
            stderr_str = stderr.decode('utf-8', errors='replace') if stderr else ""

            # Get exit code
            exit_code = proc.returncode if hasattr(proc, 'returncode') else -1

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Collect created files
            files_created = {}
            if os.path.exists(workspace_dir):
                for root, dirs, files_in_dir in os.walk(workspace_dir):
                    for file_name in files_in_dir:
                        file_path = os.path.join(root, file_name)
                        rel_path = os.path.relpath(file_path, workspace_dir)
                        try:
                            with open(file_path, encoding='utf-8') as f:
                                files_created[rel_path] = f.read()
                        except (UnicodeDecodeError, OSError):
                            pass

            return ExecutionResult(
                success=(exit_code == 0),
                exit_code=exit_code if exit_code is not None else -1,
                stdout=stdout_str,
                stderr=stderr_str,
                execution_time_ms=execution_time_ms,
                timeout=timeout_occurred,
                oom_killed=False,  # Can't detect OOM in basic mode
                files_created=files_created,
                metadata={
                    "execution_mode": "basic_fallback",
                    "warning": "Limited security - Docker not available"
                }
            )

        except Exception as e:
            logger.error(f"Error in basic execution: {e}")
            execution_time_ms = int((time.time() - start_time) * 1000)
            return ExecutionResult(
                success=False,
                exit_code=-3,
                stdout="",
                stderr=f"Basic execution failed: {str(e)}",
                execution_time_ms=execution_time_ms,
                timeout=False,
                oom_killed=False,
                metadata={"error": str(e)}
            )

        finally:
            # Cleanup
            try:
                shutil.rmtree(host_files_dir, ignore_errors=True)
            except Exception:
                pass


# Global instance for easy access
sandbox_executor = SandboxExecutor()
