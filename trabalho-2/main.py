import math
import os
import random

import glfw
import numpy as np
import pygame
import pygame.freetype
from OpenGL.GL import *

pygame.init()

WIDTH, HEIGHT = 800, 600
TITLE = "TRON: ASTEROIDS"


# ============================================================
# PERSISTÊNCIA DE PLACAR (top 3 salvo em scores.txt)
# ============================================================

def load_high_scores():
    """Lê o arquivo scores.txt e retorna os 3 melhores placares.
    Formato do arquivo: cada linha tem NOME PONTUACAO.
    Retorna lista de tuplas (nome, score) ordenada decrescente."""
    if not os.path.exists("scores.txt"):
        return []
    scores = []
    with open("scores.txt", "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 2:
                scores.append((parts[0], int(parts[1])))
    return sorted(scores, key=lambda x: x[1], reverse=True)[:3]


def save_high_scores(scores):
    """Salva apenas os 3 melhores placares no arquivo, sobrescrevendo."""
    scores = sorted(scores, key=lambda x: x[1], reverse=True)[:3]
    with open("scores.txt", "w") as f:
        for name, score in scores:
            f.write(f"{name} {score}\n")


# ============================================================
# DETECÇÃO DE COLISÃO — círculo vs círculo
# Evita raiz quadrada comparando distância² com (r1+r2)²
# ============================================================

def check_collision(x1, y1, r1, x2, y2, r2):
    """Colisão circular otimizada: compara quadrados das distâncias
    para evitar math.sqrt(). Retorna True se os círculos se tocam."""
    distancia_quadrada = (x1 - x2) ** 2 + (y1 - y2) ** 2
    raios_quadrados = (r1 + r2) ** 2
    return distancia_quadrada <= raios_quadrados


# ============================================================
# ASTEROIDE — polígono irregular com rotação e wrapping de tela
# ============================================================

class Asteroid:
    """Cada asteroide é um polígono convexo irregular gerado
    aleatoriamente. Vértices são calculados em coordenadas polares
    com raio variável (0.7 a 1.3 do raio base) pra dar aspecto rochoso.

    Tamanhos: 3 (grande, 60px) → 2 (médio, 40px) → 1 (pequeno, 20px).
    Ao ser destruído, um asteroide de size > 1 gera 2 filhos de size-1
    no mesmo ponto (método split)."""

    def __init__(self, x=None, y=None, size=3, speed_factor=1.0):
        self.size = size
        self.speed_factor = speed_factor
        # Posição: se não especificada, aleatória na tela
        self.x = random.uniform(0, WIDTH) if x is None else x
        self.y = random.uniform(0, HEIGHT) if y is None else y

        # Cores neon estilo TRON (ciano, magenta, amarelo, verde, laranja, roxo)
        neon_colors = [
            (0.0, 1.0, 1.0),
            (1.0, 0.0, 1.0),
            (1.0, 1.0, 0.0),
            (0.0, 1.0, 0.0),
            (1.0, 0.5, 0.0),
            (0.5, 0.0, 1.0),
        ]
        self.color = random.choice(neon_colors)

        # Velocidade: asteroide menor = mais rápido (4 - size)
        speed_mult = (4 - size) * speed_factor * 1.3
        self.dx = random.uniform(-1.0, 1.0) * speed_mult
        self.dy = random.uniform(-1.0, 1.0) * speed_mult
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-2, 2) * speed_mult

        # Raio de colisão (85% do raio visual pra dar folga)
        self.base_radius = size * 20
        self.radius = self.base_radius * 0.85

        # Gera entre 8 e 14 vértices em círculo com ruído no raio
        num_points = random.randint(8, 14)
        self.vertices = []
        for i in range(num_points):
            angle = (i / num_points) * 2 * math.pi
            r = self.base_radius * random.uniform(0.7, 1.3)
            self.vertices.append((math.cos(angle) * r, math.sin(angle) * r))

    def split(self):
        """Divide o asteroide em 2 menores. Size 1 não divide (retorna [])."""
        if self.size > 1:
            return [
                Asteroid(self.x, self.y, self.size - 1, self.speed_factor),
                Asteroid(self.x, self.y, self.size - 1, self.speed_factor),
            ]
        return []

    def update(self, bounds_width, bounds_height, dt_mult):
        """Move o asteroide com wrapping de tela (margem de 100px).
        dt_mult normaliza o movimento independente do framerate
        (multiplica por dt*60, ou seja, 1.0 = 60 FPS de referência)."""
        self.x += self.dx * dt_mult
        self.y += self.dy * dt_mult
        self.rotation += self.rot_speed * dt_mult

        # Wrapping: quando sai de um lado, aparece do outro
        if self.x < -100:
            self.x = bounds_width + 100
        elif self.x > bounds_width + 100:
            self.x = -100
        if self.y < -100:
            self.y = bounds_height + 100
        elif self.y > bounds_height + 100:
            self.y = -100

    def draw(self):
        """Desenha o asteroide em 2 passos:
        1. Preenchimento escuro com iluminação (GL_POLYGON) — corpo 3D
        2. Contorno neon colorido sem iluminação (GL_LINE_LOOP) — wireframe TRON"""
        glPushMatrix()
        glTranslatef(self.x, self.y, 0.0)
        glRotatef(self.rotation, 0, 0, 1)

        # Corpo preenchido (reage à luz)
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, [0.0, 0.0, 0.0, 1.0])
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, [0.05, 0.05, 0.05, 1.0])
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 80.0)

        glNormal3f(0.0, 0.0, 1.0)
        glBegin(GL_POLYGON)
        for vx, vy in self.vertices:
            glVertex3f(vx, vy, 0.0)
        glEnd()

        # Contorno neon (ignora iluminação pra cor ficar pura)
        glDisable(GL_LIGHTING)
        glColor3fv(self.color)
        glBegin(GL_LINE_LOOP)
        for vx, vy in self.vertices:
            glVertex3f(vx, vy, 0.1)
        glEnd()
        glEnable(GL_LIGHTING)

        glPopMatrix()


# ============================================================
# PROJÉTIL — linha reta que morre ao sair da tela
# ============================================================

class Projectile:
    """Projétil simples: nasce no nariz da nave, viaja em linha reta
    na direção do ângulo de tiro. Update() retorna False quando
    sai dos limites da tela (para ser removido da lista)."""

    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 15.0
        self.radius = 2.0

        # Decompõe velocidade em componentes X e Y a partir do ângulo
        rad = math.radians(angle)
        self.vx = math.cos(rad) * self.speed
        self.vy = math.sin(rad) * self.speed

    def update(self, bounds_width, bounds_height, dt_mult):
        self.x += self.vx * dt_mult
        self.y += self.vy * dt_mult
        # Morre ao sair da tela (sem wrapping — diferente dos asteroides)
        if self.x < 0 or self.x > bounds_width or self.y < 0 or self.y > bounds_height:
            return False
        return True

    def draw(self):
        """Desenha traço neon rosa de 20px na direção do tiro."""
        glPushMatrix()
        glTranslatef(self.x, self.y, 0.0)
        glRotatef(self.angle, 0, 0, 1)

        glDisable(GL_LIGHTING)
        glColor3f(1.0, 0.0, 0.5)
        glBegin(GL_LINES)
        glVertex2f(0.0, 0.0)
        glVertex2f(20.0, 0.0)
        glEnd()
        glEnable(GL_LIGHTING)
        glPopMatrix()


# ============================================================
# NAVE DO JOGADOR — modelo 3D com normais e empuxo com atrito
# ============================================================

class Spaceship:
    """Nave com física simulada: aceleração, velocidade máxima, arrasto (drag).

    Modelo 3D: 7 vértices e 6 faces (triângulos e quads).
    As normais são pré-calculadas no __init__ para iluminação correta.

    Controles:
    - Mouse: mira (rotação instantânea via atan2)
    - W/Seta Cima: empuxo na direção da rotação
    - Mouse Esquerdo/Espaço: atirar (cooldown de 12 frames)"""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.ax = 0.0
        self.ay = 0.0
        self.rotation = -90.0        # Começa apontando pra cima (-90°)
        self.thrust_power = 0.15     # Aceleração por frame
        self.drag = 0.99             # Atrito: multiplica velocidade a cada frame
        self.max_speed = 8.0         # Velocidade máxima (cap)
        self.rot_speed = 4.5
        self.is_thrusting = False
        self.shoot_cooldown = 0      # Frames restantes até poder atirar
        self.radius = 12.0           # Raio de colisão

        # Vértices do modelo 3D da nave (nariz, asas, profundidade em Z)
        self.vertices = np.array(
            [
                [0.0, -20.0, 0.0],     # 0: nariz
                [-12.0, 15.0, 5.0],    # 1: asa esquerda frontal
                [0.0, 5.0, 2.0],       # 2: centro frontal
                [12.0, 15.0, 5.0],     # 3: asa direita frontal
                [-12.0, 15.0, -5.0],   # 4: asa esquerda traseira
                [0.0, 5.0, -2.0],      # 5: centro traseiro
                [12.0, 15.0, -5.0],    # 6: asa direita traseira
            ],
            dtype=np.float32,
        )

        # Faces indexadas + normais pré-calculadas
        self.faces = [
            ([0, 1, 2], self.calculate_normal(0, 1, 2)),       # Triângulo superior esquerdo
            ([0, 2, 3], self.calculate_normal(0, 2, 3)),       # Triângulo superior direito
            ([0, 5, 4], self.calculate_normal(0, 5, 4)),       # Triângulo inferior esquerdo
            ([0, 6, 5], self.calculate_normal(0, 6, 5)),       # Triângulo inferior direito
            ([1, 4, 5, 2], self.calculate_normal(1, 4, 2)),    # Lateral esquerda (quad)
            ([3, 2, 5, 6], self.calculate_normal(3, 2, 6)),    # Lateral direita (quad)
        ]

    def calculate_normal(self, i1, i2, i3):
        """Calcula vetor normal de uma face usando produto vetorial.
        Usa regra da mão direita: (v2-v1) × (v3-v1), depois normaliza."""
        v1, v2, v3 = self.vertices[i1], self.vertices[i2], self.vertices[i3]
        normal = np.cross(v2 - v1, v3 - v1)
        norm = np.linalg.norm(normal)
        return normal / norm if norm != 0 else normal

    def fire(self):
        """Cria projétil no nariz da nave. Respeita cooldown de 12 frames."""
        if self.shoot_cooldown <= 0:
            self.shoot_cooldown = 12
            rad = math.radians(self.rotation)
            # Nariz fica a 20px do centro na direção da rotação
            nose_x = self.x + math.cos(rad) * 20
            nose_y = self.y + math.sin(rad) * 20
            return Projectile(nose_x, nose_y, self.rotation)
        return None

    def update(self, win_w, win_h, dt_mult):
        """Atualiza física da nave:
        1. Decrementa cooldown de tiro
        2. Aplica empuxo se acelerando (vetor na direção da rotação)
        3. Aplica drag (atrito) pra desacelerar naturalmente
        4. Cap de velocidade máxima
        5. Wrapping de tela com margem de 20px"""
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1 * dt_mult

        # Empuxo: acelera na direção para onde a nave aponta
        if self.is_thrusting:
            rad = math.radians(self.rotation)
            self.ax = math.cos(rad) * self.thrust_power
            self.ay = math.sin(rad) * self.thrust_power
        else:
            self.ax = self.ay = 0.0

        self.vx += self.ax * dt_mult
        self.vy += self.ay * dt_mult

        # Cap de velocidade: limita sem alterar a direção
        speed = math.sqrt(self.vx**2 + self.vy**2)
        if speed > self.max_speed:
            self.vx = (self.vx / speed) * self.max_speed
            self.vy = (self.vy / speed) * self.max_speed

        # Drag: simula atrito do espaço (não realista, mas dá sensação boa)
        self.vx *= self.drag
        self.vy *= self.drag
        self.x += self.vx * dt_mult
        self.y += self.vy * dt_mult

        # Wrapping de tela
        if self.x < -20:
            self.x = win_w + 20
        elif self.x > win_w + 20:
            self.x = -20
        if self.y < -20:
            self.y = win_h + 20
        elif self.y > win_h + 20:
            self.y = -20

    def draw(self):
        """Desenha a nave com iluminação especular ciano (estilo TRON).
        Faces com 3 vértices → GL_TRIANGLES, 4 vértices → GL_QUADS.
        Se estiver acelerando, desenha chama laranja do motor (sem luz)."""
        glPushMatrix()
        glTranslatef(self.x, self.y, 0.0)
        glRotatef(self.rotation + 90, 0.0, 0.0, 1.0)  # +90 corrige orientação

        # Material da nave: escuro com brilho ciano especular
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, [0.0, 0.0, 0.0, 1.0])
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, [0.1, 0.1, 0.15, 1.0])
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.0, 1.0, 1.0, 1.0])
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 128.0)

        for face, normal in self.faces:
            glNormal3fv(normal)
            if len(face) == 3:
                glBegin(GL_TRIANGLES)
            else:
                glBegin(GL_QUADS)
            for vertex_index in face:
                glVertex3fv(self.vertices[vertex_index])
            glEnd()

        # Chama do motor: triângulo laranja (sem iluminação pra ficar neon)
        if self.is_thrusting:
            glDisable(GL_LIGHTING)
            glColor3f(1.0, 0.4, 0.0)
            glBegin(GL_TRIANGLES)
            glVertex3f(-5.0, 10.0, 0.0)
            glVertex3f(0.0, 30.0, 0.0)
            glVertex3f(5.0, 10.0, 0.0)
            glEnd()
            glEnable(GL_LIGHTING)

        glPopMatrix()


# ============================================================
# APLICAÇÃO PRINCIPAL — loop de jogo e máquina de estados
# ============================================================

class GameApp:
    """Controlador principal.

    Máquina de estados:
      MENU       → tela inicial com opções
      PLAYING    → jogo ativo
      NAME_INPUT → tela de digitação do nome (3 letras) após high score
      GAME_OVER  → tela de game over com placar

    Estados transicionam por callbacks de teclado (key_callback)."""

    def __init__(self):
        if not glfw.init():
            raise Exception("GLFW could not be initialized!")

        # Janela GLFW com 4x MSAA (anti-aliasing)
        glfw.window_hint(glfw.SAMPLES, 4)
        self.window = glfw.create_window(WIDTH, HEIGHT, TITLE, None, None)
        if not self.window:
            glfw.terminate()
            raise Exception("GLFW Window could not be created!")

        glfw.make_context_current(self.window)
        glfw.set_key_callback(self.window, self.key_callback)
        glfw.swap_interval(1)  # VSync

        # Configurações globais do OpenGL
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LINE_SMOOTH)
        glLineWidth(2.0)

        # Fontes: pygame.freetype usa fonte padrão do sistema
        # text_scale = 0.5 reduz tamanho das texturas (144px → 72px efetivo)
        self.font_large = pygame.freetype.SysFont(None, 144)
        self.font_small = pygame.freetype.SysFont(None, 72)
        self.text_scale = 0.5

        # Pré-renderiza texturas estáticas (criadas uma vez, reusadas)
        self.title_tex, self.title_size = self.create_text_texture(
            TITLE, self.font_large, (0, 255, 255, 255)
        )
        self.gameover_tex, self.go_size = self.create_text_texture(
            "GAME OVER", self.font_large, (255, 0, 80, 255)
        )
        self.restart_tex, self.res_size = self.create_text_texture(
            "PRESS ENTER", self.font_small, (200, 255, 255, 255)
        )

        # Opções do menu: cada uma tem textura normal (azul) e destacada (magenta)
        self.options = ["START GAME", "EXIT"]
        self.option_textures = []
        for opt in self.options:
            norm_tex, size = self.create_text_texture(
                opt, self.font_small, (100, 150, 255, 255)
            )
            high_tex, _ = self.create_text_texture(
                opt, self.font_small, (255, 0, 255, 255)
            )
            self.option_textures.append((norm_tex, high_tex, size))

        self.high_scores = load_high_scores()
        self.player_name = ""

        self.reset_game()
        self.game_state = "MENU"

    def reset_game(self):
        """Prepara novo jogo:
        - Nave no centro
        - 6 asteroides grandes spawnados fora do raio de segurança (250px)
        - Score zerado, dificuldade inicial 1.0
        - Spawna novo asteroide a cada 3s (diminui com dificuldade)"""
        win_w, win_h = glfw.get_window_size(self.window)
        if win_w == 0 or win_h == 0:
            win_w, win_h = WIDTH, HEIGHT

        center_x, center_y = win_w / 2, win_h / 2
        self.player_ship = Spaceship(center_x, center_y)
        self.projectiles = []
        self.asteroids = []

        self.score = 0
        self.difficulty_multiplier = 1.0
        self.spawn_timer = 3.0  # Segundos até spawnar próximo asteroide

        # Spawn inicial: 6 asteroides longe do jogador (raio de segurança 250px)
        safe_radius = 250.0
        for _ in range(6):
            while True:
                ax, ay = random.uniform(0, win_w), random.uniform(0, win_h)
                distancia = math.sqrt((ax - center_x) ** 2 + (ay - center_y) ** 2)
                if distancia > safe_radius:
                    self.asteroids.append(
                        Asteroid(
                            x=ax, y=ay, size=3, speed_factor=self.difficulty_multiplier
                        )
                    )
                    break

        self.selected_option = 0
        self.game_state = "PLAYING"

    def spawn_new_asteroid(self, win_w, win_h):
        """Spawna asteroide size=3 em uma borda aleatória da tela."""
        edge = random.randint(0, 3)
        if edge == 0:        # Topo
            ax, ay = random.uniform(0, win_w), -50
        elif edge == 1:      # Base
            ax, ay = random.uniform(0, win_w), win_h + 50
        elif edge == 2:      # Esquerda
            ax, ay = -50, random.uniform(0, win_h)
        else:                # Direita
            ax, ay = win_w + 50, random.uniform(0, win_h)
        self.asteroids.append(
            Asteroid(x=ax, y=ay, size=3, speed_factor=self.difficulty_multiplier)
        )

    def setup_lighting(self, light_x, light_y):
        """Configura luz pontual (GL_LIGHT0) na posição da nave.
        Luz azulada ambiente + difusa, especular branca.
        Atenuação linear de 0.001 simula leve queda com distância.
        GL_COLOR_MATERIAL permite usar glColor junto com iluminação."""
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.02, 0.02, 0.05, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.6, 0.8, 1.0, 1.0])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
        glLightfv(GL_LIGHT0, GL_POSITION, [light_x, light_y, 50.0, 1.0])
        glLightf(GL_LIGHT0, GL_CONSTANT_ATTENUATION, 1.0)
        glLightf(GL_LIGHT0, GL_LINEAR_ATTENUATION, 0.001)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    def create_text_texture(self, text, font, color):
        """Renderiza texto via pygame e sobe como textura OpenGL.
        Retorna (tex_id, (width, height)).
        Usada para texturas estáticas (título, menu, game over)."""
        surface, _ = font.render(text, color)
        text_data = pygame.image.tostring(surface, "RGBA", True)
        width, height = surface.get_width(), surface.get_height()
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            width,
            height,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            text_data,
        )
        return tex_id, (width, height)

    def draw_dynamic_text(self, text, font, color, x, y):
        """Renderiza texto que muda todo frame (score, nome).
        Cria textura, desenha, e DELETA em seguida (GL_DELETE_TEXTURES)
        pra não vazar memória. Retorna largura desenhada pra centralização."""
        surface, _ = font.render(text, color)
        text_data = pygame.image.tostring(surface, "RGBA", True)
        width, height = surface.get_width(), surface.get_height()

        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            width,
            height,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            text_data,
        )

        self.draw_texture(
            tex_id, x, y, width * self.text_scale, height * self.text_scale
        )
        glDeleteTextures(1, [tex_id])
        return width * self.text_scale

    def draw_texture(self, tex_id, x, y, width, height):
        """Desenha um quad texturizado na posição (x,y).
        Coordenadas de textura Y invertidas porque pygame vs OpenGL."""
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 1)
        glVertex2f(x, y)
        glTexCoord2f(1, 1)
        glVertex2f(x + width, y)
        glTexCoord2f(1, 0)
        glVertex2f(x + width, y + height)
        glTexCoord2f(0, 0)
        glVertex2f(x, y + height)
        glEnd()
        glDisable(GL_TEXTURE_2D)

    def draw_menu_cursor(self, x, y):
        """Desenha seta (diamante virado) ao lado da opção selecionada."""
        glPushMatrix()
        glTranslatef(x, y, 0)
        glRotatef(90, 0, 0, 1)
        glColor3f(0.0, 1.0, 0.8)
        glBegin(GL_LINE_LOOP)
        glVertex2f(0, -15)
        glVertex2f(-10, 10)
        glVertex2f(0, 5)
        glVertex2f(10, 10)
        glEnd()
        glPopMatrix()

    def process_death(self):
        """Chamado quando nave colide com asteroide.
        Se score > 0 E (top 3 não tá cheio OU score é maior que o 3º lugar):
          → vai pra NAME_INPUT (digitar 3 letras).
        Senão:
          → vai direto pra GAME_OVER."""
        self.high_scores = load_high_scores()

        if self.score > 0 and (
            len(self.high_scores) < 3 or self.score > self.high_scores[-1][1]
        ):
            self.player_name = ""
            self.game_state = "NAME_INPUT"
        else:
            self.game_state = "GAME_OVER"

    def key_callback(self, window, key, scancode, action, mods):
        """Callback GLFW para eventos de teclado.
        Comportamento muda conforme game_state atual (máquina de estados).
        No NAME_INPUT: só aceita teclas A-Z (códigos 65-90), backspace e enter."""
        if action == glfw.PRESS or action == glfw.REPEAT:
            if self.game_state == "MENU":
                if key == glfw.KEY_UP:
                    self.selected_option = (self.selected_option - 1) % len(
                        self.options
                    )
                elif key == glfw.KEY_DOWN:
                    self.selected_option = (self.selected_option + 1) % len(
                        self.options
                    )
                elif key == glfw.KEY_ENTER:
                    if self.selected_option == 0:
                        self.reset_game()
                    elif self.selected_option == 1:
                        glfw.set_window_should_close(self.window, True)

            elif self.game_state == "PLAYING":
                if key == glfw.KEY_ESCAPE:
                    self.game_state = "MENU"

            elif self.game_state == "GAME_OVER":
                if key == glfw.KEY_ENTER:
                    self.game_state = "MENU"

            elif self.game_state == "NAME_INPUT":
                if key == glfw.KEY_ENTER and len(self.player_name) == 3:
                    self.high_scores.append((self.player_name, self.score))
                    save_high_scores(self.high_scores)
                    self.high_scores = load_high_scores()
                    self.game_state = "GAME_OVER"
                elif key == glfw.KEY_BACKSPACE:
                    self.player_name = self.player_name[:-1]
                elif 65 <= key <= 90 and len(self.player_name) < 3:
                    self.player_name += chr(key)

    def handle_gameplay_input(self, dt_mult):
        """Processa input durante o jogo (chamado a cada frame no PLAYING).

        Mira: a nave sempre aponta pro cursor do mouse.
        O ângulo é calculado com atan2(dy, dx) — diferença entre
        posição do mouse e posição da nave.

        Tiro: mouse esquerdo OU espaço, respeitando cooldown da nave."""
        # Mira via mouse: calcula ângulo entre nave e cursor
        mx, my = glfw.get_cursor_pos(self.window)
        dx = mx - self.player_ship.x
        dy = my - self.player_ship.y
        self.player_ship.rotation = math.degrees(math.atan2(dy, dx))

        # Empuxo: W ou Seta Cima
        if (
            glfw.get_key(self.window, glfw.KEY_UP) == glfw.PRESS
            or glfw.get_key(self.window, glfw.KEY_W) == glfw.PRESS
        ):
            self.player_ship.is_thrusting = True
        else:
            self.player_ship.is_thrusting = False

        # Tiro: Mouse Esquerdo ou Espaço
        if (
            glfw.get_mouse_button(self.window, glfw.MOUSE_BUTTON_LEFT) == glfw.PRESS
            or glfw.get_key(self.window, glfw.KEY_SPACE) == glfw.PRESS
        ):
            new_projectile = self.player_ship.fire()
            if new_projectile:
                self.projectiles.append(new_projectile)

    def run(self):
        """Loop principal do jogo.

        Estrutura do frame:
        1. Calcula dt (delta time) e dt_mult (normalizado pra 60 FPS)
        2. Desenha asteroides de fundo (em todos os estados)
        3. Desenha UI conforme game_state (MENU/PLAYING/NAME_INPUT/GAME_OVER)
        4. No PLAYING: física, colisões, spawn, iluminação 3D

        Projeção: glOrtho com Y invertido (0 no topo) — sistema de
        coordenadas de tela tradicional, compatível com pygame/freetype."""
        last_time = glfw.get_time()

        while not glfw.window_should_close(self.window):
            # Delta time: normalizado para 60 FPS de referência
            # dt_mult = 1.0 a 60 FPS; >1.0 se mais lento, <1.0 se mais rápido
            current_time = glfw.get_time()
            dt = current_time - last_time
            last_time = current_time
            dt_mult = dt * 60.0

            glfw.poll_events()

            # Viewport: usa framebuffer size (importante em telas HiDPI)
            fb_w, fb_h = glfw.get_framebuffer_size(self.window)
            glViewport(0, 0, fb_w, fb_h)
            win_w, win_h = glfw.get_window_size(self.window)
            if win_w == 0 or win_h == 0:
                continue

            # Projeção ortográfica 2D (Y invertido: 0 = topo)
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            glOrtho(0, win_w, win_h, 0, -1, 10)
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()

            glClearColor(0.02, 0.02, 0.05, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            # Fundo: asteroides desenhados em TODOS os estados
            # No MENU e GAME_OVER ficam parados (não chama update)
            glDisable(GL_LIGHTING)
            for asteroid in self.asteroids:
                if self.game_state == "PLAYING":
                    asteroid.update(win_w, win_h, dt_mult)
                asteroid.draw()

            if self.game_state == "MENU":
                glDisable(GL_LIGHTING)
                glColor3f(1.0, 1.0, 1.0)
                tw, th = self.title_size
                draw_tw, draw_th = tw * self.text_scale, th * self.text_scale
                self.draw_texture(
                    self.title_tex,
                    (win_w - draw_tw) / 2,
                    win_h / 4 - draw_th,
                    draw_tw,
                    draw_th,
                )

                for i, (norm_tex, high_tex, size) in enumerate(self.option_textures):
                    ow, oh = size
                    draw_ow, draw_oh = ow * self.text_scale, oh * self.text_scale
                    x = (win_w - draw_ow) / 2
                    y = win_h / 2 + (i * 80)

                    if i == self.selected_option:
                        self.draw_texture(high_tex, x, y - draw_oh, draw_ow, draw_oh)
                        self.draw_menu_cursor(x - 40, y - (draw_oh / 2))
                    else:
                        self.draw_texture(norm_tex, x, y - draw_oh, draw_ow, draw_oh)

            elif self.game_state == "PLAYING":
                self.handle_gameplay_input(dt_mult)
                self.player_ship.update(win_w, win_h, dt_mult)

                # Remove projéteis que saíram da tela (update retorna False)
                self.projectiles = [
                    p for p in self.projectiles if p.update(win_w, win_h, dt_mult)
                ]

                # Dificuldade aumenta com o tempo: multiplicador sobe, spawn acelera
                self.difficulty_multiplier += dt * 0.015
                self.spawn_timer -= dt
                if self.spawn_timer <= 0:
                    self.spawn_timer = max(0.5, 4.0 / self.difficulty_multiplier)
                    self.spawn_new_asteroid(win_w, win_h)

                # Colisão projétil ↔ asteroide: itera sobre cópias [:] das listas
                # porque podemos remover elementos durante a iteração
                for p in self.projectiles[:]:
                    for a in self.asteroids[:]:
                        if check_collision(p.x, p.y, p.radius, a.x, a.y, a.radius):
                            if p in self.projectiles:
                                self.projectiles.remove(p)
                            if a in self.asteroids:
                                self.asteroids.remove(a)
                                self.asteroids.extend(a.split())  # Divide se size>1
                                # Pontuação por tamanho: grande=50, médio=100, pequeno=200
                                if a.size == 3:
                                    self.score += 50
                                elif a.size == 2:
                                    self.score += 100
                                else:
                                    self.score += 200
                            break

                # Colisão nave ↔ asteroide
                for a in self.asteroids:
                    if check_collision(
                        self.player_ship.x,
                        self.player_ship.y,
                        self.player_ship.radius,
                        a.x,
                        a.y,
                        a.radius,
                    ):
                        self.process_death()

                # Iluminação 3D: luz na posição da nave, depth test pra nave
                self.setup_lighting(self.player_ship.x, self.player_ship.y)
                glEnable(GL_DEPTH_TEST)
                self.player_ship.draw()
                glDisable(GL_DEPTH_TEST)

                for p in self.projectiles:
                    p.draw()
                glDisable(GL_LIGHTING)

                # HUD: score no canto superior esquerdo
                score_text = f"SCORE: {self.score}"
                self.draw_dynamic_text(
                    score_text, self.font_small, (200, 200, 200, 255), 20, 20
                )

            elif self.game_state == "NAME_INPUT":
                glDisable(GL_LIGHTING)

                hs_text = "NEW HIGH SCORE!"
                surface, _ = self.font_small.render(hs_text, (0, 255, 255, 255))
                w = surface.get_width() * self.text_scale
                self.draw_dynamic_text(
                    hs_text,
                    self.font_small,
                    (0, 255, 255, 255),
                    (win_w - w) / 2,
                    win_h / 2 - 60,
                )

                # Placeholder estilo arcade: underline piscando se < 3 letras
                input_display = self.player_name + (
                    "_" if len(self.player_name) < 3 else ""
                )
                prompt_text = f"ENTER NAME: {input_display}"
                surface, _ = self.font_small.render(prompt_text, (255, 255, 0, 255))
                w = surface.get_width() * self.text_scale
                self.draw_dynamic_text(
                    prompt_text,
                    self.font_small,
                    (255, 255, 0, 255),
                    (win_w - w) / 2,
                    win_h / 2,
                )

            elif self.game_state == "GAME_OVER":
                glDisable(GL_LIGHTING)

                tw, th = self.go_size
                draw_tw, draw_th = tw * self.text_scale, th * self.text_scale
                self.draw_texture(
                    self.gameover_tex,
                    (win_w - draw_tw) / 2,
                    win_h / 4,
                    draw_tw,
                    draw_th,
                )

                fs_text = f"SCORE: {self.score}"
                surface, _ = self.font_small.render(fs_text, (255, 255, 0, 255))
                w = surface.get_width() * self.text_scale
                self.draw_dynamic_text(
                    fs_text,
                    self.font_small,
                    (255, 255, 0, 255),
                    (win_w - w) / 2,
                    win_h / 4 + 60,
                )

                # Tabela de placar: exibe top 3 com nome e score
                top_y = win_h / 2 + 20
                lbl = "--- TOP 3 ---"
                surface, _ = self.font_small.render(lbl, (0, 255, 255, 255))
                w = surface.get_width() * self.text_scale
                self.draw_dynamic_text(
                    lbl, self.font_small, (0, 255, 255, 255), (win_w - w) / 2, top_y
                )

                for i, (n, s) in enumerate(self.high_scores):
                    row = f"{i + 1}. {n} - {s}"
                    surface, _ = self.font_small.render(row, (200, 200, 200, 255))
                    w = surface.get_width() * self.text_scale
                    self.draw_dynamic_text(
                        row,
                        self.font_small,
                        (200, 200, 200, 255),
                        (win_w - w) / 2,
                        top_y + 40 + (i * 35),
                    )

                rw, rh = self.res_size
                draw_rw, draw_rh = rw * self.text_scale, rh * self.text_scale
                self.draw_texture(
                    self.restart_tex,
                    (win_w - draw_rw) / 2,
                    win_h - 100,
                    draw_rw,
                    draw_rh,
                )

            glfw.swap_buffers(self.window)

        glfw.terminate()


if __name__ == "__main__":
    app = GameApp()
    app.run()
