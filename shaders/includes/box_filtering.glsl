vec4
filtering_box4(sampler2D texture, vec2 uv, vec2 texel_size, int level)
{
  vec4 tl = textureLod(texture, uv + texel_size * vec2(-1.0, -1.0), level);
  vec4 tr = textureLod(texture, uv + texel_size * vec2( 1.0, -1.0), level);
  vec4 br = textureLod(texture, uv + texel_size * vec2( 1.0,  1.0), level);
  vec4 bl = textureLod(texture, uv + texel_size * vec2(-1.0,  1.0), level);

    vec4 result = (tl + tr + br + bl) / 4.0;

    return result;
}


vec4
filtering_box9(sampler2D texture, vec2 uv, vec2 texel_size, int level)
{
  vec4 center = textureLod(texture, uv, level);

  vec4 tl = textureLod(texture, uv + texel_size * vec2(-1.0, -1.0), level);
  vec4 tm = textureLod(texture, uv + texel_size * vec2( 0.0, -1.0), level);
  vec4 tr = textureLod(texture, uv + texel_size * vec2( 1.0, -1.0), level);
  vec4 mr = textureLod(texture, uv + texel_size * vec2( 1.0,  0.0), level);
  vec4 br = textureLod(texture, uv + texel_size * vec2( 1.0,  1.0), level);
  vec4 bm = textureLod(texture, uv + texel_size * vec2( 0.0,  1.0), level);
  vec4 bl = textureLod(texture, uv + texel_size * vec2(-1.0,  1.0), level);
  vec4 ml = textureLod(texture, uv + texel_size * vec2(-1.0,  0.0), level);

    vec4 result = center * 4.0 +
        (tm + mr + bm + ml) * 2.0 +
        (tl + tr + br + bl);

    return result / 16.0;
}


vec4
filtering_box13(sampler2D texture, vec2 uv, vec2 texel_size, int level)
{
  vec4 center = textureLod(texture, uv, level);

  vec4 inner_tl = textureLod(texture, uv + texel_size * vec2(-1.0, -1.0), level);
  vec4 inner_tr = textureLod(texture, uv + texel_size * vec2( 1.0, -1.0), level);
  vec4 inner_br = textureLod(texture, uv + texel_size * vec2( 1.0,  1.0), level);
  vec4 inner_bl = textureLod(texture, uv + texel_size * vec2(-1.0,  1.0), level);

  vec4 outer_tl = textureLod(texture, uv + texel_size * vec2(-2.0, -2.0), level);
  vec4 outer_tm = textureLod(texture, uv + texel_size * vec2( 0.0, -2.0), level);
  vec4 outer_tr = textureLod(texture, uv + texel_size * vec2( 2.0, -2.0), level);
  vec4 outer_mr = textureLod(texture, uv + texel_size * vec2( 2.0,  0.0), level);
  vec4 outer_br = textureLod(texture, uv + texel_size * vec2( 2.0,  2.0), level);
  vec4 outer_bm = textureLod(texture, uv + texel_size * vec2( 0.0,  2.0), level);
  vec4 outer_bl = textureLod(texture, uv + texel_size * vec2(-2.0,  2.0), level);
  vec4 outer_ml = textureLod(texture, uv + texel_size * vec2(-2.0,  0.0), level);

    vec4 result =
        (inner_tl + inner_tr + inner_br + inner_bl) / 8.0 +
        (outer_tl + outer_tm + center + outer_ml) / 32.0 +
        (outer_tm + outer_tr + outer_mr + center) / 32.0 +
        (center + outer_mr + outer_br + outer_bm) / 32.0 +
        (outer_ml + center + outer_bm + outer_bl) / 32.0;

    return result;
}
