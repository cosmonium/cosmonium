#version 140

// tex_0: reflection texture as produced by reflection camera
// tex_1: distortion texture
//
in vec4 texcoord0;
in vec4 texcoord1;

uniform sampler2D p3d_Texture0;
uniform sampler2D p3d_Texture1;
uniform vec4 waterdistort;

out vec4 color;

void main()
{
	// calculate distortion from distortion map
	vec4 distortion = normalize(texture(p3d_Texture1, texcoord1.xy / texcoord1.w) - waterdistort.x) * waterdistort.y;

	// projectively sample the 2D reflection texture
   	// o_color.rgb = tex2Dproj(p3d_Texture0, texcoord0).rgb;
   	vec4 coord = vec4(texcoord0.xy + distortion.xy, texcoord0.zw);
   	vec4 reflection  = texture(p3d_Texture0, coord.xy / coord.w);

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

