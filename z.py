"""
TIKTOK ACCOUNT NURTURING BOT v2.0
Tự động nuôi tài khoản mới, tăng trust score
Tương tác tự nhiên, tránh detection
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
# ENUMS & DATA CLASSES
# ============================================
class NurtureStage(Enum):
    """Các giai đoạn nuôi tài khoản"""
    DAY_1_2 = "day_1_2"      # Khởi động nhẹ
    DAY_3_7 = "day_3_7"      # Tăng tương tác
    DAY_8_14 = "day_8_14"    # Mở rộng
    DAY_15_30 = "day_15_30"  # Ổn định
    MATURE = "mature"        # Tài khoản trưởng thành

class ActionType(Enum):
    """Loại hành động nuôi account"""
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
    """Thông tin tài khoản TikTok cần nuôi"""
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
    trust_score: float = 0.0  # 0-100 điểm
    stage: NurtureStage = NurtureStage.DAY_1_2
    created_at: float = field(default_factory=time.time)
    last_action: float = 0
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
    """Task nuôi account"""
    task_id: str
    account: TikTokAccount
    action: ActionType
    target_data: Dict  # video_id, user_id, etc.
    priority: int = 1
    scheduled_time: float = 0
    retry_count: int = 0

@dataclass
class NurtureResult:
    """Kết quả thực hiện task"""
    task_id: str
    account_id: str
    action: str
    success: bool
    timestamp: str
    response_data: Optional[Dict] = None
    error: Optional[str] = None
    trust_score_change: float = 0.0

# ============================================
# CONTENT DISCOVERY ENGINE
# ============================================
class ContentDiscovery:
    """Engine tìm content phù hợp để tương tác"""
    
    def __init__(self):
        self.trending_hashtags = self._load_trending_hashtags()
        self.popular_music = self._load_popular_music()
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
    
    def _load_trending_hashtags(self) -> List[str]:
        """Load trending hashtags (có thể update từ API)"""
        return [
            "#fyp", "#foryou", "#viral", "#trending",
            "#tiktokvietnam", "#vietnam", "#music",
            "#dance", "#comedy", "#funny", "#cooking",
            "#gaming", "#beauty", "#fitness", "#travel",
        ]
    
    def _load_popular_music(self) -> List[str]:
        """Load popular music IDs"""
        # Trong thực tế sẽ lấy từ TikTok API
        return [
            "music_123456", "music_789012", "music_345678",
            "music_901234", "music_567890", "music_123890",
        ]
    
    def discover_for_interests(self, interests: List[str], limit: int = 20) -> List[Dict]:
        """Tìm content phù hợp với sở thích"""
        discovered = []
        
        for interest in interests[:3]:  # Lấy 3 interests chính
            if interest in self.categories:
                keywords = self.categories[interest]
                
                # Giả lập tìm video
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
        """Tìm trending content"""
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
    """Engine chiến lược nuôi account theo từng giai đoạn"""
    
    def __init__(self):
        self.strategies = {
            NurtureStage.DAY_1_2: self._day_1_2_strategy,
            NurtureStage.DAY_3_7: self._day_3_7_strategy,
            NurtureStage.DAY_8_14: self._day_8_14_strategy,
            NurtureStage.DAY_15_30: self._day_15_30_strategy,
            NurtureStage.MATURE: self._mature_strategy,
        }
        
    def generate_daily_plan(self, account: TikTokAccount) -> List[Dict]:
        """Tạo kế hoạch hàng ngày cho account"""
        strategy_func = self.strategies.get(account.stage)
        if not strategy_func:
            logger.error(f"No strategy for stage {account.stage}")
            return []
        
        return strategy_func(account)
    
    def _day_1_2_strategy(self, account: TikTokAccount) -> List[Dict]:
        """Chiến lược ngày 1-2: Khởi động nhẹ"""
        plan = []
        
        # Ngày 1: Chỉ xem video
        if account.age_days == 0:
            for i in range(15):  # 15 views
                plan.append({
                    "action": ActionType.VIEW,
                    "duration": random.randint(20, 40),
                    "priority": 1,
                    "time_offset": i * random.randint(180, 600),  # 3-10 phút giữa views
                })
        
        # Ngày 2: Thêm likes
        elif account.age_days == 1:
            # 20 views
            for i in range(20):
                if i % 4 == 0:  # Mỗi view thứ 4 là like
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
        """Chiến lược ngày 3-7: Tăng dần tương tác"""
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
            
            # Chọn action theo weight
            actions = list(action_weights.keys())
            weights = list(action_weights.values())
            action = random.choices(actions, weights=weights, k=1)[0]
            
            action_config = {
                "action": action,
                "priority": random.randint(1, 3),
                "time_offset": i * random.randint(120, 480),  # 2-8 phút
            }
            
            if action == ActionType.VIEW:
                action_config["duration"] = random.randint(30, 60)
            elif action == ActionType.COMMENT:
                action_config["comment_type"] = random.choice(["short", "emoji", "question"])
            
            plan.append(action_config)
        
        return plan
    
    def _day_8_14_strategy(self, account: TikTokAccount) -> List[Dict]:
        """Chiến lược ngày 8-14: Mở rộng tương tác"""
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
                "time_offset": i * random.randint(90, 360),  # 1.5-6 phút
            }
            
            if action == ActionType.VIEW:
                action_config["duration"] = random.randint(15, 90)
            elif action == ActionType.COMMENT:
                action_config["comment_length"] = random.choice(["short", "medium"])
            
            plan.append(action_config)
        
        return plan
    
    def _day_15_30_strategy(self, account: TikTokAccount) -> List[Dict]:
        """Chiến lược ngày 15-30: Ổn định"""
        plan = []
        
        # Thêm unfollow strategy (follow-back check)
        if account.age_days % 3 == 0 and account.following_count > 50:
            # Unfollow những người không follow back
            unfollow_count = min(10, account.following_count // 10)
            for i in range(unfollow_count):
                plan.append({
                    "action": ActionType.UNFOLLOW,
                    "priority": 2,
                    "time_offset": i * random.randint(300, 900),
                })
        
        # Tương tác bình thường
        daily_actions = random.randint(40, 70)
        
        for i in range(daily_actions):
            action = random.choice([
                ActionType.VIEW, ActionType.LIKE, ActionType.COMMENT,
                ActionType.FOLLOW, ActionType.SHARE
            ])
            
            plan.append({
                "action": action,
                "priority": random.randint(1, 3),
                "time_offset": i * random.randint(60, 300),  # 1-5 phút
            })
        
        return plan
    
    def _mature_strategy(self, account: TikTokAccount) -> List[Dict]:
        """Chiến lược tài khoản trưởng thành"""
        plan = []
        
        # Hoạt động như người dùng thật
        sessions_per_day = random.randint(3, 6)
        current_time = 0
        
        for session in range(sessions_per_day):
            # Mỗi session kéo dài 10-30 phút
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
            
            # Thời gian nghỉ giữa các session
            if session < sessions_per_day - 1:
                break_duration = random.randint(1800, 7200)  # 30 phút - 2 giờ
                current_time += break_duration
        
        return plan

# ============================================
# TIKTOK INTERACTION CLIENT
# ============================================
class TikTokInteractionClient:
    """Client thực hiện các tương tác với TikTok"""
    
    def __init__(self, proxy_manager=None):
        self.proxy_manager = proxy_manager
        self.base_urls = [
            "https://api16-normal-c-useast1a.tiktokv.com",
            "https://api19-normal-c-useast1a.tiktokv.com",
        ]
        self.session_cache = {}
        
    async def perform_action(self, account: TikTokAccount, 
                           action: ActionType, target_data: Dict) -> NurtureResult:
        """Thực hiện một hành động tương tác"""
        task_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Kiểm tra giới hạn hàng ngày
            if not self._check_daily_limit(account, action):
                return NurtureResult(
                    task_id=task_id,
                    account_id=account.account_id,
                    action=action.value,
                    success=False,
                    timestamp=datetime.now().isoformat(),
                    error="Daily limit reached"
                )
            
            # Thực hiện action
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
            
            # Tính trust score change
            trust_change = self._calculate_trust_change(action, result_data.get('success', False))
            
            # Cập nhật stats
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
        """Kiểm tra giới hạn hàng ngày"""
        action_key = action.value + 's'  # views, likes, etc.
        if action_key in account.today_stats:
            limit = account.daily_limits.get(action_key[:-1], 100)  # Remove 's'
            return account.today_stats[action_key] < limit
        return True
    
    def _update_account_stats(self, account: TikTokAccount, action: ActionType):
        """Cập nhật thống kê account"""
        action_key = action.value + 's'
        if action_key in account.today_stats:
            account.today_stats[action_key] += 1
            
            # Cập nhật tổng stats
            if action == ActionType.LIKE:
                account.like_count += 1
            elif action == ActionType.FOLLOW:
                account.following_count += 1
            elif action == ActionType.UNFOLLOW:
                account.following_count = max(0, account.following_count - 1)
    
    def _calculate_trust_change(self, action: ActionType, success: bool) -> float:
        """Tính điểm trust score thay đổi"""
        if not success:
            return -0.5
        
        scores = {
            ActionType.VIEW: 0.1,
            ActionType.LIKE: 0.2,
            ActionType.COMMENT: 0.5,
            ActionType.FOLLOW: 0.3,
            ActionType.UNFOLLOW: 0.1,  # Unfollow cũng là hành vi tự nhiên
            ActionType.SHARE: 0.7,
            ActionType.SEARCH: 0.4,
            ActionType.PROFILE_VIEW: 0.15,
        }
        
        return scores.get(action, 0.1)
    
    async def _send_view(self, account: TikTokAccount, target_data: Dict) -> Dict:
        """Gửi view request"""
        # Giả lập API call
      
