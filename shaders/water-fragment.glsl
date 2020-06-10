#version 140

#if __VERSION__ > 120
#define texture2D texture
#endif

// reflection_tex: reflection texture as produced by reflection camera
// distortion_tex: distortion texture
//
in vec4 texcoord0;
in vec4 texcoord1;

uniform sampler2D reflection_tex;
uniform sampler2D distortion_tex;
uniform vec4 waterdistort;

out vec4 color;

void main()
{
	// calculate distortion from distortion map
	vec4 distortion = normalize(texture2D(distortion_tex, texcoord1.xy / texcoord1.w) - waterdistort.x) * waterdistort.y;

	// projectively sample the 2D reflection texture
   	vec4 coord = vec4(texcoord0.xy + distortion.xy, texcoord0.zw);
	vec4 reflection  = texture2D(reflection_tex, coord.xy / coord.w);

	// refraction factor: smaller numbers make the water appear more reflective ("shinier")
    float factor = waterdistort.z;

	// refraction (1.0 = perfect mirror, 0.0 total refraction)
	float ref = waterdistort.w;
	vec4 refraction = vec4(0, 0, ref, 0.0f);

	// calculate fragment color
	color = mix( reflection, refraction, factor );

   	// optionally set alpha component to transparency,
   	// a constant value in this simple example
   	// o_color.a = 0.6;
}

