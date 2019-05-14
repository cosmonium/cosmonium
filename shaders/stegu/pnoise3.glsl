/*
    3D Perlin-Noise from example by Stefan Gustavson, found at
    http://staffwww.itn.liu.se/~stegu/simplexnoise/
*/
 
uniform sampler2D permTexture;          // Permutation texture
const float permTexUnit = 1.0/256.0;        // Perm texture texel-size
const float permTexUnitHalf = 0.5/256.0;    // Half perm texture texel-size
 
float fade(in float t) {
    return t*t*t*(t*(t*6.0-15.0)+10.0);
}
 
float pnoise3(in vec3 p)
{
    vec3 pi = permTexUnit*floor(p)+permTexUnitHalf; // Integer part, scaled so +1 moves permTexUnit texel
    // and offset 1/2 texel to sample texel centers
    vec3 pf = fract(p);     // Fractional part for interpolation
 
    // Noise contributions from (x=0, y=0), z=0 and z=1
    float perm00 = texture2D(permTexture, pi.xy).a ;
    vec3  grad000 = texture2D(permTexture, vec2(perm00, pi.z)).rgb * 4.0 - 1.0;
    float n000 = dot(grad000, pf);
    vec3  grad001 = texture2D(permTexture, vec2(perm00, pi.z + permTexUnit)).rgb * 4.0 - 1.0;
    float n001 = dot(grad001, pf - vec3(0.0, 0.0, 1.0));
 
    // Noise contributions from (x=0, y=1), z=0 and z=1
    float perm01 = texture2D(permTexture, pi.xy + vec2(0.0, permTexUnit)).a ;
    vec3  grad010 = texture2D(permTexture, vec2(perm01, pi.z)).rgb * 4.0 - 1.0;
    float n010 = dot(grad010, pf - vec3(0.0, 1.0, 0.0));
    vec3  grad011 = texture2D(permTexture, vec2(perm01, pi.z + permTexUnit)).rgb * 4.0 - 1.0;
    float n011 = dot(grad011, pf - vec3(0.0, 1.0, 1.0));
 
    // Noise contributions from (x=1, y=0), z=0 and z=1
    float perm10 = texture2D(permTexture, pi.xy + vec2(permTexUnit, 0.0)).a ;
    vec3  grad100 = texture2D(permTexture, vec2(perm10, pi.z)).rgb * 4.0 - 1.0;
    float n100 = dot(grad100, pf - vec3(1.0, 0.0, 0.0));
    vec3  grad101 = texture2D(permTexture, vec2(perm10, pi.z + permTexUnit)).rgb * 4.0 - 1.0;
    float n101 = dot(grad101, pf - vec3(1.0, 0.0, 1.0));
 
    // Noise contributions from (x=1, y=1), z=0 and z=1
    float perm11 = texture2D(permTexture, pi.xy + vec2(permTexUnit, permTexUnit)).a ;
    vec3  grad110 = texture2D(permTexture, vec2(perm11, pi.z)).rgb * 4.0 - 1.0;
    float n110 = dot(grad110, pf - vec3(1.0, 1.0, 0.0));
    vec3  grad111 = texture2D(permTexture, vec2(perm11, pi.z + permTexUnit)).rgb * 4.0 - 1.0;
    float n111 = dot(grad111, pf - vec3(1.0, 1.0, 1.0));
 
    // Blend contributions along x
    vec4 n_x = mix(vec4(n000, n001, n010, n011),
            vec4(n100, n101, n110, n111), fade(pf.x));
 
    // Blend contributions along y
    vec2 n_xy = mix(n_x.xy, n_x.zw, fade(pf.y));
 
    // Blend contributions along z
    float n_xyz = mix(n_xy.x, n_xy.y, fade(pf.z));
 
    // We're done, return the final noise value.
    return n_xyz;
}
