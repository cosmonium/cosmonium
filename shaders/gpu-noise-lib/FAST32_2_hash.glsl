//
//	FastHash32_2
//
//	An alternative to FastHash32
//	- slightly slower
//	- can have a larger domain
//	- allows for a 4D implementation
//
//	(eg)4D is computed like so....
//	coord = mod( coord, DOMAIN );
//	coord = ( coord * SCALE ) + OFFSET;
//	coord *= coord;
//	hash = mod( coord.x * coord.y * coord.z * coord.w, SOMELARGEFLOAT ) / SOMELARGEFLOAT;
//
vec4 FAST32_2_hash_2D( vec2 gridcell )	//	generates a random number for each of the 4 cell corners
{
    //	gridcell is assumed to be an integer coordinate
    const vec2 OFFSET = vec2( 403.839172, 377.242706 );
    const float DOMAIN = 69.0;		//	NOTE:  this can most likely be extended with some tweaking of the other parameters
    const float SOMELARGEFLOAT = 32745.708984;
    const vec2 SCALE = vec2( 2.009842, 1.372549 );

    vec4 P = vec4( gridcell.xy, gridcell.xy + 1.0 );
    P = P - floor(P * ( 1.0 / DOMAIN )) * DOMAIN;
    P = ( P * SCALE.xyxy ) + OFFSET.xyxy;
    P *= P;
    return fract( P.xzxz * P.yyww * ( 1.0 / SOMELARGEFLOAT ) );
}
void FAST32_2_hash_3D( 	vec3 gridcell,
                        out vec4 z0_hash,			//  vec4 == ( x0y0, x1y0, x0y1, x1y1 )
                        out vec4 z1_hash	)		//	generates a random number for each of the 8 cell corners
{
    //	gridcell is assumed to be an integer coordinate
    const vec3 OFFSET = vec3( 55.882355, 63.167774, 52.941177 );
    const float DOMAIN = 69.0;		//	NOTE:  this can most likely be extended with some tweaking of the other parameters
    const float SOMELARGEFLOAT = 69412.070313;
    const vec3 SCALE = vec3( 0.235142, 0.205890, 0.216449 );

    //	truncate the domain
    gridcell = gridcell - floor(gridcell * ( 1.0 / DOMAIN )) * DOMAIN;
    vec3 gridcell_inc1 = step( gridcell, vec3( DOMAIN - 1.5 ) ) * ( gridcell + 1.0 );

    //	calculate the noise
    gridcell = ( gridcell * SCALE ) + OFFSET;
    gridcell_inc1 = ( gridcell_inc1 * SCALE ) + OFFSET;
    gridcell *= gridcell;
    gridcell_inc1 *= gridcell_inc1;

    vec4 x0y0_x1y0_x0y1_x1y1 = vec4( gridcell.x, gridcell_inc1.x, gridcell.x, gridcell_inc1.x ) * vec4( gridcell.yy, gridcell_inc1.yy );

    z0_hash = fract( x0y0_x1y0_x0y1_x1y1 * gridcell.zzzz * ( 1.0 / SOMELARGEFLOAT ) );
    z1_hash = fract( x0y0_x1y0_x0y1_x1y1 * gridcell_inc1.zzzz * ( 1.0 / SOMELARGEFLOAT ) );
}
void FAST32_2_hash_4D( 	vec4 gridcell,
                        out vec4 z0w0_hash,		//  vec4 == ( x0y0, x1y0, x0y1, x1y1 )
                        out vec4 z1w0_hash,
                        out vec4 z0w1_hash,
                        out vec4 z1w1_hash	)
{
    //    gridcell is assumed to be an integer coordinate

    //	TODO: 	these constants need tweaked to find the best possible noise.
    //			probably requires some kind of brute force computational searching or something....
    const vec4 OFFSET = vec4( 16.841230, 18.774548, 16.873274, 13.664607 );
    const float DOMAIN = 69.0;
    const float SOMELARGEFLOAT = 47165.636719;
    const vec4 SCALE = vec4( 0.102007, 0.114473, 0.139651, 0.084550 );

    //	truncate the domain
    gridcell = gridcell - floor(gridcell * ( 1.0 / DOMAIN )) * DOMAIN;
    vec4 gridcell_inc1 = step( gridcell, vec4( DOMAIN - 1.5 ) ) * ( gridcell + 1.0 );

    //	calculate the noise
    gridcell = ( gridcell * SCALE ) + OFFSET;
    gridcell_inc1 = ( gridcell_inc1 * SCALE ) + OFFSET;
    gridcell *= gridcell;
    gridcell_inc1 *= gridcell_inc1;

    vec4 x0y0_x1y0_x0y1_x1y1 = vec4( gridcell.x, gridcell_inc1.x, gridcell.x, gridcell_inc1.x ) * vec4( gridcell.yy, gridcell_inc1.yy );
    vec4 z0w0_z1w0_z0w1_z1w1 = vec4( gridcell.z, gridcell_inc1.z, gridcell.z, gridcell_inc1.z ) * vec4( gridcell.ww, gridcell_inc1.ww ) * ( 1.0 / SOMELARGEFLOAT );

    z0w0_hash = fract( x0y0_x1y0_x0y1_x1y1 * z0w0_z1w0_z0w1_z1w1.xxxx );
    z1w0_hash = fract( x0y0_x1y0_x0y1_x1y1 * z0w0_z1w0_z0w1_z1w1.yyyy );
    z0w1_hash = fract( x0y0_x1y0_x0y1_x1y1 * z0w0_z1w0_z0w1_z1w1.zzzz );
    z1w1_hash = fract( x0y0_x1y0_x0y1_x1y1 * z0w0_z1w0_z0w1_z1w1.wwww );
}
void FAST32_2_hash_4D( 	vec4 gridcell,
                        out vec4 z0w0_hash_0,		//  vec4 == ( x0y0, x1y0, x0y1, x1y1 )
                        out vec4 z0w0_hash_1,
                        out vec4 z0w0_hash_2,
                        out vec4 z0w0_hash_3,
                        out vec4 z1w0_hash_0,
                        out vec4 z1w0_hash_1,
                        out vec4 z1w0_hash_2,
                        out vec4 z1w0_hash_3,
                        out vec4 z0w1_hash_0,
                        out vec4 z0w1_hash_1,
                        out vec4 z0w1_hash_2,
                        out vec4 z0w1_hash_3,
                        out vec4 z1w1_hash_0,
                        out vec4 z1w1_hash_1,
                        out vec4 z1w1_hash_2,
                        out vec4 z1w1_hash_3	)
{
    //    gridcell is assumed to be an integer coordinate

    //	TODO: 	these constants need tweaked to find the best possible noise.
    //			probably requires some kind of brute force computational searching or something....
    const vec4 OFFSET = vec4( 16.841230, 18.774548, 16.873274, 13.664607 );
    const float DOMAIN = 69.0;
    const vec4 SOMELARGEFLOATS = vec4( 56974.746094, 47165.636719, 55049.667969, 49901.273438 );
    const vec4 SCALE = vec4( 0.102007, 0.114473, 0.139651, 0.084550 );

    //	truncate the domain
    gridcell = gridcell - floor(gridcell * ( 1.0 / DOMAIN )) * DOMAIN;
    vec4 gridcell_inc1 = step( gridcell, vec4( DOMAIN - 1.5 ) ) * ( gridcell + 1.0 );

    //	calculate the noise
    gridcell = ( gridcell * SCALE ) + OFFSET;
    gridcell_inc1 = ( gridcell_inc1 * SCALE ) + OFFSET;
    gridcell *= gridcell;
    gridcell_inc1 *= gridcell_inc1;

    vec4 x0y0_x1y0_x0y1_x1y1 = vec4( gridcell.x, gridcell_inc1.x, gridcell.x, gridcell_inc1.x ) * vec4( gridcell.yy, gridcell_inc1.yy );
    vec4 z0w0_z1w0_z0w1_z1w1 = vec4( gridcell.z, gridcell_inc1.z, gridcell.z, gridcell_inc1.z ) * vec4( gridcell.ww, gridcell_inc1.ww );

    vec4 hashval = x0y0_x1y0_x0y1_x1y1 * z0w0_z1w0_z0w1_z1w1.xxxx;
    z0w0_hash_0 = fract( hashval * ( 1.0 / SOMELARGEFLOATS.x ) );
    z0w0_hash_1 = fract( hashval * ( 1.0 / SOMELARGEFLOATS.y ) );
    z0w0_hash_2 = fract( hashval * ( 1.0 / SOMELARGEFLOATS.z ) );
    z0w0_hash_3 = fract( hashval * ( 1.0 / SOMELARGEFLOATS.w ) );
    hashval = x0y0_x1y0_x0y1_x1y1 * z0w0_z1w0_z0w1_z1w1.yyyy;
    z1w0_hash_0 = fract( hashval * ( 1.0 / SOMELARGEFLOATS.x ) );
    z1w0_hash_1 = fract( hashval * ( 1.0 / SOMELARGEFLOATS.y ) );
    z1w0_hash_2 = fract( hashval * ( 1.0 / SOMELARGEFLOATS.z ) );
    z1w0_hash_3 = fract( hashval * ( 1.0 / SOMELARGEFLOATS.w ) );
    hashval = x0y0_x1y0_x0y1_x1y1 * z0w0_z1w0_z0w1_z1w1.zzzz;
    z0w1_hash_0 = fract( hashval * ( 1.0 / SOMELARGEFLOATS.x ) );
    z0w1_hash_1 = fract( hashval * ( 1.0 / SOMELARGEFLOATS.y ) );
    z0w1_hash_2 = fract( hashval * ( 1.0 / SOMELARGEFLOATS.z ) );
    z0w1_hash_3 = fract( hashval * ( 1.0 / SOMELARGEFLOATS.w ) );
    hashval = x0y0_x1y0_x0y1_x1y1 * z0w0_z1w0_z0w1_z1w1.wwww;
    z1w1_hash_0 = fract( hashval * ( 1.0 / SOMELARGEFLOATS.x ) );
    z1w1_hash_1 = fract( hashval * ( 1.0 / SOMELARGEFLOATS.y ) );
    z1w1_hash_2 = fract( hashval * ( 1.0 / SOMELARGEFLOATS.z ) );
    z1w1_hash_3 = fract( hashval * ( 1.0 / SOMELARGEFLOATS.w ) );
}
