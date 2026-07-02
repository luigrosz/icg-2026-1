#version 120

varying vec3 FragPos;
varying vec3 Normal;
varying vec3 VertColor;

uniform vec3 lightPos;
uniform vec3 lightColor;
uniform vec3 viewPos;

// Exercício 1: Variável uniform de tempo para efeito de alerta
uniform float uTime;

// Exercício 2: Variável uniform para controle do expoente especular (shininess)
uniform float uShininess;

void main()
{
    // Componente ambiente
    float ambientStrength = 0.15;
    vec3 ambient = ambientStrength * lightColor;

    // Normaliza vetores para iluminação
    vec3 norm = normalize(Normal);
    vec3 lightDir = normalize(lightPos - FragPos);

    // Componente difusa
    float diff = max(dot(norm, lightDir), 0.0);

    // Exercício 1: Oscila a cor difusa entre intensidade original e vermelho máximo
    // usando sin() com o tempo uniforme enviado pelo Python
    float alertFactor = abs(sin(uTime * 2.0)); // oscila entre 0.0 e 1.0

    // Cor difusa original (intensidade total com cor da luz)
    vec3 diffuseOriginal = diff * lightColor;

    // Cor difusa vermelha máxima
    vec3 diffuseRed = diff * vec3(1.0, 0.0, 0.0);

    // Interpola entre original e vermelho usando o fator de alerta
    vec3 diffuse = mix(diffuseOriginal, diffuseRed, alertFactor);

    // Componente especular
    vec3 viewDir = normalize(viewPos - FragPos);
    vec3 reflectDir = reflect(-lightDir, norm);

    // Exercício 2: Usa uShininess (expoente de reflexão especular)
    // Valores baixos (~1) = material fosco, valores altos (~128) = metal polido
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), uShininess);
    float specularStrength = 0.5;
    vec3 specular = specularStrength * spec * lightColor;

    // Resultado final = (ambiente + difusa + especular) * cor do vértice
    vec3 result = (ambient + diffuse + specular) * VertColor;
    gl_FragColor = vec4(result, 1.0);
}
