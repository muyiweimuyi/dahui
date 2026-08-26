import pygame
import json
import sys
import os

from pygame import mouse

#都是世界坐标，不要写错
# ==================== 初始化 ====================
pygame.init()
zoom = 1.0
pan_offset = [0, 0]           # 平移偏移量（屏幕像素）
dragging_pan = False
pan_start = (0, 0)
MAP_OFFSET_X = 40      # ← 这里定义
MAP_OFFSET_Y = 500       # ← 这里定义
ZOOM_MIN = 0.5
ZOOM_MAX = 3.0
#======================鼠标缩放=====================
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("方舟地图编辑器 v2")
#=========================屏幕参数====================
clock = pygame.time.Clock()
text_size=20
font = pygame.font.Font("k8x12-2.ttf", text_size)
running=1
dog_pos=(0,0)
first_pos=0
second_pos=0
mouse_flag=["f","ob_ladder","none"]
map_data = []
flag_counter=0
#========================一些变量===========================
all_sprite=pygame.sprite.Group()
view=None
# 在初始化时定义一个自定义事件类型
UPDATE_EVENT = pygame.USEREVENT + 1
# 在主循环中，定时（例如每 50 毫秒）发布一次
pygame.time.set_timer(UPDATE_EVENT, 50)  # 每50ms触发一次
#======================世界/屏幕坐标===========================
def world_to_screen(x,y):
    """世界坐标 -> 屏幕坐标"""
    sx = MAP_OFFSET_X + pan_offset[0] + x * zoom
    sy = MAP_OFFSET_Y + pan_offset[1] + y * zoom
    return sx, sy

def screen_to_world(screen_pos):
    """屏幕坐标 -> 世界坐标"""
    wx = (screen_pos[0] - MAP_OFFSET_X - pan_offset[0]) / zoom
    wy = (screen_pos[1] - MAP_OFFSET_Y - pan_offset[1]) / zoom
    return wx, wy
def draw_on_floor(self_x,self_y,self_w,self_h):
    x = MAP_OFFSET_X + pan_offset[0] + self_x * zoom
    y = MAP_OFFSET_Y + pan_offset[1] + self_y * zoom
    w = self_w * zoom
    h = self_h * zoom
    pygame.draw.rect(screen,(0,0,0),(x,y,w,h))
def handle_mouse_wheel(event):
    global zoom, pan_offset
    old_zoom = zoom
    zoom *= 1.1 ** event.y   # event.y 是滚轮滚动量，正负决定放大或缩小
    zoom = max(ZOOM_MIN, min(ZOOM_MAX, zoom))  # 限制范围
    # 保证缩放以鼠标位置为中心
    mouse_screen = pygame.mouse.get_pos()
    # 缩放前鼠标指向的世界坐标
    wx = (mouse_screen[0] - MAP_OFFSET_X - pan_offset[0]) / old_zoom
    wy = (mouse_screen[1] - MAP_OFFSET_Y - pan_offset[1]) / old_zoom
    # 调整平移，使缩放后鼠标下的世界坐标不变
    pan_offset[0] = mouse_screen[0] - MAP_OFFSET_X - wx * zoom
    pan_offset[1] = mouse_screen[1] - MAP_OFFSET_Y - wy * zoom
def pos_to_pos(pos_1,pos_2):
     # 将世界坐标转换为屏幕坐标
     wx1,wy1=world_to_screen( pos_1[0],pos_1[1])
     wx2,wy2=world_to_screen( pos_2[0],pos_2[1])
     # 计算左上角和宽高（允许任意顺序）
     world_x = min(wx1, wx2)
     world_y = min(wy1, wy2)
     world_w = abs(wx2 - wx1)
     world_h = abs(wy2 - wy1)
     return pygame.Rect(world_x,world_y,world_w,world_h)
def pos_to_pos_creatfloor(first_pos,second_pos):
            wx1,wy1= first_pos[0],first_pos[1]
            wx2,wy2= second_pos[0],second_pos[1]
            world_x = min(wx1, wx2)
            world_y = min(wy1, wy2)
            world_w = abs(wx2 - wx1)
            world_h = abs(wy2 - wy1)
            objection=Floor(world_x,world_y,world_w,world_h)
            all_sprite.add(objection)
#=========================鼠标逻辑=========================================
def mouse_draw(event):
    global first_pos 
    global second_pos
    global mouse_flag
    global view
    global flag_counter
    mouse_pos=pygame.mouse.get_pos()
    first_pos_text=font.render(f"起点: {first_pos}",True,(0,100,0))
    second_pos_text=font.render(f"终点: {second_pos}",True,(0,100,0))
    mode_text = font.render(f"模式: {mouse_flag[flag_counter]}", True, (0, 100,0))
    screen.blit(first_pos_text,(0,0))
    screen.blit(second_pos_text,(0,text_size))
    screen.blit(mode_text, (0, text_size*2))
    if event.type==pygame.KEYDOWN:
       if event.key==pygame.K_w:
            if flag_counter>0:
                 flag_counter-=1
            else:
                flag_counter=len(mouse_flag)-1
       if event.key==pygame.K_s:
            if flag_counter<len(mouse_flag)-1:
                    flag_counter+=1
            else:
                    flag_counter=0
       if event.key==pygame.K_ESCAPE:
                 first_pos=0 
                 second_pos=0
                 flag_counter=len(mouse_flag)-1
    if mouse_flag[flag_counter]=="f":
        if first_pos!=0 :
            if second_pos!=0:
                pygame.draw.rect(screen,(0,100,0),pos_to_pos(first_pos,second_pos),2)
            else:
                wx1,wy1=world_to_screen( first_pos[0],first_pos[1])
                wx2,wy2= mouse_pos[0],mouse_pos[1]
                # 计算左上角和宽高（允许任意顺序）
                world_x = min(wx1, wx2)
                world_y = min(wy1, wy2)
                world_w = abs(wx2 - wx1)
                world_h = abs(wy2 - wy1)
                pygame.draw.rect(screen,(0,100,0),(world_x,world_y,world_w,world_h),2)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if first_pos==0:
                first_pos=screen_to_world(mouse_pos)    
            else:
                second_pos=screen_to_world(mouse_pos)
        if event.type==pygame.KEYDOWN:
            if event.key==pygame.K_SPACE:
                first_pos=0
                second_pos=0
            if event.key==pygame.K_RETURN:
                wx1,wy1= first_pos[0],first_pos[1]
                wx2,wy2= second_pos[0],second_pos[1]
                world_x = min(wx1, wx2)
                world_y = min(wy1, wy2)
                world_w = abs(wx2 - wx1)
                world_h = abs(wy2 - wy1)
                objection=Floor(world_x,world_y,world_w,world_h)
                all_sprite.add(objection)
                first_pos=0
                second_pos=0
    elif mouse_flag[flag_counter]=="ob_ladder":
        wx1,wy1=screen_to_world(mouse_pos)
        view=ladder(wx1,wy1)
        screen.blit(view.image, view.rect)
        if event.type==pygame.KEYDOWN:
            if event.key==pygame.K_SPACE:
                first_pos=0
                second_pos=0
            if event.key==pygame.K_RETURN:
                view.kill()
                objection=ladder(wx1,wy1)
                all_sprite.add(objection)
                first_pos=0
                second_pos=0
#========================精灵/变量=============================
class Floor(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color=(0, 100, 0)):
        super().__init__()
        self.world_x = x
        self.world_y = y
        self.world_w = width
        self.world_h = height
        self.color = color
        # 临时占位，稍后在 update 中创建真实 image 和 rect
        self.image = pygame.Surface((1, 1))
        self.rect = pygame.Rect(0, 0, 1, 1)
        self.flag="unchoose"
    def update(self,mouse_pos,mouse_click,event):
        """根据当前缩放和平移更新屏幕显示"""
        global zoom, pan_offset
        # 计算屏幕坐标和尺寸（世界坐标 → 屏幕坐标）
        sx = MAP_OFFSET_X + pan_offset[0] + self.world_x * zoom
        sy = MAP_OFFSET_Y + pan_offset[1] + self.world_y * zoom
        sw = self.world_w * zoom
        sh = self.world_h * zoom
        # 避免尺寸为 0 或负数
        sw = max(1, sw)
        sh = max(1, sh)
        # 重新创建 Surface（因为尺寸可能变化）
        self.image = pygame.Surface((int(sw), int(sh)))
        self.image.fill(self.color)
        # 更新 rect 位置
        self.rect = self.image.get_rect(topleft=(int(sx), int(sy)))
        if self.flag == "choose":
                # 正在拖拽：跟着鼠标走，松开时放下
                self.world_x,self.world_y = screen_to_world(mouse_pos)
                if event.key==pygame.K_k:
                       self.kill()
        if not mouse_click:
                self.flag = "unchoose"
        elif self.flag == "unchoose":
            # 空闲状态：点击选中
            if self.rect.collidepoint(mouse_pos) and mouse_click:
                self.flag = "choose"
class MapSprite(pygame.sprite.Sprite):
    def __init__(self, x, y,  color=None, image_path=None):
        """
        参数：
            x, y, width, height: 世界坐标和尺寸
            color: RGB 颜色元组 (r,g,b)，如果提供则使用纯色（优先于贴图）
            image_path: 图片文件路径，如果提供则加载图片作为纹理
        """
        super().__init__()
        self.world_x = x
        self.world_y = y
        self.color = color
        self.image_original = None
        if image_path:
            try:
                self.image_original = pygame.image.load(image_path).convert_alpha()
                self.world_w=self.image_original.get_width()
                self.world_h=self.image_original.get_height()
            except:
                print(f"警告：无法加载图片 {image_path}，将使用纯色替代")
                self.color = color or (0, 100, 0)  # 默认绿色
        # 如果没有贴图且没有颜色，设为默认绿色
        if not self.image_original and not self.color:
            self.color = (0, 100, 0)

        # 占位 image/rect，由 update 生成
        self.image = pygame.Surface((1, 1))
        self.rect = pygame.Rect(0, 0, 1, 1)
     

    def update(self,mouse_pos,mouse_click,event):
        """根据当前 zoom 和 pan_offset 生成屏幕图像"""
        global zoom, pan_offset
        sx = MAP_OFFSET_X + pan_offset[0] + self.world_x * zoom
        sy = MAP_OFFSET_Y + pan_offset[1] + self.world_y * zoom
        sw = max(1, self.world_w * zoom)
        sh = max(1, self.world_h * zoom)

        # 创建目标 Surface
        surf = pygame.Surface((int(sw), int(sh)), pygame.SRCALPHA)  # 支持透明

        if self.image_original:
            # 有贴图：缩放图片并绘制到 surf
            scaled = pygame.transform.scale(self.image_original, (int(sw), int(sh)))
            surf.blit(scaled, (0, 0))
        else:
            # 纯色填充
            surf.fill(self.color)

        self.image = surf
        self.rect = surf.get_rect(topleft=(int(sx), int(sy)))
        if self.flag == "choose":
                self.world_x,self.world_y = screen_to_world(mouse_pos)
                if event.key==pygame.K_k:
                       self.kill()
        if not mouse_click:
                self.flag = "unchoose"
        elif self.flag == "unchoose":
            # 空闲状态：点击选中
            if self.rect.collidepoint(mouse_pos) and mouse_click:
                self.flag = "choose"

class ladder(MapSprite):
    def __init__(self, x, y, image_path="ladder.png"):
        super().__init__(x, y, image_path)
def update_all(mouse_pos, mouse_click, group,event):
        """更新卡片拖拽和自动吸附"""
        # 更新所有卡片
        for sprite in group:
            sprite.update(mouse_pos,mouse_click,event)



#==========读和写============================================
DATA_FILE = "map_data.json"
def load_data():
    """从 JSON 文件加载数据，如果文件不存在返回空字典"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    """保存字典到 JSON 文件"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print("数据已保存。")        
def load_map():
    try:
        with open("map_data.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        return   # 如果文件不存在，就不加载

    all_sprite.empty()   # 清空当前精灵
    for item in data:
        # 根据 type 创建对应的 Floor 或 ladder 对象
        if item["type"] == "Floor":
            sprite = Floor(item["x"], item["y"], item["w"], item["h"])
        elif item["type"] == "ladder":
            sprite = ladder(item["x"], item["y"], color=tuple(item["color"]) if item.get("color") else None)
        all_sprite.add(sprite)
 #======================初始化============================
load_map()          
#==================主循环==============================
while running:
    screen.fill((0, 0, 0))
    mouse_pos=pygame.mouse.get_pos()
    left_click = pygame.mouse.get_pressed()[0]
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # 鼠标滚轮缩放
        if event.type == UPDATE_EVENT:
        # 什么也不做，只是为了保持事件循环活跃
            pass
        if event.type == pygame.MOUSEWHEEL:
            handle_mouse_wheel(event)
        
        mouse_draw(event)
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        pan_offset[1] += 2   # 调大数值移动更快
    if keys[pygame.K_DOWN]:
        pan_offset[1] -= 2
    if keys[pygame.K_LEFT]:
        pan_offset[0] -= 2
    if keys[pygame.K_RIGHT]:
        pan_offset[0] += 2
    if keys[pygame.K_l]:
        map_data=[]
        for sprite in all_sprite:
            map_data.append({
                "type": sprite.__class__.__name__,
                "x": sprite.world_x,
                "y": sprite.world_y,
                "w": sprite.world_w,
                "h": sprite.world_h,
                "color": sprite.color
            })
        # 然后保存
        save_data(map_data)
    sx, sy = world_to_screen(dog_pos[0], dog_pos[1])
    pygame.draw.circle(screen, (0, 100, 0), (int(sx), int(sy)), 5)
    update_all(mouse_pos,left_click,all_sprite,event)
    all_sprite.draw(screen)
    pygame.display.update()
    clock.tick(60)
    
pygame.quit()
# 构建要保存的数据

