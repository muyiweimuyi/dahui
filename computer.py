from pickle import FALSE
from webbrowser import get
import os
import json
import sys
import pygame
from pygame.constants import K_RALT
text_size=20

# ========== 全局变量 ==========
computer_flag = False
computer_sprite = pygame.sprite.Group()
# ========== 布局常量（你可以在这里调整位置和数量）==========
# 终端机整体位置
COMPUTER_X = 350     # 终端机左上角X
COMPUTER_Y = 100   # 终端机左上角Y
# 屏幕位置和大小
SCREEN_X = COMPUTER_X + 20
SCREEN_Y = COMPUTER_Y + 20
SCREEN_W = 600
SCREEN_H = 400
text_y=SCREEN_H//text_size
text_x=SCREEN_X//text_size
# 插槽布局
SOCKET_COLS = 4       # 每行几个插槽
SOCKET_ROWS = 2       # 共几行
SOCKET_GAP_X = 100     # 插槽之间的水平间距
SOCKET_GAP_Y = 100    # 插槽之间的垂直间距
SOCKET_START_X = COMPUTER_X + 20
SOCKET_START_Y = COMPUTER_Y + 450

# 初始卡片布局
CARD_COUNT = 6        # 初始有多少张卡片
CARD_START_X = COMPUTER_X + 50
CARD_START_Y = COMPUTER_Y +650
CARD_GAP_X = 100       # 卡片之间的间距
#==========读写入==========
PROGRAM_DIR="program"
# ========== 精灵类定义 ==========

class Paper(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.image.load("paper_start.png").convert_alpha()
        self.rect = self.image.get_rect(center=(x, y))
        self.flag = "unchoose"      # 状态：unchoose / choose / inserted
        self.w = self.rect.width
        self.h = self.rect.height
        self.target_socket = None   # 插入的目标插槽

    def update(self, mouse_pos, mouse_click):
        if self.flag == "choose":
            # 正在拖拽：跟着鼠标走，松开时放下
            self.rect.center = mouse_pos
            if not mouse_click:
                self.flag = "unchoose"
        elif self.flag == "unchoose":
            # 空闲状态：点击选中
            if self.rect.collidepoint(mouse_pos) and mouse_click:
                self.flag = "choose"
        elif self.flag == "inserted":
            # 已插入插槽：点击后弹出
            if self.rect.collidepoint(mouse_pos) and mouse_click:
                self.eject()   # 调用弹出方法
                self.flag = "choose"  # 立即进入拖拽状态，避免再次吸附

    def snap_to_socket(self, socket):
        """插入到指定插槽"""
        self.flag = "inserted"
        self.target_socket = socket
        self.rect.center = socket.rect.center
    def eject(self):
            if self.target_socket:
                self.target_socket.inserted_paper = None
                self.target_socket = None
            self.flag = "unchoose"
            self.rect.y -= 10
class ComputerScreen(pygame.sprite.Sprite):
    def __init__(self, x, y, width=300, height=200):
        super().__init__()
        global text_x
        global text_y
        global text_size
        global PROGRAM_DIR
        self.font = pygame.font.Font("unifont-16.0.04.ttf", text_size)
        self.width = width
        self.height = height
        self.image = pygame.Surface((width, height))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.is_on = True
        self.screen_color = (0, 0, 0)
        self.output_lines = ["ASM-2100 Terminal Ready.", "Type .help for commands."]
        self.text = []
        self.input_text=""
        self.scoll_pos=0
        self.input_pos=0
        self.color=(0,255,0)
        self.vivisible_lines=[]
        self.mode="command"
        self.font_y=self.font.get_height()
        self.current_file = ""
    def update(self):
        if not self.is_on:
            return

        if self.mode == "command":
            self.update_command_display()
        elif self.mode == "editor":
            self.update_editor_display()
    def handle(self, event):
        global computer_flag
        if event.type != pygame.KEYDOWN:
                return

        # 开关电脑
        keys = pygame.key.get_pressed()
        if event.key == pygame.K_e and  (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]):
            computer_flag = not computer_flag
            self.update()
            return

        # 电脑关闭时不处理其他按键
        if not computer_flag:
            return

        # 根据模式分发
        if self.mode == "command":
            self.command_line(event)
        elif self.mode == "editor":
            self.editor_line(event)   # 以后拆分编辑器
#===============渲染字符=====
    def get_outputline(self):
        total = len(self.output_lines)
        end = total - self.scoll_pos
        start = max(0, end - (text_y-1))
        return self.output_lines[start:end]
    def get_cursor_x(self):
        prompt = ">"
        prompt_width = self.font.size(prompt)[0]
        text_before_cursor = self.input_text[:self.input_pos]
        text_width = self.font.size(text_before_cursor)[0]
        return prompt_width + text_width
    def editor_line(self, event):
        line = self.edit_lines[self.edit_line_index]

        if event.unicode and event.unicode.isprintable():
            char = event.unicode
            self.edit_lines[self.edit_line_index] = (
                line[:self.input_pos] + char + line[self.input_pos:]
            )
            self.input_pos += 1

        elif event.key == pygame.K_BACKSPACE:
            if self.input_pos > 0:
                self.edit_lines[self.edit_line_index] = (
                    line[:self.input_pos - 1] + line[self.input_pos:]
                )
                self.input_pos -= 1

        elif event.key == pygame.K_LEFT:
            if self.input_pos > 0:
                self.input_pos -= 1

        elif event.key == pygame.K_RIGHT:
            if self.input_pos < len(line):
                self.input_pos += 1

        elif event.key == pygame.K_RETURN:
            # 当前行按回车：在该行下方插入一个新行
            self.edit_lines.insert(self.edit_line_index + 1, "")
            self.edit_line_index += 1
            self.input_pos = 0

        elif event.key == pygame.K_UP:
            if self.edit_line_index > 0:
                self.edit_line_index -= 1
                self.input_pos = min(self.input_pos, len(self.edit_lines[self.edit_line_index]))

        elif event.key == pygame.K_DOWN:
            if self.edit_line_index < len(self.edit_lines) - 1:
                self.edit_line_index += 1
                self.input_pos = min(self.input_pos, len(self.edit_lines[self.edit_line_index]))
        elif event.key ==pygame.K_ESCAPE:
            self.save_program(self.current_file)
    def update_editor_display(self):
        self.image.fill(self.screen_color)

        y = 0
        for i, line in enumerate(self.edit_lines):
            if i == self.edit_line_index:
                prefix = "> "
            else:
                prefix = "  "
            text = self.font.render(prefix + line, True, self.color)
            self.image.blit(text, (0, y))
            y += text_size

        # 绘制光标
        line = self.edit_lines[self.edit_line_index]
        before = line[:self.input_pos]
        cursor_x = self.font.size("> " + before)[0]
        cursor_y = self.edit_line_index * text_size
        pygame.draw.line(
            self.image,
            self.color,
            (cursor_x, cursor_y),
            (cursor_x, cursor_y + text_size)
        )
    def command_line(self, event):
        if event.unicode and event.unicode.isprintable():
            char = event.unicode
            self.input_text = self.input_text[:self.input_pos] + char + self.input_text[self.input_pos:]
            self.input_pos += 1

        elif event.key == pygame.K_BACKSPACE:
            if self.input_pos > 0:
                self.input_text = self.input_text[:self.input_pos - 1] + self.input_text[self.input_pos:]
                self.input_pos -= 1

        elif event.key == pygame.K_RETURN:
            self.output_lines.append(">" + self.input_text)
            # 这里以后可以调用命令解析
            self.execute_command()   # 如果有命令解析函数
            self.input_text = ""
            self.input_pos = 0
            self.scoll_pos = 0

        elif event.key == pygame.K_LEFT:
            if self.input_pos > 0:
                self.input_pos -= 1

        elif event.key == pygame.K_RIGHT:
            if self.input_pos < len(self.input_text):
                self.input_pos += 1

        elif event.key == pygame.K_UP:
            max_scroll = max(0, len(self.output_lines) - (self.height // self.font_y - 1))
            if self.scoll_pos < max_scroll:
                self.scoll_pos += 1

        elif event.key == pygame.K_DOWN:
            if self.scoll_pos > 0:
                self.scoll_pos -= 1
    def update_command_display(self):
        self.image.fill(self.screen_color)

        # 绘制历史输出
        self.visible_lines = self.get_outputline()
        line = 0
        for lines in self.visible_lines:
            text = self.font.render(lines, True, self.color)
            self.image.blit(text, (0, line * text_size))
            line += 1

        # 绘制输入行
        input_y = (text_y - 1) * text_size
        text_1 = self.font.render(">" + self.input_text, True, self.color)
        self.image.blit(text_1, (0, input_y))

        # 绘制光标
        input_x = self.get_cursor_x()
        pygame.draw.line(
            self.image,
            self.color,
            (input_x + 1, input_y),               # 加1是因为提示符 ">"
            (input_x + 1, input_y + text_size)
        )
 #=========写入与读取=============================
    def load_program(self, name):
        filepath = os.path.join(PROGRAM_DIR, name + ".json")

        # 文件不存在，创建空文件
        if not os.path.exists(filepath):
            if not os.path.exists(PROGRAM_DIR):
                os.makedirs(PROGRAM_DIR)

            empty_data = {
                "name": name,
                "lines": [""]
            }
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(empty_data, f, ensure_ascii=False, indent=2)

            self.edit_lines = [""]
            self.edit_line_index = 0
            self.input_pos = 0
            self.output_lines.append(f"已创建新文件 {name}")
            self.mode="editor"
            return True

        # 文件存在，正常读取
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.edit_lines = data.get("lines", [""])
            self.edit_line_index = 0
            self.input_pos = 0
            self.output_lines.append(f"已读取 {name}")
            self.mode="editor"
            return True

        except Exception as e:
            self.output_lines.append(f"读取失败: {e}")
            return False
        
    def save_program(self, name):
        if not name:
            self.output_lines.append("没有文件名，无法保存")
            return False

        if not os.path.exists(PROGRAM_DIR):
            os.makedirs(PROGRAM_DIR)

        filepath = os.path.join(PROGRAM_DIR, name + ".json")

        data = {
            "name": name,
            "lines": self.edit_lines,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.output_lines.append(f"已保存 {name}")
        self.mode = "command"
        return True
    def list_programs(self):
        """列出 programs 目录下所有可读的 JSON 文件"""
        if not os.path.exists(PROGRAM_DIR):
            self.output_lines.append("没有程序目录")
            return []

        try:
            files = os.listdir(PROGRAM_DIR)
            json_files = [f for f in files if f.endswith(".json")]

            if not json_files:
                self.output_lines.append("没有可读的程序")
                return []

            self.output_lines.append("可用的程序:")
            for f in json_files:
                name = f[:-5]  # 去掉 .json 后缀
                self.output_lines.append(f"  {name}")

            return json_files

        except Exception as e:
            self.output_lines.append(f"读取目录失败: {e}")
            return []
    def run_program(self, name):
        """运行指定名字的程序文件"""
        filepath = os.path.join(PROGRAM_DIR, name + ".json")

        if not os.path.exists(filepath):
            self.output_lines.append(f"文件不存在: {name}")
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            lines = data.get("lines", [])      
            self.execute_lines(lines)

        except Exception as e:
            self.output_lines.append(f"读取失败: {e}")
#=====================代码解释================================
    def execute_lines(self, lines):
        """逐行解释执行代码"""
        self.pc = 0
        self.loop_stack = []  # 用于循环跳转

        while self.pc < len(lines):
            line = lines[self.pc].strip()

            # 跳过空行和注释
            if not line or line.startswith("//"):
                self.pc += 1
                continue

            # PRINT
            if line.startswith("PRINT"):
                self.execute_print(line,self.current_file)
                self.pc += 1

            # LOOP
            elif line.startswith("LOOP"):
                self.execute_loop(lines)

            # IF
            elif line.startswith("IF"):
                self.execute_if(line)
                self.pc += 1

            # END（循环外不应该出现，忽略）
            elif line == "END":
                self.output_lines.append("错误: 孤立的 END")
                self.pc += 1

            # 未识别
            else:
                self.output_lines.append(f"错误: 无法识别指令 '{line}'")
                return

    def execute_print(self, line,name):
        """执行 PRINT 语句"""
        content = line[5:].strip()

        # 字符串
        if content.startswith('"') and content.endswith('"'):
            self.output_lines.append(name + " " + content[1:-1])

        # 变量
        elif content in self.variables:
            self.output_lines.append(name + " " + str(self.variables[content]))

        # 数字或表达式（先直接输出）
        else:
            self.output_lines.append(name + " " + content)

    def execute_loop(self, lines):
        """执行 LOOP 语句，支持嵌套"""
        parts = lines[self.pc].strip().split()
        if len(parts) < 2:
            self.output_lines.append("错误: LOOP 缺少次数")
            self.pc += 1
            return

        # 循环次数（可以是数字或变量）
        if parts[1] in self.variables:
            count = self.variables[parts[1]]
        else:
            try:
                count = int(parts[1])
            except:
                self.output_lines.append(f"错误: LOOP 次数无效 '{parts[1]}'")
                self.pc += 1
                return

        # 找到循环体的开始和结束
        start = self.pc + 1
        end = start
        depth = 0

        while end < len(lines):
            l = lines[end].strip()
            if l.startswith("LOOP"):
                depth += 1
            elif l == "END":
                if depth == 0:
                    break
                else:
                    depth -= 1
            end += 1

        if end >= len(lines):
            self.output_lines.append("错误: LOOP 缺少 END")
            return

        # 执行循环
        for _ in range(count):
            i = start
            while i < end:
                l = lines[i].strip()
                if not l or l.startswith("//"):
                    i += 1
                    continue

                if l.startswith("PRINT"):
                    self.execute_print(l)

                elif l.startswith("IF"):
                    self.execute_if(l)

                elif l.startswith("LOOP"):
                    # 嵌套循环
                    self.pc = i
                    self.execute_loop(lines)
                    i = self.pc

                i += 1

        # 跳过后面的代码，直到循环结束
        self.pc = end

    def execute_if(self, line):
        """执行 IF 语句"""
        if " THEN " not in line:
            self.output_lines.append("错误: IF 缺少 THEN")
            return

        condition = line[3:line.index(" THEN ")].strip()
        action = line[line.index(" THEN ") + 6:].strip()

        if self.eval_condition(condition):
            if action.startswith("PRINT"):
                self.execute_print(action)
            elif action.startswith("SET"):
                # 以后实现 SET
                pass
            else:
                self.output_lines.append(f"错误: IF 后无法执行 '{action}'")

    def eval_condition(self, condition):
        """简单条件判断，支持变量和数字"""
        for op in [">=", "<=", "==", ">", "<"]:
            if op in condition:
                left, right = condition.split(op)
                left = left.strip()
                right = right.strip()

                # 获取左边值
                if left in self.variables:
                    left_val = self.variables[left]
                else:
                    try:
                        left_val = int(left)
                    except:
                        return False

                # 获取右边值
                if right in self.variables:
                    right_val = self.variables[right]
                else:
                    try:
                        right_val = int(right)
                    except:
                        return False

                # 比较
                if op == ">":
                    return left_val > right_val
                elif op == "<":
                    return left_val < right_val
                elif op == ">=":
                    return left_val >= right_val
                elif op == "<=":
                    return left_val <= right_val
                elif op == "==":
                    return left_val == right_val

        return False

    def execute_if(self, line):
        """执行 IF 语句"""
        if " THEN " not in line:
            self.output_lines.append("错误: IF 缺少 THEN")
            return

        condition = line[3:line.index(" THEN ")].strip()
        action = line[line.index(" THEN ") + 6:].strip()

        if self.eval_condition(condition):
            if action.startswith("PRINT"):
                self.execute_print(action)
            elif action.startswith("SET"):
                # 以后实现 SET
                pass
            else:
                self.output_lines.append(f"错误: IF 后无法执行 '{action}'")

    
    def execute_command(self):
        parts = self.input_text.strip().split()

        if not parts:
            return

        command = parts[0]          # 第一个词是命令
        args = parts[1:]            # 后面的词是参数

      

        if command == ".help":
            self.output_lines.append(".open <file name>")
            self.output_lines.append(".run <file name>")
            self.output_lines.append(".list")
            self.output_lines.append(".get_manipulable_object")

        elif command == ".list":
            self.list_programs()

        elif command == ".open":
            if args:
                self.load_program(args[0])
                self.current_file=args[0]
            else:
                self.output_lines.append(" .open need argumn  <file name>")

        elif command == ".run":
            if args:
                self.current_file=args[0]
                self.run_program(args[0])
                
            else:
                self.output_lines.append("用法: .run <file name>")

        else:
            self.output_lines.append(self.input_text+ "is not a command or a file or and manipulable object")





class Socket(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.image.load("socket.png").convert_alpha()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.w = self.rect.width
        self.h = self.rect.height
        self.inserted_paper = None  # 当前插入的卡片

    def get_w(self):
        return self.w

    def get_h(self):
        return self.h
def update_papers(mouse_pos, mouse_click, papers, sockets):
        """更新卡片拖拽和自动吸附"""
        # 更新所有卡片
        for paper in papers:
            paper.update(mouse_pos, mouse_click)

        # 自动吸附：卡片松开时，如果靠近插槽就插入
        for paper in papers:
            if paper.flag == "unchoose":
                for socket in sockets:
                    if socket.rect.colliderect(paper.rect):
                        paper.snap_to_socket(socket)
                        socket.inserted_paper = paper
# ========== 设置函数 ==========

def setup_computer():
    """
    在主游戏开始时调用一次。
    自动创建所有插槽、卡片，并加入 computer_sprite 精灵组。
    返回屏幕对象的引用，方便主游戏操作。
    """
    # 清空精灵组
    computer_sprite.empty()

    # 创建电脑屏幕
    screen_obj = ComputerScreen(SCREEN_X, SCREEN_Y, SCREEN_W, SCREEN_H)
    computer_sprite.add(screen_obj)

    # 批量创建插槽
    sockets = []
    for row in range(SOCKET_ROWS):
        for col in range(SOCKET_COLS):
            x = SOCKET_START_X + col * SOCKET_GAP_X
            y = SOCKET_START_Y + row * SOCKET_GAP_Y
            s = Socket(x, y)
            sockets.append(s)
            computer_sprite.add(s)

    # 批量创建初始卡片
    papers = pygame.sprite.Group()
    for i in range(CARD_COUNT):
        x = CARD_START_X + i * CARD_GAP_X
        y = CARD_START_Y
        p = Paper(x, y)
        papers.add(p)
        computer_sprite.add(p)

    return screen_obj, sockets, papers


def computer_update(screen,flag):
    """在主循环中调用，绘制电脑界面"""
    global computer_flag
    if flag=="book_on":
        computer_flag=False
    if computer_flag:
        computer_sprite.draw(screen)

    #"ASM-2100 Terminal Ready.", "Type HELP for commands."argument: 