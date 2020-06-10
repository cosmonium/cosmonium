
#version 140

in vec2 p3d_MultiTexCoord0;
in vec4 p3d_Vertex;
in vec4 p3d_Normal;

uniform vec4 wateranim;
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelMatrix;
uniform float osg_FrameTime;

// texcoord0: projective mapping for the reflection texture
// texcoord1: texture coords into the distortion map, scaled and animated
//
out vec4 texcoord0;
out vec4 texcoord1;

void main()
{
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;

	// projective matrix (MR)
    mat4 scaleMatrix = mat4(vec4(0.5f, 0.0f, 0.0f, 0.0f),
                            vec4(0.0f, 0.5f, 0.0f, 0.0f),
                            vec4(0.0f, 0.0f, 0.5f, 0.0f),
                            vec4(0.5f, 0.5f, 0.5f, 1.0f));
   	mat4 matMR = scaleMatrix * p3d_ModelViewProjectionMatrix;

	// transform the vertex position by the projective
   	// texture matrix and copy the result into homogeneous
   	// texture coordinate set 0
   	texcoord0 = matMR * p3d_Vertex;

	// water distortion map
    // animate and scale distortions
	texcoord1.xy = p3d_MultiTexCoord0.xy * wateranim.z + wateranim.xy * osg_FrameTime;
}
