from pickle import NONE

import pygame
import computer
import dog_and_camera
import book
pygame.init()
screen = pygame.display.set_mode((1400, 850))
clock = pygame.time.Clock()
pygame.display.set_caption("dogworld")
running = True
book_and_computer=""
book_st=False
com_st=False
#------初始化方舟之书-------------
player_book=book.Book()
book.read_book()
print("手册加载完毕，总页数：", len(book.book_pages))
# ---- 初始化电脑系统（一次性创建好所有部件） ----
comp_screen, comp_sockets, comp_papers = computer.setup_computer()
computer.computer_flag = False   # 让电脑界面显示
# ------ 狗子初始化，摄像机初始化------
dog_and_camera.load_map()
dog = dog_and_camera.Dog()
dog_sprite=pygame.sprite.GroupSingle()
dog_sprite.add(dog)
all_sprites = pygame.sprite.Group()
# ---- 主循环 ----
dog.update(None,dog_and_camera.all_floor)
while running:
    # 事件处理
    book_st=player_book.bookflag
    com_st=computer.computer_flag
    keys = pygame.key.get_pressed()
    mouse_pos = pygame.mouse.get_pos()
    left_click = pygame.mouse.get_pressed()[0]
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        player_book.handle(event)
        comp_screen.handle(event)
    # 调用模块函数，传入所需参数
    computer.update_papers(mouse_pos, left_click, comp_papers, comp_sockets)
    if book_st==0 and player_book.bookflag==1:
        book_and_computer="book_on"
    if com_st==0 and computer.computer_flag==1:
        book_and_computer="com_on"
    if com_st==0 and book_st==0:
        dog.update(event,dog_and_camera.all_floor)
#---------电脑更新---------------------------
    # 绘制
    screen.fill((30, 30, 30))
    
   
    dog_and_camera.all_sprite.update()
    dog_and_camera.all_sprite.draw(screen)
    dog_sprite.draw(screen)
    dog.camera_update()
    player_book.update(screen,book_and_computer)#书的更新
    # 绘制电脑系统（如果电脑标志为真）
    computer.computer_update(screen,book_and_computer)
    comp_screen.update()
    comp_screen.update_programs()
    all_sprites.draw(screen,book_and_computer)
    pygame.display.flip()
    clock.tick(60)
    print(dog.world_x)
    book_and_computer=""

pygame.quit()