from __future__ import annotations

def load_all_shared_hooks():
    """Auto-imports shared RPC utilities like dynamic function registration
    so they are available in all DCCs without manual imports.
    """

    from tp.libs.rpc.hooks import shared_remote_registration

    # Add more shared modules here in the future
