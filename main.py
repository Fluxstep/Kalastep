import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timedelta
from wordfreq import zipf_frequency
from wordfreq import zipf_frequency

print(zipf_frequency("fork", "en"))
print(zipf_frequency("onward", "en"))
print(zipf_frequency("playing", "en"))
import time
import random

# ================= CONFIG =================

load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)

# ================= FILES =================

SERVERS_FILE = "servers.json"
LEADERBOARD_FILE = "leaderboard.json"
COINS_FILE = "coins.json"
DAILY_FILE = "daily.json"

# ================= AUTO-CREATE FILES =================

def ensure_file_exists(filename):
    """Create file if it doesn't exist"""
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            json.dump({}, f, indent=4)
        print(f"✅ Created {filename}")
    else:
        print(f"✅ Found {filename}")

ensure_file_exists(SERVERS_FILE)
ensure_file_exists(LEADERBOARD_FILE)
ensure_file_exists(COINS_FILE)
ensure_file_exists(DAILY_FILE)

# ================= LOAD DATA =================

def load_servers():
    try:
        with open(SERVERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_servers(data):
    with open(SERVERS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_leaderboard():
    try:
        with open(LEADERBOARD_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_leaderboard(data):
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_coins_data():
    try:
        with open(COINS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_coins_data(data):
    with open(COINS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_daily():
    try:
        with open(DAILY_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_daily(data):
    with open(DAILY_FILE, "w") as f:
        json.dump(data, f, indent=4)

def is_real_word(word):
    return zipf_frequency(word, "en") > 0

servers = load_servers()
leaderboard = load_leaderboard()
coins_data = load_coins_data()
daily_claims = load_daily()

# ================= GAME STATE =================

game_states = {}
setup_sessions = {}  # {user_id: {"guild_id": ..., "step": ..., "data": ...}}

# ================= DICTIONARY & WORD VALIDATION =================

BAD_ENDINGS = {'rd', 'ng', 'lf', 'mp', 'nk', 'lp', 'ft', 'lm', 'ld', 'lt'}

def load_dictionary():
    """Load English dictionary from NLTK or fallback"""
    try:
        import nltk
        nltk.download('words', quiet=True)
        from nltk.corpus import words
        word_set = set(word.lower() for word in words.words() if len(word) >= 4)
        print(f"✅ Loaded {len(word_set)} words from NLTK")
        return word_set
    except
        dictionary = set()

BAD_ENDINGS = {'rd', 'ng', 'lf', 'mp', 'nk', 'lp', 'ft', 'lm', 'ld', 'lt'}

def load_dictionary():
    """Load English dictionary safely"""
    global dictionary

    try:
        import nltk
        nltk.download('words', quiet=True)
        from nltk.corpus import words

        dictionary = set(w.lower() for w in words.words() if len(w) >= 4)

        print(f"✅ Loaded {len(dictionary)} words from NLTK")

    except Exception as e:
        print(f"⚠️ NLTK failed: {e}")

        # SAFE fallback (prevents crash)
        dictionary = {
            "fork", "onward", "playing", "discord", "python",
            "server", "channel", "message", "world", "game"
        }

        print(f"⚠️ Using fallback dictionary ({len(dictionary)} words)")
# ================= HELPER FUNCTIONS =================

def get_guild_id(ctx_or_message):
    """Extract guild ID"""
    if hasattr(ctx_or_message, 'guild') and ctx_or_message.guild:
        return str(ctx_or_message.guild.id)
    return "dm"

def ensure_guild_data(data_dict, guild_id):
    """Ensure guild exists"""
    guild_id = str(guild_id)
    if guild_id not in data_dict:
        data_dict[guild_id] = {}
    return data_dict[guild_id]

def get_server_channels(guild_id):
    """Get server config"""
    guild_id = str(guild_id)
    if guild_id in servers:
        return servers[guild_id]
    return None

def init_game_state(guild_id):
    """Initialize game state"""
    guild_id = str(guild_id)
    if guild_id not in game_states:
        game_states[guild_id] = {
            'last_word': None,
            'last_user': None,
            'used_words': set()
        }

def is_valid_word(word):
    """Check if word is valid"""
    if not word.isalpha():
        return False
    if len(word) < 4:
        return False
    if word not in dictionary:
        return False
    return True

def has_bad_ending(word):
    """Check if word ends with bad ending"""
    for bad_ending in BAD_ENDINGS:
        if word.endswith(bad_ending):
            return True
    return False

def get_next_words(prefix):
    """Get words starting with prefix"""
    return [word for word in dictionary if word.startswith(prefix)]

def find_valid_words(last_two_letters, used_words):
    """Find valid words"""
    candidates = get_next_words(last_two_letters)
    candidates = [w for w in candidates if w not in used_words]
    
    if candidates:
        return candidates, last_two_letters
    
    fallback = get_next_words(last_two_letters[-1:])
    fallback = [w for w in fallback if w not in used_words]
    
    return fallback, last_two_letters[-1:]

def get_hint_word(last_word, used_words):
    """Get hint word"""
    if not last_word:
        return random.choice(list(dictionary))
    
    last_two = last_word[-2:]
    words, _ = find_valid_words(last_two, used_words)
    
    if words:
        return random.choice(words)
    return None

# ================= COINS (GUILD-ISOLATED) =================

def add_coins(guild_id, user_id, amount):
    """Add coins"""
    guild_id = str(guild_id)
    user_id = str(user_id)
    
    guild_data = ensure_guild_data(coins_data, guild_id)
    guild_data[user_id] = guild_data.get(user_id, 0) + amount
    save_coins_data(coins_data)
    return guild_data[user_id]

def remove_coins(guild_id, user_id, amount):
    """Remove coins"""
    guild_id = str(guild_id)
    user_id = str(user_id)
    
    guild_data = ensure_guild_data(coins_data, guild_id)
    current = guild_data.get(user_id, 0)
    
    if current >= amount:
        guild_data[user_id] = current - amount
        save_coins_data(coins_data)
        return True
    return False

def get_user_coins(guild_id, user_id):
    """Get user coins"""
    guild_id = str(guild_id)
    user_id = str(user_id)
    
    guild_data = ensure_guild_data(coins_data, guild_id)
    return guild_data.get(user_id, 0)

def has_claimed_daily(guild_id, user_id):
    """Check if claimed daily"""
    guild_id = str(guild_id)
    user_id = str(user_id)
    daily_key = f"{guild_id}_{user_id}"
    
    if daily_key not in daily_claims:
        return False
    
    last_claim_time = datetime.fromisoformat(daily_claims[daily_key])
    return datetime.now() - last_claim_time < timedelta(hours=24)

def get_remaining_daily_time(guild_id, user_id):
    """Get remaining daily time"""
    guild_id = str(guild_id)
    user_id = str(user_id)
    daily_key = f"{guild_id}_{user_id}"
    
    if daily_key not in daily_claims:
        return None
    
    last_claim_time = datetime.fromisoformat(daily_claims[daily_key])
    next_claim_time = last_claim_time + timedelta(hours=24)
    remaining = next_claim_time - datetime.now()
    
    hours = remaining.seconds // 3600
    minutes = (remaining.seconds % 3600) // 60
    
    return f"{hours}h {minutes}m"

def claim_daily(guild_id, user_id):
    """Claim daily reward"""
    guild_id = str(guild_id)
    user_id = str(user_id)
    daily_key = f"{guild_id}_{user_id}"
    
    daily_claims[daily_key] = datetime.now().isoformat()
    save_daily(daily_claims)
    add_coins(guild_id, user_id, 25)

# ================= LEADERBOARD (GUILD-ISOLATED) =================

def add_leaderboard_point(guild_id, user_id):
    """Add leaderboard point"""
    guild_id = str(guild_id)
    user_id = str(user_id)
    
    guild_data = ensure_guild_data(leaderboard, guild_id)
    guild_data[user_id] = guild_data.get(user_id, 0) + 1
    save_leaderboard(leaderboard)
    return guild_data[user_id]

# ================= EVENTS =================

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    print(f"📚 Dictionary loaded with {len(dictionary)} words")
    print(f"🔒 Guild isolation: ENABLED")

@bot.event
async def on_guild_join(guild):
    """When bot joins a server"""
    try:
        existing_role = discord.utils.get(guild.roles, name="KalaOwner")
        
        if not existing_role:
            role = await guild.create_role(name="KalaOwner", color=discord.Color.gold())
            print(f"✅ Created KalaOwner role in {guild.name}")
        else:
            role = existing_role

        await guild.owner.add_roles(role)
        print(f"✅ Gave KalaOwner to {guild.owner} in {guild.name}")
    except Exception as e:
        print(f"❌ Error setting up roles: {e}")

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors silently"""
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        return
    # Ignore other errors silently to prevent spam

@bot.event
async def on_message(message):
    global leaderboard, coins_data

    if message.author.bot:
        return

    guild_id = get_guild_id(message)
    server_config = get_server_channels(guild_id)

    # Handle commands
    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    # No server config, ignore
    if not server_config:
        return

    # Ignore messages in commands channel
    if message.channel.id == server_config["commands"]:
        try:
            await message.delete()
        except:
            pass
        return

    # Coin earning in general chat
    if message.channel.id == server_config["general"]:
        if message.content.strip():
            add_coins(guild_id, message.author.id, 1)
        return

    # Only process game messages
    if message.channel.id != server_config["game"]:
        return

    # DELETE ALL MESSAGES STARTING WITH ! (commands in game channel)
    if message.content.startswith("!"):
        try:
            await message.delete()
        except:
            pass
        return

    init_game_state(guild_id)
    state = game_states[guild_id]

    word = message.content.lower().strip()

    # Validate word
    if not is_valid_word(word):
        embed = discord.Embed(
            title="❌ Invalid Word",
            description=f"**{word}** is not a valid English word.",
            color=discord.Color.red()
        )
        embed.set_footer(text="Made by Fluxstep")
        try:
            await message.author.send(embed=embed)
        except:
            pass
        await message.delete()
        return

    # Check bad endings
    if has_bad_ending(word):
        embed = discord.Embed(
            title="❌ Invalid Ending",
            description=f"**{word}** cannot be used because its ending has no valid continuations.",
            color=discord.Color.red()
        )
        embed.set_footer(text="Made by Fluxstep")
        try:
            await message.author.send(embed=embed)
        except:
            pass
        await message.delete()
        return

    # Check same player twice
    if state['last_user'] == message.author.id:
        embed = discord.Embed(
            title="❌ Same Player Twice",
            description="You can't play twice in a row!",
            color=discord.Color.red()
        )
        embed.set_footer(text="Made by Fluxstep")
        try:
            await message.author.send(embed=embed)
        except:
            pass
        await message.delete()
        return

    # Check word already used
    if word in state['used_words']:
        embed = discord.Embed(
            title="❌ Word Already Used",
            description=f"**{word}** has already been played!",
            color=discord.Color.red()
        )
        embed.set_footer(text="Made by Fluxstep")
        try:
            await message.author.send(embed=embed)
        except:
            pass
        await message.delete()
        return

    # Check chain rule
    if state['last_word']:
        last_two = state['last_word'][-2:]
        
        if word.startswith(last_two):
            chain_match = True
        elif word.startswith(state['last_word'][-1:]):
            chain_match = True
        else:
            chain_match = False

        if not chain_match:
            embed = discord.Embed(
                title="❌ Chain Rule Broken",
                description=f"**{word}** must start with **{last_two}**",
                color=discord.Color.red()
            )
            embed.set_footer(text="Made by Fluxstep")
            try:
                await message.author.send(embed=embed)
            except:
                pass
            await message.delete()
            return

    # Accept word
    state['last_word'] = word
    state['last_user'] = message.author.id
    state['used_words'].add(word)

    points = add_leaderboard_point(guild_id, message.author.id)
    add_coins(guild_id, message.author.id, 1)

    embed = discord.Embed(
        title="✅ Word Accepted",
        description=f"{message.author.mention} played **{word}**",
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Points: {points} | Earned: +1 💰")
    
    try:
        confirmation = await message.channel.send(embed=embed)
        await confirmation.delete(delay=10)
    except:
        pass

# ================= SETUP COMMAND (PREFIX) =================

@bot.command()
async def setup(ctx):
    """Setup Kaladont for this server [KalaOwner only]"""
    # Check permissions
    if ctx.author != ctx.guild.owner:
        kala_owner_role = discord.utils.get(ctx.guild.roles, name="KalaOwner")
        if not kala_owner_role or kala_owner_role not in ctx.author.roles:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="Only KalaOwner can use this command.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Made by Fluxstep")
            try:
                await ctx.author.send(embed=embed)
            except:
                pass
            await ctx.message.delete()
            return

    # Start setup session
    user_id = ctx.author.id
    guild_id = str(ctx.guild.id)

    setup_sessions[user_id] = {
        "guild_id": guild_id,
        "step": 1,
        "data": {}
    }

    embed = discord.Embed(
        title="🎮 Kaladont Setup - Step 1/3",
        description="Please send the **General Chat Channel ID**\n\nHow to get it:\n1. Right-click the channel\n2. Click 'Copy Channel ID'",
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Made by Fluxstep")

    try:
        await ctx.author.send(embed=embed)
    except:
        pass

    await ctx.message.delete()

    # Wait for response
    def check(m):
        return m.author == ctx.author and m.guild is None

    try:
        # Step 1: General Channel
        msg = await bot.wait_for("message", check=check, timeout=300)
        try:
            general_id = int(msg.content)
            if not ctx.guild.get_channel(general_id):
                embed = discord.Embed(
                    title="❌ Invalid Channel",
                    description="That channel doesn't exist in this server.",
                    color=discord.Color.red()
                )
                embed.set_footer(text="Made by Fluxstep")
                await ctx.author.send(embed=embed)
                del setup_sessions[user_id]
                return
        except ValueError:
            embed = discord.Embed(
                title="❌ Invalid Input",
                description="Please send a valid channel ID (numbers only).",
                color=discord.Color.red()
            )
            embed.set_footer(text="Made by Fluxstep")
            await ctx.author.send(embed=embed)
            del setup_sessions[user_id]
            return

        setup_sessions[user_id]["data"]["general"] = general_id

        # Step 2: Commands Channel
        embed = discord.Embed(
            title="🎮 Kaladont Setup - Step 2/3",
            description="Please send the **Commands Channel ID**",
            color=discord.Color.blurple()
        )
        embed.set_footer(text="Made by Fluxstep")
        await ctx.author.send(embed=embed)

        msg = await bot.wait_for("message", check=check, timeout=300)
        try:
            commands_id = int(msg.content)
            if not ctx.guild.get_channel(commands_id):
                embed = discord.Embed(
                    title="❌ Invalid Channel",
                    description="That channel doesn't exist in this server.",
                    color=discord.Color.red()
                )
                embed.set_footer(text="Made by Fluxstep")
                await ctx.author.send(embed=embed)
                del setup_sessions[user_id]
                return
        except ValueError:
            embed = discord.Embed(
                title="❌ Invalid Input",
                description="Please send a valid channel ID (numbers only).",
                color=discord.Color.red()
            )
            embed.set_footer(text="Made by Fluxstep")
            await ctx.author.send(embed=embed)
            del setup_sessions[user_id]
            return

        setup_sessions[user_id]["data"]["commands"] = commands_id

        # Step 3: Game Channel
        embed = discord.Embed(
            title="🎮 Kaladont Setup - Step 3/3",
            description="Please send the **Game Channel ID**",
            color=discord.Color.blurple()
        )
        embed.set_footer(text="Made by Fluxstep")
        await ctx.author.send(embed=embed)

        msg = await bot.wait_for("message", check=check, timeout=300)
        try:
            game_id = int(msg.content)
            if not ctx.guild.get_channel(game_id):
                embed = discord.Embed(
                    title="❌ Invalid Channel",
                    description="That channel doesn't exist in this server.",
                    color=discord.Color.red()
                )
                embed.set_footer(text="Made by Fluxstep")
                await ctx.author.send(embed=embed)
                del setup_sessions[user_id]
                return
        except ValueError:
            embed = discord.Embed(
                title="❌ Invalid Input",
                description="Please send a valid channel ID (numbers only).",
                color=discord.Color.red()
            )
            embed.set_footer(text="Made by Fluxstep")
            await ctx.author.send(embed=embed)
            del setup_sessions[user_id]
            return

        setup_sessions[user_id]["data"]["game"] = game_id

        # Save configuration
        servers[guild_id] = {
            "general": general_id,
            "commands": commands_id,
            "game": game_id
        }
        save_servers(servers)

        # Confirmation
        general_channel = ctx.guild.get_channel(general_id)
        commands_channel = ctx.guild.get_channel(commands_id)
        game_channel = ctx.guild.get_channel(game_id)

        embed = discord.Embed(
            title="✅ Setup Completed!",
            description="Kaladont is ready to play!",
            color=discord.Color.green()
        )
        embed.add_field(name="General Chat", value=general_channel.mention, inline=False)
        embed.add_field(name="Commands", value=commands_channel.mention, inline=False)
        embed.add_field(name="Game", value=game_channel.mention, inline=False)
        embed.set_footer(text="Made by Fluxstep")
        await ctx.author.send(embed=embed)

        # Send public message in game channel
        game_embed = discord.Embed(
            title="🎮 Kaladont has started!",
            description="Start with any valid word with at least 4 letters.\n\nNext word must start with the last 2 letters of the previous word.",
            color=discord.Color.blurple()
        )
        game_embed.set_footer(text="Made by Fluxstep")
        await game_channel.send(embed=game_embed)

        del setup_sessions[user_id]

    except asyncio.TimeoutError:
        embed = discord.Embed(
            title="⏰ Setup Timeout",
            description="Setup took too long. Please try again.",
            color=discord.Color.orange()
        )
        embed.set_footer(text="Made by Fluxstep")
        await ctx.author.send(embed=embed)
        if user_id in setup_sessions:
            del setup_sessions[user_id]

# ================= COMMANDS =================

@bot.command()
async def reset(ctx):
    """Reset the game"""
    guild_id = get_guild_id(ctx)
    server_config = get_server_channels(guild_id)

    if not server_config or ctx.channel.id != server_config["game"]:
        await ctx.message.delete()
        return

    init_game_state(guild_id)
    state = game_states[guild_id]

    state['last_word'] = None
    state['last_user'] = None
    state['used_words'].clear()

    embed = discord.Embed(
        title="✅ Game Reset",
        description="Kaladont has been reset!",
        color=discord.Color.green()
    )
    embed.set_footer(text="Made by Fluxstep")

    msg = await ctx.channel.send(embed=embed)
    await ctx.message.delete()
    await msg.delete(delay=5)

@bot.command()
async def stats(ctx, member: discord.Member = None):
    """Show stats"""
    guild_id = get_guild_id(ctx)
    server_config = get_server_channels(guild_id)

    if not server_config or ctx.channel.id != server_config["commands"]:
        await ctx.message.delete()
        return

    if member is None:
        member = ctx.author

    guild_leaderboard = ensure_guild_data(leaderboard, guild_id)
    count = guild_leaderboard.get(str(member.id), 0)
    rank = 1

    for uid, points in sorted(guild_leaderboard.items(), key=lambda x: x[1], reverse=True):
        if uid == str(member.id):
            break
        rank += 1

    embed = discord.Embed(
        title="📊 Player Stats",
        description=f"{member.mention}",
        color=discord.Color.blurple()
    )
    embed.add_field(name="Valid Words", value=f"**{count}**", inline=True)
    embed.add_field(name="Rank", value=f"**#{rank}**", inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="Made by Fluxstep")

    await ctx.send(embed=embed)

@bot.command()
async def wallet(ctx):
    """Check coins"""
    guild_id = get_guild_id(ctx)
    server_config = get_server_channels(guild_id)

    if not server_config or ctx.channel.id != server_config["commands"]:
        await ctx.message.delete()
        return

    user_coins = get_user_coins(guild_id, ctx.author.id)

    embed = discord.Embed(
        title="💰 Wallet",
        description=f"{ctx.author.mention}",
        color=discord.Color.gold()
    )
    embed.add_field(name="Coins", value=f"**{user_coins}**", inline=False)
    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    embed.set_footer(text="Made by Fluxstep")

    await ctx.send(embed=embed)

@bot.command()
async def daily(ctx):
    """Claim daily reward"""
    guild_id = get_guild_id(ctx)
    server_config = get_server_channels(guild_id)

    if not server_config or ctx.channel.id != server_config["commands"]:
        await ctx.message.delete()
        return

    if has_claimed_daily(guild_id, ctx.author.id):
        remaining = get_remaining_daily_time(guild_id, ctx.author.id)
        embed = discord.Embed(
            title="⏳ Already Claimed",
            description=f"Time remaining: **{remaining}**",
            color=discord.Color.orange()
        )
        embed.set_footer(text="Made by Fluxstep")
        await ctx.send(embed=embed, ephemeral=True)
        return

    claim_daily(guild_id, ctx.author.id)

    embed = discord.Embed(
        title="✅ Daily Reward Claimed",
        description=f"{ctx.author.mention}\n\n**+25 💰**",
        color=discord.Color.green()
    )
    embed.set_footer(text="Made by Fluxstep")

    await ctx.send(embed=embed, ephemeral=True)

@bot.command()
async def shop(ctx):
    """View shop"""
    guild_id = get_guild_id(ctx)
    server_config = get_server_channels(guild_id)

    if not server_config or ctx.channel.id != server_config["commands"]:
        await ctx.message.delete()
        return

    embed = discord.Embed(
        title="🛍️ Kaladont Shop",
        description="Purchase items with your coins!",
        color=discord.Color.gold()
    )

    embed.add_field(
        name="💡 Hint",
        value="Get a suggestion for the next word\n**Cost: 15 💰**\n`!hint`",
        inline=False
    )

    embed.add_field(
        name="⏭️ Skip",
        value="Skip impossible endings\n**Cost: 30 💰**\n`!skip`",
        inline=False
    )

    embed.set_footer(text="Made by Fluxstep")

    await ctx.send(embed=embed)

@bot.command()
async def hint(ctx):
    """Get a hint"""
    guild_id = get_guild_id(ctx)
    server_config = get_server_channels(guild_id)

    if not server_config or ctx.channel.id != server_config["game"]:
        await ctx.message.delete()
        return

    user_coins = get_user_coins(guild_id, ctx.author.id)

    if user_coins < 15:
        embed = discord.Embed(
            title="❌ Not Enough Coins",
            description=f"You need **15 💰** to buy a hint.\n\nYour balance: **{user_coins} 💰**",
            color=discord.Color.red()
        )
        embed.set_footer(text="Made by Fluxstep")
        try:
            await ctx.author.send(embed=embed)
        except:
            pass
        await ctx.message.delete()
        return

    remove_coins(guild_id, ctx.author.id, 15)

    init_game_state(guild_id)
    state = game_states[guild_id]
    hint_word = get_hint_word(state['last_word'], state['used_words'])

    if state['last_word']:
        last_two = state['last_word'][-2:]
        suggested = hint_word if hint_word else "No words available"
        
        embed = discord.Embed(
            title="💡 Hint",
            color=discord.Color.yellow()
        )
        embed.add_field(name="Required", value=f"**{last_two}** (or fallback: **{state['last_word'][-1:]}**)", inline=False)
        embed.add_field(name="Suggested Word", value=f"**{suggested}**", inline=False)
        embed.add_field(name="Cost", value="**-15 💰**", inline=False)
    else:
        suggested = hint_word if hint_word else "..."
        embed = discord.Embed(
            title="💡 Hint",
            color=discord.Color.yellow()
        )
        embed.add_field(name="Description", value="Start the game with any 4+ letter word!", inline=False)
        embed.add_field(name="Suggested Word", value=f"**{suggested}**", inline=False)
        embed.add_field(name="Cost", value="**-15 💰**", inline=False)

    embed.set_footer(text="Made by Fluxstep")
    
    try:
        await ctx.author.send(embed=embed)
    except:
        pass
    await ctx.message.delete()

@bot.command()
async def skip(ctx):
    """Skip chain"""
    guild_id = get_guild_id(ctx)
    server_config = get_server_channels(guild_id)

    if not server_config or ctx.channel.id != server_config["game"]:
        await ctx.message.delete()
        return

    user_coins = get_user_coins(guild_id, ctx.author.id)

    if user_coins < 30:
        embed = discord.Embed(
            title="❌ Not Enough Coins",
            description=f"You need **30 💰** to skip.\n\nYour balance: **{user_coins} 💰**",
            color=discord.Color.red()
        )
        embed.set_footer(text="Made by Fluxstep")
        try:
            await ctx.author.send(embed=embed)
        except:
            pass
        await ctx.message.delete()
        return

    remove_coins(guild_id, ctx.author.id, 30)

    init_game_state(guild_id)
    state = game_states[guild_id]

    if not state['last_word']:
        embed = discord.Embed(
            title="⚠️ No Word to Skip",
            description="The game hasn't started yet!",
            color=discord.Color.orange()
        )
        embed.set_footer(text="Made by Fluxstep")
        try:
            await ctx.author.send(embed=embed)
        except:
            pass
        await ctx.message.delete()
        return

    old_ending = state['last_word'][-2:]
    state['last_word'] = None
    state['last_user'] = None

    embed = discord.Embed(
        title="⏭️ Chain Skipped",
        color=discord.Color.orange()
    )
    embed.add_field(name="Previous Ending", value=f"**{old_ending}**", inline=False)
    embed.add_field(name="Status", value="Chain requirement has been cleared.", inline=False)
    embed.add_field(name="Cost", value="**-30 💰**", inline=False)
    embed.set_footer(text="Made by Fluxstep")

    try:
        await ctx.author.send(embed=embed)
    except:
        pass
    await ctx.message.delete()

@bot.command(name="help")
async def help_command(ctx):
    """Show help"""
    guild_id = get_guild_id(ctx)
    server_config = get_server_channels(guild_id)

    if not server_config or ctx.channel.id != server_config["commands"]:
        await ctx.message.delete()
        return

    embed = discord.Embed(
        title="📖 Kaladont Help",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="🎮 How to Play",
        value="• Type a 4+ letter English word in the game channel\n"
              "• Next word must start with the last 2 letters\n"
              "• If no valid words exist, fallback to last 1 letter\n"
              "• Can't play twice in a row\n"
              "• Can't repeat words\n"
              "• Earn +1 💰 per valid word",
        inline=False
    )

    embed.add_field(
        name="💰 Coin System",
        value="• Earn **+1 💰** per valid word in game channel\n"
              "• Earn **+1 💰** per message in general chat\n"
              "• Earn **+25 💰** daily with `!daily`",
        inline=False
    )

    embed.add_field(
        name="⚙️ Commands (COMMANDS CHANNEL)",
        value="• `!help` - Show this menu\n"
              "• `!top` - View leaderboard\n"
              "• `!stats [member]` - Show player stats\n"
              "• `!wallet` - Check your coins\n"
              "• `!daily` - Claim daily 25 coins\n"
              "• `!shop` - View shop",
        inline=False
    )

    embed.add_field(
        name="🎯 Game Commands (GAME CHANNEL)",
        value="• `!hint` - Buy a hint (**15 💰**)\n"
              "• `!skip` - Skip chain (**30 💰**)\n"
              "• `!reset` - Reset the game",
        inline=False
    )

    embed.set_footer(text="Made by Fluxstep")
    await ctx.send(embed=embed)

@bot.command()
async def top(ctx):
    """Show leaderboard"""
    guild_id = get_guild_id(ctx)
    server_config = get_server_channels(guild_id)

    if not server_config or ctx.channel.id != server_config["commands"]:
        await ctx.message.delete()
        return

    guild_leaderboard = ensure_guild_data(leaderboard, guild_id)

    if not guild_leaderboard:
        embed = discord.Embed(
            title="🏆 Kaladont Leaderboard",
            description="Nobody has played yet!",
            color=discord.Color.gold()
        )
        embed.set_footer(text="Made by Fluxstep")
        await ctx.send(embed=embed)
        return

    sorted_scores = sorted(guild_leaderboard.items(), key=lambda x: x[1], reverse=True)

    medals = ["🥇", "🥈", "🥉"]
    desc = ""

    for i, (uid, count) in enumerate(sorted_scores[:10]):
        rank = medals[i] if i < 3 else f"#{i+1}"
        user_coins = get_user_coins(guild_id, int(uid))
        desc += f"{rank} <@{uid}> — **{count}** words • **{user_coins} 💰**\n"

    embed = discord.Embed(
        title="🏆 Kaladont Leaderboard",
        description=desc,
        color=discord.Color.gold()
    )
    embed.set_footer(text="Made by Fluxstep | Per-Server Leaderboard")

    await ctx.send(embed=embed)

# ================= RUN BOT =================

import asyncio
bot.run(TOKEN)
