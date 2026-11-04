"""
Multi-Tenant Architecture and Role-Based Access Control (RBAC) Module (FÁZE 12)
Provides:
 - Secure Password Hashing (PBKDF2-HMAC-SHA256 with random salt)
 - Cryptographic JWT (JSON Web Tokens) creation and verification
 - RBAC Permission Matrix:
     * ADMIN: Full system access, tenant management, user management
     * ENGINEER: Create, edit, simulate, and export projects
     * AUDITOR: Review projects, IPMVP verification, generate compliance reports
     * INVESTOR: Read-only access to financial metrics, cash flows, and executive summaries
 - Multi-Tenancy Data Isolation:
     * Each project and portfolio belongs to a specific tenant_id
     * Cross-tenant query filtering
"""

import hashlib
import hmac
import base64
import json
import time
import uuid
import sqlite3
import os
from typing import Dict, Any, List, Optional

JWT_SECRET = "auraenergy_enterprise_secret_key_2026_x89"
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "projects.db")

# Role definitions & permissions
ROLES_PERMISSIONS = {
    "ADMIN": ["users:manage", "tenants:manage", "projects:read", "projects:write", "projects:delete", "sim:run", "audit:verify"],
    "ENGINEER": ["projects:read", "projects:write", "sim:run", "audit:verify"],
    "AUDITOR": ["projects:read", "audit:verify", "reports:generate"],
    "INVESTOR": ["projects:read", "reports:view"]
}


def hash_password(password: str, salt: Optional[str] = None) -> str:
    if not salt:
        salt = uuid.uuid4().hex[:16]
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"{salt}:{key.hex()}"


def verify_password(stored_hash: str, password: str) -> bool:
    try:
        salt, expected_hex = stored_hash.split(":")
        check_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return hmac.compare_digest(check_key.hex(), expected_hex)
    except Exception:
        return False


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')


def _b64url_decode(s: str) -> bytes:
    padding = '=' * (4 - (len(s) % 4))
    return base64.urlsafe_b64decode(s + padding)


def generate_jwt(user_id: str, email: str, role: str, tenant_id: str, expires_in_seconds: int = 86400) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "tenant_id": tenant_id,
        "iat": now,
        "exp": now + expires_in_seconds,
        "jti": uuid.uuid4().hex
    }
    
    hdr_b64 = _b64url_encode(json.dumps(header).encode('utf-8'))
    pay_b64 = _b64url_encode(json.dumps(payload).encode('utf-8'))
    msg = f"{hdr_b64}.{pay_b64}".encode('utf-8')
    sig = hmac.new(JWT_SECRET.encode('utf-8'), msg, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(sig)
    
    return f"{hdr_b64}.{pay_b64}.{sig_b64}"


def verify_jwt(token: str) -> Optional[Dict[str, Any]]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        hdr_b64, pay_b64, sig_b64 = parts
        msg = f"{hdr_b64}.{pay_b64}".encode('utf-8')
        expected_sig = hmac.new(JWT_SECRET.encode('utf-8'), msg, hashlib.sha256).digest()
        actual_sig = _b64url_decode(sig_b64)
        
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        
        payload = json.loads(_b64url_decode(pay_b64).decode('utf-8'))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


def init_auth_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tenants (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                subscription_plan TEXT DEFAULT 'ENTERPRISE',
                created_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (tenant_id) REFERENCES tenants (id)
            )
        """)
        # Seed default tenant and admin if not exists
        cursor.execute("SELECT COUNT(*) FROM tenants")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO tenants VALUES ('tenant_corp_01', 'ČEZ ESCO Partner a.s.', 'ENTERPRISE_PRO', datetime('now'))")
            cursor.execute("INSERT INTO tenants VALUES ('tenant_demo', 'Demonstrační Energetická s.r.o.', 'STANDARD', datetime('now'))")
            
            pwd_admin = hash_password("admin123")
            pwd_eng = hash_password("engineer123")
            pwd_aud = hash_password("auditor123")
            pwd_inv = hash_password("investor123")
            
            cursor.execute("INSERT INTO users VALUES ('usr_admin', 'tenant_corp_01', 'admin@auraenergy.cz', 'Hlavní Administrátor', ?, 'ADMIN', datetime('now'))", (pwd_admin,))
            cursor.execute("INSERT INTO users VALUES ('usr_eng', 'tenant_corp_01', 'inzenyr@auraenergy.cz', 'Ing. Jan Dvořák (Projektant)', ?, 'ENGINEER', datetime('now'))", (pwd_eng,))
            cursor.execute("INSERT INTO users VALUES ('usr_aud', 'tenant_corp_01', 'auditor@auraenergy.cz', 'Ing. Petr Kovář (Auditor)', ?, 'AUDITOR', datetime('now'))", (pwd_aud,))
            cursor.execute("INSERT INTO users VALUES ('usr_inv', 'tenant_corp_01', 'investor@auraenergy.cz', 'Fond Čisté Energie (Investor)', ?, 'INVESTOR', datetime('now'))", (pwd_inv,))
        conn.commit()


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    init_auth_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.tenant_id, u.email, u.full_name, u.password_hash, u.role, t.name as tenant_name 
            FROM users u JOIN tenants t ON u.tenant_id = t.id 
            WHERE u.email = ?
        """, (email,))
        row = cursor.fetchone()
        if not row:
            return None
        if not verify_password(row["password_hash"], password):
            return None
        
        token = generate_jwt(row["id"], row["email"], row["role"], row["tenant_id"])
        return {
            "token": token,
            "user": {
                "id": row["id"],
                "email": row["email"],
                "full_name": row["full_name"],
                "role": row["role"],
                "tenant_id": row["tenant_id"],
                "tenant_name": row["tenant_name"],
                "permissions": ROLES_PERMISSIONS.get(row["role"], [])
            }
        }


def list_tenant_users(tenant_id: str) -> List[Dict[str, Any]]:
    init_auth_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, tenant_id, email, full_name, role, created_at FROM users WHERE tenant_id = ?", (tenant_id,))
        return [dict(r) for r in cursor.fetchall()]
