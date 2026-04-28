import pygame
import sys
import random
import json
import os
import math
import time


# ===============================================================================================

# GHI CHÚ CHO GIẢNG VIÊN:l
# - File này gồm 2 phần chính:
#   (1) PHẦN GAME HOÀN CHỈNH CHẠY ĐƯỢC: có sử dụng AI hỗ trợ ghép UI, scene, chuyển logic sang pygame
#   (2) PHẦN CODE GỐC SINH VIÊN: giữ nguyên ở CUỐI FILE, không chỉnh sửa, làm minh chứng phần tự làm
#
# - AI KHÔNG sinh ra toàn bộ chương trình từ đầu.
# - Sinh viên:
#   + Tự xây dựng: luật chơi Wordle, xử lý dữ liệu, thuật toán check, save/load, rank, cắt chỉnh sửa, tố chức lưu sound, png
#   + AI hỗ trợ: ghép scene, chuẩn hóa UI, kết nối các phần thành game hoàn chỉnh
# ===============================================================================================


"""
Cơ chế tính điểm
base:   Tiếng Việt 120
        Tiếng Anh 100
        Phép toán 90
classic (infinity time): không tính điểm, hệ số x0
90s:                  x1.2
120s:                  x1
bật timeperguess:     x1.2
time bonus: 0.15 x (t_left/t_limit)^3
bật hard mode:        x1.4 
hard mode: cố định từ xanh, bắt buộc có từ vàng
về phép toán:
cố định dấu =
chỉ có + - *, không / hay ()
số nguyên không âm
vế trái bắt buộc phải có dấu, phép tính phải đúng không được bừa
"""

#_______________________________________________________________________________________________
#                   PHẦN GAME HOÀN CHỈNH CHƠI ĐƯỢC (sử dụng AI để ghép)
#_______________________________________________________________________________________________

# -----------------------------------------------------------------------------------------------
# CHỨC NĂNG: MÃ HÓA DỮ LIỆU SAVE / RANK
# - Sinh viên tự thiết kế cơ chế XOR đơn giản để tránh sửa file JSON trực tiếp
# - Không dùng thư viện mã hóa ngoài
# - Mục đích: bảo vệ điểm số và dữ liệu người chơi
# -----------------------------------------------------------------------------------------------

_KEY = 101  

def save_secure_json(path, obj):
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    encrypted = bytes(b ^ _KEY for b in data)
    with open(path, "wb") as f:
        f.write(encrypted)

def load_secure_json(path, default=None):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "rb") as f:
            encrypted = f.read()
        decrypted = bytes(b ^ _KEY for b in encrypted)
        return json.loads(decrypted.decode("utf-8"))
    except:
        return default
    
# -----------------------------------------------------------------------------------------------
# CONFIG HỆ THỐNG & KHỞI TẠO PYGAME
# - Thiết lập màn hình, FPS, màu sắc chuẩn cho toàn bộ game
# - Đây là phần cấu hình nền tảng để các scene hoạt động thống nhất
# -----------------------------------------------------------------------------------------------

pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 960, 540
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("WORDLE NIGHT - ULTIMATE")
CLOCK = pygame.time.Clock()

# Colors
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_BG_DARK = (18, 18, 19)
COLOR_RED_WRONG = (200, 50, 50)
COLOR_YELLOW = (200, 180, 50)
COLOR_GREEN = (83, 141, 78)
COLOR_DISABLED = (100, 100, 100) 

# Paths
ASSETS = "assets/"
DATA_DIR = "data/"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


# -----------------------------------------------------------------------------------------------
# QUẢN LÝ FONT
# - Ưu tiên font pixel & font tiếng Việt
# - Có cơ chế fallback sang font hệ thống nếu thiếu file
# - Sinh viên chủ động xử lý lỗi tài nguyên
# -----------------------------------------------------------------------------------------------

# 1. Main font
try:
    path = ASSETS + "fonts/pixel.ttf"
    FONT_PIXEL_16 = pygame.font.Font(path, 16)
    FONT_PIXEL_20 = pygame.font.Font(path, 20)
    FONT_PIXEL_24 = pygame.font.Font(path, 24)
    FONT_PIXEL_32 = pygame.font.Font(path, 32)
    FONT_PIXEL_40 = pygame.font.Font(path, 40)
except:
    print("Warning: Font pixel.ttf not found. Using system font.")
    FONT_PIXEL_16 = pygame.font.SysFont("arial", 16)
    FONT_PIXEL_20 = pygame.font.SysFont("arial", 20)
    FONT_PIXEL_24 = pygame.font.SysFont("arial", 24)
    FONT_PIXEL_32 = pygame.font.SysFont("arial", 32)
    FONT_PIXEL_40 = pygame.font.SysFont("arial", 40)

# 2. Vietnamese font
try:
    FONT_VIET_20 = pygame.font.Font(ASSETS + "fonts/backup.ttf", 20)
    FONT_VIET_24 = pygame.font.Font(ASSETS + "fonts/backup.ttf", 24)
    FONT_VIET_32 = pygame.font.Font(ASSETS + "fonts/backup.ttf", 32)
    FONT_VIET_40 = pygame.font.Font(ASSETS + "fonts/backup.ttf", 40)
except:
    print("Warning: Font pixel.ttf not found. Using system font.")
    FONT_PIXEL_16 = pygame.font.SysFont("arial", 16)
    FONT_PIXEL_20 = pygame.font.SysFont("arial", 20)
    FONT_PIXEL_24 = pygame.font.SysFont("arial", 24)
    FONT_PIXEL_32 = pygame.font.SysFont("arial", 32)
    FONT_PIXEL_40 = pygame.font.SysFont("arial", 40)
 

# 3. Backup font
try:
    FONT_BACKUP = pygame.font.Font(ASSETS + "fonts/backup.ttf", 32)
    FONT_BACKUP_LARGE = pygame.font.Font(ASSETS + "fonts/backup.ttf", 40)
except:
    FONT_BACKUP = pygame.font.SysFont("arial", 32)
    FONT_BACKUP_LARGE = pygame.font.SysFont("arial", 40)

# -----------------------------------------------------------------------------------------------
# LOAD HÌNH ẢNH (ASSETS)
# - Hàm load ảnh có xử lý lỗi thiếu file
# - Nếu không có asset → tạo Surface tạm để game không bị crash
# -----------------------------------------------------------------------------------------------

IMG = {}

def load_img(path, scale=None):
    full_path = ASSETS + path
    try:
        img = pygame.image.load(full_path).convert_alpha()
        if scale:
            img = pygame.transform.scale(img, scale)
        return img
    except Exception as e:
        print(f"Missing asset: {full_path}")
        surf = pygame.Surface(scale if scale else (30, 30))
        surf.fill((100, 100, 100))
        return surf

# UI Base
IMG['bg_menu'] = load_img("bg/bg_menu.png", (WIDTH, HEIGHT))
IMG['bg_game'] = load_img("bg/bg_game.png", (WIDTH, HEIGHT))
IMG['logo'] = load_img("ui/logo.png")
IMG['panel'] = load_img("ui/panel.png")

IMG['gold'] = load_img("ui/gold.png", (30, 30))
IMG['silver'] = load_img("ui/silver.png", (30, 30))
IMG['bronze'] = load_img("ui/bronze.png", (30, 30))

IMG['btn'] = load_img("ui/btn.png", (200, 53))
IMG['btn_hover'] = load_img("ui/btn_hover.png", (200, 53))
IMG['btn_disabled'] = IMG['btn'].copy()
IMG['btn_disabled'].fill((100, 100, 100), special_flags=pygame.BLEND_MULT)

IMG['back'] = load_img("ui/back.png")
IMG['back_hover'] = load_img("ui/back_hover.png")

IMG['input'] = load_img("ui/input.png")
IMG['input_focus'] = load_img("ui/input_focus.png")
IMG['toggle_on'] = load_img("ui/toggle_on.png")
IMG['toggle_off'] = load_img("ui/toggle_off.png")

IMG['tile_empty'] = load_img("tiles/tile_empty.png")
IMG['tile_green'] = load_img("tiles/tile_green.png")
IMG['tile_yellow'] = load_img("tiles/tile_yellow.png")
tile_base = load_img("tiles/tile_empty.png")
IMG['tile_red'] = tile_base.copy()
IMG['tile_red'].fill(COLOR_RED_WRONG, special_flags=pygame.BLEND_MULT)
IMG['tile_disabled'] = load_img("tiles/tile_disabled.png")

IMG['key_normal'] = load_img("keys/key_normal.png")
IMG['key_normal_press'] = load_img("keys/key_normal_press.png")
IMG['key_green'] = load_img("keys/key_green.png")
IMG['key_yellow'] = load_img("keys/key_yellow.png")
IMG['key_enter'] = load_img("keys/key_enter.png")
IMG['key_enter_press'] = load_img("keys/key_enter_press.png")
IMG['key_back'] = load_img("keys/key_backspace.png")
IMG['key_back_press'] = load_img("keys/key_backspace_press.png")

key_base = load_img("keys/key_normal.png")
IMG['key_red'] = key_base.copy()
IMG['key_red'].fill((220, 100, 100), special_flags=pygame.BLEND_MULT)

# -----------------------------------------------------------------------------------------------
# ÂM THANH TRONG GAME
# - Load âm thanh theo tên
# - Nếu thiếu file âm thanh, game vẫn chạy bình thường
# -----------------------------------------------------------------------------------------------

SOUNDS = {}
def load_snd(path):
    try: return pygame.mixer.Sound(ASSETS + path)
    except: return None

SOUNDS['type'] = load_snd("sounds/type.wav")
SOUNDS['wrong'] = load_snd("sounds/wrong.wav")
SOUNDS['flip'] = load_snd("sounds/flip.wav")
SOUNDS['correct'] = load_snd("sounds/correct.wav")
SOUNDS['win'] = load_snd("sounds/win.wav")
SOUNDS['lose'] = load_snd("sounds/lose.wav")

def play_sound(name):
    if SOUNDS.get(name): SOUNDS[name].play()



# _____________________________________________________________________________
#                                LOGIC & UTILS
# - Các hàm hỗ trợ vẽ chữ, xử lý chuỗi, chuẩn hóa dữ liệu
# - Dùng lại ở nhiều scene
# _____________________________________________________________________________

def draw_text_centered(text, font, color, rect, screen, offset=(0,0)):
    txt_surf = font.render(str(text), True, color)
    txt_rect = txt_surf.get_rect(center=(rect.centerx + offset[0], rect.centery + offset[1]))
    screen.blit(txt_surf, txt_rect)


# -----------------------------------------------------------------------------------------------
# CHẾ ĐỘ WORDLE TOÁN HỌC (TỰ THIẾT KẾ)
# - Sinh biểu thức toán hợp lệ có kết quả đúng
# - Kiểm soát độ dài chuỗi để phù hợp giao diện Wordle
# - Đây là phần mở rộng sáng tạo của sinh viên
# -----------------------------------------------------------------------------------------------

def generate_math_word():
    start_time = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start_time < 2000:
        a = random.randint(1,9)
        b = random.randint(1,9)
        c = random.randint(1,9)
        ops = [random.choice(['+','-','*']), random.choice(['+','-','*'])]
        expr = f"{a}{ops[0]}{b}{ops[1]}{c}"
        try:
            val = eval(expr)
            if 0 <= val < 100:
                val_str = f"{val:02}"
                full = f"{expr}={val_str}"
                if len(full) == 8: return full
        except: continue
    return "1+2+3=06"


# -----------------------------------------------------------------------------------------------
# XỬ LÝ TIẾNG VIỆT
# - Chuẩn hóa dấu tiếng Việt → không dấu để so sánh
# - Giữ nguyên chữ hiển thị cho người chơi
# - Sinh viên tự xây dựng mapping ký tự
# -----------------------------------------------------------------------------------------------

def tudoanviet(word):
    guess = ''
    word = word.lower()
    mapping = {
        'aáàạãảăắằặẵẳâậầẩấẫ': 'a', 'uúùũủụưứừửữự': 'u',
        'oỏòóõọôồốổỗộơớờợỡở': 'o', 'eéèẻẽẹêểễếềệ': 'e',
        'iíìịĩỉ': 'i', 'yýỳỷỹỵ': 'y', 'đ': 'd'
    }
    for char in word:
        if char == ' ': continue
        found = False
        for k, v in mapping.items():
            if char in k:
                guess += v
                found = True
                break
        if not found: guess += char
    return guess


DICT_ENG_GUESS = set()
DICT_VIET_CHECK = set()
LIST_ENG_TARGET = []
LIST_VIET_TARGET = []
# -----------------------------------------------------------------------------------------------
# LOAD TỪ ĐIỂN
# - English: vocabulary.txt + vocabularycheck.txt
# - Vietnamese: vocabularyV.txt + normalized_vocab.txt
# - Có xử lý file lỗi / định dạng không chuẩn
# -----------------------------------------------------------------------------------------------

def load_dictionaries():
    global DICT_ENG_GUESS, DICT_VIET_CHECK, LIST_ENG_TARGET, LIST_VIET_TARGET
    
    if os.path.exists("vocabulary.txt"):
        try:
            with open("vocabulary.txt", "r", encoding="utf-8") as f:
                content = f.read()
                words = content.replace('\n', ' ').split()
                if len(words) == 1 and len(words[0]) > 20: 
                    raw = words[0]
                    words = [raw[i:i+5] for i in range(0, len(raw), 5)]
                
                valid_eng = [w.upper() for w in words if len(w) == 5 and w.isalpha()]
                LIST_ENG_TARGET = valid_eng[:]          
                DICT_ENG_GUESS = set(valid_eng) 
        except: pass

    if os.path.exists("vocabularycheck.txt"):
        try:
            with open("vocabularycheck.txt", "r", encoding="utf-8") as f:
                words = f.read().split()
                extra = [w.upper() for w in words if len(w) == 5 and w.isalpha()]
                DICT_ENG_GUESS.update(extra)
        except:
            pass

    
    if os.path.exists("vocabularyV.txt"):
        try:
            with open("vocabularyV.txt", "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
                clean_lines = []
                for line in lines:
                    if "[" in line and "]" in line: continue
                    clean = line.replace('"', '').replace(',', '').strip()
                    if clean: clean_lines.append(clean)
                LIST_VIET_TARGET = clean_lines
        except: pass

    if os.path.exists("normalized_vocab.txt"):
        try:
            with open("normalized_vocab.txt", "r", encoding="utf-8") as f:
                content = f.read()
                content = content.replace('[', '').replace(']', '').replace("'", "")
                import re
                content = re.sub(r'source: \d+', '', content)
                words = [w.strip().upper() for w in content.split(',')]
                DICT_VIET_CHECK = set(w for w in words if len(w) == 7)
        except: pass

load_dictionaries()

# -----------------------------------------------------------------------------------------------
# HỆ THỐNG XẾP HẠNG (RANKBOARD)
# - Quản lý đăng ký / đăng nhập
# - Lưu số trận, số trận thắng, điểm
# - Dữ liệu được mã hóa khi lưu
# -----------------------------------------------------------------------------------------------

class Rankboard:
    def __init__(self, path=DATA_DIR + "rank.json"):
        self.path = path
        self.players = {}
        self.load()

    def load(self):
        data = load_secure_json(self.path, default={})
        if isinstance(data, dict):
            self.players = data
        else:
            self.players = {}

    def save(self):
        save_secure_json(self.path, self.players)

    def login(self, username, password):
        if username not in self.players: return None
        if self.players[username]["password"] != password: return None
        return username

    def register(self, username, password):
        if username in self.players or len(username) < 3 or len(password) < 3:
            return None
        self.players[username] = {
            "password": password,
            "played": 0,
            "won": 0,
            "point": 0
        }
        self.save()
        return username

    def delete_player(self, username):
        if username in self.players:
            del self.players[username]
            self.save()
            return True
        return False

    def update_stats(self, username, won, score):
        if not username or username not in self.players: return
        self.players[username]["played"] += 1
        if won:
            self.players[username]["won"] += 1
            self.players[username]["point"] += score
        self.save()

    def get_top_players(self, n=20):
        lst = []
        for name, data in self.players.items():
            d = data.copy()
            d['username'] = name
            lst.append(d)
        return sorted(lst, key=lambda x: x['point'], reverse=True)[:n]

RANK_SYSTEM = Rankboard()
CURRENT_USER = None

# -----------------------------------------------------------------------------------------------
# LƯU / TẢI TRẠNG THÁI GAME
# - Cho phép resume game
# - Giới hạn số file save
# - Xóa save khi game kết thúc
# -----------------------------------------------------------------------------------------------

class SaveManager:
    def __init__(self, path=DATA_DIR + "savegame.json"):
        self.path = path
        self.saves = {}
        self.load()

    def load(self):
        data = load_secure_json(self.path, default={})
        if isinstance(data, dict):
            self.saves = data
        else:
            self.saves = {}

    def save_disk(self):
        save_secure_json(self.path, self.saves)

    def save_game(self, username, game_data):
        if not username: return
        game_data['timestamp'] = time.time()

        if username in self.saves:
            self.saves[username] = game_data
        else:
            if len(self.saves) >= 5:
                oldest = min(
                    self.saves,
                    key=lambda k: self.saves[k].get('timestamp', 0)
                )
                del self.saves[oldest]
            self.saves[username] = game_data

        self.save_disk()

    def get_save(self, username):
        return self.saves.get(username)

    def delete_save(self, username):
        if username in self.saves:
            del self.saves[username]
            self.save_disk()

SAVE_MANAGER = SaveManager()

# _____________________________________________________________________________
#                                GAME LOGIC
# _____________________________________________________________________________
# -----------------------------------------------------------------------------------------------
# LÕI LOGIC WORDLE 
# - Kiểm tra guess
# - Luật green / yellow / red
# - Hard mode
# - Undo / Redo
# - Tính điểm
#
# Đây là phần thuật toán chính, không phụ thuộc UI
# -----------------------------------------------------------------------------------------------

class GameState:
    def __init__(self, hard, word, language, time_limit):
        self.word = word
        self.status = 'playing'
        self.n = 0
        self.language = language
        self.time_limit = time_limit
        self.hard = hard
        self.history = [] 
        self.redo_stack = []
        
        if language == 'E': 
            self.len = 5; self.dictionary = DICT_ENG_GUESS
        elif language == 'V': 
            self.len = 7; self.dictionary = DICT_VIET_CHECK
        elif language == 'Cac': 
            self.len = 8; self.dictionary = None

        self.word_norm = tudoanviet(self.word).upper() if language == 'V' else self.word
        self.hard_green = [None] * self.len
        self.hard_yellow = set()

    def restore(self, data):
        self.word = data['word']
        self.word_norm = data['word_norm']
        self.n = data['n']
        self.history = data['history']
        self.hard_green = data['hard_green']
        self.hard_yellow = set(data['hard_yellow']) 
        self.status = data['status']
        self.redo_stack = []

    def check(self, guess):
        guess = guess.upper()
        if len(guess) != self.len: return 'length_error'
        
        if self.language == 'Cac':
            if guess.count('=') != 1: return 'invalid_math'
            try:
                lhs, rhs = guess.split('=')
                if not rhs.isdigit() and not (rhs.startswith('-') and rhs[1:].isdigit()): return 'invalid_math'
                if eval(lhs) != int(rhs): 
                    if self.hard: return 'math_wrong_val' 
                    return 'math_wrong_val' 
            except: return 'invalid_math'
        elif self.dictionary and guess not in self.dictionary:
            return 'not_in_dict'

        if self.hard:
            for i, char in enumerate(self.hard_green):
                if char and guess[i] != char: return 'hard_green'
            for char in self.hard_yellow:
                if char not in guess: return 'hard_yellow'

        self.n += 1
        res = ['red'] * self.len
        word_list = list(self.word_norm)
        
        for i in range(self.len):
            if guess[i] == word_list[i]:
                res[i] = 'green'
                word_list[i] = None
                if self.hard: self.hard_green[i] = guess[i]

        for i in range(self.len):
            if res[i] == 'red' and guess[i] in word_list:
                res[i] = 'yellow'
                word_list[word_list.index(guess[i])] = None
                if self.hard: self.hard_yellow.add(guess[i])

        self.history.append((guess, res))
        self.redo_stack.clear()

        if res.count('green') == self.len: self.status = 'win'
        elif self.n >= 6: self.status = 'lose'

        return res

    def force_skip_turn(self):
        self.n += 1
        res = ['disabled'] * self.len
        self.history.append(("", res))
        if self.n >= 6: self.status = 'lose'
        return res

    def undo(self):
        if not self.history or self.time_limit is not None: return None
        last = self.history.pop()
        self.redo_stack.append(last)
        self.n -= 1
        self.status = 'playing'
        if self.hard:
            self.hard_green = [None] * self.len
            self.hard_yellow = set()
            for g, r in self.history:
                for i in range(self.len):
                    if r[i] == 'green': self.hard_green[i] = g[i]
                    if r[i] == 'yellow': self.hard_yellow.add(g[i])
        return True

    def redo(self):
        if not self.redo_stack or self.time_limit is not None: return None
        item = self.redo_stack.pop()
        self.history.append(item)
        self.n += 1
        guess, res = item
        if self.hard:
            for i in range(self.len):
                if res[i] == 'green': self.hard_green[i] = guess[i]
                if res[i] == 'yellow': self.hard_yellow.add(guess[i])
        if res.count('green') == self.len: self.status = 'win'
        elif self.n >= 6: self.status = 'lose'
        return item

    def calculate_score(self, total_time_used, time_per_guess_active):
        if self.status != 'win' or self.time_limit is None: return 0
        base = 100
        if self.language == 'Cac': base = 90
        elif self.language == 'E': base = 120
        
        score = base
        if self.hard: score *= 1.4
        if time_per_guess_active: score *= 1.2
        
        if self.time_limit > 0:
            score *= (1 + 0.15 * (max(0, (self.time_limit - total_time_used) / self.time_limit) ** 3))
        
        return int(score)

# _____________________________________________________________________________
#                                UI CLASSES
# - Button, Toggle, Tile, Key
# - Đóng vai trò hiển thị & tương tác
# _____________________________________________________________________________

class Button:
    def __init__(self, center_x, y, text, is_back=False, disabled=False, color_override=None):
        self.text = text
        self.is_back = is_back
        self.disabled = disabled
        self.color_override = color_override

        if is_back:
            self.img_idle = IMG['back']
            self.img_hover = IMG['back_hover']
            self.rect = self.img_idle.get_rect(topleft=(center_x, y))
        else:
            self.img_idle = IMG['btn']
            self.img_hover = IMG['btn_hover']
            self.img_disabled = IMG['btn_disabled']
            self.rect = self.img_idle.get_rect(midtop=(center_x, y))
        
        self.hover = False

    def update(self, mouse_pos):
        if self.disabled:
            self.hover = False
            return
        self.hover = self.rect.collidepoint(mouse_pos)

    def draw(self, screen):

        if self.disabled and not self.is_back:
            img = self.img_disabled
        else:
            img = self.img_hover if self.hover else self.img_idle
            
        screen.blit(img, self.rect)
        
        if not self.is_back:
            if self.color_override:
                color = self.color_override
            else:
                color = (150,150,150) if self.disabled else COLOR_BLACK
            draw_text_centered(self.text, FONT_PIXEL_20, color, self.rect, screen, (0, 2))

    def clicked(self, event):
        if self.disabled: return False
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.hover

class Toggle:
    def __init__(self, x, y, value=False):
        self.value = value
        self.rect = IMG['toggle_on'].get_rect(topleft=(x, y))

    def draw(self, screen):
        screen.blit(IMG['toggle_on'] if self.value else IMG['toggle_off'], self.rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.value = not self.value
                play_sound('type')

class Tile:
    def __init__(self, x, y, size):
        self.rect = pygame.Rect(x, y, size, size)
        self.letter = ""
        self.state = "empty" 
        self.anim_scale = 1.0
        self.animating = False
        self.target_state = ""

    def set_reveal(self, state):
        self.target_state = state
        self.animating = True
        self.anim_scale = 1.0
        self.anim_phase = 0 

    def update(self):
        if self.animating:
            speed = 0.15
            if self.anim_phase == 0:
                self.anim_scale -= speed
                if self.anim_scale <= 0:
                    self.anim_scale = 0
                    self.state = self.target_state
                    self.anim_phase = 1
                    play_sound('flip')
            else:
                self.anim_scale += speed
                if self.anim_scale >= 1.0:
                    self.anim_scale = 1.0
                    self.animating = False

    def draw(self, screen):
        img_key = f"tile_{self.state}"
        img = IMG.get(img_key, IMG['tile_empty'])
        draw_rect = self.rect.copy()
        w = int(self.rect.width * self.anim_scale)
        if w > 0:
            scaled = pygame.transform.scale(img, (w, self.rect.height))
            dest = scaled.get_rect(center=self.rect.center)
            screen.blit(scaled, dest)
            
            if self.letter:
                fs = int(self.rect.height * 0.6)
                use_font = FONT_PIXEL_32 if fs > 30 else FONT_PIXEL_20
                
                txt = use_font.render(self.letter, True, COLOR_BLACK)
                if txt.get_width() > 0:
                    txt = pygame.transform.scale(txt, (int(txt.get_width()*self.anim_scale), txt.get_height()))
                screen.blit(txt, txt.get_rect(center=(draw_rect.centerx+1, draw_rect.centery +3.5)))

class Key:
    def __init__(self, x, y, w, h, label, kind='normal'):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.kind = kind
        self.state = 'normal'
        self.pressed = False

    def update_state(self, new_state):
        priority = {'green': 3, 'yellow': 2, 'red': 1, 'normal': 0, 'disabled': 0}
        if new_state == 'disabled': return
        if priority.get(new_state, 0) > priority.get(self.state, 0):
            self.state = new_state

    def draw(self, screen):
        base_name = f"key_{self.state}"
        if self.kind != 'normal': base_name = f"key_{self.kind}"
        
        draw_rect = self.rect.copy()
        if self.pressed:
            if f"{base_name}_press" in IMG: img = IMG[f"{base_name}_press"]
            else: img = IMG.get(base_name, IMG['key_normal']); draw_rect.y += 2
        else:
            img = IMG.get(base_name, IMG['key_normal'])

        img = pygame.transform.scale(img, (self.rect.width, self.rect.height))
        screen.blit(img, draw_rect)
        
        if self.kind == 'normal':
            offset_y = 2 if self.pressed else 0
            col = COLOR_WHITE if self.state == 'red' else COLOR_BLACK
            txt = FONT_PIXEL_20.render(self.label, True, col)
            screen.blit(txt, txt.get_rect(center=(draw_rect.centerx, draw_rect.centery + offset_y - 6)))

# _____________________________________________________________________________
#                                SCENES
# - Mỗi scene là một màn hình riêng
# - AI hỗ trợ ghép scene
#  _____________________________________________________________________________

class SceneLogin:
    def __init__(self):
        self.u = InputBox(480, 250)
        self.p = InputBox(480, 330, True)
        self.btn_login = Button(370, 410, "LOGIN")
        self.btn_reg = Button(590, 410, "REGISTER")
        self.msg = ""
        self.timer = 0

    def run(self):
        global CURRENT_USER
        while True:
            CLOCK.tick(60)
            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT: 
                    RANK_SYSTEM.save()

                    SAVE_MANAGER.save_disk()

                    return "EXIT"
                self.u.handle(e)
                self.p.handle(e)
                if self.btn_login.clicked(e):
                    if RANK_SYSTEM.login(self.u.text, self.p.text):
                        CURRENT_USER = self.u.text
                        play_sound('correct')
                        return "MENU"
                    else: self.msg = "Login Failed"; play_sound('wrong'); self.timer = 60
                if self.btn_reg.clicked(e):
                    if RANK_SYSTEM.register(self.u.text, self.p.text):
                        CURRENT_USER = self.u.text
                        play_sound('correct')
                        return "MENU"
                    else: self.msg = "Error/Taken"; play_sound('wrong'); self.timer = 60

            mouse = pygame.mouse.get_pos()
            self.btn_login.update(mouse); self.btn_reg.update(mouse)
            
            SCREEN.blit(IMG['bg_game'], (0,0))
            SCREEN.blit(IMG['logo'], IMG['logo'].get_rect(center=(480, 120)))
            draw_text_centered("USERNAME:", FONT_PIXEL_20, COLOR_WHITE, self.u.rect, SCREEN, (-110,-35))
            draw_text_centered("PASSWORD:", FONT_PIXEL_20, COLOR_WHITE, self.p.rect, SCREEN, (-110,-35))
            self.u.draw(SCREEN); self.p.draw(SCREEN)
            self.btn_login.draw(SCREEN); self.btn_reg.draw(SCREEN)
            
            if self.timer > 0:
                self.timer -= 1
                t = FONT_PIXEL_24.render(self.msg, True, COLOR_RED_WRONG)
                SCREEN.blit(t, (480 - t.get_width()//2, 480))
            
            pygame.display.flip()

class SceneDeleteConfirm:
    def __init__(self):
        self.p = InputBox(480, 280, True)
        self.btn_confirm = Button(480, 360, "CONFIRM", color_override=COLOR_RED_WRONG)
        self.btn_cancel = Button(480, 430, "CANCEL")
        self.msg = ""
        self.timer = 0
    
    def run(self):
        global CURRENT_USER
        self.p.text = "" 
        while True:
            CLOCK.tick(60)
            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    RANK_SYSTEM.save()
                    SAVE_MANAGER.save_disk()
                    return "EXIT"
                
                self.p.handle(e)
                
                if self.btn_confirm.clicked(e):
                    if not CURRENT_USER: return "LOGIN"
                    stored_pass = RANK_SYSTEM.players[CURRENT_USER]["password"]
                    if self.p.text == stored_pass:
                        RANK_SYSTEM.delete_player(CURRENT_USER)
                        SAVE_MANAGER.delete_save(CURRENT_USER)
                        play_sound('type')
                        CURRENT_USER = None
                        return "LOGIN"
                    else:
                        play_sound('wrong')
                        self.msg = "Incorrect Password"
                        self.timer = 60
                
                if self.btn_cancel.clicked(e):
                    play_sound('type')
                    return "MENU"

            mouse = pygame.mouse.get_pos()
            self.btn_confirm.update(mouse)
            self.btn_cancel.update(mouse)

            SCREEN.blit(IMG['bg_game'], (0,0))
            
            title = FONT_PIXEL_32.render("DELETE ACCOUNT", True, COLOR_RED_WRONG)
            SCREEN.blit(title, title.get_rect(center=(480, 150)))
            
            warn = FONT_PIXEL_20.render("Enter password to confirm. This cannot be undone!", True, COLOR_WHITE)
            SCREEN.blit(warn, warn.get_rect(center=(480, 190)))

            draw_text_centered("PASSWORD:", FONT_PIXEL_20, COLOR_WHITE, self.p.rect, SCREEN, (-110,-35))
            self.p.draw(SCREEN)
            
            self.btn_confirm.draw(SCREEN)
            self.btn_cancel.draw(SCREEN)

            if self.timer > 0:
                self.timer -= 1
                t = FONT_PIXEL_24.render(self.msg, True, COLOR_RED_WRONG)
                SCREEN.blit(t, (480 - t.get_width()//2, 480))

            pygame.display.flip()

class InputBox:
    def __init__(self, x, y, is_pass=False):
        self.rect = IMG['input'].get_rect(midtop=(x, y))
        self.text = ""
        self.active = False
        self.is_pass = is_pass

    def handle(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(e.pos)
        if e.type == pygame.KEYDOWN and self.active:
            if e.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                play_sound('type')
            elif e.key == pygame.K_TAB: self.active = False
            elif len(self.text) < 12 and e.unicode.isprintable():
                self.text += e.unicode.upper()
                play_sound('type')

    def draw(self, screen):
        screen.blit(IMG['input_focus'] if self.active else IMG['input'], self.rect)
        show = "*" * len(self.text) if self.is_pass else self.text
        t = FONT_PIXEL_24.render(show, True, COLOR_WHITE)
        screen.blit(t, (self.rect.x + 15, self.rect.centery - t.get_height()//2))

class SceneMenu:
    def __init__(self):
        self.b_play = Button(480, 240, "NEW GAME")
        self.b_resume = Button(480, 310, "RESUME", disabled=True)
        self.b_rank = Button(480, 380, "RANK")
        self.b_rule = Button(480, 450, "RULES")    
        self.logout_rect = pygame.Rect(WIDTH-120, 20, 100, 30)        
        self.delete_acc_rect = pygame.Rect(WIDTH-120, HEIGHT-50, 100, 30)

    def run(self):
        global CURRENT_USER
        has_save = False
        if CURRENT_USER and SAVE_MANAGER.get_save(CURRENT_USER):
            has_save = True
        self.b_resume.disabled = not has_save

        while True:
            CLOCK.tick(60)
            mouse = pygame.mouse.get_pos()
            for e in pygame.event.get():
                if e.type == pygame.QUIT: 
                    RANK_SYSTEM.save()

                    SAVE_MANAGER.save_disk()

                    return "EXIT"
                
                if self.b_play.clicked(e): play_sound('type'); return "MODE_SELECT"
                
                if self.b_resume.clicked(e): 
                    play_sound('type')
                    save_data = SAVE_MANAGER.get_save(CURRENT_USER)
                    if save_data:
                        return ("GAME", {'resume': True, 'data': save_data})

                if self.b_rank.clicked(e): play_sound('type'); return "RANK"
                if self.b_rule.clicked(e): play_sound('type'); return "RULES"
                
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if self.logout_rect.collidepoint(e.pos):
                        CURRENT_USER = None
                        return "LOGIN"
                    if self.delete_acc_rect.collidepoint(e.pos):
                        play_sound('type')
                        return "DELETE_CONFIRM"

            self.b_play.update(mouse)
            self.b_resume.update(mouse)
            self.b_rank.update(mouse)
            self.b_rule.update(mouse)
            
            SCREEN.blit(IMG['bg_menu'], (0,0))
            SCREEN.blit(IMG['logo'], IMG['logo'].get_rect(center=(480, 120)))
            
            self.b_play.draw(SCREEN)
            self.b_resume.draw(SCREEN)
            self.b_rank.draw(SCREEN)
            self.b_rule.draw(SCREEN)
            
            if CURRENT_USER:
                t = FONT_PIXEL_20.render(f"Hi, {CURRENT_USER}!", True, COLOR_WHITE)
                SCREEN.blit(t, (20, 20))
                
                # Logout
                pygame.draw.rect(SCREEN, COLOR_RED_WRONG, self.logout_rect, border_radius=5)
                draw_text_centered(" LOG OUT", FONT_PIXEL_20, COLOR_WHITE, self.logout_rect, SCREEN)
                
                # Delete Acc
                pygame.draw.rect(SCREEN, COLOR_RED_WRONG, self.delete_acc_rect, border_radius=5)
                draw_text_centered("DEL ACC", FONT_PIXEL_20, COLOR_WHITE, self.delete_acc_rect, SCREEN)
            
            pygame.display.flip()

class SceneModeSelect:
    def __init__(self):
        self.langs = ["English", "Vietnamese", "Math"]
        self.codes = ["E", "V", "Cac"]
        self.idx_l = 0
        
        self.times = [90, 120, None]
        self.idx_t = 0
        
        self.btn_lang = Button(650, 180, self.langs[0])
        self.btn_time = Button(650, 250, "90s")
        self.tog_tpg = Toggle(700, 320)
        self.tog_hard = Toggle(700, 390)
        
        self.btn_start = Button(480, 450, "START!!!")
        self.btn_back = Button(30, 30, "", is_back=True)

    def run(self):
        while True:
            CLOCK.tick(60)
            mouse = pygame.mouse.get_pos()
            for e in pygame.event.get():
                if e.type == pygame.QUIT: 
                    RANK_SYSTEM.save()

                    SAVE_MANAGER.save_disk()

                    return "EXIT"
                self.tog_tpg.handle_event(e)
                self.tog_hard.handle_event(e)
                
                if self.btn_lang.clicked(e):
                    play_sound('type')
                    self.idx_l = (self.idx_l + 1) % 3
                    self.btn_lang.text = self.langs[self.idx_l]
                
                if self.btn_time.clicked(e):
                    play_sound('type')
                    self.idx_t = (self.idx_t + 1) % 3
                    t = self.times[self.idx_t]
                    self.btn_time.text = f"{t}s" if t else "Inf"
                
                if self.btn_back.clicked(e): return "MENU"
                if self.btn_start.clicked(e):
                    play_sound('correct')
                    tpg = self.tog_tpg.value
                    if self.times[self.idx_t] is None: tpg = False 

                    return ("GAME", {
                        'resume': False,
                        'lang': self.codes[self.idx_l],
                        'time': self.times[self.idx_t],
                        'tpg': tpg,
                        'hard': self.tog_hard.value
                    })

            self.btn_lang.update(mouse); self.btn_time.update(mouse)
            self.btn_start.update(mouse); self.btn_back.update(mouse)
            
            SCREEN.blit(IMG['bg_menu'], (0,0))
            
            s = pygame.Surface((600, 350))
            s.set_alpha(150); s.fill(COLOR_BLACK)
            SCREEN.blit(s, (180, 130))
            
            labels = ["Language:", "Time Limit:", "Time/Guess:", "Hard Mode:"]
            ys = [190, 260, 330, 400]
            for i, l in enumerate(labels):
                t = FONT_PIXEL_24.render(l, True, COLOR_WHITE)
                SCREEN.blit(t, (250, ys[i]))
                
            self.btn_lang.draw(SCREEN)
            self.btn_time.draw(SCREEN)
            self.tog_tpg.draw(SCREEN)
            self.tog_hard.draw(SCREEN)
            self.btn_start.draw(SCREEN)
            self.btn_back.draw(SCREEN)
            
            if self.times[self.idx_t] is None and self.tog_tpg.value:
                w = FONT_PIXEL_20.render("TPG requires Time Limit", True, COLOR_RED_WRONG)
                SCREEN.blit(w, (750, 330))

            pygame.display.flip()

class SceneGame:
    def __init__(self, cfg):
        self.cfg = cfg
        self.paused = False
        
        if cfg.get('resume'):
            data = cfg['data']
            self.cfg = data['cfg']
            self.word = data['word']
            self.logic = GameState(self.cfg['hard'], self.word, self.cfg['lang'], self.cfg['time'])
            self.logic.restore(data)
            
            self.start_t = pygame.time.get_ticks() - (data['elapsed_total'] * 1000)
            self.turn_start_t = pygame.time.get_ticks() 
        else:
            if cfg['lang'] == 'E':
                self.word = random.choice(LIST_ENG_TARGET).upper() if LIST_ENG_TARGET else "HELLO"
            elif cfg['lang'] == 'V':
                self.word = random.choice(LIST_VIET_TARGET) if LIST_VIET_TARGET else "VIỆT NAM"
            else: self.word = generate_math_word()

            self.logic = GameState(cfg['hard'], self.word, cfg['lang'], cfg['time'])
            self.start_t = pygame.time.get_ticks()
            self.turn_start_t = self.start_t

        self.tile_size = 45 
        self.tile_gap = 5
        self.tiles = []
        self.keys = []
        self.create_grid()
        self.create_keyboard()
        
        self.key_map = {}
        for k in self.keys:
            if k.kind == 'enter': self.key_map['ENTER'] = k
            elif k.kind == 'back': self.key_map['BACK'] = k
            else: self.key_map[k.label] = k

        if cfg.get('resume'):
            for i, (guess, res) in enumerate(self.logic.history):
                for j, color in enumerate(res):
                    self.tiles[i][j].state = color
                    self.tiles[i][j].letter = guess[j]
                    for k in self.keys:
                        if k.label == guess[j]: k.update_state(color)

        self.guess = ""
        self.tpg_limit = 0
        if self.cfg['tpg'] and self.cfg['time']:
            self.tpg_limit = self.cfg['time'] / 6.0

        self.game_over = False
        self.win = False
        self.shake = 0
        self.msg = ""
        self.msg_t = 0
        
        self.btn_resume = Button(480, 200, "RESUME")
        self.btn_quit = Button(480, 270, "QUIT TO MENU")
        self.btn_pause_icon = Button(900, 30, "||")
        self.btn_pause_icon.rect = pygame.Rect(910, 10, 40, 40)
        
        self.undo_rect = pygame.Rect(WIDTH//2 - 90, 10, 80, 30)
        self.redo_rect = pygame.Rect(WIDTH//2 + 10, 10, 80, 30)

    def create_grid(self):
        cols = self.logic.len
        rows = 6
        total_w = cols * self.tile_size + (cols-1) * self.tile_gap
        start_x = (WIDTH - total_w) // 2
        start_y = 50 
        for r in range(rows):
            row = []
            for c in range(cols):
                x = start_x + c * (self.tile_size + self.tile_gap)
                y = start_y + r * (self.tile_size + self.tile_gap)
                t = Tile(x, y, self.tile_size)
                if self.cfg['lang'] == 'Cac' and c == 5: t.letter = "="
                row.append(t)
            self.tiles.append(row)

    def create_keyboard(self):
        if self.cfg['lang'] == 'Cac':
            rows = ["1234567890", "+-*"]
        else:
            rows = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
        start_y = HEIGHT - 180
        key_w, key_h = 40, 50
        gap = 4
        for i, r_str in enumerate(rows):
            row_w = len(r_str) * (key_w + gap)
            start_x = (WIDTH - row_w) // 2
            y = start_y + i * (key_h + gap)
            for j, char in enumerate(r_str):
                x = start_x + j * (key_w + gap)
                self.keys.append(Key(x, y, key_w, key_h, char))
        
        ly = start_y + (len(rows)-1) * (key_h + gap)
        if self.cfg['lang'] == 'Cac': ly = start_y + (key_h + gap) 
        self.keys.append(Key(WIDTH//2 - 260, ly , 100, 50, "", "back"))
        self.keys.append(Key(WIDTH//2 + 190, ly - 40 , 75, 89, "", "enter"))

    def save_state(self):
        if self.game_over: 
            SAVE_MANAGER.delete_save(CURRENT_USER)
            return

        elapsed = (pygame.time.get_ticks() - self.start_t) / 1000
        data = {
            'cfg': self.cfg,
            'word': self.logic.word,
            'word_norm': self.logic.word_norm,
            'n': self.logic.n,
            'history': self.logic.history,
            'hard_green': self.logic.hard_green,
            'hard_yellow': list(self.logic.hard_yellow), 
            'status': self.logic.status,
            'elapsed_total': elapsed
        }
        SAVE_MANAGER.save_game(CURRENT_USER, data)

    def handle_input(self, val):
        if self.game_over or self.paused: return
        
        if val == "BACK":
            self.guess = self.guess[:-1]
            play_sound('type')
        elif val == "ENTER":
            final_guess = self.guess
            if self.cfg['lang'] == 'Cac' and len(self.guess) >= 5:
                final_guess = self.guess[:5] + "=" + self.guess[5:]
            
            if len(final_guess) != self.logic.len:
                self.msg = "Not enough letters"; self.msg_t = 60; self.shake=10
                play_sound('wrong')
                return
            self.submit(final_guess)
        else:
            limit = self.logic.len
            if self.cfg['lang'] == 'Cac': limit = self.logic.len - 1 
            if len(self.guess) < limit:
                self.guess += val; play_sound('type')

    def submit(self, guess_str):
        res = self.logic.check(guess_str)
        if isinstance(res, str):
            msgs = {'not_in_dict':"Not in dictionary", 'length_error':"Length error",
                    'invalid_math':"Invalid Equation", 'math_wrong_val':"Math incorrect",
                    'hard_green':"Must use revealed hints", 'hard_yellow':"Must use yellow hints"}
            self.msg = msgs.get(res, "Error"); self.msg_t = 60; self.shake = 10; play_sound('wrong')
            return

        row = self.tiles[self.logic.n - 1]
        for i, color in enumerate(res):
            row[i].set_reveal(color)
            char = guess_str[i]
            for k in self.keys:
                if k.label == char: k.update_state(color)

        self.guess = ""
        self.turn_start_t = pygame.time.get_ticks() 
        
        if self.logic.status != 'playing':
            self.end_game()

    def end_game(self):
        self.game_over = True
        SAVE_MANAGER.delete_save(CURRENT_USER) 
        self.win = (self.logic.status == 'win')
        if self.win: play_sound('win')
        else: play_sound('lose')
        
        elapsed = (pygame.time.get_ticks() - self.start_t) / 1000
        score = self.logic.calculate_score(elapsed, self.cfg['tpg'])
        RANK_SYSTEM.update_stats(CURRENT_USER, self.win, score)

    def handle_undo_redo(self, action):
        if self.cfg['time'] is not None: return 
        
        if action == "UNDO":
            if self.logic.undo():
                row_idx = self.logic.n 
                for t in self.tiles[row_idx]:
                    t.state = 'empty'; t.letter = ""
                    if self.cfg['lang'] == 'Cac' and self.tiles[row_idx].index(t) == 5: t.letter = "="
                self.guess = ""; play_sound('flip')

        elif action == "REDO":
            res = self.logic.redo()
            if res:
                guess_str, colors = res
                row_idx = self.logic.n - 1
                for i, color in enumerate(colors):
                    self.tiles[row_idx][i].letter = guess_str[i]
                    self.tiles[row_idx][i].set_reveal(color)
                play_sound('flip')
                if self.logic.status != 'playing': self.end_game()

    def run(self):
        while True:
            CLOCK.tick(60)
            events = pygame.event.get()
            current_t = pygame.time.get_ticks()
            elapsed_total = (current_t - self.start_t) / 1000
            
            # Time
            if not self.game_over and not self.paused:
                if self.cfg['time']:
                    if elapsed_total >= self.cfg['time']:
                        self.logic.status = 'lose'
                        self.end_game()
                
                if self.tpg_limit > 0 and not self.game_over:
                    elapsed_turn = (current_t - self.turn_start_t) / 1000
                    if elapsed_turn >= self.tpg_limit:
                        self.msg = "Time's up for turn!"; self.msg_t = 60; play_sound('wrong')
                        res = self.logic.force_skip_turn()
                        row = self.tiles[self.logic.n - 1]
                        for i, color in enumerate(res): row[i].state = 'disabled'
                        self.guess = ""; self.turn_start_t = current_t
                        if self.logic.status == 'lose': self.end_game()

            # Events
            mouse = pygame.mouse.get_pos()
            for e in events:
                if e.type == pygame.QUIT:
                    RANK_SYSTEM.save()

                    SAVE_MANAGER.save_disk()

                    self.save_state()
                    return "EXIT"
                
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        self.paused = not self.paused
                    
                    if not self.paused and not self.game_over:
                        k_upper = e.unicode.upper()
                        if e.key == pygame.K_BACKSPACE and 'BACK' in self.key_map: self.key_map['BACK'].pressed = True
                        elif e.key == pygame.K_RETURN and 'ENTER' in self.key_map: self.key_map['ENTER'].pressed = True
                        elif k_upper in self.key_map: self.key_map[k_upper].pressed = True

                        if e.key == pygame.K_BACKSPACE: self.handle_input("BACK")
                        elif e.key == pygame.K_RETURN: self.handle_input("ENTER")
                        elif e.key == pygame.K_LEFT and self.cfg['time'] is None: self.handle_undo_redo("UNDO")
                        elif e.key == pygame.K_RIGHT and self.cfg['time'] is None: self.handle_undo_redo("REDO")
                        else:
                            if self.cfg['lang'] == 'Cac':
                                if e.unicode in "0123456789+-*": self.handle_input(e.unicode)
                            elif e.unicode.isalpha(): self.handle_input(k_upper)
                
                if e.type == pygame.KEYUP:
                    k_upper = e.unicode.upper()
                    if e.key == pygame.K_BACKSPACE and 'BACK' in self.key_map: self.key_map['BACK'].pressed = False
                    elif e.key == pygame.K_RETURN and 'ENTER' in self.key_map: self.key_map['ENTER'].pressed = False
                    elif k_upper in self.key_map: self.key_map[k_upper].pressed = False
                
                if self.paused:
                    self.btn_resume.update(mouse); self.btn_quit.update(mouse)
                    if self.btn_resume.clicked(e): self.paused = False
                    if self.btn_quit.clicked(e): 
                        self.save_state()
                        return "MENU"
                    continue
                
                if self.game_over:
                    if e.type == pygame.MOUSEBUTTONDOWN:
                         if pygame.Rect(WIDTH//2-100, HEIGHT//2+80, 200, 50).collidepoint(e.pos):
                             return "MENU"
                    continue

                if e.type == pygame.MOUSEBUTTONDOWN:
                    if self.btn_pause_icon.rect.collidepoint(e.pos): self.paused = True
                    
                    if self.cfg['time'] is None:
                        if self.undo_rect.collidepoint(e.pos): self.handle_undo_redo("UNDO")
                        if self.redo_rect.collidepoint(e.pos): self.handle_undo_redo("REDO")

                    for k in self.keys:
                        if k.rect.collidepoint(e.pos):
                            k.pressed = True
                            if k.kind == 'back': self.handle_input("BACK")
                            elif k.kind == 'enter': self.handle_input("ENTER")
                            else: self.handle_input(k.label)
                if e.type == pygame.MOUSEBUTTONUP:
                    for k in self.keys: k.pressed = False

            SCREEN.blit(IMG['bg_game'], (0,0))
            
            pygame.draw.rect(SCREEN, COLOR_WHITE, (920, 15, 5, 20))
            pygame.draw.rect(SCREEN, COLOR_WHITE, (930, 15, 5, 20))

            sx = 0
            if self.shake > 0:
                self.shake -= 1; sx = math.sin(self.shake * 0.5) * 8

            for r, row in enumerate(self.tiles):
                if r == self.logic.n and not self.game_over:
                    for c, tile in enumerate(row):
                        if self.cfg['lang'] == 'Cac':
                            if c < 5: tile.letter = self.guess[c] if c < len(self.guess) else ""
                            elif c == 5: tile.letter = "="
                            else:
                                idx_in_guess = c - 1
                                tile.letter = self.guess[idx_in_guess] if idx_in_guess < len(self.guess) else ""
                        else:
                            tile.letter = self.guess[c] if c < len(self.guess) else ""
                
                for tile in row:
                    tile.rect.x += sx; tile.update(); tile.draw(SCREEN); tile.rect.x -= sx

            for k in self.keys: k.draw(SCREEN)
            
            if self.cfg['time']:
                rem = max(0, int(self.cfg['time'] - elapsed_total))
                col = (255,50,50) if rem < 10 else COLOR_WHITE
                SCREEN.blit(FONT_PIXEL_32.render(f"{rem}", True, col), (30,30))
                
                if self.tpg_limit > 0:
                    t_turn = (current_t - self.turn_start_t) / 1000
                    rem_turn = max(0, self.tpg_limit - t_turn)
                    bar_w = 200
                    fill_w = int((rem_turn / self.tpg_limit) * bar_w)
                    pygame.draw.rect(SCREEN, (100,100,100), (WIDTH//2 - 100, 15, bar_w, 10))
                    pygame.draw.rect(SCREEN, (255, 200, 0), (WIDTH//2 - 100, 15, fill_w, 10))
            else:
                SCREEN.blit(FONT_PIXEL_20.render("INF", True, COLOR_WHITE), (30,30))
                undo_col = COLOR_WHITE if self.undo_rect.collidepoint(mouse) else (180,180,180)
                redo_col = COLOR_WHITE if self.redo_rect.collidepoint(mouse) else (180,180,180)
                draw_text_centered("< UNDO", FONT_PIXEL_20, undo_col, self.undo_rect, SCREEN)
                draw_text_centered("REDO >", FONT_PIXEL_20, redo_col, self.redo_rect, SCREEN)

            if self.msg_t > 0:
                self.msg_t -= 1
                t = FONT_PIXEL_24.render(self.msg, True, COLOR_WHITE)
                
                bg = pygame.Rect(WIDTH//2 - t.get_width()//2 - 10, 100, t.get_width()+20, 40)
                pygame.draw.rect(SCREEN, COLOR_BLACK, bg, border_radius=5)
                SCREEN.blit(t, (bg.x+10, bg.y+5))

            if self.paused:
                overlay = pygame.Surface((WIDTH,HEIGHT))
                overlay.set_alpha(200); overlay.fill(COLOR_BLACK)
                SCREEN.blit(overlay, (0,0))
                draw_text_centered("PAUSED", FONT_PIXEL_40, COLOR_WHITE, pygame.Rect(0, 100, WIDTH, 50), SCREEN)
                self.btn_resume.draw(SCREEN); self.btn_quit.draw(SCREEN)

            if self.game_over:
                overlay = pygame.Surface((WIDTH,HEIGHT))
                overlay.set_alpha(200); overlay.fill(COLOR_BLACK)
                SCREEN.blit(overlay, (0,0))
                panel_rect = IMG['panel'].get_rect(center=(WIDTH//2, HEIGHT//2))
                SCREEN.blit(IMG['panel'], panel_rect)
                
                res_txt = "VICTORY" if self.win else "DEFEAT"
                col = (50, 200, 50) if self.win else COLOR_RED_WRONG
                draw_text_centered(res_txt, FONT_PIXEL_40, col, panel_rect, SCREEN, (0, -60))
                
                target_font = FONT_BACKUP if self.cfg['lang'] == 'V' else FONT_VIET_24
                lbl = target_font.render(f"Word: {self.logic.word}", True, COLOR_BLACK)
                SCREEN.blit(lbl, lbl.get_rect(center=(panel_rect.centerx, panel_rect.centery - 10)))
                
                score = 0
                if self.win: score = self.logic.calculate_score(elapsed_total, self.cfg['tpg'])
                draw_text_centered(f"Score: +{score}", FONT_PIXEL_24, COLOR_BLACK, panel_rect, SCREEN, (0, 30))
                
                br = pygame.Rect(0,0,200,50); br.center = (WIDTH//2, HEIGHT//2 + 100)
                SCREEN.blit(IMG['btn'], br)
                draw_text_centered("CONTINUE", FONT_PIXEL_20, COLOR_BLACK, br, SCREEN)

            pygame.display.flip()

class SceneRank:
    def __init__(self):
        self.btn = Button(30, 30, "", is_back=True)
    def run(self):
        data = RANK_SYSTEM.get_top_players()
        while True:
            CLOCK.tick(60)
            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT: 
                    RANK_SYSTEM.save()

                    SAVE_MANAGER.save_disk()

                    return "EXIT"
                if self.btn.clicked(e): return "MENU"
            
            self.btn.update(pygame.mouse.get_pos())
            SCREEN.blit(IMG['bg_game'], (0,0))                    
            sy = 130
            headers = ["#", "PLAYER", "WON", "SCORE"]
            xs = [150, 300, 550, 700]
            for i, h in enumerate(headers):
                SCREEN.blit(FONT_PIXEL_24.render(h, True, (200,200,200)), (xs[i], sy-115))
            
            for i, p in enumerate(data):
                y = sy -80 + i * 24
                c = COLOR_WHITE
                if i==0: c = (255,215,0)
                elif i==1: c = (192,192,192)
                elif i==2: c = (205,127,50)
                
                if i == 0: SCREEN.blit(IMG['gold'], (xs[1] - 35, y - 5))
                elif i == 1: SCREEN.blit(IMG['silver'], (xs[1] - 35, y - 5))
                elif i == 2: SCREEN.blit(IMG['bronze'], (xs[1] - 35, y - 5))

                SCREEN.blit(FONT_PIXEL_20.render(str(i+1), True, c), (xs[0], y))
                SCREEN.blit(FONT_PIXEL_20.render(p['username'], True, c), (xs[1], y))
                SCREEN.blit(FONT_PIXEL_20.render(str(p['won']), True, c), (xs[2], y))
                SCREEN.blit(FONT_PIXEL_20.render(str(p['point']), True, c), (xs[3], y))

            self.btn.draw(SCREEN)
            pygame.display.flip()

class SceneRules:
    def __init__(self):
        self.btn = Button(30, 30, "", is_back=True)
    def run(self):
        while True:
             mouse = pygame.mouse.get_pos()
             for e in pygame.event.get():
                 if e.type == pygame.QUIT: 
                    RANK_SYSTEM.save()

                    SAVE_MANAGER.save_disk()

                    return "EXIT"
                 if self.btn.clicked(e): return "MENU"
             self.btn.update(mouse)
             SCREEN.fill(COLOR_BG_DARK)
             SCREEN.blit(IMG['bg_menu'], (0,0))
             s = pygame.Surface((800, 400)); s.set_alpha(200); s.fill(COLOR_BLACK)
             SCREEN.blit(s, (80, 70))
             draw_text_centered("RULES", FONT_PIXEL_40, (255, 215, 0), pygame.Rect(0, 80, WIDTH, 50), SCREEN)
             lines = [
                 "1. Guess the hidden word/equation.",
                 "2. Green = Correct Letter & Spot.",
                 "3. Yellow = Correct Letter, Wrong Spot.",
                 "4. Math Mode: 8 characters (e.g., 2+3*4=14).",
                 "5. Time Per Guess (TPG): Time Limit / 6.",
                 "6. Inf Mode: No points, Undo/Redo available.",
                 "7. Hard Mode: Must use revealed hints."
             ]
             for i, l in enumerate(lines):
                 t = FONT_PIXEL_24.render(l, True, COLOR_WHITE)
                 SCREEN.blit(t, (120, 150 + i*35))
             self.btn.draw(SCREEN)
             pygame.display.flip()

# _____________________________________________________________________________
#                                MAIN LOOP
# _____________________________________________________________________________

def main():
    state = "LOGIN"
    scenes = {
        "LOGIN": SceneLogin(),
        "MENU": SceneMenu(),
        "MODE_SELECT": SceneModeSelect(),
        "RANK": SceneRank(),
        "RULES": SceneRules(),
        "DELETE_CONFIRM": SceneDeleteConfirm() 
    }
    cfg = {}
    
    while True:
        if state == "GAME":
            game = SceneGame(cfg)
            state = game.run()
        elif state == "EXIT":
            RANK_SYSTEM.save()
            SAVE_MANAGER.save_disk()
            RANK_SYSTEM.save()

            SAVE_MANAGER.save_disk()

            pygame.quit()
            sys.exit()
        else:
            if state not in scenes: state = "MENU"
            res = scenes[state].run()
            if isinstance(res, tuple):
                state = res[0]
                cfg = res[1]
            else:
                state = res

if __name__ == "__main__":
    main()

"""
 _____________________________________________________________________________
                            CODE GỐC CHỈ BAO GỒM LOGIC
 _____________________________________________________________________________

 -----------------------------------------------------------------------------
                        LOGIC GỐC, KHÔNG LIÊN QUAN TỚI PYGAME
 -----------------------------------------------------------------------------

          
def generate_math_word():
    while True:
        a = random.randint(1,9)
        b = random.randint(1,9)
        c = random.randint(1,9)
        ops = [random.choice(['+','-','*']), random.choice(['+','-','*'])]
        expr = f"{a}{ops[0]}{b}{ops[1]}{c}"

        try:
            val = eval(expr)
            full = f"{expr}={val}"

            if 0 <= val < 100 and len(full) == 8:
                return full

        except:
            continue

def tudoanviet(word):
    guess = ''
    word = word.lower()

    for i in word:

        if i == ' ':
            continue

        if i in 'aáàạãảăắằặẵẳâậầẩấẫ':
            guess += 'a'

        elif i in 'uúùũủụưứừửữự':
            guess += 'u'

        elif i in 'oỏòóõọôồốổỗộơớờợỡở':
            guess += 'o'

        elif i in 'eéèẻẽẹêểễếềệ':
            guess += 'e'

        elif i in 'iíìịĩỉ':
            guess += 'i'

        elif i in 'yýỳỷỹỵ':
            guess += 'y'

        elif i in 'đ':
            guess += 'd'

        else:
            guess += i

    return guess

class Player():
    def __init__(self,username,password):
        self.username = username
        self.password = password
        self.game_played = 0
        self.game_won = 0
        self.point = 0

    def update(self,win,point):
        self.game_played +=1
        if win:
            self.game_won +=1
            self.point += point



class Rankboard:
    def __init__(self, path="data/rank.json"):
        self.path = path
        self.players = {}
        self.load()

    def load(self):
        if not os.path.exists(self.path):
            return
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for name, info in data.items():
                p = Player(name, info["password"])
                p.game_played = info["played"]
                p.game_won = info["won"]
                p.point = info["point"]
                self.players[name] = p

    def save(self):
        data = {}
        for name, p in self.players.items():
            data[name] = {
                "password": p.password,
                "played": p.game_played,
                "won": p.game_won,
                "point": p.point
            }
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def login(self, username, password):
        if username not in self.players:
            return None
        if self.players[username].password != password:
            return None
        return self.players[username]

    def register(self, username, password):
        if username in self.players:
            return None
        self.players[username] = Player(username, password)
        self.save()
        return self.players[username]

    def top(self, n=20):
        return sorted(self.players.values(), key=lambda p: p.point, reverse=True)[:n]


class GameState():

    def __init__(self,hard,word,language,time_limit,mode = 0,nmax = 6, length = 5):
        self.mode = mode
        self.word = word
        self.status = 'playing'
        self.n = 0
        self.language = language
        self.time_limit = time_limit
        self.hard = hard
        self.history = []

        if self.mode == 0 and self.language == 'E':
            self.nmax = 6
            self.len = 5

        elif self.mode == 0 and self.language == 'V':
            self.nmax = 6
            self.len = 7

        elif self.mode == 0 and self.language == 'Cac':
            self.nmax = 6
            self.len = 8
            oops = ['+','-','*']

        else:
            if self.nmax == 'inf':
                self.nmax = 9999

            else:
                self.nmax = int(nmax)
                self.len = length

        self.is_math = (self.language == 'Cac')

        if self.hard:
            self.locked_green = [None] * self.len
            self.required_yellow = set()

        if self.is_math:
            self.forbidden_ops = set()
            self.required_ops = set()

        if self.len == 5 and self.language == 'E':
            with open('vocabulary.txt', 'r') as f:
                self.dictionary = set(f.read().splitlines())
        
        if self.language == 'V':
            self.word_norm = tudoanviet(self.word)

        else:
            self.word_norm = self.word




    def check(self,guess):
        true = []

        if self.language == 'Cac':
            if not self.validate_math_guess(guess, self.hard):
                return None


        if self.hard == True:
            # kiểm tra ô xanh bị khóa
            for i in range(self.len):
                if self.locked_green[i] is not None:
                    if guess[i] != self.locked_green[i]:
                        return None  # guess không hợp lệ, KHÔNG trừ lượt

            # kiểm tra chữ vàng bắt buộc
            for ch in self.required_yellow:
                if ch not in guess:
                    return None
                
        if self.language == 'E' and self.len == 5:
            if guess not in self.dictionary:
                return 'not_in_dict'  

        self.n+=1

        for i in range(self.len):
            
            if guess[i] == self.word_norm[i]:
                true.append('green') #Đúng chữ đúng vị trí
            
            elif guess[i] in self.word_norm:
                true.append('yellow') #Đúng chữ sai vị trí
            
            else:
                true.append('red') #Sai
        
        if self.hard == True:
            
            for i in range(self.len):
            
                if true[i] == 'green':
                    self.locked_green[i] = self.word_norm[i]
            
                    if self.word_norm[i] in self.required_yellow:
                        self.required_yellow.remove(self.word_norm[i])
            
                elif true[i] == 'yellow':
                    self.required_yellow.add(guess[i])



        if true.count('green') == self.len:
            self.status = 'win'

        elif self.n == self.nmax and self.status != 'win':
            self.status = 'lose'

        self.history.append((guess, true))
        return true

    
    def ScoreCaculator(self, time_left,time_per_guess):
        
        if self.status == 'lose' or self.time_limit is None:
            score = 0
        
        else:
        
            if self.language == 'V':  # tiếng Việt
                score = 100

            elif self.language== 'E': # Eng
                score = 120
            
            elif self.language == 'Cac': # phép toán
                score = 150
            
            if time_per_guess == 1:
                score *= 1.4
            
            if self.time_limit == 90:
                score *= 1.2
            
            if self.hard == True:
                score *= 1.2
        
            #time bonus
            score *= (1 + 0.15 * ( max(0, time_left / self.time_limit) ** 3))
        return score

    def validate_math_guess(self,guess: str, hard_mode=True):
        
        # 1. phải có đúng 1 dấu =
        if guess.count('=') != 1:
            return False

        left, right = guess.split('=')

        # 2. phải có số ở vế phải
        if not right.isdigit():
            return False

        try:
            value = eval(left)

        except:
            return False

        # 3. hard mode: kết quả phải đúng
        if hard_mode:
            return value == int(right)

        return True
            

def maingame():


    hard = input("Hard mode? (on/off): ").lower() == 'on'
    language = input('E/V/Cac')
    time_limit = int(input('90s/120s/inf'))
    mode = int(input())

    if language == 'E' and mode == 0:
        with open('vocabulary.txt','r',encoding = 'utf-8') as f:   #chọn 1 từ ngẫu nhiên từ file vocabulary.txt
            lines = f.read().splitlines()
            word = random.choice(lines)

    elif language == 'V' and mode == 0:
        with open('vocabularyV.txt','r',encoding = 'utf-8') as f:   #chọn 1 từ ngẫu nhiên từ file vocabulary.txt
            lines = f.read().splitlines()[1:-2]
            word = random.choice(lines)

    elif language == 'Cac' and mode == 0:
        word = generate_math_word()

    if mode == 0:
        play = GameState(hard, word, language, time_limit,mode)
    
    else:
        nmax = (input('Nhập số lượt đoán (nhập inf để có vô hạn lượt)'))
        play = GameState(hard, word, language, time_limit,mode,nmax)

    start = 0
    
    while start != '1':
        start = input('Press 1 to start!!!')
    
    while play.status == 'playing':
        guess = input()
        result = play.check(guess)
        if result is None:
            print("Hard mode: phải giữ chữ xanh & dùng lại chữ vàng")
            continue
      
---------------------------------------------------------------------------
                UI TỪNG PHẦN (CÓ SỬ DỤNG AI ĐỂ VIẾT TRƯỚC SƯỜN CODE)
---------------------------------------------------------------------------
$$$SCENEGAME

# ================= INIT =================
pygame.init()
WIDTH, HEIGHT = 960, 540
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Wordle Night - Side Layout")
CLOCK = pygame.time.Clock()

# ================= ASSETS =================
BG_GAME = pygame.image.load("assets/bg/bg_game.png").convert()
FONT = pygame.font.Font("assets/fonts/pixel.ttf", 20)

TILES = {
    "empty": pygame.image.load("assets/tiles/tile_empty.png").convert_alpha(),
    "green": pygame.image.load("assets/tiles/tile_green.png").convert_alpha(),
    "yellow": pygame.image.load("assets/tiles/tile_yellow.png").convert_alpha(),
    "disabled": pygame.image.load("assets/tiles/tile_disabled.png").convert_alpha(),
}

KEYS = {
    "normal": pygame.image.load("assets/keys/key_normal.png").convert_alpha(),
    "green": pygame.image.load("assets/keys/key_green.png").convert_alpha(),
    "yellow": pygame.image.load("assets/keys/key_yellow.png").convert_alpha(),
    "disabled": pygame.image.load("assets/keys/key_disabled.png").convert_alpha(),
    "enter": pygame.image.load("assets/keys/key_enter.png").convert_alpha(),
    "enter_press": pygame.image.load("assets/keys/key_enter_press.png").convert_alpha(),
    "back": pygame.image.load("assets/keys/key_backspace.png").convert_alpha(),
    "back_press": pygame.image.load("assets/keys/key_backspace_press.png").convert_alpha(),
}

# ================= TILE =================
class Tile:
    SIZE = 60
    GAP = 4

    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, self.SIZE, self.SIZE)
        self.letter = ""
        self.state = "empty"

    def draw(self, screen):
        screen.blit(TILES[self.state], self.rect)
        if self.letter:
            txt = FONT.render(self.letter, True, (255, 255, 255))
            screen.blit(txt, txt.get_rect(center=self.rect.center))

# ================= KEY =================
class Key:
    WIDTH = 46
    HEIGHT = 56
    GAP = 6

    def __init__(self, x, y, label="", kind="normal", width=None):
        self.kind = kind
        self.label = label
        self.width = width if width else self.WIDTH
        self.rect = pygame.Rect(x, y, self.width, self.HEIGHT)
        self.pressed = False
        self.state = "normal"

    def draw(self, screen):
        if self.kind == "enter":
            img = KEYS["enter_press"] if self.pressed else KEYS["enter"]
            screen.blit(img, self.rect)
            return

        if self.kind == "back":
            img = KEYS["back_press"] if self.pressed else KEYS["back"]
            screen.blit(img, self.rect)
            return

        screen.blit(KEYS[self.state], self.rect)
        txt = FONT.render(self.label, True, (0, 0, 0))
        screen.blit(txt, txt.get_rect(center=self.rect.center))

# ================= GAME UI =================
class GameUI:
    def __init__(self):
        self.tiles = []
        self.keys = []
        self.create_tiles()
        self.create_keyboard()

    def create_tiles(self):
        grid_w = 5 * Tile.SIZE + 4 * Tile.GAP
        start_x = WIDTH - grid_w - 40
        start_y = HEIGHT // 2 - (6 * Tile.SIZE + 5 * Tile.GAP) // 2

        for r in range(6):
            row = []
            for c in range(5):
                x = start_x + c * (Tile.SIZE + Tile.GAP)
                y = start_y + r * (Tile.SIZE + Tile.GAP)
                row.append(Tile(x, y))
            self.tiles.append(row)

    def create_keyboard(self):
        rows = ["QWERTYUIOP", "ASDFGHJKL",'ZXCVBNM']
        start_x = 40
        start_y = HEIGHT // 2 - 120

        for r, row in enumerate(rows):
            offset = 0
            if r == 1:
                offset = (Key.WIDTH + Key.GAP) // 2     
            if r == 2:
                offset = Key.WIDTH + Key.GAP   + 35      

            for i, ch in enumerate(row):
                x = start_x + offset + i * (Key.WIDTH + Key.GAP)
                y = start_y + r * (Key.HEIGHT + Key.GAP)
                self.keys.append(Key(x, y, ch))


        third_row_y = start_y + 2 * (Key.HEIGHT + Key.GAP)

        # BACKSPACE (thẳng cột Q, A)
        self.keys.append(
            Key(start_x - 20, third_row_y,'Backspace', kind="back", width=72)
        )

        # ENTER (bên phải)
        z_row_width = len(rows[2]) * (Key.WIDTH + Key.GAP)
        self.keys.append(
            Key(500,
            230,'Enter',
            kind="enter",
            width=72)
        )

    def draw(self):
        SCREEN.blit(BG_GAME, (0, 0))

        for row in self.tiles:
            for tile in row:
                tile.draw(SCREEN)

        for key in self.keys:
            key.draw(SCREEN)

--------------------------------------------------------

$$$SCENEMENU

# ================= INIT =================
pygame.init()
WIDTH, HEIGHT = 960, 540
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Wordle Night")
CLOCK = pygame.time.Clock()

# ================= LOAD ASSETS =================
BG_MENU = pygame.image.load("assets/bg/bg_menu.png").convert()

LOGO = pygame.image.load("assets/ui/logo.png").convert_alpha()
LOGO = pygame.transform.scale(LOGO,(423,164))
BTN_IMG = pygame.image.load("assets/ui/btn.png").convert_alpha()
BTN_HOVER = pygame.image.load("assets/ui/btn_hover.png").convert_alpha()

FONT = pygame.font.Font("assets/fonts/pixel.ttf", 32)

# ================= BUTTON =================
class Button:
    def __init__(self, x, y, text):
        self.image = BTN_IMG
        self.hover_image = BTN_HOVER

        self.rect = self.image.get_rect(center=(x, y))

        self.text_surf = FONT.render(text, True, (0,0,0))
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)

    def draw(self, screen):
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            screen.blit(self.hover_image, self.rect)
        else:
            screen.blit(self.image, self.rect)

        self.text_rect.center = self.rect.center
        screen.blit(self.text_surf, self.text_rect)

    def clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )

# ================= MENU =================
class Menu:
    def __init__(self):
        cx = WIDTH // 2

        # Logo
        self.logo_rect = LOGO.get_rect(midtop=(cx, 70))

        # Buttons
        start_y = self.logo_rect.bottom + 80
        gap = 70

        self.play_btn = Button(cx, start_y, "Play")
        self.rank_btn = Button(cx, start_y + gap, "Rankboard")
        self.rules_btn = Button(cx, start_y + gap * 2, "Rules")

    def update(self, events):
        for event in events:
            if self.play_btn.clicked(event):
                print(" Play")
                return "GAME"

            if self.rank_btn.clicked(event):
                print(" Rankboard")
                return "RANK"

            if self.rules_btn.clicked(event):
                print(" Rules")
                return "RULES"

        return "MENU"

    def draw(self):
        SCREEN.blit(BG_MENU, (0, 0))
        SCREEN.blit(LOGO, self.logo_rect)

        self.play_btn.draw(SCREEN)
        self.rank_btn.draw(SCREEN)
        self.rules_btn.draw(SCREEN)

-------------------------------------------------------------------------------

$$$SCENELOGIN

# ================== WINDOW ==================
SCREEN = pygame.display.set_mode((960, 540))
pygame.display.set_caption("WORDLE NIGHT")
CLOCK = pygame.time.Clock()

ASSETS = "assets/"

# ================== LOAD ==================
bg = pygame.image.load(ASSETS + "bg/bg_game.png").convert()
logo = pygame.image.load(ASSETS + "ui/logo.png").convert_alpha()
input_img = pygame.image.load(ASSETS + "ui/input.png").convert_alpha()
input_focus = pygame.image.load(ASSETS + "ui/input_focus.png").convert_alpha()

btn = pygame.image.load(ASSETS + "ui/btn.png").convert_alpha()
btn_hover = pygame.image.load(ASSETS + "ui/btn_hover.png").convert_alpha()

FONT = pygame.font.Font(ASSETS + "fonts/pixel.ttf", 20)

# ================== TEXT UTILS ==================
def draw_text_bold(text, x, y, color=(255,255,255)):
    text = text.upper()
    base = FONT.render(text, True, color)
    for dx, dy in [(0,0),(1,0),(0,1),(1,1)]:
        SCREEN.blit(base, (x+dx, y+dy))

# ================== INPUT ==================
class InputBox:
    def __init__(self, center_x, y, password=False):
        self.image = input_img
        self.focus_img = input_focus
        self.rect = self.image.get_rect(midtop=(center_x, y))
        self.active = False
        self.text = ""
        self.password = password

    def handle(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(e.pos)

        if e.type == pygame.KEYDOWN and self.active:
            if e.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif len(self.text) < 14 and e.unicode.isprintable():
                self.text += e.unicode.upper()

    def draw(self):
        img = self.focus_img if self.active else self.image
        SCREEN.blit(img, self.rect)

        show = "*" * len(self.text) if self.password else self.text
        draw_text_bold(
            show,
            self.rect.x + 14,
            self.rect.y + self.rect.height//2 - 10
        )

# ================== BUTTON ==================
class Button:
    def __init__(self, center_x, y, text):
        self.text = text
        self.rect = btn.get_rect(midtop=(center_x, y))
        self.hover = False

    def update(self, mouse):
        self.hover = self.rect.collidepoint(mouse)

    def draw(self):
        SCREEN.blit(btn_hover if self.hover else btn, self.rect)
        draw_text_bold(
            self.text,
            self.rect.centerx - 35,
            self.rect.centery - 10,
        )

# ================== LAYOUT ==================
bg = pygame.transform.scale(bg, SCREEN.get_size())

logo_rect = logo.get_rect(center=(480, 110))

username = InputBox(480, 240)
password = InputBox(480, 320, password=True)

login_btn = Button(370-40, 400, "LOGIN")
register_btn = Button(590+40, 400, "REGISTER")

--------------------------------------------------------------------

$$$SCENEMODE

pygame.init()
WIDTH, HEIGHT = 960, 540
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Wordle Mode Select")
CLOCK = pygame.time.Clock()

# ================= ASSETS =================
BG_MENU = pygame.image.load("assets/bg/bg_menu.png").convert()

PANEL_RAW = pygame.image.load("assets/ui/panel.png").convert_alpha()
BTN = pygame.image.load("assets/ui/btn.png").convert_alpha()
BTN_HOVER = pygame.image.load("assets/ui/btn_hover.png").convert_alpha()
BTN = pygame.transform.scale(BTN, (200,53))
BTN_HOVER = pygame.transform.scale(BTN_HOVER, (200,53))
TOGGLE_ON = pygame.image.load("assets/ui/toggle_on.png").convert_alpha()
TOGGLE_OFF = pygame.image.load("assets/ui/toggle_off.png").convert_alpha()

FONT_TITLE = pygame.font.Font("assets/fonts/pixel.ttf", 36)
FONT = pygame.font.Font("assets/fonts/pixel.ttf", 24)

# ================= PANEL TRANSPARENCY =================
PANEL = PANEL_RAW.copy()
PANEL.set_alpha(220)   

# ================= UI COMPONENTS =================
class Toggle:
    def __init__(self, x, y, value=False):
        self.value = value
        self.rect = TOGGLE_ON.get_rect(topleft=(x, y))

    def draw(self, screen):
        screen.blit(TOGGLE_ON if self.value else TOGGLE_OFF, self.rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.value = not self.value

class OptionButton:
    def __init__(self, x, y, text):
        self.rect = BTN.get_rect(topleft=(x, y))
        self.text = text

    def draw(self, screen):
        img = BTN_HOVER if self.rect.collidepoint(pygame.mouse.get_pos()) else BTN
        screen.blit(img, self.rect)

        txt = FONT.render(self.text, True, (0, 0, 0))
        screen.blit(txt, txt.get_rect(center=self.rect.center))

    def clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )



# ================= MODE SELECT =================
class ModeSelect:
    def __init__(self):
        self.panel_rect = PANEL.get_rect(center=(WIDTH // 2, 250))

        px, py = self.panel_rect.topleft
        self.start_y = py + 80
        self.gap = 50

        # State
        self.languages = ["English", "Vietnamese", "Math"]
        self.lang_index = 0
        self.language = self.languages[self.lang_index]

        self.btn_lang = OptionButton(px + 260, self.start_y, self.language)

        self.time_limits = [60,90,None]
        self.tlm_index = 0
        self.time_limit = self.time_limits[self.tlm_index]
        # Toggles
        self.toggle_time = Toggle(px + 470, self.start_y + self.gap * 3.5)
        self.toggle_hard = Toggle(px + 470, self.start_y + self.gap * 5)

        # Buttons
        self.btn_lang = OptionButton(px + 400, self.start_y + self.gap * 0.5, self.language)
        self.btn_tlm = OptionButton(px + 400, self.start_y + self.gap * 2, self.format_time_limit())

        self.btn_start = OptionButton(
            px + self.panel_rect.width // 2 - BTN.get_width() // 2,
            py + self.panel_rect.height - 80,
            "START!!!"
        )
    def format_time_limit(self):
        return f"{self.time_limit}s" if self.time_limit else "Infinity"
    
    def label(self, text, x, y):
        SCREEN.blit(FONT.render(text, True, (0, 0, 0)), (x, y))

    def draw(self):
        # BG dùng chung với MENU
        SCREEN.blit(BG_MENU, (0, 0))

        # Panel trong suốt
        SCREEN.blit(PANEL, self.panel_rect)


        px, py = self.panel_rect.topleft

        self.label("Language:", px + 40, self.start_y + (0.5 * self.gap))
        self.btn_lang.draw(SCREEN)

        self.label("Time:", px + 40, self.start_y + self.gap * 2)
        self.btn_tlm.draw(SCREEN)

        self.label("Time per Guess:", px + 40, self.start_y + self.gap * 3.5)
        self.toggle_time.draw(SCREEN)

        self.label("Hard Mode:", px + 40, self.start_y + self.gap * 5)
        self.toggle_hard.draw(SCREEN)

        self.btn_start.draw(SCREEN)

    def handle_event(self, event):
        self.toggle_time.handle_event(event)
        self.toggle_hard.handle_event(event)

        if self.btn_lang.clicked(event):
            self.lang_index = (self.lang_index + 1) % len(self.languages)
            self.language = self.languages[self.lang_index]
            self.btn_lang.text = self.language

        if self.btn_tlm.clicked(event):
            self.tlm_index = (self.tlm_index + 1) % len(self.time_limits)
            self.time_limit = self.time_limits[self.tlm_index]
            self.btn_tlm.text = self.format_time_limit()



        if self.btn_start.clicked(event):
            print("START GAME")
            print("Language:", self.language)
            print("Time limit:", self.time_limit)
            print("Time per Guess:", self.toggle_time.value)
            print("Hard Mode:", self.toggle_hard.value)


"""