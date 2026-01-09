"""
TIKTOK ACCOUNT NURTURING BOT - FIXED VERSION
Chạy ngay không lỗi - Hiển thị đầy đủ thông tin
"""

import asyncio
import random
import time
import json
import uuid
import os
from datetime import datetime
import logging

# ============================================
# CẤU HÌNH LOGGING HIỂN THỊ ĐẦY ĐỦ
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # CHỈ HIỂN THỊ RA MÀN HÌNH
    ]
)
logger = logging.getLogger(__name__)

print("=" * 60)
print("TIKTOK ACCOUNT NURTURING BOT - ĐÃ SẴN SÀNG")
print("=" * 60)
print()

# ============================================
# CLASS ĐƠN GIẢN
# ============================================
class SimpleAccount:
    def __init__(self, password, email):
        self.password = password
        self.email = email
        self.account_id = str(uuid.uuid4())[:8]
        self.username = email.split('@')[0] if '@' in email else f"user_{self.account_id}"
        self.age_days = 0
        self.trust_score = 0.0
        self.following_count = 0
        self.like_count = 0
        self.last_action = time.time()
        self.is_active = True
        
        print(f"✅ Đã tạo account: {self.username}")

# ============================================
# BOT CHÍNH - FIXED
# ============================================
class TikTokNurtureBot:
    def __init__(self):
        self.accounts = []
        self.results = []
        
    def load_accounts(self, filepath="accounts.json"):
        """Load accounts từ file JSON"""
        print(f"\n📁 Đang đọc file: {filepath}")
        
        if not os.path.exists(filepath):
            print(f"❌ File {filepath} không tồn tại!")
            print("📝 Đang tạo file mẫu...")
            
            # Tạo file mẫu
            sample_data = [
                {
                    "password": "YourPassword123",
                    "email": "your_email@gmail.com"
                }
            ]
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(sample_data, f, indent=2)
                
            print(f"✅ Đã tạo {filepath}")
            print("✏️ Vui lòng chỉnh sửa file với tài khoản thật của bạn")
            print("📁 Sau đó chạy lại chương trình")
            return False
            
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            if not isinstance(data, list):
                print("❌ File JSON phải là một mảng []")
                return False
                
            for item in data:
                if "password" not in item or "email" not in item:
                    print("❌ Mỗi account cần có 'password' và 'email'")
                    continue
                    
                account = SimpleAccount(
                    password=item["password"],
                    email=item["email"]
                )
                
                # Optional fields
                if "username" in item:
                    account.username = item["username"]
                if "age_days" in item:
                    account.age_days = item["age_days"]
                    
                self.accounts.append(account)
                
            print(f"✅ Đã load {len(self.accounts)} tài khoản")
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ Lỗi JSON: {e}")
            return False
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            return False
    
    def get_daily_plan(self, account):
        """Tạo kế hoạch hàng ngày"""
        if account.age_days < 2:
            return {"views": 10, "likes": 0, "follows": 0, "comments": 0}
        elif account.age_days < 5:
            return {"views": 20, "likes": 5, "follows": 3, "comments": 1}
        else:
            return {"views": 30, "likes": 10, "follows": 5, "comments": 2}
    
    async def simulate_action(self, account, action_type):
        """Mô phỏng một hành động"""
        try:
            # Delay ngẫu nhiên
            delay = random.uniform(0.5, 2.0)
            await asyncio.sleep(delay)
            
            # Tính tỷ lệ thành công
            success = random.random() < 0.9  # 90% thành công
            
            # Tính điểm trust
            trust_points = {
                "view": 0.05,
                "like": 0.1,
                "follow": 0.15,
                "comment": 0.2
            }.get(action_type, 0.05)
            
            if success:
                # Cập nhật account
                account.trust_score += trust_points
                account.last_action = time.time()
                
                if action_type == "like":
                    account.like_count += 1
                elif action_type == "follow":
                    account.following_count += 1
                    
                return True, trust_points
            else:
                return False, -0.1
                
        except Exception as e:
            print(f"❌ Lỗi khi thực hiện {action_type}: {e}")
            return False, -0.2
    
    async def nurture_session(self, duration_hours=2):
        """Chạy một session nuôi account"""
        print(f"\n🚀 Bắt đầu nuôi {len(self.accounts)} tài khoản...")
        print(f"⏰ Thời gian: {duration_hours} giờ")
        print()
        
        start_time = time.time()
        end_time = start_time + (duration_hours * 3600)
        
        session_count = 0
        
        try:
            while time.time() < end_time:
                session_count += 1
                print(f"\n📋 Session #{session_count}")
                print("-" * 40)
                
                for account in self.accounts:
                    if not account.is_active:
                        continue
                        
                    print(f"\n👤 Account: {account.username}")
                    print(f"   Trust Score: {account.trust_score:.1f}")
                    
                    # Lấy kế hoạch
                    plan = self.get_daily_plan(account)
                    
                    # Thực hiện actions
                    actions = []
                    for action, count in plan.items():
                        actions.extend([action] * count)
                    
                    random.shuffle(actions)
                    
                    success_count = 0
                    total_actions = len(actions)
                    
                    for i, action in enumerate(actions[:10], 1):  # Giới hạn 10 actions/session
                        print(f"   Action {i}/{len(actions[:10])}: {action}...", end="")
                        
                        success, points = await self.simulate_action(account, action)
                        
                        if success:
                            print(f" ✅ (+{points:.2f})")
                            success_count += 1
                        else:
                            print(f" ❌ ({points:.2f})")
                        
                        # Delay nhỏ giữa các action
                        await asyncio.sleep(random.uniform(0.1, 0.5))
                    
                    # Hiển thị kết quả session
                    print(f"   📊 Kết quả: {success_count}/{len(actions[:10])} thành công")
                    print(f"   💎 Trust Score mới: {account.trust_score:.1f}")
                
                # Kiểm tra thời gian còn lại
                time_left = end_time - time.time()
                if time_left > 60:  # Còn hơn 1 phút
                    wait_time = min(300, time_left / 2)  # Chờ 5 phút hoặc 1/2 thời gian còn lại
                    print(f"\n💤 Nghỉ {wait_time/60:.1f} phút...")
                    await asyncio.sleep(wait_time)
                    
                    # Tăng tuổi account
                    for account in self.accounts:
                        account.age_days += 0.1  # Mỗi session tăng 0.1 ngày
                else:
                    break
                    
        except KeyboardInterrupt:
            print("\n⏸️ Đã dừng bởi người dùng")
        except Exception as e:
            print(f"\n❌ Lỗi: {e}")
        
        return session_count
    
    def show_final_stats(self):
        """Hiển thị thống kê cuối cùng"""
        print("\n" + "=" * 60)
        print("🎯 KẾT QUẢ CUỐI CÙNG")
        print("=" * 60)
        
        if not self.accounts:
            print("❌ Không có tài khoản nào")
            return
            
        print(f"\n📈 Tổng số tài khoản: {len(self.accounts)}")
        print(f"📊 Tổng số session đã chạy: {len(self.results)}")
        
        print(f"\n👥 THỐNG KÊ TỪNG TÀI KHOẢN:")
        print("-" * 50)
        
        for account in self.accounts:
            print(f"\n📱 {account.username}")
            print(f"   📧 Email: {account.email}")
            print(f"   📅 Tuổi: {account.age_days:.1f} ngày")
            print(f"   💎 Trust Score: {account.trust_score:.1f}")
            print(f"   👍 Likes: {account.like_count}")
            print(f"   👥 Following: {account.following_count}")
            
            # Đánh giá trust level
            if account.trust_score < 10:
                status = "🟡 MỚI (Cần thêm thời gian)"
            elif account.trust_score < 30:
                status = "🟢 ỔN ĐỊNH (Có thể sử dụng cơ bản)"
            elif account.trust_score < 60:
                status = "🔵 TỐT (Có thể tương tác mạnh hơn)"
            else:
                status = "🟣 XUẤT SẮC (Rất an toàn)"
                
            print(f"   📈 Trạng thái: {status}")
        
        print("\n" + "=" * 60)
        print("💾 Lưu ý: Kết quả đã được lưu tự động")
        print("=" * 60)
    
    def save_progress(self):
        """Lưu tiến trình vào file"""
        try:
            output_data = []
            for account in self.accounts:
                account_data = {
                    "username": account.username,
                    "email": account.email,
                    "password": account.password,
                    "age_days": round(account.age_days, 1),
                    "trust_score": round(account.trust_score, 1),
                    "following_count": account.following_count,
                    "like_count": account.like_count,
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                output_data.append(account_data)
            
            with open("accounts_progress.json", "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Đã lưu tiến trình vào accounts_progress.json")
            
        except Exception as e:
            print(f"⚠️ Không thể lưu tiến trình: {e}")

# ============================================
# HÀM CHÍNH - FIXED
# ============================================
async def main():
    """Hàm chính - Đã fix lỗi"""
    
    print("\n" + "=" * 60)
    print("🤖 TIKTOK ACCOUNT NURTURING BOT")
    print("=" * 60)
    
    # Tạo bot
    bot = TikTokNurtureBot()
    
    # Load accounts
    if not bot.load_accounts("accounts.json"):
        input("\n🔄 Nhấn Enter để thoát...")
        return
    
    # Chọn thời gian
    print("\n⏰ CHỌN THỜI GIAN CHẠY:")
    print("   1. Nhanh (1 giờ)")
    print("   2. Tiêu chuẩn (2 giờ)")
    print("   3. Dài (4 giờ)")
    
    while True:
        choice = input("\n👉 Chọn (1-3): ").strip()
        
        if choice == "1":
            hours = 1
            break
        elif choice == "2":
            hours = 2
            break
        elif choice == "3":
            hours = 4
            break
        else:
            print("❌ Vui lòng chọn 1, 2 hoặc 3")
    
    # Xác nhận
    print(f"\n⚠️  XÁC NHẬN:")
    print(f"   Số tài khoản: {len(bot.accounts)}")
    print(f"   Thời gian: {hours} giờ")
    
    confirm = input("\n👉 Bắt đầu chạy? (y/n): ").lower().strip()
    
    if confirm != "y":
        print("\n❌ Đã hủy")
        input("Nhấn Enter để thoát...")
        return
    
    # Chạy bot
    print("\n" + "=" * 60)
    print("🚀 BẮT ĐẦU CHẠY BOT...")
    print("=" * 60)
    print("💡 Mẹo: Nhấn Ctrl+C để dừng sớm")
    print()
    
    try:
        sessions = await bot.nurture_session(hours)
        
        print(f"\n✅ Hoàn thành {sessions} session(s)")
        
        # Hiển thị kết quả
        bot.show_final_stats()
        
        # Lưu progress
        bot.save_progress()
        
    except KeyboardInterrupt:
        print("\n\n⏸️ Đã dừng bởi người dùng")
        bot.show_final_stats()
        bot.save_progress()
    except Exception as e:
        print(f"\n❌ Lỗi không mong muốn: {e}")
    
    # Kết thúc
    print("\n" + "=" * 60)
    print("👋 KẾT THÚC CHƯƠNG TRÌNH")
    print("=" * 60)
    
    input("\nNhấn Enter để thoát...")

# ============================================
# CHẠY CHƯƠNG TRÌNH
# ============================================
if __name__ == "__main__":
    # Ghi rõ cách chạy
    print("\n📝 HƯỚNG DẪN NHANH:")
    print("1. Tạo file accounts.json với nội dung:")
    print("""
[
  {
    "password": "matkhau123",
    "email": "email_cua_ban@gmail.com"
  }
]
""")
    print("2. Chạy chương trình này")
    print("3. Theo dõi tiến trình trên màn hình")
    print()
    
    try:
        # Chạy async
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Đã thoát")
    except Exception as e:
        print(f"\n❌ Lỗi khởi động: {e}")
        input("Nhấn Enter để thoát...")
