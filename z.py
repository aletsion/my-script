"""
TIKTOK ACCOUNT NURTURING BOT v2.0
Tự động nuôi tài khoản TikTok mới, tăng trust score
"""

import asyncio
import aiohttp
import random
import time
import json
import csv
import hashlib
import uuid
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
import logging
from enum import Enum
import re
from pathlib import Path

# ============================================
# CẤU HÌNH LOGGING
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tiktok_nurturing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================
# ENUMS & DATA CLASSES - ĐƯỢC SỬA LỖI JSON
# ============================================
class NurtureStage(Enum):
    DAY_1_2 = "day_1_2"
    DAY_3_7 = "day_3_7"
    DAY_8_14 = "day_8_14"
    DAY_15_30 = "day_15_30"
    MATURE = "mature"

class ActionType(Enum):
    VIEW = "view"
    LIKE = "like"
    COMMENT = "comment"
    FOLLOW = "follow"
    UNFOLLOW = "unfollow"
    SHARE = "share"
    WATCH_TIME = "watch_time"
    SEARCH = "search"
    PROFILE_VIEW = "profile_view"

@dataclass
class TikTokAccount:
    account_id: str
    username: str
    password: str
    nickname: str
    email: Optional[str] = None
    phone: Optional[str] = None
    age_days: int = 0
    follower_count: int = 0
    following_count: int = 0
    like_count: int = 0
    video_count: int = 0
    trust_score: float = 0.0
    stage: NurtureStage = NurtureStage.DAY_1_2
    created_at: float = field(default_factory=time.time)
    last_action: float = 0
    
    # Sửa lỗi: Không dùng lambda trong field
    daily_limits: Dict = field(default_factory=lambda: {
        "views": 100,
        "likes": 50,
        "comments": 20,
        "follows": 30,
        "unfollows": 15,
    })
    
    today_stats: Dict = field(default_factory=lambda: {
        "views": 0,
        "likes": 0,
        "comments": 0,
        "follows": 0,
        "unfollows": 0,
    })
    
    interests: List[str] = field(default_factory=lambda: [
        "music", "comedy", "dance", "cooking", "gaming",
        "beauty", "fitness", "travel", "education"
    ])
    
    device_profile: Dict = field(default_factory=dict)
    cookies: Dict = field(default_factory=dict)
    session_tokens: Dict = field(default_factory=dict)
    is_active: bool = True

@dataclass
class NurtureTask:
    task_id: str
    account: TikTokAccount
    action: ActionType
    target_data: Dict
    priority: int = 1
    scheduled_time: float = 0
    retry_count: int = 0

@dataclass 
class NurtureResult:
    task_id: str
    account_id: str
    action: str
    success: bool
    timestamp: str
    response_data: Optional[Dict] = None
    error: Optional[str] = None
    trust_score_change: float = 0.0

# ============================================
# HÀM TIỆN ÍCH ĐỂ XỬ LÝ JSON
# ============================================
def safe_json_dumps(data):
    """Chuyển đổi dữ liệu thành JSON an toàn"""
    def default_serializer(obj):
        if isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        raise TypeError(f"Type {type(obj)} not serializable")
    
    return json.dumps(data, default=default_serializer, indent=2, ensure_ascii=False)

def save_accounts_to_file(accounts: List[TikTokAccount], filename: str):
    """Lưu accounts vào file JSON an toàn"""
    accounts_data = []
    for account in accounts:
        account_dict = asdict(account)
        # Chuyển Enum thành string
        account_dict['stage'] = account.stage.value
        accounts_data.append(account_dict)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(accounts_data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(accounts)} accounts to {filename}")

def load_accounts_from_file(filename: str) -> List[TikTokAccount]:
    """Load accounts từ file JSON"""
    accounts = []
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            accounts_data = json.load(f)
        
        for acc_data in accounts_data:
            # Chuyển string stage thành Enum
            if 'stage' in acc_data:
                try:
                    acc_data['stage'] = NurtureStage(acc_data['stage'])
                except:
                    acc_data['stage'] = NurtureStage.DAY_1_2
            
            # Tạo account object
            account = TikTokAccount(**acc_data)
            accounts.append(account)
            
        logger.info(f"Loaded {len(accounts)} accounts from {filename}")
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {filename}: {e}")
        logger.error(f"Error at line {e.lineno}, column {e.colno}: {e.msg}")
        
        # Hiển thị lỗi cụ thể
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if e.lineno - 1 < len(lines):
                error_line = lines[e.lineno - 1]
                logger.error(f"Problem line: {error_line}")
                logger.error(f"Error position: {e.colno}")
    
    except Exception as e:
        logger.error(f"Error loading accounts: {e}")
    
    return accounts

# ============================================
# CONTENT DISCOVERY ENGINE
# ============================================
class ContentDiscovery:
    def __init__(self):
        self.trending_hashtags = [
            "#fyp", "#foryou", "#viral", "#trending",
            "#tiktokvietnam", "#vietnam", "#music",
            "#dance", "#comedy", "#funny", "#cooking",
            "#gaming", "#beauty", "#fitness", "#travel",
        ]
        
        self.popular_music = [
            "music_123456", "music_789012", "music_345678",
            "music_901234", "music_567890", "music_123890",
        ]
        
        self.categories = {
            "music": ["song", "music", "audio", "remix"],
            "comedy": ["funny", "comedy", "meme", "joke"],
            "dance": ["dance", "choreography", "kpop"],
            "cooking": ["recipe", "cooking", "food", "eat"],
            "gaming": ["game", "gaming", "esports", "mobilegame"],
            "beauty": ["makeup", "skincare", "beauty", "fashion"],
            "fitness": ["workout", "fitness", "gym", "health"],
            "travel": ["travel", "vietnam", "destination", "wanderlust"],
            "education": ["learn", "tips", "tutorial", "knowledge"],
        }
    
    def discover_for_interests(self, interests: List[str], limit: int = 20) -> List[Dict]:
        discovered = []
        
        for interest in interests[:3]:
            if interest in self.categories:
                keywords = self.categories[interest]
                
                for i in range(limit // 3):
                    video_data = {
                        "video_id": f"video_{hashlib.md5(f'{interest}_{i}'.encode()).hexdigest()[:10]}",
                        "author_id": f"author_{random.randint(10000, 99999)}",
                        "description": f"Video về {interest} #{random.choice(keywords)}",
                        "hashtags": [f"#{interest}"] + random.sample(self.trending_hashtags, 2),
                        "music_id": random.choice(self.popular_music) if interest == "music" else None,
                        "duration": random.randint(15, 60),
                        "like_count": random.randint(100, 10000),
                        "comment_count": random.randint(10, 1000),
                        "share_count": random.randint(5, 500),
                        "category": interest,
                        "created_time": int(time.time()) - random.randint(3600, 86400*7),
                    }
                    discovered.append(video_data)
        
        random.shuffle(discovered)
        return discovered[:limit]
    
    def discover_trending(self, limit: int = 15) -> List[Dict]:
        trending = []
        
        for i in range(limit):
            video_data = {
                "video_id": f"trending_{hashlib.md5(str(i).encode()).hexdigest()[:10]}",
                "author_id": f"trending_author_{random.randint(1000, 9999)}",
                "description": f"Trending video #{i+1} {random.choice(self.trending_hashtags)}",
                "hashtags": random.sample(self.trending_hashtags, 3),
                "music_id": random.choice(self.popular_music),
                "duration": random.randint(15, 45),
                "like_count": random.randint(1000, 100000),
                "comment_count": random.randint(100, 10000),
                "share_count": random.randint(50, 5000),
                "category": "trending",
                "created_time": int(time.time()) - random.randint(3600, 86400*2),
            }
            trending.append(video_data)
        
        return trending

# ============================================
# NURTURE STRATEGY ENGINE
# ============================================
class NurtureStrategy:
    def __init__(self):
        self.strategies = {
            NurtureStage.DAY_1_2: self._day_1_2_strategy,
            NurtureStage.DAY_3_7: self._day_3_7_strategy,
            NurtureStage.DAY_8_14: self._day_8_14_strategy,
            NurtureStage.DAY_15_30: self._day_15_30_strategy,
            NurtureStage.MATURE: self._mature_strategy,
        }
    
    def generate_daily_plan(self, account: TikTokAccount) -> List[Dict]:
        strategy_func = self.strategies.get(account.stage)
        if not strategy_func:
            return []
        
        return strategy_func(account)
    
    def _day_1_2_strategy(self, account: TikTokAccount) -> List[Dict]:
        plan = []
        
        if account.age_days == 0:
            for i in range(15):
                plan.append({
                    "action": ActionType.VIEW,
                    "duration": random.randint(20, 40),
                    "priority": 1,
                    "time_offset": i * random.randint(180, 600),
                })
        
        elif account.age_days == 1:
            for i in range(20):
                if i % 4 == 0:
                    plan.append({
                        "action": ActionType.LIKE,
                        "priority": 2,
                        "time_offset": i * random.randint(240, 720),
                    })
                else:
                    plan.append({
                        "action": ActionType.VIEW,
                        "duration": random.randint(25, 50),
                        "priority": 1,
                        "time_offset": i * random.randint(240, 720),
                    })
        
        return plan
    
    def _day_3_7_strategy(self, account: TikTokAccount) -> List[Dict]:
        plan = []
        actions_per_day = 30 + (account.age_days * 5)
        
        for i in range(actions_per_day):
            action_weights = {
                ActionType.VIEW: 50,
                ActionType.LIKE: 30,
                ActionType.COMMENT: 10,
                ActionType.FOLLOW: 8,
                ActionType.PROFILE_VIEW: 2,
            }
            
            actions = list(action_weights.keys())
            weights = list(action_weights.values())
            action = random.choices(actions, weights=weights, k=1)[0]
            
            action_config = {
                "action": action,
                "priority": random.randint(1, 3),
                "time_offset": i * random.randint(120, 480),
            }
            
            if action == ActionType.VIEW:
                action_config["duration"] = random.randint(30, 60)
            elif action == ActionType.COMMENT:
                action_config["comment_type"] = random.choice(["short", "emoji", "question"])
            
            plan.append(action_config)
        
        return plan
    
    def _day_8_14_strategy(self, account: TikTokAccount) -> List[Dict]:
        plan = []
        actions_per_day = 50
        
        for i in range(actions_per_day):
            action_weights = {
                ActionType.VIEW: 40,
                ActionType.LIKE: 25,
                ActionType.COMMENT: 15,
                ActionType.FOLLOW: 10,
                ActionType.SHARE: 5,
                ActionType.SEARCH: 5,
            }
            
            actions = list(action_weights.keys())
            weights = list(action_weights.values())
            action = random.choices(actions, weights=weights, k=1)[0]
            
            action_config = {
                "action": action,
                "priority": random.randint(1, 3),
                "time_offset": i * random.randint(90, 360),
            }
            
            if action == ActionType.VIEW:
                action_config["duration"] = random.randint(15, 90)
            elif action == ActionType.COMMENT:
                action_config["comment_length"] = random.choice(["short", "medium"])
            
            plan.append(action_config)
        
        return plan
    
    def _day_15_30_strategy(self, account: TikTokAccount) -> List[Dict]:
        plan = []
        
        if account.age_days % 3 == 0 and account.following_count > 50:
            unfollow_count = min(10, account.following_count // 10)
            for i in range(unfollow_count):
                plan.append({
                    "action": ActionType.UNFOLLOW,
                    "priority": 2,
                    "time_offset": i * random.randint(300, 900),
                })
        
        daily_actions = random.randint(40, 70)
        
        for i in range(daily_actions):
            action = random.choice([
                ActionType.VIEW, ActionType.LIKE, ActionType.COMMENT,
                ActionType.FOLLOW, ActionType.SHARE
            ])
            
            plan.append({
                "action": action,
                "priority": random.randint(1, 3),
                "time_offset": i * random.randint(60, 300),
            })
        
        return plan
    
    def _mature_strategy(self, account: TikTokAccount) -> List[Dict]:
        plan = []
        
        sessions_per_day = random.randint(3, 6)
        current_time = 0
        
        for session in range(sessions_per_day):
            session_duration = random.randint(600, 1800)
            actions_in_session = random.randint(10, 30)
            
            for i in range(actions_in_session):
                action_weights = {
                    ActionType.VIEW: 60,
                    ActionType.LIKE: 20,
                    ActionType.COMMENT: 10,
                    ActionType.FOLLOW: 5,
                    ActionType.SHARE: 5,
                }
                
                actions = list(action_weights.keys())
                weights = list(action_weights.values())
                action = random.choices(actions, weights=weights, k=1)[0]
                
                plan.append({
                    "action": action,
                    "priority": random.randint(1, 3),
                    "time_offset": current_time + (i * random.randint(20, 120)),
                })
            
            current_time += session_duration
            
            if session < sessions_per_day - 1:
                break_duration = random.randint(1800, 7200)
                current_time += break_duration
        
        return plan

# ============================================
# TIKTOK INTERACTION CLIENT
# ============================================
class TikTokInteractionClient:
    def __init__(self, proxy_manager=None):
        self.proxy_manager = proxy_manager
        self.base_urls = [
            "https://api16-normal-c-useast1a.tiktokv.com",
            "https://api19-normal-c-useast1a.tiktokv.com",
        ]
        self.session_cache = {}
    
    async def perform_action(self, account: TikTokAccount, 
                           action: ActionType, target_data: Dict) -> NurtureResult:
        task_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            if not self._check_daily_limit(account, action):
                return NurtureResult(
                    task_id=task_id,
                    account_id=account.account_id,
                    action=action.value,
                    success=False,
                    timestamp=datetime.now().isoformat(),
                    error="Daily limit reached"
                )
            
            result_data = None
            
            if action == ActionType.VIEW:
                result_data = await self._send_view(account, target_data)
            elif action == ActionType.LIKE:
                result_data = await self._send_like(account, target_data)
            elif action == ActionType.COMMENT:
                result_data = await self._send_comment(account, target_data)
            elif action == ActionType.FOLLOW:
                result_data = await self._send_follow(account, target_data)
            elif action == ActionType.UNFOLLOW:
                result_data = await self._send_unfollow(account, target_data)
            elif action == ActionType.SHARE:
                result_data = await self._send_share(account, target_data)
            else:
                return NurtureResult(
                    task_id=task_id,
                    account_id=account.account_id,
                    action=action.value,
                    success=False,
                    timestamp=datetime.now().isoformat(),
                    error=f"Action {action} not implemented"
                )
            
            trust_change = self._calculate_trust_change(action, result_data.get('success', False))
            
            if result_data.get('success'):
                self._update_account_stats(account, action)
            
            return NurtureResult(
                task_id=task_id,
                account_id=account.account_id,
                action=action.value,
                success=result_data.get('success', False),
                timestamp=datetime.now().isoformat(),
                response_data=result_data,
                trust_score_change=trust_change
            )
            
        except Exception as e:
            logger.error(f"Action failed: {str(e)}")
            return NurtureResult(
                task_id=task_id,
                account_id=account.account_id,
                action=action.value,
                success=False,
                timestamp=datetime.now().isoformat(),
                error=str(e)
            )
    
    def _check_daily_limit(self, account: TikTokAccount, action: ActionType) -> bool:
        action_key = action.value + 's'
        if action_key in account.today_stats:
            limit_key = action.value if action.value != 'unfollow' else 'unfollows'
            limit = account.daily_limits.get(limit_key, 100)
            return account.today_stats[action_key] < limit
        return True
    
    def _update_account_stats(self, account: TikTokAccount, action: ActionType):
        action_key = action.value + 's'
        if action_key in account.today_stats:
            account.today_stats[action_key] += 1
            
            if action == ActionType.LIKE:
                account.like_count += 1
            elif action == ActionType.FOLLOW:
                account.following_count += 1
            elif action == ActionType.UNFOLLOW:
                account.following_count = max(0, account.following_count - 1)
    
    def _calculate_trust_change(self, action: ActionType, success: bool) -> float:
        if not success:
            return -0.5
        
        scores = {
            ActionType.VIEW: 0.1,
            ActionType.LIKE: 0.2,
            ActionType.COMMENT: 0.5,
            ActionT
