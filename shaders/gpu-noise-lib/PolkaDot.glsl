//
//      PolkaDot Noise 2D
//      http://briansharpe.files.wordpress.com/2011/12/polkadotsample.jpg
//      http://briansharpe.files.wordpress.com/2012/01/polkaboxsample.jpg
//      TODO, these images have random intensity and random radius.  This noise now has intensity as proportion to radius.  Images need updated.  TODO
//
//      Generates a noise of smooth falloff polka dots.
//      Allow for control on radius.  Intensity is proportional to radius
//      Return value range of 0.0->1.0
//
float PolkaDot2D(       vec2 P,
                    float radius_low,           //      radius range is 0.0->1.0
                    float radius_high   )
{
    //  establish our grid cell and unit position
    vec2 Pi = floor(P);
    vec2 Pf = P - Pi;

    //  calculate the hash.
    //  ( various hashing methods listed in order of speed )
    vec4 hash = FAST32_hash_2D_Cell( Pi );

    //  user variables
    float RADIUS = max( 0.0, radius_low + hash.z * ( radius_high - radius_low ) );
    float VALUE = RADIUS / max( radius_high, radius_low );      //      new keep value in proportion to radius.  Behaves better when used for bumpmapping, distortion and displacement

    //  calc the noise and return
    RADIUS = 2.0/RADIUS;
    Pf *= RADIUS;
    Pf -= ( RADIUS - 1.0 );
    Pf += hash.xy * ( RADIUS - 2.0 );
    //Pf *= Pf;         //      this gives us a cool box looking effect
    return Falloff_Xsq_C2( min( dot( Pf, Pf ), 1.0 ) ) * VALUE;
}
//      PolkaDot2D_FixedRadius, PolkaDot2D_FixedValue, PolkaDot2D_FixedRadius_FixedValue TODO


//
//      PolkaDot Noise 3D
//      http://briansharpe.files.wordpress.com/2011/12/polkadotsample.jpg
//      http://briansharpe.files.wordpress.com/2012/01/polkaboxsample.jpg
//      TODO, these images have random intensity and random radius.  This noise now has intensity as proportion to radius.  Images need updated.  TODO
//
//      Generates a noise of smooth falloff polka dots.
//      Allow for control on radius.  Intensity is proportional to radius
//      Return value range of 0.0->1.0
//
float PolkaDot3D(       vec3 P,
                    float radius_low,           //      radius range is 0.0->1.0
                    float radius_high   )
{
    //  establish our grid cell and unit position
    vec3 Pi = floor(P);
    vec3 Pf = P - Pi;

    //  calculate the hash.
    vec4 hash = FAST32_hash_3D_Cell( Pi );

    //  user variables
    float RADIUS = max( 0.0, radius_low + hash.w * ( radius_high - radius_low ) );
    float VALUE = RADIUS / max( radius_high, radius_low );      //      new keep value in proportion to radius.  Behaves better when used for bumpmapping, distortion and displacement

    //  calc the noise and return
    RADIUS = 2.0/RADIUS;
    Pf *= RADIUS;
    Pf -= ( RADIUS - 1.0 );
    Pf += hash.xyz * ( RADIUS - 2.0 );
    //Pf *= Pf;         //      this gives us a cool box looking effect
    return Falloff_Xsq_C2( min( dot( Pf, Pf ), 1.0 ) ) * VALUE;
}
