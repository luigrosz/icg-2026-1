#!/usr/bin/env python3
"""
Aula 11 — Bounding Sphere Concêntrica + Direção Impacto AABB

Exercício 1: Duas esferas concêntricas.
    Esfera interna (R, colisão) + externa (1.5×R, aviso).
    Inimigo orbita player → zona externa = alerta amarelo, interna = colisão verm.

Exercício 2: Colisão AABB com resposta direcional.
    Cubo verde (WASD) colide com barreira fixa. Seta colorida mostra eixo de impacto.
"""

import sys, math, ctypes
import glfw
from OpenGL.GL import *
from OpenGL.GLU import *

# ── shader ──────────────────────────────────────────────────

def compile_shader(src, stype):
    s = glCreateShader(stype)
    glShaderSource(s, src)
    glCompileShader(s)
    if glGetShaderiv(s, GL_COMPILE_STATUS) != GL_TRUE:
        label = "VERTEX" if stype == GL_VERTEX_SHADER else "FRAGMENT"
        print(f"Erro shader {label}:\n{glGetShaderInfoLog(s).decode()}")
        return None
    return s

def load_program(vs_path, fs_path):
    with open(vs_path) as f: vs_src = f.read()
    with open(fs_path) as f: fs_src = f.read()
    vs = compile_shader(vs_src, GL_VERTEX_SHADER)
    fs = compile_shader(fs_src, GL_FRAGMENT_SHADER)
    if not vs or not fs: return None
    prog = glCreateProgram()
    glAttachShader(prog, vs); glAttachShader(prog, fs)
    glBindAttribLocation(prog, 0, "aPos")
    glBindAttribLocation(prog, 1, "aColor")
    glLinkProgram(prog)
    if glGetProgramiv(prog, GL_LINK_STATUS) != GL_TRUE:
        print(f"Erro link:\n{glGetProgramInfoLog(prog).decode()}")
        return None
    glDeleteShader(vs); glDeleteShader(fs)
    return prog

# ── geometria ───────────────────────────────────────────────

def make_cube(s, color):
    """36 verts. Layout: pos3 + col3 = 6 floats."""
    d = s
    v = [(-d,-d,-d),( d,-d,-d),( d, d,-d),(-d, d,-d),
         (-d,-d, d),( d,-d, d),( d, d, d),(-d, d, d)]
    faces = [(4,5,6,7),(1,0,3,2),(4,5,1,0),(7,6,2,3),(0,4,7,3),(1,5,6,2)]
    verts = []; r,g,b = color
    for i0,i1,i2,i3 in faces:
        for idx in (i0,i1,i2,i0,i2,i3):
            verts.extend(v[idx]); verts.extend((r,g,b))
    return verts, 36

def make_sphere_wire(cx, cy, cz, r, color, seg=20):
    """3 círculos (XY, XZ, YZ). 3*(seg+1) linhas = 6*(seg+1) verts."""
    data = []; rc,gc,bc = color
    for plane in range(3):
        for i in range(seg+1):
            a = 2*math.pi*i/seg
            if plane == 0:    # XY
                x=cx+r*math.cos(a); y=cy+r*math.sin(a); z=cz
            elif plane == 1:  # XZ
                x=cx+r*math.cos(a); y=cy; z=cz+r*math.sin(a)
            else:             # YZ
                x=cx; y=cy+r*math.cos(a); z=cz+r*math.sin(a)
            data.extend((x,y,z,rc,gc,bc))
    return data, 3*(seg+1)

def make_arrow(x1,y1,z1, x2,y2,z2, color):
    """Linha de 2 vértices. Layout: pos3+col3."""
    r,g,b = color
    return [x1,y1,z1,r,g,b, x2,y2,z2,r,g,b], 2

# ── VBO ─────────────────────────────────────────────────────

def make_vbo(data):
    arr = (ctypes.c_float*len(data))(*data)
    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, ctypes.sizeof(arr), arr, GL_DYNAMIC_DRAW)
    glBindBuffer(GL_ARRAY_BUFFER, 0)
    return vbo

def update_vbo(vbo, data):
    arr = (ctypes.c_float*len(data))(*data)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, ctypes.sizeof(arr), arr, GL_DYNAMIC_DRAW)
    glBindBuffer(GL_ARRAY_BUFFER, 0)

def draw_vbo(vbo, count, mode=GL_TRIANGLES):
    stride = 6*ctypes.sizeof(ctypes.c_float)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glVertexAttribPointer(0,3,GL_FLOAT,GL_FALSE,stride,ctypes.c_void_p(0))
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(1,3,GL_FLOAT,GL_FALSE,stride,ctypes.c_void_p(3*4))
    glEnableVertexAttribArray(1)
    glDrawArrays(mode, 0, count)
    glDisableVertexAttribArray(0)
    glDisableVertexAttribArray(1)
    glBindBuffer(GL_ARRAY_BUFFER, 0)

# ── colisão ─────────────────────────────────────────────────

def sphere_dist(p1, r1, p2, r2):
    """Retorna (distancia, colidiu?) para bounding spheres."""
    dx=p1[0]-p2[0]; dy=p1[1]-p2[1]; dz=p1[2]-p2[2]
    d = math.hypot(math.hypot(dx,dy),dz)
    return d, d < r1+r2

def aabb_overlap(min1, max1, min2, max2):
    return all(min1[i] <= max2[i] and max1[i] >= min2[i] for i in range(3))

def aabb_pushback(pos, half, b_min, b_max):
    """Retorna (pos_atualizada, eixo_str). Menor penetração define face."""
    p_min = (pos[0]-half, pos[1]-half, pos[2]-half)
    p_max = (pos[0]+half, pos[1]+half, pos[2]+half)
    ox = min(p_max[0],b_max[0]) - max(p_min[0],b_min[0])
    oy = min(p_max[1],b_max[1]) - max(p_min[1],b_min[1])
    oz = min(p_max[2],b_max[2]) - max(p_min[2],b_min[2])
    if ox <= oy and ox <= oz:
        if pos[0] < (b_min[0]+b_max[0])/2:
            pos[0] = b_min[0]-half; return pos, '+x'
        else:
            pos[0] = b_max[0]+half; return pos, '-x'
    elif oy <= oz:
        if pos[1] < (b_min[1]+b_max[1])/2:
            pos[1] = b_min[1]-half; return pos, '+y'
        else:
            pos[1] = b_max[1]+half; return pos, '-y'
    else:
        if pos[2] < (b_min[2]+b_max[2])/2:
            pos[2] = b_min[2]-half; return pos, '+z'
        else:
            pos[2] = b_max[2]+half; return pos, '-z'

# ── cena fixa ───────────────────────────────────────────────

def draw_ground():
    glUseProgram(0)
    glColor4f(0.2,0.2,0.25,1.0)
    glBegin(GL_LINES)
    for i in range(-6,7):
        glVertex3f(i,-0.5,-6); glVertex3f(i,-0.5,6)
        glVertex3f(-6,-0.5,i); glVertex3f(6,-0.5,i)
    glEnd()

def draw_hud_text(lines):
    """Desenha texto HUD 2D sobre a cena (linhas no viewport)."""
    glUseProgram(0)
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()
    glColor4f(1,1,1,0.85)
    for i, line in enumerate(lines):
        glRasterPos2f(-0.95, 0.92 - i*0.07)
        for ch in line:
            glBitmap(8,13,0,0,0,0, None)  # just render char
            # Use glutBitmapCharacter if available; skip for simplicity
    glEnable(GL_DEPTH_TEST)

# ── matrizes ────────────────────────────────────────────────

def identity():
    m=[0.0]*16; m[0]=m[5]=m[10]=m[15]=1.0; return m

def translate(m,x,y,z):
    out=m[:]
    out[12]=m[0]*x+m[4]*y+m[8]*z+m[12]
    out[13]=m[1]*x+m[5]*y+m[9]*z+m[13]
    out[14]=m[2]*x+m[6]*y+m[10]*z+m[14]
    out[15]=m[3]*x+m[7]*y+m[11]*z+m[15]
    return out

def look_at(ex,ey,ez,cx,cy,cz,ux,uy,uz):
    fl=math.hypot(math.hypot(cx-ex,cy-ey),cz-ez)
    if fl==0: return identity()
    fx,fy,fz=(cx-ex)/fl,(cy-ey)/fl,(cz-ez)/fl
    ul=math.hypot(math.hypot(ux,uy),uz); ux,uy,uz=ux/ul,uy/ul,uz/ul
    sx=fy*uz-fz*uy; sy=fz*ux-fx*uz; sz=fx*uy-fy*ux
    ux=sy*fz-sz*fy; uy=sz*fx-sx*fz; uz=sx*fy-sy*fx
    return [sx,ux,-fx,0, sy,uy,-fy,0, sz,uz,-fz,0,
            -sx*ex-sy*ey-sz*ez, -ux*ex-uy*ey-uz*ez, fx*ex+fy*ey+fz*ez, 1]

def perspective(fov,aspect,near,far):
    f=1.0/math.tan(math.radians(fov)/2); r=1.0/(near-far)
    return [f/aspect,0,0,0, 0,f,0,0, 0,0,(far+near)*r,-1,  0,0,2*far*near*r,0]

# ── MAIN ────────────────────────────────────────────────────

def main():
    if not glfw.init(): sys.exit("Falha GLFW")
    window=glfw.create_window(900,650,"Aula 11 — Bounding Sphere + Direção Impacto",None,None)
    if not window: glfw.terminate(); sys.exit("Falha janela")
    glfw.make_context_current(window); glfw.swap_interval(1)

    glClearColor(0.06,0.06,0.10,1.0)
    glEnable(GL_DEPTH_TEST); glDepthFunc(GL_LEQUAL)

    prog=load_program("aula11/vertex.vs","aula11/fragment.frag")
    if not prog: sys.exit("Falha shaders")
    loc_model=glGetUniformLocation(prog,"model")
    loc_view=glGetUniformLocation(prog,"view")
    loc_proj=glGetUniformLocation(prog,"projection")

    # ════════════════════════════════════════════════════════════
    # EXERCÍCIO 1: Bounding Sphere concêntrica
    # ════════════════════════════════════════════════════════════

    PLAYER_R = 0.7          # raio colisão real
    PLAYER_WARN_R = 1.05    # raio aviso = 1.5 × R

    player_pos = [-2.5, 0.0, 0.0]
    player_state = "neutro"
    # Player cubo
    pd, pn = make_cube(0.5, (0.2,0.5,1.0))
    pl_vbo = make_vbo(pd)
    # Esferas wireframe
    sw_inner_d, sw_inner_n = make_sphere_wire(0,0,0, PLAYER_R,    (0.2,0.9,0.3), 20)
    sw_outer_d, sw_outer_n = make_sphere_wire(0,0,0, PLAYER_WARN_R, (1.0,0.9,0.1), 20)
    inner_sw_vbo = make_vbo(sw_inner_d)
    outer_sw_vbo = make_vbo(sw_outer_d)

    # Inimigo orbita em torno do player
    enemy_pos = [0.0, 0.0, 0.0]
    enemy_angle = 0.0
    ENEMY_SPEED = 25.0
    ENEMY_ORBIT_R = 1.8
    ENEMY_R = 0.25
    ed, en = make_cube(ENEMY_R, (1.0,0.2,0.2))
    enemy_vbo = make_vbo(ed)

    # ════════════════════════════════════════════════════════════
    # EXERCÍCIO 2: AABB com direção de impacto
    # ════════════════════════════════════════════════════════════

    AABB_HALF = 0.4
    aabb_pos = [2.5, 0.0, 0.0]
    aabb_color_norm = (0.3, 0.9, 0.3)
    aabb_color_hit  = (1.0, 0.5, 0.0)
    aabb_colliding = False
    aabb_axis = None

    ad, an = make_cube(AABB_HALF, aabb_color_norm)
    aabb_vbo = make_vbo(ad)

    # Barreira fixa
    BH = 0.6
    bpos = [4.0, 0.0, 0.0]
    bd, bn = make_cube(BH, (0.65,0.15,0.1))
    bar_vbo = make_vbo(bd)
    b_min = (bpos[0]-BH, bpos[1]-BH, bpos[2]-BH)
    b_max = (bpos[0]+BH, bpos[1]+BH, bpos[2]+BH)

    # Seta de direção
    arrow_dummy, arrow_n = make_arrow(0,0,0,0,0,0,(0,0,0))
    arrow_vbo = make_vbo(arrow_dummy)

    # ════════════════════════════════════════════════════════════
    # Estado
    # ════════════════════════════════════════════════════════════

    held = set()
    cx,cy,cz = 0.0, 5.0, 7.0
    cyaw,cpitch = 0.0, -30.0
    last_t = glfw.get_time()

    def kcb(w,key,_,act,__):
        if act==glfw.PRESS:
            held.add(key)
            if key==glfw.KEY_ESCAPE: glfw.set_window_should_close(w,True)
            elif key==glfw.KEY_R:
                aabb_pos[0]=2.5; aabb_pos[1]=0.0; aabb_pos[2]=0.0
        elif act==glfw.RELEASE:
            held.discard(key)
    glfw.set_key_callback(window,kcb)

    while not glfw.window_should_close(window):
        now = glfw.get_time(); dt = min(now-last_t, 0.05); last_t = now

        # ── Orbe inimigo ──
        enemy_angle += dt * ENEMY_SPEED
        er = math.radians(enemy_angle)
        enemy_pos[0] = player_pos[0] + math.cos(er) * ENEMY_ORBIT_R
        enemy_pos[2] = player_pos[2] + math.sin(er) * ENEMY_ORBIT_R
        enemy_pos[1] = player_pos[1] + math.sin(er*1.3) * 0.5

        # ── Bounding Sphere test (Ex1) ──
        d_in, _   = sphere_dist(player_pos, PLAYER_R,      enemy_pos, ENEMY_R)
        d_out, _  = sphere_dist(player_pos, PLAYER_WARN_R, enemy_pos, ENEMY_R)

        if d_in < (PLAYER_R + ENEMY_R):
            player_state = "COLISAO"
        elif d_out < (PLAYER_WARN_R + ENEMY_R):
            player_state = "ALERTA"
        else:
            player_state = "NEUTRO"

        state_map = {
            "NEUTRO":  (0.2,0.5,1.0),
            "ALERTA":  (1.0,1.0,0.1),
            "COLISAO": (1.0,0.0,0.0),
        }
        pcol = state_map[player_state]
        pd, pn = make_cube(0.5, pcol)
        update_vbo(pl_vbo, pd)

        # ── Move AABB (Ex2) ──
        spd = 2.5 * dt
        if glfw.KEY_W in held: aabb_pos[2] -= spd
        if glfw.KEY_S in held: aabb_pos[2] += spd
        if glfw.KEY_A in held: aabb_pos[0] -= spd
        if glfw.KEY_D in held: aabb_pos[0] += spd
        if glfw.KEY_Q in held: aabb_pos[1] += spd
        if glfw.KEY_E in held: aabb_pos[1] -= spd

        # ── AABB collision (Ex2) ──
        ap_min = (aabb_pos[0]-AABB_HALF, aabb_pos[1]-AABB_HALF, aabb_pos[2]-AABB_HALF)
        ap_max = (aabb_pos[0]+AABB_HALF, aabb_pos[1]+AABB_HALF, aabb_pos[2]+AABB_HALF)

        if aabb_overlap(ap_min, ap_max, b_min, b_max):
            aabb_colliding = True
            aabb_pos, aabb_axis = aabb_pushback(aabb_pos, AABB_HALF, b_min, b_max)
        else:
            aabb_colliding = False
            aabb_axis = None

        # Atualiza cor AABB
        ac = aabb_color_hit if aabb_colliding else aabb_color_norm
        ad, an = make_cube(AABB_HALF, ac)
        update_vbo(aabb_vbo, ad)

        # Atualiza seta direção
        if aabb_colliding and aabb_axis:
            ax_vec = {'+x':(0.7,0,0), '-x':(-0.7,0,0), '+y':(0,0.7,0), '-y':(0,-0.7,0),
                      '+z':(0,0,0.7), '-z':(0,0,-0.7)}
            vec = ax_vec[aabb_axis]
            ax_color = (1,0,0) if 'x' in aabb_axis else (0,1,0) if 'y' in aabb_axis else (0,0.5,1)
            arr_d, arr_c = make_arrow(
                aabb_pos[0], aabb_pos[1], aabb_pos[2],
                aabb_pos[0]+vec[0], aabb_pos[1]+vec[1], aabb_pos[2]+vec[2],
                ax_color
            )
            update_vbo(arrow_vbo, arr_d)
            arrow_n = arr_c
        else:
            arr_d, arrow_n = make_arrow(0,0,0,0,0,0,(0,0,0))
            update_vbo(arrow_vbo, arr_d)
            arrow_n = 2

        # ── Câmera ──
        if glfw.KEY_LEFT in held: cyaw -= 1.5
        if glfw.KEY_RIGHT in held: cyaw += 1.5
        if glfw.KEY_UP in held: cpitch = min(89.0, cpitch+1.5)
        if glfw.KEY_DOWN in held: cpitch = max(-89.0, cpitch-1.5)

        w,h = glfw.get_framebuffer_size(window)
        glViewport(0,0,w,h)

        proj = perspective(45, w/max(h,1), 0.1, 50)
        tx = cx - math.sin(math.radians(cyaw))*math.cos(math.radians(cpitch))
        ty = cy + math.sin(math.radians(cpitch))
        tz = cz - math.cos(math.radians(cyaw))*math.cos(math.radians(cpitch))
        view_mat = look_at(cx,cy,cz, tx,ty,tz, 0,1,0)

        glClear(int(GL_COLOR_BUFFER_BIT)|int(GL_DEPTH_BUFFER_BIT))

        # ── Chão ──
        draw_ground()

        glUseProgram(prog)
        glUniformMatrix4fv(loc_proj,1,GL_FALSE,(ctypes.c_float*16)(*proj))
        glUniformMatrix4fv(loc_view,1,GL_FALSE,(ctypes.c_float*16)(*view_mat))

        # ════════════════════════════════════════════════════════
        # EXERCÍCIO 1 — Player + esferas concêntricas + inimigo
        # ════════════════════════════════════════════════════════

        m = translate(identity(), player_pos[0], player_pos[1], player_pos[2])
        glUniformMatrix4fv(loc_model,1,GL_FALSE,(ctypes.c_float*16)(*m))

        # Esfera externa (aviso) — amarelo
        draw_vbo(outer_sw_vbo, sw_outer_n, GL_LINES)
        # Esfera interna (colisão) — verde
        draw_vbo(inner_sw_vbo, sw_inner_n, GL_LINES)
        # Player
        draw_vbo(pl_vbo, pn)

        # Inimigo (orbita)
        m = translate(identity(), enemy_pos[0], enemy_pos[1], enemy_pos[2])
        glUniformMatrix4fv(loc_model,1,GL_FALSE,(ctypes.c_float*16)(*m))
        draw_vbo(enemy_vbo, en)

        # ════════════════════════════════════════════════════════
        # EXERCÍCIO 2 — AABB + barreira + seta impacto
        # ════════════════════════════════════════════════════════

        # Barreira
        m = translate(identity(), bpos[0], bpos[1], bpos[2])
        glUniformMatrix4fv(loc_model,1,GL_FALSE,(ctypes.c_float*16)(*m))
        draw_vbo(bar_vbo, bn)

        # AABB móvel
        m = translate(identity(), aabb_pos[0], aabb_pos[1], aabb_pos[2])
        glUniformMatrix4fv(loc_model,1,GL_FALSE,(ctypes.c_float*16)(*m))
        draw_vbo(aabb_vbo, an)

        # Seta de impacto
        if aabb_colliding:
            m = identity()
            glUniformMatrix4fv(loc_model,1,GL_FALSE,(ctypes.c_float*16)(*m))
            draw_vbo(arrow_vbo, arrow_n, GL_LINES)

        # ── HUD ──
        draw_hud_text([
            f"Ex1: Player estado = {player_state}",
            f"     Esfera interna R={PLAYER_R}, externa R={PLAYER_WARN_R} (1.5x)",
            f"Ex2: AABB colisao = {'SIM' if aabb_colliding else 'NAO'}  "
            f"direcao: {aabb_axis or '-'}  (seta colorida visivel)",
            f"    WASD move AABB verde. Seta = eixo impacto. R=reset.",
            f"Setas = camera. Q/E=sobe/desce.",
        ])

        glfw.swap_buffers(window); glfw.poll_events()

    glDeleteProgram(prog); glfw.terminate()

if __name__=="__main__": main()
