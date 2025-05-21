from aiogram import Bot
from aiogram.types import User
from config.settings import REQUIRED_SUBSCRIPTIONS

async def check_subscriptions(bot: Bot, user: User) -> dict:
    """
    Check if user is subscribed to required channels
    Returns dict with subscription status for each channel
    """
    results = {}
    
    for sub_id, url in REQUIRED_SUBSCRIPTIONS.items():
        try:
            # Extract channel username from URL
            channel = url.split("/")[-1]
            member = await bot.get_chat_member(channel, user.id)
            results[sub_id] = member.status in ["member", "administrator", "creator"]
        except Exception:
            results[sub_id] = False
            
    return results

async def get_missing_subscriptions(bot: Bot, user: User) -> list:
    """Get list of channels user needs to subscribe to"""
    subscriptions = await check_subscriptions(bot, user)
    return [
        url for sub_id, url in REQUIRED_SUBSCRIPTIONS.items()
        if not subscriptions.get(sub_id, False)
    ] 