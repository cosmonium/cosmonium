/*
 * This file is part of Cosmonium.
 *
 * Copyright (C) 2018-2022 Laurent Deru.
 *
 * Cosmonium is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Cosmonium is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Cosmonium.  If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef RENDER_PASS_H
#define RENDER_PASS_H

#include "pandabase.h"
#include "referenceCount.h"
#include "nodePath.h"

class GraphicsOutput;


class RenderPass : public ReferenceCount
{
public:
  RenderPass(const std::string &name, GraphicsOutput *target, DrawMask camera_mask);
  RenderPass(RenderPass& other);

  virtual ~RenderPass(void);

  void create(void);

  void remove(void);

public:
  PT(DisplayRegion) display_region;
  NodePath camera;

protected:
  const std::string &name;
  PT(GraphicsOutput) target;
  DrawMask camera_mask;
};

#endif
