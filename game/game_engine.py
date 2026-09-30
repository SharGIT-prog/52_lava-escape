import pygame
from game.player import Player
from game.world import generate_platforms, draw_lava, draw_platform, CrumblingPlatform, CRUMBLE_FRAMES

WIDTH,HEIGHT=500,640
FPS=60
BG=(20,15,30)
GROUND_Y=HEIGHT+200

class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen=pygame.display.set_mode((WIDTH,HEIGHT))
        pygame.display.set_caption("Lava Escape")
        self.clock=pygame.time.Clock()
        self.font=pygame.font.SysFont("monospace",24,bold=True)
        self.big_font=pygame.font.SysFont("monospace",42,bold=True)
        self.reset()

    def reset(self):
        self.platforms=generate_platforms(WIDTH,GROUND_Y)
        self.player=Player(WIDTH//2-16,GROUND_Y-50)
        self.cam_y=0
        self.lava_y=GROUND_Y+60
        self.lava_rise=0.4
        self.score=0
        self.game_over=False
        self.won=False
        self.top_y=self.platforms[-1].y
        self.frame=0

    def handle_events(self):
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return False
            if event.type==pygame.KEYDOWN and event.key==pygame.K_r: self.reset()
        return True

    def update(self):
        if self.game_over or self.won: return
        keys=pygame.key.get_pressed()
        self.player.update(keys,self.platforms,WIDTH)
        self._update_crumbling()
        target=self.player.rect.centery-HEIGHT//2
        if target<self.cam_y: self.cam_y=target
        self.lava_y-=self.lava_rise
        self.lava_rise=min(1.2,self.lava_rise+0.0003)
        self.score=max(0,(GROUND_Y-self.player.rect.y)//10)
        self.frame+=1
        if self.player.rect.bottom>=self.lava_y:
            self.game_over=True
        if self.player.rect.top<=self.top_y-20:
            self.won=True

    def _update_crumbling(self):
        landed=self.player.landed_on
        if isinstance(landed,CrumblingPlatform) and landed.timer is None:
            landed.timer=0  # first landing starts the 1-second countdown
        broken=[]
        for p in self.platforms:
            if isinstance(p,CrumblingPlatform) and p.timer is not None:
                p.timer+=1
                if p.timer>=CRUMBLE_FRAMES: broken.append(p)
        if broken:  # remove by identity (Rect == compares values)
            self.platforms=[p for p in self.platforms if not any(p is b for b in broken)]

    def draw(self):
        self.screen.fill(BG)
        for p in self.platforms:
            draw_platform(self.screen,p,self.cam_y)
        self.player.draw(self.screen,self.cam_y)
        draw_lava(self.screen,self.lava_y,self.cam_y,WIDTH,HEIGHT,self.frame)
        sc=self.font.render(f"Height: {self.score}m  R=Restart",True,(220,200,180))
        self.screen.blit(sc,(8,10))
        if self.game_over:
            self._msg("LAVA GOT YOU!",(220,80,40))
        if self.won:
            self._msg("ESCAPED!",(80,220,100))
        pygame.display.flip()

    def _msg(self,text,color):
        ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
        ov.fill((0,0,0,150))
        self.screen.blit(ov,(0,0))
        m=self.big_font.render(text,True,color)
        s=self.font.render("Press R to Play Again",True,(200,200,200))
        self.screen.blit(m,(WIDTH//2-m.get_width()//2,HEIGHT//2-40))
        self.screen.blit(s,(WIDTH//2-s.get_width()//2,HEIGHT//2+20))

    def run(self):
        running=True
        while running:
            running=self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()