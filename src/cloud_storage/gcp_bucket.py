"""
This script handles synchronization between a Google Cloud Storage (GCS) bucket and a local directory ('analysis_workspace').

It authenticates with GCS using a base64-encoded service account, then downloads all files under a specified GCS prefix if:
- The local folder is empty, or
- The remote files are newer than local copies.

This ensures the local environment has the most up-to-date data files needed for analysis or application processing.

Key functions:
- `get_gcs_fs()`: Authenticates and returns a GCS filesystem object.
- `sync_gcs_to_local()`: Downloads files from GCS to the local cache, checking timestamps to avoid redundant downloads.
"""


import base64
import json
from pathlib import Path
from src.config.appconfig import settings as app_settings
from google.oauth2 import service_account
import gcsfs
from datetime import datetime, timezone
import time



def sync_gcs_to_local(gcs_fs, gcs_bucket, gcs_prefix):
    """Ensure all files from GCS are downloaded to 'analysis_workspace'"""
    local_cache = Path("./analysis_workspace")
    gcs_path = f"{gcs_bucket}/{gcs_prefix}".rstrip("/")

    # Ensure the local directory exists
    local_cache.mkdir(parents=True, exist_ok=True)

    try:
        gcs_files = gcs_fs.ls(gcs_path)
        print(f"\n🔍 Found {len(gcs_files)} files in GCS: {gcs_files}")  # Debugging

        if not gcs_files:
            raise FileNotFoundError(f"GCS path '{gcs_path}' is empty")

    except Exception as e:
        raise FileNotFoundError(f"Error accessing GCS path '{gcs_path}': {e}")

    print(f"\n🔍 Found {len(gcs_files)} files in GCS:")
    for f in gcs_files:
        print(f"   - {f}")

    print("\n🔄 Checking local sync...\n")

    downloaded_files = []

    for blob_path in gcs_files:
        # Skip directories
        if blob_path.endswith("/"):
            print(f"⏩ Skipping directory: {blob_path}")
            continue  # Skip to the next file

        local_path = local_cache / Path(blob_path).name
        try:
            # Always download if the local folder is empty
            if not any(local_cache.iterdir()):
                download = True
            else:
                # Check timestamps
                blob_info = gcs_fs.info(blob_path)
                gcs_last_modified = datetime.fromisoformat(blob_info["updated"]).astimezone(timezone.utc)

                if local_path.exists():
                    local_last_modified = datetime.fromtimestamp(local_path.stat().st_mtime, tz=timezone.utc)
                    download = local_last_modified < gcs_last_modified
                else:
                    download = True

            if download:
                # Delete the existing file before writing new content
                if local_path.exists():
                    local_path.unlink()

                with gcs_fs.open(blob_path, "rb") as remote_file:
                    content = remote_file.read()
                    local_path.write_bytes(content)
                    downloaded_files.append(local_path)
                    print(f"✅ Downloaded: {local_path} ({len(content)} bytes)")
                    time.sleep(1)  # Reduce throttling

            else:
                print(f"⏩ Skipping (up-to-date): {blob_path}")

        except Exception as e:
            print(f"❌ Error downloading {blob_path}: {e}")

    # Print local folder content
    local_files = list(local_cache.glob("*"))
    print(f"\n📂 Local 'analysis_workspace' now contains {len(local_files)} files:")
    for f in local_files:
        print(f"   - {f.name}")

    if len(downloaded_files) == len(gcs_files) - 1:  # Subtract 1 because we skip the directory
        print("\n✅ All files downloaded successfully.\n")
    else:
        print("\n⚠️ Some files are missing! Check logs.\n")

    return local_cache


# Authenticate with GCS
def get_gcs_fs():
    """Ensure GCS authentication is working"""
    try:
        service_account_b64 = app_settings.service_account_b64
        service_account_info = json.loads(base64.b64decode(service_account_b64).decode())

        # Create credentials
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=[
                "https://www.googleapis.com/auth/devstorage.full_control",
                "https://www.googleapis.com/auth/cloud-platform"
            ]
        )

        gcs_fs = gcsfs.GCSFileSystem(token=credentials)
        return gcs_fs
    except Exception as e:
        print(f"GCS Authentication Failed: {str(e)}")