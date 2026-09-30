import pygame
from game.player import Player
from game.world import (generate_platforms, draw_lava, draw_platform, CrumblingPlatform, CRUMBLE_FRAMES,
                        SpringPlatform, SPRING_BOUNCE_VEL, SPRING_RECOIL_FRAMES)

WIDTH,HEIGHT=500,640
FPS=60
BG=(20,15,30)
GROUND_Y=HEIGHT+200

LAVA_RISE_START=0.4              # initial lava speed (px/frame)
LAVA_RISE_MAX=1.2                # cap on the base lava speed
BURST_INTERVAL=15*FPS            # a Lava Burst starts every 15 seconds...
BURST_DURATION=3*FPS             # ...and lasts 3 seconds
BURST_MULT=2.0                   # lava speed multiplier during a burst

class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen=pygame.display.set_mode((WIDTH,HEIGHT))
        pygame.display.set_caption("Lava Escape")
        self.clock=pygame.time.Clock()
        self.font=pygame.font.SysFont("monospace",24,bold=True)
        self.big_font=pygame.font.SysFont("monospace",42,bold=True)
        self.small_font=pygame.font.SysFont("monospace",16,bold=True)
        self.reset()

    def reset(self):
        self.platforms=generate_platforms(WIDTH,GROUND_Y)
        self.player=Player(WIDTH//2-16,GROUND_Y-50)
        self.cam_y=self.player.rect.centery-HEIGHT//2  # start with the player on screen (same formula as the follow camera)
        self.lava_y=GROUND_Y+60
        self.lava_rise=LAVA_RISE_START
        self.burst_left=0  # frames remaining in the current Lava Burst (0 = none)
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
        self._update_springs()
        target=self.player.rect.centery-HEIGHT//2
        if target<self.cam_y: self.cam_y=target
        self.burst_left=self._burst_frames_left()
        self.lava_y-=self.lava_rise*(BURST_MULT if self.burst_left>0 else 1)
        self.lava_rise=min(LAVA_RISE_MAX,self.lava_rise+0.0003)
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

    def _update_springs(self):
        for p in self.platforms:
            if isinstance(p,SpringPlatform) and p.recoil is not None:
                p.recoil+=1
                if p.recoil>=SPRING_RECOIL_FRAMES: p.recoil=None
        landed=self.player.landed_on
        if isinstance(landed,SpringPlatform):
            self.player.vel_y=SPRING_BOUNCE_VEL
            self.player.on_ground=False  # so a held jump key can't override the bounce
            landed.recoil=0  # animation starts at full squash on this frame

    def _burst_frames_left(self):
        # Bursts begin at 15s, 30s, 45s... of play time and last 3s each.
        if self.frame<BURST_INTERVAL: return 0
        phase=self.frame%BURST_INTERVAL
        return BURST_DURATION-phase if phase<BURST_DURATION else 0

    def _text(self,font,text,color,pos,center=False):
        shadow=font.render(text,True,(0,0,0))
        img=font.render(text,True,color)
        x,y=pos
        if center: x-=img.get_width()//2
        self.screen.blit(shadow,(x+2,y+2))
        self.screen.blit(img,(x,y))

    def _draw_danger_hud(self):
        bursting=self.burst_left>0
        blink=(self.frame//6)%2==0
        # danger meter: fills as the base lava speed (lava_rise) climbs from its start to its cap
        frac=max(0.0,min(1.0,(self.lava_rise-LAVA_RISE_START)/(LAVA_RISE_MAX-LAVA_RISE_START)))
        x,y,w,h=8,42,220,16
        pygame.draw.rect(self.screen,(40,30,45),(x,y,w,h),border_radius=4)
        green,yellow,red=(80,200,90),(240,200,40),(230,50,30)
        a,b,t=(green,yellow,frac*2) if frac<0.5 else (yellow,red,(frac-0.5)*2)
        color=tuple(int(p+(q-p)*t) for p,q in zip(a,b))
        if frac>0:
            pygame.draw.rect(self.screen,color,(x,y,max(6,int(w*frac)),h),border_radius=4)
        border=((255,60,30) if blink else (255,255,255)) if bursting else (200,180,160)
        pygame.draw.rect(self.screen,border,(x,y,w,h),2,border_radius=4)
        speed=self.lava_rise*(BURST_MULT if bursting else 1)/LAVA_RISE_START
        self._text(self.small_font,f"LAVA x{speed:.1f}",(255,90,60) if bursting else (220,200,180),(x+w+8,y))
        if bursting:
            # brief warning: flashing banner, countdown, and a pulsing red frame around the screen
            self._text(self.big_font,"LAVA BURST!",(255,70,30) if blink else (255,200,60),(WIDTH//2,80),center=True)
            self._text(self.small_font,f"lava speed x{BURST_MULT:g} for {self.burst_left/FPS:.1f}s",(255,220,180),(WIDTH//2,132),center=True)
            pulse=90+int(90*abs((self.frame%30)-15)/15)
            fr=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
            pygame.draw.rect(fr,(255,40,20,pulse),(0,0,WIDTH,HEIGHT),8)
            self.screen.blit(fr,(0,0))

    def draw(self):
        self.screen.fill(BG)
        for p in self.platforms:
            draw_platform(self.screen,p,self.cam_y)
        self.player.draw(self.screen,self.cam_y)
        draw_lava(self.screen,self.lava_y,self.cam_y,WIDTH,HEIGHT,self.frame)
        sc=self.font.render(f"Height: {self.score}m  R=Restart",True,(220,200,180))
        self.screen.blit(sc,(8,10))
        self._draw_danger_hud()
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