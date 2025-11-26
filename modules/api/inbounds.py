from modules.api.client import RemnaAPI
from modules.api.users import UserAPI
from modules.api.config_profiles import ConfigProfileAPI
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

class InboundAPI:
    """API methods for inbound management (v208 via config profiles)"""
    @staticmethod
    def _is_active_status(value) -> bool:
        """Return True if a status value represents active/enabled."""
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        try:
            text = str(value).strip().upper()
            return text in {"ACTIVE", "ENABLED", "TRUE", "ON"}
        except Exception:
            return False
    
    @staticmethod
    async def get_inbounds():
        """Get all inbounds across all config profiles"""
        # v208 exposes inbounds via config profiles
        result = await RemnaAPI.get("config-profiles/inbounds")
        # API returns { response: { total, inbounds: [...] } } which client unwraps to response
        # Our RemnaAPI already returns json['response'] when present
        if isinstance(result, dict) and 'inbounds' in result:
            return result['inbounds']
        return result
    
    @staticmethod
    async def get_full_inbounds():
        """Get inbounds with full details (same as get_inbounds in v208)"""
        return await InboundAPI.get_inbounds()
    
    @staticmethod
    async def get_inbound_users(inbound_uuid: str):
        """Get users associated with specific inbound in v208"""
        try:
            logger.info(f"Getting users for inbound {inbound_uuid}")
            # Resolve target inbound details for robust matching
            try:
                all_inbounds = await InboundAPI.get_inbounds()
                target = next((i for i in (all_inbounds or []) if str(i.get('uuid')) == str(inbound_uuid)), None)
            except Exception as e:
                logger.warning(f"Failed to fetch inbounds to resolve target details: {e}")
                target = None

            def matches_inbound_ref(ref, tgt) -> bool:
                if ref is None:
                    return False
                # Accept direct string reference as UUID
                if isinstance(ref, str):
                    return str(ref) == str(inbound_uuid)
                if not isinstance(ref, dict):
                    return False
                # Match by UUID when present
                if str(ref.get('uuid')) == str(inbound_uuid):
                    return True
                # Fallback match by tag + (port or listenPort) + type if target is known
                if tgt and isinstance(tgt, dict):
                    try:
                        tag_ok = (ref.get('tag') and tgt.get('tag') and str(ref.get('tag')) == str(tgt.get('tag')))
                        # some payloads use 'port' or 'listenPort'
                        ref_port = ref.get('port') if ref.get('port') is not None else ref.get('listenPort')
                        tgt_port = tgt.get('port') if tgt.get('port') is not None else tgt.get('listenPort')
                        port_ok = (ref_port is not None and tgt_port is not None and int(ref_port) == int(tgt_port))
                        type_ok = (ref.get('type') and tgt.get('type') and str(ref.get('type')) == str(tgt.get('type')))
                        if tag_ok and port_ok and type_ok:
                            return True
                    except Exception:
                        pass
                return False
            # Build a set of config profile UUIDs that include this inbound
            profile_uuids_for_inbound = set()
            try:
                profiles = await ConfigProfileAPI.get_profiles()
                for profile in profiles or []:
                    profile_uuid = profile.get("uuid") or profile.get("id")
                    if not profile_uuid:
                        continue
                    try:
                        profile_inbounds = await ConfigProfileAPI.get_profile_inbounds(profile_uuid)
                        if any((ib.get("uuid") == inbound_uuid) for ib in (profile_inbounds or [])):
                            profile_uuids_for_inbound.add(profile_uuid)
                    except Exception as e:
                        logger.warning(f"Failed to get inbounds for profile {profile_uuid}: {e}")
            except Exception as e:
                logger.warning(f"Failed to enumerate profiles for inbound mapping: {e}")
            
            # Get all users
            users_response = await UserAPI.get_all_users()
            if not users_response:
                logger.warning("No users response received")
                return []
            
            users = []
            if isinstance(users_response, dict) and 'users' in users_response:
                users = users_response['users']
            elif isinstance(users_response, list):
                users = users_response
            
            if not users:
                logger.warning("No users found in response")
                return []
            
            logger.info(f"Found {len(users)} total users")
            
            # Filter users by active subscriptions that use this inbound
            inbound_users = []
            active_users = 0
            users_with_subscriptions = 0
            users_with_profile = 0
            users_with_direct_sub_inbound = 0
            users_with_matching_inbound = 0
            
            for user in users:
                # Check if user has active status
                if InboundAPI._is_active_status(user.get('status')):
                    active_users += 1
                    # Check if user's subscription uses this inbound
                    subscription = user.get('subscription')
                    subscriptions = user.get('subscriptions') if isinstance(user.get('subscriptions'), list) else None
                    # Normalize both singular and plural subscriptions
                    subscription_items = []
                    if subscription and isinstance(subscription, dict):
                        subscription_items.append(subscription)
                    if subscriptions:
                        for s in subscriptions:
                            if isinstance(s, dict):
                                subscription_items.append(s)

                    for sub in subscription_items:
                        try:
                            if InboundAPI._is_active_status(sub.get('status')):
                                users_with_subscriptions += 1
                            # Direct subscription-bound inbounds (array)
                            sub_inbounds = sub.get('inbounds') or []
                            if isinstance(sub_inbounds, list) and any(
                                matches_inbound_ref(si, target) for si in sub_inbounds
                            ):
                                inbound_users.append(user)
                                users_with_direct_sub_inbound += 1
                                logger.info(f"Found user {user.get('username', 'unknown')} via subscription.inbounds for inbound {inbound_uuid}")
                                subscription_items = []
                                break
                        except Exception:
                            pass

                    # Resolve user's config profile UUID from multiple possible fields
                    # Try derive profile from any subscription item first
                    config_profile_uuid = None
                    for sub in subscription_items or [subscription or {}]:
                        if not isinstance(sub, dict):
                            continue
                        config_profile_uuid = (
                            sub.get('configProfileUuid')
                            or (sub.get('configProfile', {}) or {}).get('uuid') if isinstance(sub.get('configProfile'), dict) else sub.get('configProfile')
                        )
                        if config_profile_uuid:
                            break
                    # Fallbacks from user fields
                    if not config_profile_uuid:
                        config_profile_uuid = (
                            user.get('configProfileUuid')
                            or (user.get('configProfile', {}) or {}).get('uuid') if isinstance(user.get('configProfile'), dict) else user.get('configProfile')
                        )
                    if config_profile_uuid:
                        users_with_profile += 1
                        # Fast path: if we pre-computed profiles containing this inbound
                        if (profile_uuids_for_inbound and config_profile_uuid in profile_uuids_for_inbound):
                            inbound_users.append(user)
                            users_with_matching_inbound += 1
                            logger.info(f"Found user {user.get('username', 'unknown')} via profile map using inbound {inbound_uuid}")
                            continue
                        # On-demand verify profile inbounds when map is empty or uncertain
                        try:
                            profile_inbounds = await ConfigProfileAPI.get_profile_inbounds(str(config_profile_uuid))
                            if any(matches_inbound_ref(pi, target) for pi in (profile_inbounds or [])):
                                inbound_users.append(user)
                                users_with_matching_inbound += 1
                                logger.info(f"Found user {user.get('username', 'unknown')} using inbound {inbound_uuid}")
                                continue
                        except Exception as e:
                            logger.warning(f"Failed to verify profile {config_profile_uuid} inbounds: {e}")
            
            logger.info(
                f"User stats: {active_users} active, {users_with_subscriptions} with subscriptions, "
                f"{users_with_profile} with profile, {users_with_direct_sub_inbound} via subscription.inbounds, "
                f"{users_with_matching_inbound} with matching inbound"
            )
            
            # Alternative approach: check if user has inbound directly in their data
            if not inbound_users:
                logger.info("Trying alternative approach - checking user data directly")
                for user in users:
                    if InboundAPI._is_active_status(user.get('status')):
                        # Check if user has inbound data directly
                        user_inbounds = user.get('inbounds', [])
                        if user_inbounds:
                            for user_inbound in user_inbounds:
                                if matches_inbound_ref(user_inbound, target):
                                    inbound_users.append(user)
                                    logger.info(f"Found user {user.get('username', 'unknown')} with direct inbound reference")
                                    break
                        
                        # Check if user has activeInbounds
                        active_inbounds = user.get('activeInbounds', [])
                        if active_inbounds:
                            for active_inbound in active_inbounds:
                                if matches_inbound_ref(active_inbound, target):
                                    inbound_users.append(user)
                                    logger.info(f"Found user {user.get('username', 'unknown')} with activeInbound reference")
                                    break

            # Heuristic fallback: match by tag equality (project-specific)
            if not inbound_users and isinstance(target, dict) and target.get('tag'):
                try:
                    t_tag = str(target.get('tag')).strip().lower()
                    for user in users:
                        if not InboundAPI._is_active_status(user.get('status')):
                            continue
                        u_tag = str(user.get('tag') or '').strip().lower()
                        if u_tag and u_tag == t_tag:
                            inbound_users.append(user)
                    logger.info(f"Heuristic tag match added {len(inbound_users)} users for inbound {inbound_uuid}")
                except Exception as e:
                    logger.warning(f"Heuristic tag match failed: {e}")
            
            # Final fallback: use profile users endpoint if available
            if not inbound_users and profile_uuids_for_inbound:
                try:
                    logger.info("Trying profile users endpoint as final fallback")
                    seen = set()
                    for p_uuid in profile_uuids_for_inbound:
                        try:
                            p_users = await ConfigProfileAPI.get_profile_users(p_uuid)
                            for u in p_users or []:
                                if isinstance(u, dict):
                                    u_uuid = str(u.get('uuid'))
                                    if u_uuid and u_uuid not in seen:
                                        inbound_users.append(u)
                                        seen.add(u_uuid)
                        except Exception as e:
                            logger.warning(f"Failed to load users for profile {p_uuid}: {e}")
                    logger.info(f"Profile users fallback added {len(inbound_users)} users")
                except Exception as e:
                    logger.warning(f"Profile users fallback failed: {e}")
            
            logger.info(f"Final result: {len(inbound_users)} users found for inbound {inbound_uuid}")
            if not inbound_users:
                try:
                    # Extra diagnostics: log available keys to identify correct linkage fields in v208
                    sample = users[:3]
                    for idx, u in enumerate(sample, 1):
                        if not isinstance(u, dict):
                            continue
                        logger.info(f"Diag user#{idx} keys: {list(u.keys())}")
                        sub = u.get('subscription') or {}
                        subs = u.get('subscriptions') if isinstance(u.get('subscriptions'), list) else []
                        if isinstance(sub, dict):
                            logger.info(f"Diag user#{idx} subscription keys: {list(sub.keys())}")
                            if isinstance(sub.get('configProfile'), dict):
                                logger.info(f"Diag user#{idx} subscription.configProfile keys: {list(sub.get('configProfile').keys())}")
                        for jdx, s in enumerate(subs[:2], 1):
                            if isinstance(s, dict):
                                logger.info(f"Diag user#{idx} subscriptions[{jdx}] keys: {list(s.keys())}")
                        if isinstance(u.get('configProfile'), dict):
                            logger.info(f"Diag user#{idx} configProfile keys: {list(u.get('configProfile').keys())}")
                        if isinstance(u.get('inbounds'), list) and u.get('inbounds'):
                            logger.info(f"Diag user#{idx} inbounds[0] keys: {list(u.get('inbounds')[0].keys()) if isinstance(u.get('inbounds')[0], dict) else type(u.get('inbounds')[0]).__name__}")
                        if isinstance(u.get('activeInbounds'), list) and u.get('activeInbounds'):
                            logger.info(f"Diag user#{idx} activeInbounds[0] keys: {list(u.get('activeInbounds')[0].keys()) if isinstance(u.get('activeInbounds')[0], dict) else type(u.get('activeInbounds')[0]).__name__}")
                except Exception as e:
                    logger.warning(f"Diag logging failed: {e}")
            return inbound_users
            
        except Exception as e:
            logger.error(f"Error getting users for inbound {inbound_uuid}: {e}")
            return []
    
    @staticmethod
    async def get_inbound_users_count(inbound_uuid: str):
        """Get count of users associated with specific inbound"""
        try:
            users = await InboundAPI.get_inbound_users(inbound_uuid)
            return len(users)
        except Exception as e:
            logger.error(f"Error getting users count for inbound {inbound_uuid}: {e}")
            return 0

    @staticmethod
    def _parse_dt(value) -> Optional[datetime]:
        try:
            if not value:
                return None
            text = str(value)
            if text.endswith('Z'):
                text = text[:-1] + '+00:00'
            return datetime.fromisoformat(text)
        except Exception:
            return None

    @staticmethod
    def _is_recent(ts: Optional[datetime], minutes: int = 5) -> bool:
        if not ts:
            return False
        try:
            now = datetime.now(timezone.utc)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            return (now - ts) <= timedelta(minutes=minutes)
        except Exception:
            return False

    @staticmethod
    async def get_inbound_online_count(inbound: dict) -> int:
        """Simple online count - show total active users since we can't match by tags"""
        try:
            # Get all users and count online (recent activity)
            all_resp = await UserAPI.get_all_users()
            all_users = []
            if isinstance(all_resp, dict) and 'users' in all_resp:
                all_users = all_resp['users'] or []
            elif isinstance(all_resp, list):
                all_users = all_resp

            if not all_users:
                return 0

            online_count = 0
            for user in all_users:
                # Check if user is active
                if not InboundAPI._is_active_status(user.get('status')):
                    continue
                
                # Check if user was online recently (last 5 minutes)
                ts = InboundAPI._parse_dt(user.get('onlineAt'))
                if InboundAPI._is_recent(ts, minutes=5):
                    online_count += 1
                    
            logger.info(f"Online users count: {online_count} (checked {len(all_users)} users)")
            return online_count
            
        except Exception as e:
            logger.error(f"Error getting online count for inbound {inbound.get('uuid', 'unknown')}: {e}")
            return 0
    
    @staticmethod
    async def get_inbound_users_stats(inbound_uuid: str):
        """Get statistics of users associated with specific inbound"""
        try:
            users = await InboundAPI.get_inbound_users(inbound_uuid)
            
            if not users:
                return {
                    'enabled': 0,
                    'disabled': 0,
                    'total': 0
                }
            
            enabled = sum(1 for user in users if user.get('status') == 'active')
            disabled = len(users) - enabled
            
            return {
                'enabled': enabled,
                'disabled': disabled,
                'total': len(users)
            }
            
        except Exception as e:
            logger.error(f"Error getting users stats for inbound {inbound_uuid}: {e}")
            return {
                'enabled': 0,
                'disabled': 0,
                'total': 0
            }
    
    @staticmethod
    async def debug_user_structure():
        """Debug function to understand user data structure in v208"""
        try:
            users_response = await UserAPI.get_all_users()
            if not users_response:
                logger.warning("No users response for debugging")
                return
            
            users = []
            if isinstance(users_response, dict) and 'users' in users_response:
                users = users_response['users']
            elif isinstance(users_response, list):
                users = users_response
            
            if not users:
                logger.warning("No users found for debugging")
                return
            
            # Log structure of first few users
            for i, user in enumerate(users[:3]):
                logger.info(f"User {i+1} structure:")
                logger.info(f"  - username: {user.get('username', 'N/A')}")
                logger.info(f"  - status: {user.get('status', 'N/A')}")
                logger.info(f"  - subscription: {user.get('subscription', 'N/A')}")
                logger.info(f"  - inbounds: {user.get('inbounds', 'N/A')}")
                logger.info(f"  - activeInbounds: {user.get('activeInbounds', 'N/A')}")
                logger.info(f"  - configProfileUuid: {user.get('configProfileUuid', 'N/A')}")
                
                # Log subscription details if exists
                subscription = user.get('subscription')
                if subscription:
                    logger.info(f"  - subscription.status: {subscription.get('status', 'N/A')}")
                    logger.info(f"  - subscription.configProfileUuid: {subscription.get('configProfileUuid', 'N/A')}")
                    logger.info(f"  - subscription.inbounds: {subscription.get('inbounds', 'N/A')}")
                
                logger.info("  ---")
                
        except Exception as e:
            logger.error(f"Error in debug_user_structure: {e}")
