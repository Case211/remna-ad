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
        """Get Remnawave health status (API v2.2.6)"""
        return await RemnaAPI.get("system/health")

    @staticmethod
    async def get_nodes_metrics():
        """Get nodes metrics from Prometheus endpoint (API v2.2.6)"""
        return await RemnaAPI.get("system/nodes/metrics")

    @staticmethod
    async def get_remnawave_settings():
        """Get Remnawave settings (API v2.2.6)"""
        return await RemnaAPI.get("remnawave-settings")

    @staticmethod
    async def run_srr_matcher(payload):
        """Run SRR matcher tester (API v2.2.6)"""
        return await RemnaAPI.post("system/testers/srr-matcher", payload)

    @staticmethod
    async def happ_encrypt(payload):
        """Encrypt data for HAPP tool (API v2.2.6)"""
        return await RemnaAPI.post("system/tools/happ/encrypt", payload)

    @staticmethod
    async def generate_x25519_keys():
        """Generate x25519 keypair (API v2.2.6)"""
        return await RemnaAPI.get("system/tools/x25519/generate")

    
    @staticmethod
    async def get_xray_config():
        """Not available in v208"""
        return None
    
    @staticmethod
    async def update_xray_config(config_data):
        """Not available in v208"""
        return None
