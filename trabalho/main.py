#!/usr/bin/env python3

# Importações de bibliotecas padrão
import math  # Funções matemáticas (seno, cosseno, radianos, etc.)
import sys  # Funções do sistema (ex: sys.exit para encerrar o programa)

# Importação do GLFW — biblioteca para criar janelas e capturar entrada do teclado/mouse
import glfw

# Importações do OpenGL — biblioteca gráfica para desenhar formas 3D
from OpenGL.GL import (
    GL_BLEND,  # Constante para habilitar transparência
    GL_COLOR_BUFFER_BIT,  # Constante para limpar o buffer de cor (a imagem na tela)
    GL_DEPTH_BUFFER_BIT,  # Constante para limpar o buffer de profundidade (quem está na frente)
    GL_DEPTH_TEST,  # Constante para habilitar teste de profundidade (objetos atrás ficam atrás)
    GL_LINE_LOOP,  # Modo de desenho: linhas conectadas em loop (usado para anéis)
    GL_MODELVIEW,  # Matriz que controla posição/rotação dos objetos e câmera
    GL_ONE_MINUS_SRC_ALPHA,  # Fator de transparência para blending
    GL_POINTS,  # Modo de desenho: pontos individuais (usado para estrelas)
    GL_PROJECTION,  # Matriz que controla a perspectiva (como uma lente de câmera)
    GL_QUADS,  # Modo de desenho: quadriláteros (usado para faces do cubo)
    GL_SRC_ALPHA,  # Fator de transparência para blending
    GL_TRIANGLES,  # Modo de desenho: triângulos (usado para octaedro e tetraedro)
    glBegin,  # Inicia definição de vértices de uma forma
    glBlendFunc,  # Configura como transparência é calculada
    glClear,  # Limpa a tela para redesenhar
    glClearColor,  # Define a cor de fundo da tela
    glColor3f,  # Define cor RGB (vermelho, verde, azul) — valores de 0.0 a 1.0
    glColor4f,  # Define cor RGBA (RGB + alfa/transparência)
    glEnable,  # Habilita uma funcionalidade do OpenGL
    glEnd,  # Finaliza definição de vértices
    glLoadIdentity,  # Reseta a matriz atual para a identidade (sem transformações)
    glMatrixMode,  # Seleciona qual matriz será modificada (projeção ou modelo)
    glPointSize,  # Define o tamanho dos pontos desenhados
    glPopMatrix,  # Restaura a matriz salva anteriormente (desfaz transformações temporárias)
    glPushMatrix,  # Salva a matriz atual na pilha (para aplicar transformações temporárias)
    glRotatef,  # Aplica rotação: (ângulo em graus, eixo X, eixo Y, eixo Z)
    glScalef,  # Aplica escala: (fator X, fator Y, fator Z)
    glTranslatef,  # Move/translada objetos: (deslocamento X, Y, Z)
    glVertex3f,  # Define um vértice (ponto) no espaço 3D: (x, y, z)
    glViewport,  # Define a área da janela onde o OpenGL vai desenhar
)
from OpenGL.GLU import gluLookAt, gluPerspective
# gluLookAt — posiciona a câmera no espaço 3D (posição, alvo, vetor "para cima")
# gluPerspective — configura a projeção em perspectiva (campo de visão, proporção, perto, longe)

# ========================
# Variáveis globais da câmera
# ========================
cam_x, cam_y, cam_z = 0.0, 3.0, 9.0  # Posição inicial da câmera (x, y, z)
cam_yaw = 0.0  # Rotação horizontal da câmera (esquerda/direita), em graus
cam_pitch = -18.0  # Rotação vertical da câmera (cima/baixo), em graus — negativo = olhando para baixo
MOVE_SPEED = 0.05  # Velocidade de movimento da câmera por frame
ROT_SPEED = 1.5  # Velocidade de rotação da câmera por frame (graus)

# ========================
# Variáveis globais da animação
# ========================
anim_angle = 0.0  # Ângulo atual da animação (aumenta a cada frame, controla rotação dos objetos)
anim_speed = 1.0  # Multiplicador de velocidade da animação (ajustável com +/-)

# Conjunto de teclas atualmente pressionadas (permite detectar teclas mantidas)
keys_held = set()


def draw_octahedron(r=0.8):
    """Desenha um octaedro (diamante/sol) com raio r.
    Um octaedro tem 6 vértices e 8 faces triangulares.
    Usado como o "sol" no centro do sistema solar."""

    # Define os 6 vértices do octaedro (cima, baixo, direita, esquerda, frente, trás)
    top = (0, r, 0)  # Vértice superior
    bot = (0, -r, 0)  # Vértice inferior
    rgt = (r, 0, 0)  # Vértice direito
    lft = (-r, 0, 0)  # Vértice esquerdo
    frt = (0, 0, r)  # Vértice frontal
    bck = (0, 0, -r)  # Vértice traseiro

    # Cor de cada vértice (tons de amarelo/laranja para parecer um sol)
    col = {
        top: (1.0, 1.0, 0.1),  # Amarelo claro
        bot: (1.0, 0.4, 0.0),  # Laranja escuro
        rgt: (1.0, 0.6, 0.0),  # Laranja
        lft: (1.0, 0.8, 0.0),  # Amarelo alaranjado
        frt: (1.0, 0.9, 0.1),  # Amarelo
        bck: (0.9, 0.3, 0.0),  # Laranja escuro
    }

    # Define as 8 faces triangulares do octaedro
    # Cada face conecta 3 vértices
    # 4 faces superiores (conectadas ao vértice "top")
    # 4 faces inferiores (conectadas ao vértice "bot")
    faces = [
        (top, rgt, frt),  # Face superior: cima-direita-frente
        (top, frt, lft),  # Face superior: cima-frente-esquerda
        (top, lft, bck),  # Face superior: cima-esquerda-trás
        (top, bck, rgt),  # Face superior: cima-trás-direita
        (bot, frt, rgt),  # Face inferior: baixo-frente-direita
        (bot, lft, frt),  # Face inferior: baixo-esquerda-frente
        (bot, bck, lft),  # Face inferior: baixo-trás-esquerda
        (bot, rgt, bck),  # Face inferior: baixo-direita-trás
    ]

    # Desenha todos os triângulos
    glBegin(GL_TRIANGLES)  # Começa a desenhar triângulos
    for tri in faces:  # Para cada face triangular
        for v in tri:  # Para cada vértice da face
            glColor3f(*col[v])  # Define a cor do vértice
            glVertex3f(*v)  # Define a posição do vértice
    glEnd()  # Termina de desenhar


def draw_cube(s=0.5):
    """Desenha um cubo com lado 2*s (centralizado na origem).
    Usado como o "planeta" que orbita o sol."""

    # Define os 8 vértices do cubo
    # Cada vértice é uma combinação de -s e +s nos eixos x, y, z
    v = [
        (-s, -s, -s),  # 0: canto traseiro-inferior-esquerdo
        (s, -s, -s),  # 1: canto traseiro-inferior-direito
        (s, s, -s),  # 2: canto traseiro-superior-direito
        (-s, s, -s),  # 3: canto traseiro-superior-esquerdo
        (-s, -s, s),  # 4: canto frontal-inferior-esquerdo
        (s, -s, s),  # 5: canto frontal-inferior-direito
        (s, s, s),  # 6: canto frontal-superior-direito
        (-s, s, s),  # 7: canto frontal-superior-esquerdo
    ]

    # Cor de cada vértice (tons de azul, verde, roxo)
    c = [
        (0.10, 0.30, 1.00),  # 0: azul escuro
        (0.10, 0.80, 1.00),  # 1: azul claro
        (0.10, 1.00, 0.50),  # 2: verde água
        (0.50, 1.00, 0.10),  # 3: verde limão
        (0.20, 0.10, 0.90),  # 4: roxo
        (0.80, 0.10, 0.90),  # 5: magenta
        (1.00, 1.00, 1.00),  # 6: branco
        (0.30, 0.30, 1.00),  # 7: azul médio
    ]

    # Define as 6 faces do cubo (cada face é um quadrilátero com 4 vértices)
    quads = [
        (4, 5, 6, 7),  # Face frontal
        (1, 0, 3, 2),  # Face traseira
        (0, 1, 5, 4),  # Face inferior
        (2, 3, 7, 6),  # Face superior
        (0, 4, 7, 3),  # Face esquerda
        (1, 2, 6, 5),  # Face direita
    ]

    # Desenha todos os quadriláteros
    glBegin(GL_QUADS)  # Começa a desenhar quadriláteros
    for q in quads:  # Para cada face
        for i in q:  # Para cada vértice da face
            glColor3f(*c[i])  # Define a cor do vértice (cores interpoladas entre vértices)
            glVertex3f(*v[i])  # Define a posição do vértice
    glEnd()  # Termina de desenhar


def draw_tetrahedron(s=0.22):
    """Desenha um tetraedro (pirâmide de 4 faces) com tamanho s.
    Usado como a "lua" que orbita o planeta."""

    # Define os 4 vértices do tetraedro
    v = [
        (0, s, 0),  # 0: vértice superior (ponta)
        (-s, -s * 0.7, s),  # 1: base esquerda-frente
        (s, -s * 0.7, s),  # 2: base direita-frente
        (0, -s * 0.7, -s),  # 3: base centro-trás
    ]

    # Cor de cada vértice (tons de azul claro/branco, aspecto lunar)
    c = [
        (0.90, 0.90, 1.00),  # 0: quase branco
        (0.50, 0.50, 0.90),  # 1: azul médio
        (0.70, 0.70, 1.00),  # 2: azul claro
        (0.30, 0.30, 0.70),  # 3: azul escuro
    ]

    # Define as 4 faces triangulares do tetraedro
    faces = [(0, 1, 2), (0, 2, 3), (0, 3, 1), (1, 3, 2)]

    # Desenha todos os triângulos
    glBegin(GL_TRIANGLES)
    for tri in faces:
        for i in tri:
            glColor3f(*c[i])
            glVertex3f(*v[i])
    glEnd()


def draw_ring(radius, segments=72):
    """Desenha um anel (círculo) horizontal no plano XZ.
    Representa a órbita de um corpo celeste.
    radius = raio do anel, segments = número de segmentos (mais = mais suave)."""

    glColor4f(0.6, 0.6, 0.8, 0.25)  # Cor azul-acinzentada, bastante transparente (alfa=0.25)
    glBegin(GL_LINE_LOOP)  # Desenha linhas conectadas em loop fechado
    for i in range(segments):
        # Calcula o ângulo de cada ponto ao redor do círculo
        a = 2.0 * math.pi * i / segments
        # Posiciona o ponto no plano horizontal (XZ), y=0
        glVertex3f(math.cos(a) * radius, 0.0, math.sin(a) * radius)
    glEnd()


def draw_stars(count=200, seed=42):
    """Desenha estrelas de fundo como pontos brancos espalhados numa esfera grande.
    count = quantidade de estrelas, seed = semente para gerar posições consistentes."""

    # Gerador de números pseudo-aleatórios simples (LCG — Linear Congruential Generator)
    # Usa seed fixa para que as estrelas apareçam sempre nas mesmas posições
    rng_state = seed

    def rng():
        nonlocal rng_state
        # Fórmula LCG: próximo = (atual * a + c) mod m
        rng_state = (rng_state * 1664525 + 1013904223) & 0xFFFFFFFF
        return rng_state / 0xFFFFFFFF  # Retorna valor entre 0.0 e 1.0

    glPointSize(1.5)  # Tamanho de cada ponto (estrela)
    glColor4f(1.0, 1.0, 1.0, 0.8)  # Cor branca, levemente transparente
    glBegin(GL_POINTS)  # Começa a desenhar pontos
    for _ in range(count):
        # Gera coordenadas esféricas aleatórias para distribuir uniformemente na esfera
        theta = rng() * 2 * math.pi  # Ângulo horizontal (0 a 360°)
        phi = math.acos(2 * rng() - 1)  # Ângulo vertical (distribuição uniforme na esfera)
        R = 40.0  # Raio da esfera de estrelas (bem longe da cena)
        # Converte coordenadas esféricas para cartesianas (x, y, z)
        glVertex3f(
            R * math.sin(phi) * math.cos(theta),
            R * math.cos(phi),
            R * math.sin(phi) * math.sin(theta),
        )
    glEnd()
    glPointSize(1.0)  # Restaura tamanho padrão dos pontos


def key_callback(window, key, _scancode, action, _mods):
    """Callback chamado pelo GLFW quando uma tecla é pressionada ou solta.
    window = janela, key = código da tecla, action = PRESS/RELEASE."""
    global cam_x, cam_y, cam_z, cam_yaw, cam_pitch, anim_speed

    if action == glfw.PRESS:  # Tecla acabou de ser pressionada
        keys_held.add(key)  # Adiciona ao conjunto de teclas mantidas
        if key == glfw.KEY_ESCAPE:
            glfw.set_window_should_close(window, True)  # ESC = fecha o programa
        elif key == glfw.KEY_R:
            # R = reseta câmera para posição e rotação inicial
            cam_x, cam_y, cam_z = 0.0, 3.0, 9.0
            cam_yaw, cam_pitch = 0.0, -18.0
        elif key in (glfw.KEY_EQUAL, glfw.KEY_KP_ADD):
            # + = acelera animação (máximo 8x)
            anim_speed = min(anim_speed * 1.5, 8.0)
        elif key in (glfw.KEY_MINUS, glfw.KEY_KP_SUBTRACT):
            # - = desacelera animação (mínimo 0.1x)
            anim_speed = max(anim_speed / 1.5, 0.1)
    elif action == glfw.RELEASE:  # Tecla foi solta
        keys_held.discard(key)  # Remove do conjunto de teclas mantidas


def process_keys():
    """Processa as teclas mantidas pressionadas para mover e rotacionar a câmera.
    Chamada a cada frame para permitir movimento contínuo enquanto a tecla está mantida."""
    global cam_x, cam_y, cam_z, cam_yaw, cam_pitch

    # Calcula os vetores de direção baseados na rotação atual da câmera (yaw)
    yr = math.radians(cam_yaw)  # Converte yaw de graus para radianos
    fx, fz = -math.sin(yr), -math.cos(yr)  # Vetor "para frente" da câmera (no plano XZ)
    rx, rz = math.cos(yr), -math.sin(yr)  # Vetor "para direita" da câmera (no plano XZ)

    # Movimento da câmera (WASD + Q/E)
    if glfw.KEY_W in keys_held:  # W = anda para frente
        cam_x += fx * MOVE_SPEED
        cam_z += fz * MOVE_SPEED
    if glfw.KEY_S in keys_held:  # S = anda para trás
        cam_x -= fx * MOVE_SPEED
        cam_z -= fz * MOVE_SPEED
    if glfw.KEY_A in keys_held:  # A = anda para esquerda
        cam_x -= rx * MOVE_SPEED
        cam_z -= rz * MOVE_SPEED
    if glfw.KEY_D in keys_held:  # D = anda para direita
        cam_x += rx * MOVE_SPEED
        cam_z += rz * MOVE_SPEED
    if glfw.KEY_Q in keys_held:  # Q = sobe
        cam_y += MOVE_SPEED
    if glfw.KEY_E in keys_held:  # E = desce
        cam_y -= MOVE_SPEED

    # Rotação da câmera (setas do teclado)
    if glfw.KEY_LEFT in keys_held:  # Seta esquerda = gira câmera para esquerda
        cam_yaw -= ROT_SPEED
    if glfw.KEY_RIGHT in keys_held:  # Seta direita = gira câmera para direita
        cam_yaw += ROT_SPEED
    if glfw.KEY_UP in keys_held:  # Seta cima = olha para cima (máximo 89°)
        cam_pitch = min(89.0, cam_pitch + ROT_SPEED)
    if glfw.KEY_DOWN in keys_held:  # Seta baixo = olha para baixo (mínimo -89°)
        cam_pitch = max(-89.0, cam_pitch - ROT_SPEED)


def look_target():
    """Calcula o ponto para onde a câmera está olhando, baseado na posição e rotação (yaw/pitch).
    Retorna as coordenadas (x, y, z) do ponto alvo."""
    yr = math.radians(cam_yaw)  # Rotação horizontal em radianos
    pr = math.radians(cam_pitch)  # Rotação vertical em radianos
    return (
        cam_x - math.sin(yr) * math.cos(pr),  # X do alvo
        cam_y + math.sin(pr),  # Y do alvo (sobe/desce com pitch)
        cam_z - math.cos(yr) * math.cos(pr),  # Z do alvo
    )


def main():
    """Função principal — inicializa a janela, configura OpenGL e executa o loop de renderização."""
    global anim_angle

    # ========================
    # Inicialização do GLFW e criação da janela
    # ========================
    if not glfw.init():
        sys.exit("Erro: falha ao inicializar GLFW")

    # Cria uma janela de 800x600 pixels
    window = glfw.create_window(800, 600, "Sistema Solar — OpenGL", None, None)
    if not window:
        glfw.terminate()
        sys.exit("Erro: falha ao criar janela")

    glfw.make_context_current(window)  # Ativa o contexto OpenGL nesta janela
    glfw.set_key_callback(window, key_callback)  # Registra o callback de teclado
    glfw.swap_interval(1)  # Ativa VSync (limita FPS à taxa de atualização do monitor)

    # ========================
    # Configuração inicial do OpenGL
    # ========================
    glEnable(GL_DEPTH_TEST)  # Habilita teste de profundidade (objetos atrás não cobrem os da frente)
    glEnable(GL_BLEND)  # Habilita transparência
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)  # Configura fórmula de transparência
    glClearColor(0.02, 0.02, 0.06, 1.0)  # Cor de fundo: azul muito escuro (quase preto)

    prev_t = glfw.get_time()  # Marca o tempo inicial para calcular delta time

    # ========================
    # Loop principal de renderização — roda até a janela ser fechada
    # ========================
    while not glfw.window_should_close(window):
        # Calcula delta time (tempo entre frames) para animação suave
        now = glfw.get_time()
        dt = min(now - prev_t, 0.05)  # Limita dt a 0.05s para evitar saltos em lag
        prev_t = now

        # Atualiza o ângulo de animação (controla todas as rotações e órbitas)
        anim_angle += dt * 50.0 * anim_speed
        # Processa teclas mantidas pressionadas (movimento da câmera)
        process_keys()

        # Atualiza o viewport para o tamanho atual da janela
        w, h = glfw.get_framebuffer_size(window)
        glViewport(0, 0, w, h)

        # Configura a matriz de projeção (perspectiva 3D)
        glMatrixMode(GL_PROJECTION)  # Seleciona a matriz de projeção
        glLoadIdentity()  # Reseta a matriz
        # Campo de visão 45°, proporção largura/altura, plano perto=0.1, plano longe=100
        gluPerspective(45.0, w / max(h, 1), 0.1, 100.0)

        # Configura a matriz de modelo/visão (posição da câmera)
        glMatrixMode(GL_MODELVIEW)  # Seleciona a matriz de modelo
        glLoadIdentity()  # Reseta a matriz
        tx, ty, tz = look_target()  # Calcula para onde a câmera olha
        # Posiciona a câmera: (posição) olhando para (alvo) com Y como "para cima"
        gluLookAt(cam_x, cam_y, cam_z, tx, ty, tz, 0.0, 1.0, 0.0)

        # Limpa a tela (cor e profundidade) para começar a desenhar o novo frame
        glClear(int(GL_COLOR_BUFFER_BIT) | int(GL_DEPTH_BUFFER_BIT))

        # ========================
        # Desenha as estrelas de fundo
        # ========================
        draw_stars()

        # ========================
        # Desenha o SOL (octaedro no centro)
        # ========================
        glPushMatrix()  # Salva a matriz atual (para não afetar outros objetos)
        glRotatef(15.0, 1, 0, 0)  # Inclina 15° no eixo X (eixo de rotação inclinado)
        glRotatef(anim_angle * 0.6, 0, 1, 0)  # Gira lentamente no eixo Y (rotação própria)
        draw_octahedron(0.8)  # Desenha o octaedro com raio 0.8
        glPopMatrix()  # Restaura a matriz (desfaz as rotações acima)

        # ========================
        # Desenha a órbita do planeta (anel ao redor do sol)
        # ========================
        draw_ring(3.0)  # Anel com raio 3.0 unidades

        # ========================
        # Calcula a posição do PLANETA na órbita
        # ========================
        # Converte o ângulo de animação para radianos (multiplicado por 0.35 para orbitar devagar)
        planet_rad = math.radians(anim_angle * 0.35)
        # Posição do planeta no plano XZ (órbita circular de raio 3.0)
        px = math.cos(planet_rad) * 3.0  # Coordenada X
        pz = math.sin(planet_rad) * 3.0  # Coordenada Z

        # ========================
        # Desenha o PLANETA e seus satélites
        # ========================
        glPushMatrix()  # Salva a matriz (tudo dentro será relativo à posição do planeta)
        glTranslatef(px, 0.0, pz)  # Move para a posição do planeta na órbita

        # Desenha a órbita da lua ao redor do planeta
        draw_ring(0.85)  # Anel com raio 0.85 unidades

        # ========================
        # Desenha a LUA (tetraedro orbitando o planeta)
        # ========================
        # Calcula a posição da lua na sua órbita ao redor do planeta
        moon_rad = math.radians(anim_angle * 1.8)  # Orbita mais rápido que o planeta
        mx = math.cos(moon_rad) * 0.85  # Coordenada X (relativa ao planeta)
        mz = math.sin(moon_rad) * 0.85  # Coordenada Z (relativa ao planeta)

        glPushMatrix()  # Salva a matriz para a lua
        glTranslatef(mx, 0.0, mz)  # Move para a posição da lua
        glRotatef(anim_angle * 2.5, 1, 1, 0)  # Rotação própria da lua (gira nos eixos X e Y)
        draw_tetrahedron(0.22)  # Desenha o tetraedro (lua) com tamanho 0.22
        glPopMatrix()  # Restaura a matriz (desfaz a posição da lua)

        # ========================
        # Desenha o PLANETA em si (cubo girando)
        # ========================
        glPushMatrix()  # Salva a matriz para o planeta
        glRotatef(anim_angle * 1.3, 0.1, 1, 0.2)  # Rotação própria do planeta (eixo inclinado)
        glScalef(0.55, 0.55, 0.55)  # Reduz o tamanho do cubo para 55%
        draw_cube(0.5)  # Desenha o cubo (planeta)
        glPopMatrix()  # Restaura a matriz (desfaz rotação/escala do planeta)

        glPopMatrix()  # Restaura a matriz original (desfaz a translação para posição do planeta)

        # ========================
        # Finaliza o frame
        # ========================
        glfw.swap_buffers(window)  # Troca os buffers (exibe o frame desenhado)
        glfw.poll_events()  # Processa eventos de teclado/mouse/janela

    # Limpa recursos do GLFW ao sair do loop
    glfw.terminate()


# Ponto de entrada do programa — executa main() quando o script é rodado diretamente
if __name__ == "__main__":
    main()
