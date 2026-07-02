#!/usr/bin/env python3
"""
Aula 10 — Colisão AABB e Modo de Depuração

Exercício 1: Detecção de colisão AABB.
    Player colide com barreira → cor vermelha + recuo (pushback).
    glUniformMatrix4fv atualiza posição de recuo.

Exercício 2: Tecla 'B' ativa modo depuração.
    Desenha AABB wireframe (verde player, amarelo barreiras) sobre objetos.
"""

import sys, math, ctypes
import glfw
from OpenGL.GL import *
from OpenGL.GLU import *

# ── shader helpers ──────────────────────────────────────────

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

# ── AABB helpers ────────────────────────────────────────────

def aabb_overlap(min1, max1, min2, max2):
    return all(min1[i] <= max2[i] and max1[i] >= min2[i] for i in range(3))

def aabb_pushback(pos, half, b_min, b_max):
    """Empurra pos para fora da AABB da barreira pela menor penetração."""
    p_min = (pos[0]-half, pos[1]-half, pos[2]-half)
    p_max = (pos[0]+half, pos[1]+half, pos[2]+half)
    ox = min(p_max[0], b_max[0]) - max(p_min[0], b_min[0])
    oy = min(p_max[1], b_max[1]) - max(p_min[1], b_min[1])
    oz = min(p_max[2], b_max[2]) - max(p_min[2], b_min[2])
    if ox <= oy and ox <= oz:
        if pos[0] < b_min[0]: pos[0] = b_min[0] - half
        else:                 pos[0] = b_max[0] + half
    elif oy <= oz:
        if pos[1] < b_min[1]: pos[1] = b_min[1] - half
        else:                 pos[1] = b_max[1] + half
    else:
        if pos[2] < b_min[2]: pos[2] = b_min[2] - half
        else:                 pos[2] = b_max[2] + half
    return pos

# ── vertex data ─────────────────────────────────────────────

def make_cube(s, color):
    """36 verts: 6 faces x 2 tris. Layout: pos3 col3."""
    d = s
    v = [(-d,-d,-d),( d,-d,-d),( d, d,-d),(-d, d,-d),
         (-d,-d, d),( d,-d, d),( d, d, d),(-d, d, d)]
    faces = [
        (4,5,6,7), (1,0,3,2), (4,5,1,0),
        (7,6,2,3), (0,4,7,3), (1,5,6,2),
    ]
    verts = []
    r,g,b = color
    for i0,i1,i2,i3 in faces:
        for idx in (i0,i1,i2,i0,i2,i3):
            verts.extend(v[idx]); verts.extend((r,g,b))
    return verts, 36

def make_aabb_lines(min_xyz, max_xyz, color):
    """24 verts: 12 linhas. Layout: pos3 col3."""
    x1,y1,z1 = min_xyz
    x2,y2,z2 = max_xyz
    pts = [
        (x1,y1,z1),(x2,y1,z1),(x2,y2,z1),(x1,y2,z1),
        (x1,y1,z2),(x2,y1,z2),(x2,y2,z2),(x1,y2,z2),
    ]
    lines = [
        0,1, 1,2, 2,3, 3,0,
        4,5, 5,6, 6,7, 7,4,
        0,4, 1,5, 2,6, 3,7,
    ]
    data = []
    r,g,b = color
    for idx in lines:
        data.extend(pts[idx]); data.extend((r,g,b))
    return data, 24

# ── VBO helpers ────────────────────────────────────────────

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
    stride = 6 * ctypes.sizeof(ctypes.c_float)  # pos3 + col3
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glVertexAttribPointer(0,3,GL_FLOAT,GL_FALSE,stride,ctypes.c_void_p(0));       glEnableVertexAttribArray(0)
    glVertexAttribPointer(1,3,GL_FLOAT,GL_FALSE,stride,ctypes.c_void_p(3*4));      glEnableVertexAttribArray(1)
    glDrawArrays(mode, 0, count)
    glDisableVertexAttribArray(0); glDisableVertexAttribArray(1)
    glBindBuffer(GL_ARRAY_BUFFER, 0)

def draw_aabb_lines_vbo(vbo, min_xyz, max_xyz, color):
    """Atualiza VBO com linhas da AABB e desenha."""
    data, cnt = make_aabb_lines(min_xyz, max_xyz, color)
    update_vbo(vbo, data)
    draw_vbo(vbo, cnt, GL_LINES)

# ── scene elements ─────────────────────────────────────────

def draw_ground():
    glUseProgram(0)
    glColor4f(0.25, 0.25, 0.3, 1.0)
    glBegin(GL_LINES)
    for i in range(-5, 6):
        glVertex3f(i, -0.5, -5); glVertex3f(i, -0.5, 5)
        glVertex3f(-5, -0.5, i); glVertex3f(5, -0.5, i)
    glEnd()

# ── matrix helpers ─────────────────────────────────────────

def identity():
    m=[0.0]*16; m[0]=m[5]=m[10]=m[15]=1.0; return m

def translate(m,x,y,z):
    out=m[:]; out[12]=m[0]*x+m[4]*y+m[8]*z+m[12]
    out[13]=m[1]*x+m[5]*y+m[9]*z+m[13]
    out[14]=m[2]*x+m[6]*y+m[10]*z+m[14]
    out[15]=m[3]*x+m[7]*y+m[11]*z+m[15]
    return out

def rotate_y(m,deg):
    rad=math.radians(deg); c=math.cos(rad); s=math.sin(rad); out=m[:]
    out[0]=m[0]*c+m[8]*s;  out[1]=m[1]*c+m[9]*s
    out[2]=m[2]*c+m[10]*s; out[3]=m[3]*c+m[11]*s
    out[8]=-m[0]*s+m[8]*c; out[9]=-m[1]*s+m[9]*c
    out[10]=-m[2]*s+m[10]*c; out[11]=-m[3]*s+m[11]*c
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

# ── main ───────────────────────────────────────────────────

def main():
    if not glfw.init(): sys.exit("Falha GLFW")
    window=glfw.create_window(800,600,"Aula 10 — Colisão AABB + Debug",None,None)
    if not window: glfw.terminate(); sys.exit("Falha janela")
    glfw.make_context_current(window); glfw.swap_interval(1)

    glClearColor(0.08,0.08,0.12,1.0)
    glEnable(GL_DEPTH_TEST); glDepthFunc(GL_LEQUAL)

    prog=load_program("aula10/vertex.vs","aula10/fragment.frag")
    if not prog: sys.exit("Falha shaders")

    loc_model = glGetUniformLocation(prog,"model")
    loc_view  = glGetUniformLocation(prog,"view")
    loc_proj  = glGetUniformLocation(prog,"projection")

    # ── cria VBO para wireframe AABB (reutilizado a cada frame) ──
    wdummy, _ = make_aabb_lines((0,0,0),(1,1,1),(1,0,0))
    vbo_wire = make_vbo(wdummy)

    # ── objetos da cena ──
    HALF = 0.4
    player_pos = [0.0, 0.0, 0.0]
    player_speed = 2.0
    player_color = (0.3, 0.6, 1.0)
    player_colliding = False
    pd, pn = make_cube(HALF, player_color)
    player_vbo = make_vbo(pd)

    # barreiras: (pos_x, pos_y, pos_z, half_size, cor)
    barriers = [
        (2.0,  0.0, 0.0,  0.5, (0.9,0.3,0.2)),
        (-1.5, 0.0, 1.8,  0.5, (0.9,0.5,0.1)),
        (0.0,  0.0, -2.0, 0.5, (0.2,0.7,0.3)),
    ]
    barrier_vbos = []
    for bx,by,bz,bs,bcol in barriers:
        d, n = make_cube(bs, bcol)
        barrier_vbos.append((make_vbo(d), n))

    # ── estado ──
    debug_mode = False
    held = set()
    cx,cy,cz = 0.0, 5.0, 6.0
    cyaw, cpitch = 0.0, -35.0
    last_time = glfw.get_time()

    def kcb(w,key,_,act,__):
        nonlocal debug_mode
        if act==glfw.PRESS:
            held.add(key)
            if key==glfw.KEY_ESCAPE: glfw.set_window_should_close(w,True)
            elif key==glfw.KEY_B:     # Exercicio 2
                debug_mode = not debug_mode
                print(f"Debug: {'ON' if debug_mode else 'OFF'}")
            elif key==glfw.KEY_R:
                player_pos[0]=player_pos[1]=player_pos[2]=0.0
        elif act==glfw.RELEASE:
            held.discard(key)
    glfw.set_key_callback(window,kcb)

    while not glfw.window_should_close(window):
        now = glfw.get_time(); dt = min(now-last_time, 0.05); last_time = now

        # ── movimento player ──
        yr = math.radians(cyaw)
        fx, fz = -math.sin(yr), -math.cos(yr)
        rx, rz = math.cos(yr), -math.sin(yr)
        spd = player_speed * dt
        if glfw.KEY_W in held: player_pos[0] += fx*spd; player_pos[2] += fz*spd
        if glfw.KEY_S in held: player_pos[0] -= fx*spd; player_pos[2] -= fz*spd
        if glfw.KEY_A in held: player_pos[0] -= rx*spd; player_pos[2] -= rz*spd
        if glfw.KEY_D in held: player_pos[0] += rx*spd; player_pos[2] += rz*spd
        if glfw.KEY_Q in held: player_pos[1] += spd
        if glfw.KEY_E in held: player_pos[1] -= spd

        # ── colisão AABB (Exercicio 1) ──
        p_min = (player_pos[0]-HALF, player_pos[1]-HALF, player_pos[2]-HALF)
        p_max = (player_pos[0]+HALF, player_pos[1]+HALF, player_pos[2]+HALF)
        player_colliding = False
        for bx,by,bz,bs,_ in barriers:
            b_min = (bx-bs, by-bs, bz-bs)
            b_max = (bx+bs, by+bs, bz+bs)
            if aabb_overlap(p_min, p_max, b_min, b_max):
                player_colliding = True
                aabb_pushback(player_pos, HALF, b_min, b_max)
                p_min = (player_pos[0]-HALF, player_pos[1]-HALF, player_pos[2]-HALF)
                p_max = (player_pos[0]+HALF, player_pos[1]+HALF, player_pos[2]+HALF)

        # ── atualiza cor do player (vermelho se colidindo) ──
        new_color = (1.0,0.0,0.0) if player_colliding else (0.3,0.6,1.0)
        pd, pn = make_cube(HALF, new_color)
        update_vbo(player_vbo, pd)

        # ── câmera ──
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

        # ── chão ──
        draw_ground()

        # ── objetos com shader ──
        glUseProgram(prog)
        glUniformMatrix4fv(loc_proj,1,GL_FALSE,(ctypes.c_float*16)(*proj))
        glUniformMatrix4fv(loc_view,1,GL_FALSE,(ctypes.c_float*16)(*view_mat))

        # Player
        m = translate(identity(), player_pos[0], player_pos[1], player_pos[2])
        glUniformMatrix4fv(loc_model,1,GL_FALSE,(ctypes.c_float*16)(*m))
        draw_vbo(player_vbo, pn)

        # Barreiras
        for idx, (bx,by,bz,_,_) in enumerate(barriers):
            m = translate(identity(), bx, by, bz)
            glUniformMatrix4fv(loc_model,1,GL_FALSE,(ctypes.c_float*16)(*m))
            draw_vbo(barrier_vbos[idx][0], barrier_vbos[idx][1])

        # ── Debug AABB wireframe (Exercicio 2: tecla B) ──
        if debug_mode:
            # Player AABB (verde)
            p_min = (player_pos[0]-HALF, player_pos[1]-HALF, player_pos[2]-HALF)
            p_max = (player_pos[0]+HALF, player_pos[1]+HALF, player_pos[2]+HALF)
            m = identity()
            glUniformMatrix4fv(loc_model,1,GL_FALSE,(ctypes.c_float*16)(*m))
            draw_aabb_lines_vbo(vbo_wire, p_min, p_max, (0.0,1.0,0.0))

            # Barreiras AABB (amarelo)
            for bx,by,bz,bs,_ in barriers:
                b_min = (bx-bs, by-bs, bz-bs)
                b_max = (bx+bs, by+bs, bz+bs)
                draw_aabb_lines_vbo(vbo_wire, b_min, b_max, (1.0,1.0,0.0))

        glfw.swap_buffers(window); glfw.poll_events()

    glDeleteProgram(prog); glfw.terminate()

if __name__=="__main__": main()
