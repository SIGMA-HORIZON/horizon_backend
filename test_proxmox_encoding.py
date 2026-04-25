
from proxmoxer import ProxmoxAPI
from horizon.core.config import get_settings
import urllib3
import urllib.parse

def test_encoding():
    settings = get_settings()
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    api = ProxmoxAPI(
        settings.PROXMOX_HOST,
        user=settings.PROXMOX_USER,
        token_name=settings.PROXMOX_TOKEN_ID,
        token_value=settings.PROXMOX_TOKEN_SECRET,
        verify_ssl=settings.PROXMOX_VERIFY_SSL,
        timeout=10
    )
    
    # On va tester d'envoyer une valeur avec un espace et un +
    # sur un champ de config bidon ou un commentaire
    node = "pve"
    vmid = 100 # VM existante
    
    test_val = "test + space /"
    quoted_val = urllib.parse.quote(test_val)
    
    print(f"Original: {test_val}")
    print(f"Quoted: {quoted_val}")
    
    try:
        # On utilise 'description' ou 'tags' qui sont des strings simples
        # api.nodes(node).qemu(vmid).config.post(description=test_val)
        # print("POST with plain text: Success")
        
        api.nodes(node).qemu(vmid).config.post(description=quoted_val)
        print("POST with quoted text: Success")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_encoding()
