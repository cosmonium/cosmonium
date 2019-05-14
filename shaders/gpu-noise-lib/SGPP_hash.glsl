//
//	Permutation polynomial idea is from Stefan Gustavson's and Ian McEwan's work at...
//	http://github.com/ashima/webgl-noise
//	http://www.itn.liu.se/~stegu/GLSL-cellular
//
//	http://briansharpe.wordpress.com/2011/10/01/gpu-texture-free-noise/
//
vec4 SGPP_coord_prepare(vec4 x) { return x - floor(x * ( 1.0 / 289.0 )) * 289.0; }
vec3 SGPP_coord_prepare(vec3 x) { return x - floor(x * ( 1.0 / 289.0 )) * 289.0; }
vec4 SGPP_permute(vec4 x) { return fract( x * ( ( 34.0 / 289.0 ) * x + ( 1.0 / 289.0 ) ) ) * 289.0; }
vec4 SGPP_resolve(vec4 x) { return fract( x * ( 7.0 / 288.0 ) ); }
vec4 SGPP_hash_2D( vec2 gridcell )		//	generates a random number for each of the 4 cell corners
{
    //    gridcell is assumed to be an integer coordinate
    vec4 hash_coord = SGPP_coord_prepare( vec4( gridcell.xy, gridcell.xy + 1.0 ) );
    return SGPP_resolve( SGPP_permute( SGPP_permute( hash_coord.xzxz ) + hash_coord.yyww ) );
}
void SGPP_hash_2D( vec2 gridcell, out vec4 hash_0, out vec4 hash_1 )	//	generates 2 random numbers for each of the 4 cell corners
{
    //    gridcell is assumed to be an integer coordinate
    vec4 hash_coord = SGPP_coord_prepare( vec4( gridcell.xy, gridcell.xy + 1.0 ) );
    hash_0 = SGPP_permute( SGPP_permute( hash_coord.xzxz ) + hash_coord.yyww );
    hash_1 = SGPP_resolve( SGPP_permute( hash_0 ) );
    hash_0 = SGPP_resolve( hash_0 );
}
void SGPP_hash_3D( vec3 gridcell, out vec4 lowz_hash, out vec4 highz_hash )		//	generates a random number for each of the 8 cell corners
{
    //    gridcell is assumed to be an integer coordinate
    gridcell = SGPP_coord_prepare( gridcell );
    vec3 gridcell_inc1 = step( gridcell, vec3( 287.5 ) ) * ( gridcell + 1.0 );
    highz_hash = SGPP_permute( SGPP_permute( vec2( gridcell.x, gridcell_inc1.x ).xyxy ) + vec2( gridcell.y, gridcell_inc1.y ).xxyy );
    lowz_hash = SGPP_resolve( SGPP_permute( highz_hash + gridcell.zzzz ) );
    highz_hash = SGPP_resolve( SGPP_permute( highz_hash + gridcell_inc1.zzzz ) );
}
void SGPP_hash_3D( 	vec3 gridcell,
                    vec3 v1_mask,		//	user definable v1 and v2.  ( 0's and 1's )
                    vec3 v2_mask,
                    out vec4 hash_0,
                    out vec4 hash_1,
                    out vec4 hash_2	)		//	generates 3 random numbers for each of the 4 3D cell corners.  cell corners:  v0=0,0,0  v3=1,1,1  the other two are user definable
{
    vec3 coords0 = gridcell.xyz - floor(gridcell.xyz * ( 1.0 / 289.0 )) * 289.0;
    vec3 coords3 = step( coords0, vec3( 287.5 ) ) * ( coords0 + 1.0 );
    vec3 coords1 = mix( coords0, coords3, v1_mask );
    vec3 coords2 = mix( coords0, coords3, v2_mask );
    hash_2 = SGPP_permute( SGPP_permute( SGPP_permute( vec4( coords0.x, coords1.x, coords2.x, coords3.x ) ) + vec4( coords0.y, coords1.y, coords2.y, coords3.y ) ) + vec4( coords0.z, coords1.z, coords2.z, coords3.z ) );
    hash_0 = SGPP_resolve( hash_2  );
    hash_1 = SGPP_resolve( hash_2 = SGPP_permute( hash_2 ) );
    hash_2 = SGPP_resolve( SGPP_permute( hash_2 ) );
}
void SGPP_hash_3D( 	vec3 gridcell,
                    out vec4 lowz_hash_0,
                    out vec4 lowz_hash_1,
                    out vec4 lowz_hash_2,
                    out vec4 highz_hash_0,
                    out vec4 highz_hash_1,
                    out vec4 highz_hash_2	)	//	generates 3 random numbers for each of the 8 cell corners
{
    //    gridcell is assumed to be an integer coordinate
    gridcell = SGPP_coord_prepare( gridcell );
    vec3 gridcell_inc1 = step( gridcell, vec3( 287.5 ) ) * ( gridcell + 1.0 );
    highz_hash_2 = SGPP_permute( SGPP_permute( vec2( gridcell.x, gridcell_inc1.x ).xyxy ) + vec2( gridcell.y, gridcell_inc1.y ).xxyy );
    lowz_hash_0 = SGPP_resolve( lowz_hash_2 = SGPP_permute( highz_hash_2 + gridcell.zzzz ) );
    highz_hash_0 = SGPP_resolve( highz_hash_2 = SGPP_permute( highz_hash_2 + gridcell_inc1.zzzz ) );
    lowz_hash_1 = SGPP_resolve( lowz_hash_2 = SGPP_permute( lowz_hash_2 ) );
    highz_hash_1 = SGPP_resolve( highz_hash_2 = SGPP_permute( highz_hash_2 ) );
    lowz_hash_2 = SGPP_resolve( SGPP_permute( lowz_hash_2 ) );
    highz_hash_2 = SGPP_resolve( SGPP_permute( highz_hash_2 ) );
}
