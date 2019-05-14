//
//	implementation of the blumblumshub hash
//	as described in MNoise paper http://www.cs.umbc.edu/~olano/papers/mNoise.pdf
//
//	http://briansharpe.wordpress.com/2011/10/01/gpu-texture-free-noise/
//
vec4 BBS_coord_prepare(vec4 x) { return x - floor(x * ( 1.0 / 61.0 )) * 61.0; }
vec3 BBS_coord_prepare(vec3 x) { return x - floor(x * ( 1.0 / 61.0 )) * 61.0; }
vec4 BBS_permute(vec4 x) { return fract( x * x * ( 1.0 / 61.0 )) * 61.0; }
vec4 BBS_permute_and_resolve(vec4 x) { return fract( x * x * ( 1.0 / 61.0 ) ); }
vec4 BBS_hash_2D( vec2 gridcell )	//	generates a random number for each of the 4 cell corners
{
    //    gridcell is assumed to be an integer coordinate
    vec4 hash_coord = BBS_coord_prepare( vec4( gridcell.xy, gridcell.xy + 1.0 ) );
    vec4 p = BBS_permute( hash_coord.xzxz /* * 7.0 */ ); // * 7.0 will increase variance close to origin
    return BBS_permute_and_resolve( p + hash_coord.yyww );
}
vec4 BBS_hash_hq_2D( vec2 gridcell )	//	generates a hq random number for each of the 4 cell corners
{
    //    gridcell is assumed to be an integer coordinate
    vec4 hash_coord = BBS_coord_prepare( vec4( gridcell.xy, gridcell.xy + 1.0 ) );
    vec4 p = BBS_permute( hash_coord.xzxz /* * 7.0 */ );  // * 7.0 will increase variance close to origin
    p = BBS_permute( p + hash_coord.yyww );
    return BBS_permute_and_resolve( p + hash_coord.xzxz );
}
void BBS_hash_3D( vec3 gridcell, out vec4 lowz_hash, out vec4 highz_hash )		//	generates a random number for each of the 8 cell corners
{
    //	gridcell is assumed to be an integer coordinate

    //	was having precision issues here with 61.0  60.0 fixes it.  need to test on other cards.
    const float DOMAIN = 60.0;
    gridcell.xyz = gridcell.xyz - floor(gridcell.xyz * ( 1.0 / DOMAIN )) * DOMAIN;
    vec3 gridcell_inc1 = step( gridcell, vec3( DOMAIN - 1.5 ) ) * ( gridcell + 1.0 );

    vec4 p = BBS_permute( vec2( gridcell.x, gridcell_inc1.x ).xyxy /* * 7.0 */ );  // * 7.0 will increase variance close to origin
    p = BBS_permute( p + vec2( gridcell.y, gridcell_inc1.y ).xxyy );
    lowz_hash = BBS_permute_and_resolve( p + gridcell.zzzz );
    highz_hash = BBS_permute_and_resolve( p + gridcell_inc1.zzzz );
}
