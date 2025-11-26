from modules.api.client import RemnaAPI

class SystemAPI:
    """API methods for system management"""
    
    @staticmethod
    async def get_stats():
        """Get system statistics"""
        return await RemnaAPI.get("system/stats")
    
    @staticmethod
    async def get_bandwidth_stats():
        """Get bandwidth statistics"""
        return await RemnaAPI.get("system/stats/bandwidth")
    
    @staticmethod
    async def get_nodes_statistics():
        """Get nodes statistics"""
        return await RemnaAPI.get("system/stats/nodes")

    @staticmethod
    async def get_health():
        """Get Remnawave health status (v2.2.6)."""
        return await RemnaAPI.get("system/health")

    @staticmethod
    async def get_nodes_metrics():
        """Get nodes metrics from Prometheus endpoint (v2.2.6)."""
        return await RemnaAPI.get("system/nodes/metrics")

    @staticmethod
    async def generate_x25519_keypairs():
        """Generate x25519 keypairs (v2.2.6)."""
        return await RemnaAPI.get("system/tools/x25519/generate")

    @staticmethod
    async def encrypt_happ_crypto_link(payload):
        """Encrypt Happ crypto link (v2.2.6)."""
        return await RemnaAPI.post("system/tools/happ/encrypt", payload)

    
    # Note: xray config endpoints are not available in v2.2.6
