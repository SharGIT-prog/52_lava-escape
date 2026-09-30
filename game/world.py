import pygame
import random
import math

PLATFORM_COLOR = (100,80,50)
LAVA_COLOR = (220,60,20)

CRUMBLE_COLOR = (170,140,100)      # idle crumbling platform (lighter, cracked look)
CRUMBLE_WARN_COLOR = (230,70,30)   # colour it fades toward while counting down
CRUMBLE_FRAMES = 60                # 1 second at 60 FPS
CRUMBLE_CHANCE = 0.3               # chance a generated platform is crumbling

SPRING_COLOR = (245,205,40)        # yellow spring platform
SPRING_DARK = (180,120,10)         # coil / outline colour
SPRING_BOUNCE_VEL = -22            # launch velocity (normal jump is -13)
SPRING_RECOIL_FRAMES = 24          # length of the squash-and-stretch animation
SPRING_CHANCE = 0.12               # chance a generated platform is a spring

class CrumblingPlatform(pygame.Rect):
    """A platform that breaks 1 second after the player first lands on it.

    Subclasses pygame.Rect so collision code treats it like any other platform.
    timer is None until triggered, then counts frames up to CRUMBLE_FRAMES.
    """
    def __init__(self, *args):
        super().__init__(*args)
        self.timer = None

class SpringPlatform(pygame.Rect):
    """A platform that launches the player upward when landed on.

    Subclasses pygame.Rect so collision code treats it like any other platform.
    recoil is None when idle, else counts frames of the squash/stretch animation.
    """
    def __init__(self, *args):
        super().__init__(*args)
        self.recoil = None

def generate_platforms(width, base_y, count=30):
    plats = [pygame.Rect(0, base_y, width, 20)]  # ground (never crumbles)
    y = base_y - 110
    prev_crumbling = False
    for i in range(count):
        w = random.randint(80,200)
        x = random.randint(0, width-w)
        # never crumble two in a row or the final platform, so a safe route always exists;
        # the final platform is also never a spring
        cls = pygame.Rect
        if i < count-1:
            r = random.random()
            if r < CRUMBLE_CHANCE and not prev_crumbling:
                cls = CrumblingPlatform
            elif CRUMBLE_CHANCE <= r < CRUMBLE_CHANCE + SPRING_CHANCE:
                cls = SpringPlatform
        crumble = (cls is CrumblingPlatform)
        plats.append(cls(x, y, w, 16))
        prev_crumbling = crumble
        y -= random.randint(80,130)
    return plats

def draw_platform(screen, p, cam_y):
    if isinstance(p, SpringPlatform):
        _draw_spring(screen, p, cam_y)
        return
    if not isinstance(p, CrumblingPlatform):
        pygame.draw.rect(screen, PLATFORM_COLOR, p.move(0,-int(cam_y)), border_radius=4)
        return
    dr = pygame.Rect(p.x, p.y - int(cam_y), p.w, p.h)  # plain Rect copy (move() drops attributes)
    if p.timer is None:
        pygame.draw.rect(screen, CRUMBLE_COLOR, dr, border_radius=4)
        for cx in range(dr.x + 20, dr.right - 10, 40):  # crack marks
            pygame.draw.line(screen, (90,70,45), (cx, dr.top+2), (cx+4, dr.centery), 2)
            pygame.draw.line(screen, (90,70,45), (cx+4, dr.centery), (cx-1, dr.bottom-2), 2)
        return
    t = min(1.0, p.timer / CRUMBLE_FRAMES)
    amp = 1 + int(t * 3)                                  # shake grows as it nears breaking
    dr.x += amp if (p.timer // 2) % 2 == 0 else -amp
    color = tuple(int(a + (b-a)*t) for a, b in zip(CRUMBLE_COLOR, CRUMBLE_WARN_COLOR))
    pygame.draw.rect(screen, color, dr, border_radius=4)
    bar = pygame.Rect(dr.x, dr.y, int(dr.w * (1-t)), 4)   # countdown bar shrinks over 1 second
    pygame.draw.rect(screen, (255,240,200), bar, border_radius=2)

def _draw_spring(screen, p, cam_y):
    # Recoil: top edge is pushed down (squash) then overshoots upward (stretch),
    # with a decaying oscillation. Visual only - the collision rect never changes.
    off = 0
    if p.recoil is not None:
        k = 1 - p.recoil / SPRING_RECOIL_FRAMES
        off = int(round(9 * math.cos(p.recoil * 0.55) * k))
    top = p.y - int(cam_y) + off
    dr = pygame.Rect(p.x, top, p.w, max(6, p.bottom - int(cam_y) - top))
    pygame.draw.rect(screen, SPRING_COLOR, dr, border_radius=4)
    pygame.draw.rect(screen, SPRING_DARK, dr, 2, border_radius=4)
    pts = []  # zigzag coil across the platform
    for i, x in enumerate(range(dr.x + 8, dr.right - 6, 12)):
        pts.append((x, dr.top + 4 if i % 2 == 0 else dr.bottom - 4))
    if len(pts) > 1:
        pygame.draw.lines(screen, SPRING_DARK, False, pts, 2)

def draw_lava(screen, lava_y, cam_y, width, height, frame):
    import math
    ly = int(lava_y - cam_y)
    if ly < height:
        # lava surface wave
        pts=[(0,ly)]
        for x in range(0,width+20,20):
            pts.append((x, ly + int(math.sin(x*0.08+frame*0.1)*8)))
        pts.append((width,height)); pts.append((0,height))
        pygame.draw.polygon(screen,LAVA_COLOR,pts)
        # glow
        s=pygame.Surface((width,30),pygame.SRCALPHA)
        for i in range(15):
            pygame.draw.line(s,(255,100,0,max(0,60-i*4)),(0,i),(width,i),1)
        screen.blit(s,(0,ly-15))