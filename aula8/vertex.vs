#version 120

attribute vec3 aPos;
attribute vec3 aNormal;
attribute vec3 aColor;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

varying vec3 FragPos;
varying vec3 Normal;
varying vec3 VertColor;

void main()
{
    vec4 worldPos = model * vec4(aPos, 1.0);
    FragPos = vec3(worldPos);
    // Normal matrix (assume uniform scale for simplicity)
    Normal = mat3(model) * aNormal;
    VertColor = aColor;
    gl_Position = projection * view * worldPos;
}
