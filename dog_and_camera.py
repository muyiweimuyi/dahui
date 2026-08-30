from turtle import down
from typing import Self

import pygame
import json
import sys
import os
import bus
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
class Hardware(MapSprite):
    def __init__(self, x, y, port, width=32, height=32, image_path=None, color=None):
        super().__init__(x, y, color=color, image_path=image_path)
        self.port = port  
        self.world_w = width
        self.world_h = height
class PhysicsEntity(pygame.sprite.Sprite):
    """只负责重力和碰撞的物理基类"""

    def __init__(self):
        super().__init__()
        self.world_x = 0
        self.world_y = 0
        self.world_w = 0
        self.world_h = 0
        self.speed_y = 0
        self.speed_x = 0
        self.gr_speed = 1
        self.junp_speed = 15
        self.is_grounded = False
        self.standing_on = None   # 新增：脚下踩着谁

    def gr_update(self, floors_group):
        """重力更新 + 垂直/水平碰撞"""
        self.speed_y += self.gr_speed
        self.world_y += self.speed_y

        # 垂直碰撞
        self.is_grounded = False
        self.standing_on = None   # 每帧重置

        for floor in floors_group:
            if self.check_collision_with_floor(floor):
                if self.speed_y >= 0:
                    self.world_y = floor.world_y - self.world_h
                    self.speed_y = 0
                    self.is_grounded = True
                    self.standing_on = floor   # 记录脚下
                else:
                    self.world_y = floor.world_y + floor.world_h
                    self.speed_y = 0

        # 水平碰撞
        for floor in floors_group:
            if self.check_collision_with_floor(floor):
                center_x = self.world_x + self.world_w / 2
                floor_center_x = floor.world_x + floor.world_w / 2
                if center_x < floor_center_x:
                    self.world_x = floor.world_x - self.world_w
                else:
                    self.world_x = floor.world_x + floor.world_w
                self.speed_x = 0

    def jump(self):
        """跳跃"""
        if self.is_grounded:
            self.speed_y = -self.junp_speed
            self.is_grounded = False
            self.standing_on = None   # 跳跃时清除脚下

    def check_collision_with_floor(self, floor):
        """通用矩形碰撞检测"""
        if (self.world_x + self.world_w > floor.world_x and
            self.world_x < floor.world_x + floor.world_w and
            self.world_y + self.world_h > floor.world_y and
            self.world_y < floor.world_y + floor.world_h):
            return True
        return False
class Drown(Hardware, PhysicsEntity):
    def __init__(self, x, y, image_path="drown.png"):
        Hardware.__init__(self, x, y, port="P1", image_path=image_path)
        PhysicsEntity.__init__(self)

        self.world_w = self.image_original.get_width()
        self.world_h = self.image_original.get_height()
        self.prev_world_x = x   # 新增：上一帧位置
        self.prev_world_y = y
        self.power_down = 0
        self.power_left = 0
        self.power_right = 0

  
    def update(self,floors_group):
        Hardware.update(self)   # 更新贴图显示
        if bus.ports[self.port]["command"]!=None:
            if bus.ports[self.port]["command"]=="down":
                self.speed_y+=0.5
            elif bus.ports[self.port]["command"]=="left":
                self.speed_x-=0.5
            elif bus.ports[self.port]["command"]=="up":
                self.speed_y-=0.5
            elif bus.ports[self.port]["command"]=="right":
                self.speed_x+=0.5
        self.world_x+=self.speed_x
        bus.ports[self.port]["command"]=None
        self.gr_update(floors_group)
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
            all_sprite.add(sprite)
        elif item["type"] == "ladder":
            sprite = ladder(item["x"], item["y"])
            all_sprite.add(sprite)
        elif item["type"]=="Drown":
            sprite= Drown(item["x"], item["y"])
            all_floor.add(sprite)
            all_sprite.add(sprite)
# ========== 全局状态（世界坐标系） ==========
class Dog(PhysicsEntity):
    def __init__(self):
        super().__init__()
        global zoom, pan_offset, CAMERA_SMOOTHING, DOG_SCREEN_X_RATIO, DOG_SCREEN_Y_RATIO
        self.original_image = pygame.image.load("dahui.png").convert_alpha()
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.world_w = self.original_image.get_width()
        self.world_h = self.original_image.get_height()

    def update(self, event, floors_group):
        # 物理更新
        self.gr_update(floors_group)

        # 跟随脚下对象
        if self.standing_on and hasattr(self.standing_on, "prev_world_x"):
            dx = self.standing_on.world_x - self.standing_on.prev_world_x
            dy = self.standing_on.world_y - self.standing_on.prev_world_y
            self.world_x += dx
            self.world_y += dy

        # 左右接触检测
        self.touch_left = False
        self.touch_right = False
        old_x = self.world_x

        self.world_x -= 5
        if any(self.check_collision_with_floor(f) for f in floors_group):
            self.touch_left = True
        self.world_x = old_x

        self.world_x += 5
        if any(self.check_collision_with_floor(f) for f in floors_group):
            self.touch_right = True
        self.world_x = old_x

        # 键盘输入
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            self.jump()
        if keys[pygame.K_LEFT] and not self.touch_left:
            self.world_x -= 5
        if keys[pygame.K_RIGHT] and not self.touch_right:
            self.world_x += 5

        # 渲染更新
        sx = MAP_OFFSET_X + pan_offset[0] + self.world_x * zoom
        sy = MAP_OFFSET_Y + pan_offset[1] + self.world_y * zoom
        sw = max(1, self.world_w * zoom)
        sh = max(1, self.world_h * zoom)

        surf = pygame.Surface((int(sw), int(sh)), pygame.SRCALPHA)
        scaled = pygame.transform.scale(self.original_image, (int(sw), int(sh)))
        surf.blit(scaled, (0, 0))

        self.image = surf
        self.rect = surf.get_rect(topleft=(int(sx), int(sy)))

    def camera_update(self):
        target_screen_x = SCREEN_W * DOG_SCREEN_X_RATIO
        target_screen_y = SCREEN_H * DOG_SCREEN_Y_RATIO

        target_pan_x = target_screen_x - MAP_OFFSET_X - (self.world_x + self.world_w / 2) * zoom
        target_pan_y = target_screen_y - MAP_OFFSET_Y - (self.world_y + self.world_h / 2) * zoom

        pan_offset[0] += (target_pan_x - pan_offset[0]) * CAMERA_SMOOTHING
        pan_offset[1] += (target_pan_y - pan_offset[1]) * CAMERA_SMOOTHING