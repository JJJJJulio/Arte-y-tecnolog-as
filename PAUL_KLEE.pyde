
# Processing 3.5.4 — Python Mode (Jython)
# PAUL KLEE (inspirado) — 2D, color, ritmo, textura, movimiento sutil
# ---------------------------------------------------------------
# NOTA: No es copia de obras específicas. Es una traducción de rasgos:
# - Geometría modulada (cuadros/rectángulos/triángulos)
# - Color en capas con variación tonal (tipo acuarela/papel)
# - Líneas finas “musicales” y marcas gráficas
# - Composición por bandas + equilibrio asimétrico
# - Movimiento sutil: respiración de la paleta y micro-deriva de módulos
#
# Controles:
#   R  = Re-seed (nueva composición)
#   C  = Cambiar paleta Klee (familias)
#   M  = Memoria (estela) ON/OFF
#   S  = Guardar PNG
#   ↑/↓= Más/Menos movimiento
#
# Tip: si tu compu sufre, baja GRID_COLS/ROWS o SUBDIVS.

from __future__ import division
import random
import math

# ===================== PARÁMETROS EDITABLES =====================
W, H = 1200, 800
FPS = 60

GRID_COLS = 18
GRID_ROWS = 12
SUBDIVS   = 3          # subdivisión interna por celda (detalle)
MARGIN    = 70

LINE_ALPHA     = 70
PAPER_ALPHA    = 26    # textura por frame
MEM_ALPHA      = 18    # menor = más estela
USE_MEMORY     = True

MOVE_AMOUNT    = 0.85  # ↑/↓ ajusta en vivo
MOVE_SPEED     = 0.35
NOISE_SCALE    = 0.006

# ================================================================

# Paletas “familias” (Klee-ish): tierra / pastel / nocturna / viva
PALETTES = [
  # tierra cálida
  [ (245, 236, 220), (220, 166, 118), (196, 112, 92), (120, 86, 76), (64, 60, 58), (240, 212, 140) ],
  # pastel suave
  [ (244, 241, 236), (199, 220, 213), (238, 199, 174), (230, 218, 138), (197, 194, 222), (173, 160, 142) ],
  # nocturna
  [ (16, 18, 22), (64, 78, 104), (148, 120, 92), (210, 182, 132), (92, 52, 44), (230, 220, 200) ],
  # viva controlada
  [ (246, 244, 238), (222, 60, 60), (44, 108, 168), (240, 200, 72), (52, 140, 92), (40, 40, 42) ],
]

paletteIndex = 0
seed = 0
t0 = 0.0

# precomputo de celdas: cada celda guarda su “plan” de formas
cells = []

# ===================== UTILIDADES =====================
def reseed():
  global seed, cells, t0
  seed = int(random.random() * 1e9)
  random.seed(seed)
  randomSeed(seed)
  noiseSeed(seed)
  t0 = random.random() * 1000.0
  cells = build_cells()

def clamp(x, a, b):
  return max(a, min(b, x))

def lerp(a, b, t):
  return a + (b - a) * t

def mix_col(c1, c2, t):
  return (
    int(lerp(c1[0], c2[0], t)),
    int(lerp(c1[1], c2[1], t)),
    int(lerp(c1[2], c2[2], t))
  )

def pal():
  return PALETTES[paletteIndex]

def pick_col():
  return pal()[int(random.random() * len(pal()))]

def time_sec():
  return millis() / 1000.0

# ===================== MODELO DE CELDA =====================
def build_cells():
  # Construye una grilla con decisiones “klee-ish”: bloques, triángulos, arcos, marcas.
  out = []
  cw = (W - 2*MARGIN) / float(GRID_COLS)
  ch = (H - 2*MARGIN) / float(GRID_ROWS)

  for gy in range(GRID_ROWS):
    for gx in range(GRID_COLS):
      x = MARGIN + gx * cw
      y = MARGIN + gy * ch

      base = pick_col()
      accent = pick_col()
      ink = pick_col()

      # Decide tipo de celda
      kind = weighted_choice([
        ("blocks", 0.45),
        ("triangle", 0.18),
        ("arc", 0.14),
        ("ladder", 0.13),
        ("glyph", 0.10),
      ])

      # nivel de subdivisión variable por celda
      local_sub = SUBDIVS + (1 if random.random() < 0.35 else 0)

      out.append({
        "gx": gx, "gy": gy,
        "x": x, "y": y, "w": cw, "h": ch,
        "base": base, "accent": accent, "ink": ink,
        "kind": kind,
        "sub": local_sub,
        "phase": random.random() * 1000.0,
        "rot": (random.random() * 2 - 1) * 0.18,  # rotación leve
        "bias": (random.random() * 2 - 1) * 0.45, # sesgo compositivo
      })
  return out

def weighted_choice(items):
  # items: [(value, weight), ...]
  r = random.random() * sum(w for _, w in items)
  acc = 0.0
  for v, w in items:
    acc += w
    if r <= acc:
      return v
  return items[-1][0]

# ===================== RENDER =====================
def settings():
  size(W, H, P2D)

def setup():
  frameRate(FPS)
  smooth(8)
  reseed()
  background(*pal()[0])  # primer color como base “papel”

def draw():
  global t0

  t = time_sec() + t0

  # Fondo con memoria (estela suave)
  if USE_MEMORY:
    noStroke()
    r, g, b = pal()[0]
    fill(r, g, b, MEM_ALPHA)
    rect(0, 0, width, height)
  else:
    background(*pal()[0])

  # textura tipo papel (puntos/ruido)
  paper_texture(t)

  # grilla (estructura)
  draw_grid_frame()

  # pintar celdas
  for c in cells:
    draw_cell(c, t)

  # líneas “musicales” encima (como Klee)
  draw_musical_lines(t)

def paper_texture(t):
  # textura suave por frame
  dots = int(width * height * (PAPER_ALPHA / 255.0) * 0.00035)
  noStroke()
  for _ in range(dots):
    x = random.random() * width
    y = random.random() * height
    n = noise(x * 0.01, y * 0.01, t * 0.35)
    a = int(lerp(6, 18, n))
    fill(255, a)
    rect(x, y, 1, 1)

def draw_grid_frame():
  # Marco y guías sutiles (editorial)
  stroke(0, 35)
  strokeWeight(2)
  noFill()
  rect(MARGIN*0.65, MARGIN*0.65, width - MARGIN*1.3, height - MARGIN*1.3)

  stroke(0, 18)
  strokeWeight(1)
  cw = (W - 2*MARGIN) / float(GRID_COLS)
  ch = (H - 2*MARGIN) / float(GRID_ROWS)
  for i in range(GRID_COLS+1):
    x = MARGIN + i*cw
    line(x, MARGIN, x, H-MARGIN)
  for j in range(GRID_ROWS+1):
    y = MARGIN + j*ch
    line(MARGIN, y, W-MARGIN, y)

def draw_cell(c, t):
  x, y, w, h = c["x"], c["y"], c["w"], c["h"]

  # micro-movimiento: deriva leve en base a noise
  nx = noise(c["gx"]*0.2, c["gy"]*0.2, t*MOVE_SPEED)
  ny = noise(c["gy"]*0.2, c["gx"]*0.2, t*MOVE_SPEED + 33)
  dx = (nx - 0.5) * MOVE_AMOUNT * 10
  dy = (ny - 0.5) * MOVE_AMOUNT * 10

  pushMatrix()
  translate(x + w/2 + dx, y + h/2 + dy)
  rotate(c["rot"] * (0.7 + 0.6*(nx)))
  translate(-w/2, -h/2)

  # base “acuarela” (capas)
  base = c["base"]
  accent = c["accent"]
  ink = c["ink"]

  # capa 1
  fill(base[0], base[1], base[2], 190)
  noStroke()
  rect(2, 2, w-4, h-4)

  # capa 2 (variación tonal)
  k = noise((x)*NOISE_SCALE, (y)*NOISE_SCALE, t*0.2 + c["phase"])
  mid = mix_col(base, accent, 0.35 + 0.25*(k-0.5))
  fill(mid[0], mid[1], mid[2], 90)
  rect(6, 6, w-12, h-12)

  # detalles por tipo
  kind = c["kind"]
  if kind == "blocks":
    draw_blocks(w, h, c, t)
  elif kind == "triangle":
    draw_triangle(w, h, c, t)
  elif kind == "arc":
    draw_arc(w, h, c, t)
  elif kind == "ladder":
    draw_ladder(w, h, c, t)
  elif kind == "glyph":
    draw_glyph(w, h, c, t)

  # contorno fino (grafito)
  stroke(0, 55)
  strokeWeight(1)
  noFill()
  rect(2, 2, w-4, h-4)

  popMatrix()

def draw_blocks(w, h, c, t):
  sub = c["sub"]
  sw = w / float(sub)
  sh = h / float(sub)

  for j in range(sub):
    for i in range(sub):
      # decide si pinta bloque o deja “respirar”
      n = noise((c["gx"]*10+i)*0.12, (c["gy"]*10+j)*0.12, t*0.25 + c["phase"])
      if n > 0.43:
        col = mix_col(c["accent"], c["base"], 0.25 + 0.4*(n-0.5))
        a = int(lerp(70, 150, n))
        noStroke()
        fill(col[0], col[1], col[2], a)
        pad = 4 + (1 if (i+j) % 3 == 0 else 0)
        rect(i*sw + pad, j*sh + pad, sw - pad*2, sh - pad*2)

  # marcas lineales
  stroke(0, LINE_ALPHA)
  strokeWeight(1)
  for k in range(2):
    yy = lerp(h*0.25, h*0.8, noise(c["phase"] + k*10, t*0.2))
    line(w*0.12, yy, w*0.88, yy)

def draw_triangle(w, h, c, t):
  # triángulo “arquitectónico”
  col = mix_col(c["accent"], c["base"], 0.25)
  fill(col[0], col[1], col[2], 140)
  noStroke()

  # ligera respiración
  p = noise(c["phase"], t*0.35)
  inset = 8 + p*10

  triangle(inset, h-inset, w*0.5, inset, w-inset, h-inset)

  # líneas internas
  stroke(0, LINE_ALPHA)
  strokeWeight(1)
  for i in range(3):
    yy = lerp(h*0.25, h*0.75, i/2.0)
    line(w*0.2, yy, w*0.8, yy)

def draw_arc(w, h, c, t):
  # arco/semicírculo + puntos
  col = mix_col(c["accent"], c["base"], 0.15)
  noFill()
  stroke(col[0], col[1], col[2], 200)
  strokeWeight(3)

  p = noise(c["phase"]+77, t*0.45)
  r = min(w, h) * (0.32 + 0.12*(p-0.5))
  cx, cy = w*0.5, h*0.62
  arc(cx, cy, r*2, r*2, PI, TWO_PI)

  # puntos “constelación”
  noStroke()
  for i in range(6):
    n = noise(c["gx"]*0.2+i, c["gy"]*0.2, t*0.3)
    px = lerp(w*0.2, w*0.8, n)
    py = lerp(h*0.25, h*0.75, noise(c["gy"]*0.2+i, c["gx"]*0.2, t*0.3+9))
    fill(0, int(lerp(60, 140, n)))
    ellipse(px, py, 3, 3)

def draw_ladder(w, h, c, t):
  # “escalera” (ritmo)
  stroke(0, LINE_ALPHA)
  strokeWeight(2)
  noFill()

  x1, x2 = w*0.30, w*0.70
  line(x1, h*0.18, x1, h*0.82)
  line(x2, h*0.18, x2, h*0.82)

  steps = 6
  for i in range(steps):
    yy = lerp(h*0.22, h*0.78, i/(steps-1.0))
    wob = (noise(c["phase"] + i*4.2, t*0.4) - 0.5) * 10
    line(x1 + wob*0.2, yy, x2 - wob*0.2, yy)

  # acento de color
  col = mix_col(c["accent"], c["base"], 0.10)
  noStroke()
  fill(col[0], col[1], col[2], 120)
  rect(w*0.12, h*0.12, w*0.12, h*0.76)

def draw_glyph(w, h, c, t):
  # “marca” como signo abstracto (no texto literal)
  stroke(0, LINE_ALPHA+20)
  strokeWeight(2)
  noFill()

  p = noise(c["phase"]+123, t*0.5)
  cx, cy = w*0.52, h*0.52
  r = min(w, h) * (0.18 + 0.06*(p-0.5))

  # círculo + cruz rota
  ellipse(cx, cy, r*2, r*2)
  line(cx - r*1.2, cy, cx + r*0.6, cy)
  line(cx, cy - r*0.8, cx, cy + r*1.3)

  # pequeño bloque de color
  col = mix_col(c["accent"], c["base"], 0.0)
  noStroke()
  fill(col[0], col[1], col[2], 150)
  rect(w*0.18, h*0.18, w*0.18, h*0.18)

def draw_musical_lines(t):
  # líneas finas “musicales” sobre toda la composición
  stroke(0, 35)
  strokeWeight(1)
  noFill()

  bands = 4
  for b in range(bands):
    y = lerp(MARGIN*1.1, H - MARGIN*1.1, (b+1)/(bands+1.0))
    beginShape()
    x = MARGIN
    while x <= W - MARGIN:
      n = noise(x*0.01, b*0.2, t*0.25)
      yy = y + (n - 0.5) * (14 + b*6) * MOVE_AMOUNT
      curveVertex(x, yy)
      x += 22
    endShape()

def keyPressed():
  global paletteIndex, USE_MEMORY, MOVE_AMOUNT
  if key == 'r' or key == 'R':
    reseed()
  elif key == 'c' or key == 'C':
    paletteIndex = (paletteIndex + 1) % len(PALETTES)
  elif key == 'm' or key == 'M':
    # memoria ON/OFF
    global USE_MEMORY
    USE_MEMORY = not USE_MEMORY
  elif key == 's' or key == 'S':
    saveFrame("klee_inspired_####.png")
  elif keyCode == UP:
    MOVE_AMOUNT = min(2.5, MOVE_AMOUNT + 0.15)
  elif keyCode == DOWN:
    MOVE_AMOUNT = max(0.0, MOVE_AMOUNT - 0.15)
