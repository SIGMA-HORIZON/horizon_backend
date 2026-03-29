from enum import Enum

class RoleType(str, Enum):
    USER = "user"
    ADMIN = "admin"

class VMStatus(str, Enum):
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    STOPPED = "stopped"
    EXPIRED = "expired"
    DELETED = "deleted"

class NodeStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"

class OSType(str, Enum):
    LINUX = "linux"
    WINDOWS = "windows"

class SSHAlgorithm(str, Enum):
    ED25519 = "ed25519"
    RSA4096 = "rsa4096"

class ActionType(str, Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    VM_CREATE = "vm_create"
    VM_STOP = "vm_stop"
    VM_DELETE = "vm_delete"
    VM_MODIFY = "vm_modify"
    VM_EXTEND = "vm_extend"
    SSH_CONNECT = "ssh_connect"
    ADMIN_ACCOUNT_CREATE = "admin_account_create"
    ADMIN_ACCOUNT_MODIFY = "admin_account_modify"
    ADMIN_ACCOUNT_SUSPEND = "admin_account_suspend"
    ADMIN_VM_FORCE_STOP = "admin_vm_force_stop"
    ADMIN_POLICY_MODIFY = "admin_policy_modify"
    POLICY_VIOLATION = "policy_violation"

class NotifType(str, Enum):
    EXPIRY_WARNING = "expiry_warning"
    VM_STOPPED = "vm_stopped"
    VM_DELETED = "vm_deleted"
    ACCOUNT_SUSPENDED = "account_suspended"
