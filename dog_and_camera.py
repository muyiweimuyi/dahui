from typing import Self

import pygame
import json
import sys
import os
all_sprite=pygame.sprite.Group()
all_floor=pygame.sprite.Group()
DATA_FILE = "map_data.json"
pygame.init()
zoom = 1.0
pan_offset = [0, 0]           # 平移偏移量（屏幕像素）
dragging_pan = False
pan_start = (0, 0)
MAP_OFFSET_X = 40      # ← 这里定义
MAP_OFFSET_Y = 500       # ← 这里定义
ZOOM_MIN = 0.5
ZOOM_MAX = 3.0
CAMERA_SMOOTHING = 0.1
DOG_SCREEN_X_RATIO = 0.5
DOG_SCREEN_Y_RATIO = 0.65
SCREEN_W, SCREEN_H = 1400, 800   # 或从 pygame.display.get_surface() 获取
#=============坐标转换==============
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
#============精灵=============
class Floor(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color=(0, 0, 0)):
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
    def update(self):
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
     

    def update(self):
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
        
            
        

class ladder(MapSprite):
    def __init__(self, x, y, image_path="ladder.png"):
        super().__init__(x, y, image_path)
#==============读文件==============
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
            all_floor.add(sprite)
        elif item["type"] == "ladder":
            sprite = ladder(item["x"], item["y"], color=tuple(item["color"]) if item.get("color") else None)
        all_sprite.add(sprite)
# ========== 全局状态（世界坐标系） ==========
class Dog(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        global zoom, pan_offset,CAMERA_SMOOTHING ,DOG_SCREEN_X_RATIO,DOG_SCREEN_Y_RATIO 
        self.original_image = pygame.image.load("dahui.png").convert_alpha()
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.world_x=0
        self.world_y=0
        self.world_w=self.original_image.get_width()
        self.world_h=self.original_image.get_height()
        self.junp_speed=15
        self.speed_y=0
        self.speed_x=0
        self.gr_speed=1
        self.is_grounded = False
    def update(self,event,floors_group):
        self.gr_update(floors_group)
        self.touch_left = False
        self.touch_right = False
        old_x = self.world_x
        # 试探左移
        self.world_x -= 5
        if any(self.check_collision_with_floor(floor) for floor in floors_group):
            self.touch_left = True
        self.world_x = old_x

        # 试探右移
        self.world_x += 5
        if any(self.check_collision_with_floor(floor) for floor in floors_group):
            self.touch_right = True
        self.world_x = old_x

        # 键盘移动
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] :
            self.jump()
        if keys[pygame.K_LEFT] and not self.touch_left:
            self.world_x -= 5
        if keys[pygame.K_RIGHT] and not self.touch_right:
            self.world_x += 5
        sx = MAP_OFFSET_X + pan_offset[0] + self.world_x * zoom
        sy = MAP_OFFSET_Y + pan_offset[1] + self.world_y * zoom
        sw = max(1, self.world_w * zoom)
        sh = max(1, self.world_h * zoom)

        # 创建目标 Surface
        surf = pygame.Surface((int(sw), int(sh)), pygame.SRCALPHA)  # 支持透明

        if self.original_image:
            # 有贴图：缩放图片并绘制到 surf
            scaled = pygame.transform.scale(self.original_image, (int(sw), int(sh)))
            surf.blit(scaled, (0, 0))
        else:
            # 纯色填充
            surf.fill(self.color)

        self.image = surf
        self.rect = surf.get_rect(topleft=(int(sx), int(sy)))

       
    def jump(self):
        if self.is_grounded:        
            self.is_grounded=not self.is_grounded
            self.speed_y-=self.junp_speed
            self.is_grounded=False
    def gr_update(self,floors_group):
        self.speed_y+=self.gr_speed
        self.world_y+=self.speed_y
        for floor in floors_group:
            if self.check_collision_with_floor(floor):
                if self.speed_y >= 0:  # 下落
                    self.world_y = floor.world_y - self.world_h
                    self.speed_y = 0
                    self.is_grounded = True
                else:  # 上升撞头
                    self.world_y = floor.world_y + floor.world_h
                    self.speed_y = 0

               # 水平碰撞检测
        for floor in floors_group:
            if self.check_collision_with_floor(floor):
                dog_center_x = self.world_x + self.world_w / 2
                floor_center_x = floor.world_x + floor.world_w / 2
        
                if dog_center_x < floor_center_x:
                    self.world_x = floor.world_x - self.world_w
                else:
                    self.world_x = floor.world_x + floor.world_w
    def check_collision_with_floor(self, floor):
        """检测狗是否与地板碰撞（世界坐标）"""
        # 狗的范围
        dog_left = self.world_x
        dog_right = self.world_x + self.world_w
        dog_top = self.world_y
        dog_bottom = self.world_y + self.world_h
        
        # 地板的范围
        floor_left = floor.world_x
        floor_right = floor.world_x + floor.world_w
        floor_top = floor.world_y
        floor_bottom = floor.world_y + floor.world_h
        
        # 检测矩形重叠
        if dog_right > floor_left and dog_left < floor_right:
            if dog_bottom > floor_top and dog_top < floor_bottom:
                return True
        return False
    def camera_update():
                   # 计算狗在屏幕上的期望位置
        target_screen_x = SCREEN_W * DOG_SCREEN_X_RATIO
        target_screen_y = SCREEN_H * DOG_SCREEN_Y_RATIO

        # 根据期望屏幕位置反推目标镜头偏移
        target_pan_x = target_screen_x - MAP_OFFSET_X - (self.world_x + self.world_w / 2) * zoom
        target_pan_y = target_screen_y - MAP_OFFSET_Y - (self.world_y + self.world_h / 2) * zoom

        # 平滑插值
        pan_offset[0] += (target_pan_x - pan_offset[0]) * CAMERA_SMOOTHING
        pan_offset[1] += (target_pan_y - pan_offset[1]) * CAMERA_SMOOTHING
#调用loadmap()
#默认dog（0，0）