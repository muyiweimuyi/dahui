import pygame
pygame.init() 
text_size=20
font = pygame.font.Font("k8x12-2.ttf", text_size)
pages = []
book_pages=[]
def read_book():
    global pages
    global book_pages
    with open("kn_book.txt", "r", encoding="utf-8") as f :
        for line in f:
            stripped = line.strip()# 去掉换行符和首尾空格
            print(stripped)
            if stripped == "---":     # 如果这一行是分页标记
                book_pages.append(pages)   # 把手里攒的这页放进大箱子
                pages = []            # 手里换成一张新空白页
            else:                            # 如果不是分页标记
                pages.append(stripped) # 把这行文字放进手里这页

    if pages:                # 文件读完后，如果手里还有一页
        book_pages.append(pages)  # 把它也放进大箱子
 

class Book():
    def __init__(self):
        super().__init__()
        self.image = pygame.image.load("book.png").convert_alpha()
        self.rect = self.image.get_rect()
        self.bookpage=0
        self.bookflag=True
        self.x=200
        self.y=200
    def update(self,screen,flag):
        global book_pages
        global text_size
        self.page1=book_pages[self.bookpage]
        self.page2=book_pages[self.bookpage+1]
        if flag =="com_on":
            self.bookflag=False
        if self.bookflag:
            screen.blit(self.image,(200,200))
            self.y=200
            for line in self.page1:
                
                text=font.render(line,True,(0,0,0))
                screen.blit(text,(200,self.y))
                self.y+=text_size
            self.y=200
            for line in self.page2:
                text=font.render(line,True,(0,0,0))
                screen.blit(text,(600,self.y))
                self.y+=text_size
    def fd(self):
        self.bookpage+=2
    def bk(self):
        if self.bookpage>1:
            self.bookpage-=2
    def handle(self, event):
        if event.type == pygame.KEYDOWN:
            keys = pygame.key.get_pressed()
            if event.key == pygame.K_b  and  (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]):
                self.bookflag = not self.bookflag
            elif event.key == pygame.K_LEFT and self.bookflag:
                self.bk()
            elif event.key == pygame.K_RIGHT and self.bookflag:
                self.fd()  