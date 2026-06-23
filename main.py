import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timedelta
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

servers = load_servers()
leaderboard = load_leaderboard()
coins_data = load_coins_data()
daily_claims = load_daily()

# ================= GAME STATE =================

game_states = {}

# ================= DICTIONARY & WORD VALIDATION =================

# Words that shouldn't be used (no valid continuations)
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
    except:
        print("⚠️ Using fallback dictionary")
        pass

    fallback_words = {
        'able', 'about', 'above', 'abuse', 'access', 'acid', 'across', 'acre', 'act', 'action',
        'active', 'actor', 'adapt', 'added', 'admit', 'adopt', 'adult', 'advance', 'after',
        'again', 'against', 'agent', 'agree', 'ahead', 'alarm', 'album', 'alert', 'alien',
        'align', 'alike', 'alive', 'allow', 'almost', 'alone', 'along', 'alter', 'always',
        'amateur', 'amazing', 'among', 'amount', 'amuse', 'angel', 'anger', 'angle', 'angry',
        'animal', 'ankle', 'announce', 'annoy', 'annual', 'answer', 'antenna', 'antic',
        'anvil', 'anxiety', 'apart', 'apology', 'apparent', 'appeal', 'appear', 'appetite',
        'apple', 'apply', 'appoint', 'approve', 'april', 'apron', 'arch', 'arctic', 'ardent',
        'ardor', 'arena', 'argue', 'argument', 'arise', 'army', 'aroma', 'arose', 'around',
        'arrange', 'array', 'arrest', 'arrival', 'arrive', 'arrow', 'arsenal', 'art', 'artery',
        'article', 'artist', 'artistic', 'ascend', 'ascent', 'ash', 'ashamed', 'ashen', 'aside',
        'asked', 'asleep', 'aspect', 'aspire', 'assail', 'assault', 'assemble', 'assent', 'assert',
        'assess', 'asset', 'assign', 'assist', 'associate', 'assume', 'assurance', 'assure',
        'astern', 'astonish', 'astound', 'astray', 'astronaut', 'asylum', 'atom', 'atomic',
        'atone', 'atrocious', 'attach', 'attack', 'attain', 'attempt', 'attend', 'attention',
        'attest', 'attic', 'attire', 'attitude', 'attorney', 'attract', 'attraction', 'attractive',
        'attribute', 'auction', 'audacious', 'audience', 'audio', 'audit', 'audition', 'august',
        'aunt', 'austere', 'authentic', 'author', 'authority', 'authorize', 'autumn', 'auxiliary',
        'avail', 'available', 'avalanche', 'avarice', 'avenue', 'average', 'averse', 'avert',
        'avoid', 'await', 'awake', 'awaken', 'award', 'aware', 'away', 'awe', 'awesome', 'awful',
        'awhile', 'awkward', 'awning', 'awoke', 'awry', 'axiom', 'axis', 'axle', 'axon', 'aye',
        'azure', 'baby', 'bachelor', 'back', 'backbone', 'background', 'backing', 'backup',
        'backward', 'bacon', 'bacteria', 'badge', 'badger', 'badly', 'baffle', 'baggage', 'baggy',
        'bail', 'bait', 'bake', 'baker', 'bakery', 'balance', 'balcony', 'bald', 'baldly', 'bale',
        'ball', 'ballad', 'ballast', 'ballet', 'balloon', 'ballot', 'ballroom', 'balm', 'balmy',
        'band', 'bandage', 'bandit', 'bane', 'bang', 'bangle', 'banish', 'banister', 'bank',
        'banker', 'banking', 'bankrupt', 'banner', 'banquet', 'banter', 'baptism', 'baptize',
        'bare', 'barely', 'bargain', 'barge', 'bark', 'barley', 'barn', 'barnacle', 'barometer',
        'baron', 'baroque', 'barracks', 'barrage', 'barrel', 'barren', 'barricade', 'barrier',
        'barrio', 'barrister', 'bartender', 'barter', 'base', 'baseball', 'basement', 'baseness',
        'bases', 'basic', 'basin', 'basis', 'bask', 'basket', 'basketball', 'bass', 'bassoon',
        'batch', 'bath', 'bathe', 'bathroom', 'bathrobe', 'batik', 'baton', 'battalion', 'batten',
        'batter', 'battery', 'batting', 'battle', 'battlefield', 'battleground', 'battlement',
        'battleship', 'bauble', 'bawdy', 'bawl', 'beach', 'beacon', 'bead', 'beading', 'beady',
        'beak', 'beaker', 'beam', 'bean', 'bear', 'bearable', 'beard', 'bearer', 'bearing',
        'beast', 'beastly', 'beat', 'beaten', 'beater', 'beating', 'beatnik', 'beau', 'beautiful',
        'beautifully', 'beautify', 'beauty', 'beaver', 'became', 'because', 'beck', 'beckon',
        'become', 'becoming', 'bed', 'bedaub', 'bedazzle', 'bedbug', 'bedded', 'bedding', 'bedew',
        'bedfellow', 'bedim', 'bedlam', 'bedpan', 'bedpost', 'bedraggle', 'bedridden', 'bedrock',
        'bedroom', 'bedside', 'bedsore', 'bedspread', 'bedspring', 'bedstead', 'bedtime', 'bee',
        'beech', 'beef', 'beefy', 'beehive', 'beekeeper', 'beekeeping', 'beeswax', 'beet', 'beetle',
        'befall', 'befit', 'befitting', 'befog', 'befool', 'before', 'beforehand', 'befriend',
        'befuddle', 'beg', 'begat', 'beggar', 'beggary', 'begged', 'begin', 'beginner', 'beginning',
        'begone', 'begonia', 'begot', 'begotten', 'begrime', 'begrudge', 'begrudging', 'beguile',
        'beguiling', 'begum', 'begun', 'behalf', 'behave', 'behavior', 'behavioral', 'behead',
        'behemoth', 'behest', 'behind', 'behindhand', 'behold', 'beholder', 'beholden', 'behoove',
        'brand', 'bread', 'break', 'breed', 'brief', 'bring', 'broad', 'broke', 'brown',
        'build', 'buyer', 'cable', 'camel', 'canal', 'candy', 'cargo', 'carry', 'catch',
        'cause', 'chain', 'chair', 'chart', 'chase', 'cheap', 'check', 'chess', 'chest',
        'chief', 'child', 'china', 'chose', 'civil', 'claim', 'class', 'clean', 'clear',
        'click', 'climb', 'clock', 'close', 'cloud', 'coach', 'coast', 'color', 'couch',
        'could', 'count', 'court', 'cover', 'crack', 'craft', 'crash', 'crazy', 'cream',
        'crime', 'cross', 'crowd', 'crown', 'cycle', 'daily', 'dance', 'dealt', 'death',
        'debut', 'delay', 'dense', 'depth', 'diary', 'dirty', 'disco', 'doing', 'doubt',
        'dozen', 'draft', 'drama', 'drawn', 'dream', 'dress', 'dried', 'drink', 'drive',
        'drove', 'drown', 'dying', 'eager', 'eagle', 'early', 'earth', 'eight', 'elite',
        'empty', 'enemy', 'enjoy', 'enter', 'entry', 'equal', 'error', 'event', 'every',
        'exact', 'exist', 'extra', 'faith', 'false', 'fancy', 'fault', 'field', 'fifth',
        'fifty', 'fight', 'final', 'first', 'fixed', 'flame', 'flash', 'fleet', 'floor',
        'fluid', 'focus', 'force', 'forum', 'found', 'frame', 'frank', 'fraud', 'fresh',
        'fried', 'front', 'frost', 'fruit', 'fully', 'funny', 'games', 'gates', 'ghost',
        'giant', 'given', 'glass', 'globe', 'going', 'grace', 'grade', 'grain', 'grand',
        'grant', 'graph', 'grass', 'grave', 'great', 'green', 'gross', 'group', 'grown',
        'guard', 'guess', 'guest', 'guide', 'guilt', 'habit', 'happy', 'harsh', 'heart',
        'heavy', 'hedge', 'hello', 'hence', 'hills', 'hints', 'hired', 'hobby', 'holes',
        'holly', 'homes', 'honey', 'honor', 'horse', 'hotel', 'hours', 'house', 'human',
        'humid', 'hurry', 'ideal', 'ideas', 'image', 'imply', 'index', 'inner', 'input',
        'issue', 'items', 'japan', 'jimmy', 'joins', 'joint', 'judge', 'juice', 'jumps',
        'knife', 'knock', 'known', 'knows', 'label', 'labor', 'lakes', 'large', 'laser',
        'later', 'laugh', 'layer', 'leads', 'lease', 'least', 'leave', 'legal', 'lemon',
        'level', 'lewis', 'light', 'liked', 'likes', 'limit', 'links', 'lions', 'lists',
        'lived', 'lives', 'loads', 'loans', 'lobby', 'local', 'locks', 'lodge', 'logic',
        'loose', 'lords', 'loses', 'loves', 'lower', 'loyal', 'lucky', 'lunch', 'lying',
        'macro', 'magic', 'major', 'maker', 'males', 'march', 'marks', 'match', 'mates',
        'mayor', 'means', 'meant', 'meats', 'media', 'meets', 'menus', 'mercy', 'merge',
        'merit', 'metal', 'meter', 'micro', 'midst', 'might', 'miles', 'mills', 'minds',
        'mines', 'minor', 'minus', 'mixed', 'mixes', 'model', 'modes', 'money', 'month',
        'moral', 'motor', 'mount', 'mouse', 'mouth', 'moved', 'moves', 'movie', 'music',
        'myths', 'names', 'needs', 'nerve', 'never', 'newly', 'nexus', 'nicer', 'night',
        'ninth', 'nodes', 'noise', 'norms', 'north', 'noted', 'notes', 'novel', 'nurse',
        'occur', 'ocean', 'offer', 'often', 'older', 'olive', 'onion', 'onset', 'opens',
        'opera', 'orbit', 'order', 'organ', 'other', 'ought', 'ounce', 'outer', 'owned',
        'owner', 'oxide', 'paced', 'packs', 'pages', 'paint', 'pairs', 'panel', 'panic',
        'pants', 'paper', 'parks', 'parts', 'party', 'patch', 'paths', 'pause', 'peace',
        'pearl', 'peers', 'penny', 'perch', 'peter', 'phase', 'phone', 'photo', 'piano',
        'picks', 'piece', 'pipes', 'pitch', 'pizza', 'place', 'plain', 'plane', 'plans',
        'plant', 'plate', 'plays', 'plaza', 'plots', 'poems', 'poets', 'point', 'poles',
        'polls', 'pools', 'porch', 'ports', 'posed', 'posts', 'pound', 'power', 'press',
        'price', 'pride', 'prime', 'print', 'prior', 'prism', 'prize', 'proof', 'proud',
        'prove', 'prowl', 'prune', 'psalm', 'queen', 'query', 'quest', 'queue', 'quick',
        'quiet', 'quilt', 'quite', 'quote', 'radio', 'raids', 'rails', 'raise', 'ranch',
        'range', 'ranks', 'rapid', 'ratio', 'reach', 'react', 'reads', 'ready', 'realm',
        'rebel', 'refer', 'relax', 'reply', 'rider', 'ridge', 'rifle', 'right', 'rigid',
        'rings', 'risen', 'risks', 'river', 'roads', 'roast', 'robot', 'rocks', 'roger',
        'roles', 'roman', 'roofs', 'rooms', 'roost', 'roots', 'ropes', 'roses', 'rough',
        'round', 'route', 'royal', 'rugby', 'ruins', 'ruled', 'rules', 'rural', 'rusty',
        'sadly', 'safer', 'saint', 'salad', 'sales', 'salon', 'sandy', 'sauce', 'scale',
        'scare', 'scene', 'scent', 'scope', 'score', 'scout', 'screw', 'seals', 'seams',
        'seats', 'seeds', 'seeks', 'seems', 'sells', 'sends', 'sense', 'serve', 'setup',
        'seven', 'shall', 'shame', 'shape', 'share', 'shark', 'sharp', 'shave', 'sheet',
        'shelf', 'shell', 'shift', 'shine', 'shirt', 'shock', 'shoes', 'shoot', 'shops',
        'shore', 'short', 'shots', 'shown', 'shows', 'sight', 'signs', 'silly', 'since',
        'sixth', 'sized', 'sizes', 'skill', 'skins', 'skips', 'skirt', 'skull', 'slain',
        'slant', 'slate', 'sleep', 'slide', 'sling', 'slips', 'slope', 'small', 'smart',
        'smash', 'smell', 'smile', 'smith', 'smoke', 'solid', 'solve', 'songs', 'sorry',
        'sound', 'south', 'space', 'spare', 'spark', 'speak', 'spear', 'speed', 'spell',
        'spend', 'spent', 'spice', 'spike', 'spine', 'spoke', 'spoon', 'sport', 'spots',
        'spray', 'spree', 'staff', 'stage', 'stain', 'stake', 'stale', 'stamp', 'stand',
        'stank', 'start', 'state', 'stays', 'steak', 'steel', 'steep', 'steer', 'stems',
        'stern', 'stick', 'still', 'sting', 'stink', 'stock', 'stone', 'stood', 'stool',
        'store', 'storm', 'story', 'stove', 'strap', 'straw', 'strip', 'stuck', 'study',
        'stuff', 'stump', 'stung', 'style', 'sugar', 'suite', 'suits', 'sunny', 'super',
        'surge', 'sweet', 'swift', 'swims', 'swing', 'swiss', 'sword', 'swore', 'sworn',
        'table', 'taken', 'takes', 'tales', 'talks', 'tanks', 'tapes', 'tasks', 'taste',
        'taxes', 'teach', 'teams', 'tears', 'tease', 'teeth', 'teens', 'tells', 'tempo',
        'tends', 'tense', 'tenth', 'terms', 'texas', 'thank', 'theft', 'their', 'theme',
        'there', 'these', 'thick', 'thing', 'think', 'third', 'those', 'tides', 'tiger',
        'tight', 'tiled', 'tiles', 'timer', 'times', 'tired', 'toast', 'today', 'token',
        'tools', 'tooth', 'topic', 'torch', 'total', 'touch', 'tough', 'tours', 'tower',
        'towns', 'toxic', 'trace', 'track', 'trade', 'trail', 'train', 'trait', 'trash',
        'tread', 'treat', 'trees', 'trend', 'trial', 'tribe', 'trick', 'tried', 'tries',
        'troop', 'truck', 'truly', 'trunk', 'trust', 'truth', 'tubes', 'tulip', 'tumor',
        'turns', 'tusks', 'twice', 'twins', 'twist', 'ultra', 'uncle', 'under', 'unfit',
        'union', 'unite', 'unity', 'until', 'upper', 'upset', 'urban', 'usage', 'users',
        'usual', 'valid', 'value', 'valve', 'vapor', 'vault', 'venue', 'verge', 'verse',
        'video', 'villa', 'virus', 'visit', 'vital', 'vivid', 'vocal', 'voice', 'voter',
        'votes', 'vowed', 'wages', 'wagon', 'waist', 'walks', 'walls', 'wants', 'wards',
        'wares', 'warns', 'waste', 'watch', 'water', 'waves', 'weary', 'weave', 'weeks',
        'weigh', 'weird', 'wells', 'welsh', 'wheat', 'wheel', 'where', 'which', 'while',
        'white', 'whole', 'whose', 'widen', 'wider', 'widow', 'width', 'winds', 'wines',
        'wings', 'wired', 'wires', 'wives', 'woman', 'women', 'woods', 'words', 'works',
        'world', 'worry', 'worse', 'worst', 'worth', 'would', 'wound', 'wrist', 'write',
        'wrong', 'wrote', 'yards', 'years', 'yells', 'yield', 'young', 'yours', 'youth',
        'zebra', 'zones', 'zoned', 'zoom', 'zoomed', 'zooming', 'online', 'playing', 'flower',
        'mountain', 'discord', 'python', 'server', 'channel', 'message', 'player', 'winner',
        'loser', 'heart', 'smile', 'laugh', 'think', 'dream', 'magic', 'power', 'strong',
        'weak', 'smart', 'quick', 'slow', 'fast', 'light', 'dark', 'sunny', 'rainy'
    }

    print(f"✅ Loaded {len(fallback_words)} words from fallback dictionary")
    return fallback_words

dictionary = load_dictionary()

# ================= HELPER FUNCTIONS =================

def get_guild_id(ctx_or_message):
    """Extract guild ID from context or message"""
    if hasattr(ctx_or_message, 'guild') and ctx_or_message.guild:
        return str(ctx_or_message.guild.id)
    return "dm"

def ensure_guild_data(data_dict, guild_id):
    """Ensure guild exists in data structure"""
    guild_id = str(guild_id)
    if guild_id not in data_dict:
        data_dict[guild_id] = {}
    return data_dict[guild_id]

def get_server_channels(guild_id):
    """Get server channel configuration"""
    guild_id = str(guild_id)
    if guild_id in servers:
        return servers[guild_id]
    return None

def init_game_state(guild_id):
    """Initialize game state for a guild"""
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
    """Check if word ends with a bad ending"""
    for bad_ending in BAD_ENDINGS:
        if word.endswith(bad_ending):
            return True
    return False

def get_next_words(prefix):
    """Get all valid words starting with prefix"""
    return [word for word in dictionary if word.startswith(prefix)]

def find_valid_words(last_two_letters, used_words):
    """Find valid words for chain rule"""
    candidates = get_next_words(last_two_letters)
    candidates = [w for w in candidates if w not in used_words]
    
    if candidates:
        return candidates, last_two_letters
    
    fallback = get_next_words(last_two_letters[-1:])
    fallback = [w for w in fallback if w not in used_words]
    
    return fallback, last_two_letters[-1:]

def get_hint_word(last_word, used_words):
    """Get a hint word"""
    if not last_word:
        return random.choice(list(dictionary))
    
    last_two = last_word[-2:]
    words, _ = find_valid_words(last_two, used_words)
    
    if words:
        return random.choice(words)
    return None

# ================= COINS (GUILD-ISOLATED) =================

def add_coins(guild_id, user_id, amount):
    """Add coins to a user"""
    guild_id = str(guild_id)
    user_id = str(user_id)
    
    guild_data = ensure_guild_data(coins_data, guild_id)
    guild_data[user_id] = guild_data.get(user_id, 0) + amount
    save_coins_data(coins_data)
    return guild_data[user_id]

def remove_coins(guild_id, user_id, amount):
    """Remove coins from a user"""
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
    """Get user's coins"""
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
    """Add point to leaderboard"""
    guild_id = str(guild_id)
    user_id = str(user_id)
    
    guild_data = ensure_guild_data(leaderboard, guild_id)
    guild_data[user_id] = guild_data.get(user_id, 0) + 1
    save_leaderboard(leaderboard)
    return guild_data[user_id]

# ================= SETUP VIEW =================

class SetupModal(discord.ui.Modal, title="Kaladont Setup"):
    general = discord.ui.TextInput(label="General Chat Channel ID", placeholder="123456789")
    commands = discord.ui.TextInput(label="Commands Channel ID", placeholder="123456789")
    game = discord.ui.TextInput(label="Game Channel ID", placeholder="123456789")

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        
        try:
            general_id = int(self.general.value)
            commands_id = int(self.commands.value)
            game_id = int(self.game.value)
        except:
            embed = discord.Embed(
                title="❌ Invalid Channel ID",
                description="All channel IDs must be numbers.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Made by Fluxstep")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Verify channels exist
        guild = interaction.guild
        general_channel = guild.get_channel(general_id)
        commands_channel = guild.get_channel(commands_id)
        game_channel = guild.get_channel(game_id)

        if not general_channel or not commands_channel or not game_channel:
            embed = discord.Embed(
                title="❌ Setup Failed",
                description="One or more channels don't exist in this server.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Made by Fluxstep")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Save configuration
        servers[guild_id] = {
            "general": general_id,
            "commands": commands_id,
            "game": game_id
        }
        save_servers(servers)

        # Send done view
        view = DoneButton(interaction, general_channel, commands_channel, game_channel)
        embed = discord.Embed(
            title="✅ Configuration Preview",
            description="Please confirm these channels:",
            color=discord.Color.green()
        )
        embed.add_field(name="General Chat", value=general_channel.mention, inline=False)
        embed.add_field(name="Commands", value=commands_channel.mention, inline=False)
        embed.add_field(name="Game", value=game_channel.mention, inline=False)
        embed.set_footer(text="Made by Fluxstep")

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class DoneButton(discord.ui.View):
    def __init__(self, interaction, general, commands, game):
        super().__init__()
        self.interaction = interaction
        self.general = general
        self.commands = commands
        self.game = game

    @discord.ui.button(label="✅ Done", style=discord.ButtonStyle.green)
    async def done_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="✅ Setup Completed",
            description="Kaladont is ready to play!",
            color=discord.Color.green()
        )
        embed.add_field(name="General Chat", value=self.general.mention, inline=False)
        embed.add_field(name="Commands", value=self.commands.mention, inline=False)
        embed.add_field(name="Game", value=self.game.mention, inline=False)
        embed.set_footer(text="Made by Fluxstep")

        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Send public message in game channel
        game_embed = discord.Embed(
            title="🎮 Kaladont has started!",
            description="Start with any valid word with at least 4 letters.\n\nNext word must start with the last 2 letters of the previous word.",
            color=discord.Color.blurple()
        )
        game_embed.set_footer(text="Made by Fluxstep")

        await self.game.send(embed=game_embed)

# ================= EVENTS =================

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    print(f"📚 Dictionary loaded with {len(dictionary)} words")
    print(f"🔒 Guild isolation: ENABLED")

@bot.event
async def on_guild_join(guild):
    """When bot joins a new server"""
    try:
        # Create KalaOwner role if it doesn't exist
        existing_role = discord.utils.get(guild.roles, name="KalaOwner")
        
        if not existing_role:
            role = await guild.create_role(name="KalaOwner", color=discord.Color.gold())
            print(f"✅ Created KalaOwner role in {guild.name}")
        else:
            role = existing_role
            print(f"✅ KalaOwner role already exists in {guild.name}")

        # Give role to owner
        await guild.owner.add_roles(role)
        print(f"✅ Gave KalaOwner to {guild.owner} in {guild.name}")
    except Exception as e:
        print(f"❌ Error setting up roles: {e}")

@bot.event
async def on_message(message):
    global leaderboard, coins_data

    if message.author.bot:
        return

    guild_id = get_guild_id(message)
    server_config = get_server_channels(guild_id)

    # If server not setup, process commands anyway
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
        await message.author.send(embed=embed)
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
        await message.author.send(embed=embed)
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
        await message.author.send(embed=embed)
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
        await message.author.send(embed=embed)
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
            await message.author.send(embed=embed)
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

# ================= COMMANDS =================

@bot.command()
async def setup(ctx):
    """Setup Kaladont for this server [KalaOwner only]"""
    # Check if user is owner or has KalaOwner role
    if ctx.author != ctx.guild.owner:
        kala_owner_role = discord.utils.get(ctx.guild.roles, name="KalaOwner")
        if not kala_owner_role or kala_owner_role not in ctx.author.roles:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="Only KalaOwner can use this command.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Made by Fluxstep")
            await ctx.send(embed=embed, ephemeral=True)
            return

    modal = SetupModal()
    await ctx.interaction.response.send_modal(modal)

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
        await ctx.author.send(embed=embed)
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
    
    await ctx.author.send(embed=embed)
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
        await ctx.author.send(embed=embed)
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
        await ctx.author.send(embed=embed)
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

    await ctx.author.send(embed=embed)
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

bot.run(TOKEN)
