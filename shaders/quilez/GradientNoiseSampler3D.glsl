// 3D Perlin noise
float   Noise(vec3 p)
{
    const float one = 1.0 / 256.0;

    // Find unit cube that contains point
    // Find relative x,y,z of point in cube
    vec3 P = mod(floor(p), 256.0) * one;
    p -= floor(p);

    // Compute fade curves for each of x,y,z
    vec3 ff = p * p * p * (p * (p * 6.0 - 15.0) + 10.0);

    // Hash coordinates of the 8 cube corners
    vec4 AA = texture(PermSampler, P.xy) + P.z;

    float a = dot(texture(PermGradSampler, AA.x      ).rgb,  p);
    float b = dot(texture(PermGradSampler, AA.z      ).rgb,  p + vec3(-1,  0,  0));
    float c = dot(texture(PermGradSampler, AA.y      ).rgb,  p + vec3( 0, -1,  0));
    float d = dot(texture(PermGradSampler, AA.w      ).rgb,  p + vec3(-1, -1,  0));
    float e = dot(texture(PermGradSampler, AA.x + one).rgb,  p + vec3( 0,  0, -1));
    float f = dot(texture(PermGradSampler, AA.z + one).rgb,  p + vec3(-1,  0, -1));
    float g = dot(texture(PermGradSampler, AA.y + one).rgb,  p + vec3( 0, -1, -1));
    float h = dot(texture(PermGradSampler, AA.w + one).rgb,  p + vec3(-1, -1, -1));

    float k0 =   a;
    float k1 =   b - a;
    float k2 =   c - a;
    float k3 =   e - a;
    float k4 =   a - b - c + d;
    float k5 =   a - c - e + g;
    float k6 =   a - b - e + f;
    float k7 = - a + b + c - d + e - f - g + h;

    return k0 + k1*ff.x + k2*ff.y + k3*ff.z + k4*ff.x*ff.y + k5*ff.y*ff.z + k6*ff.z*ff.x + k7*ff.x*ff.y*ff.z;
}
