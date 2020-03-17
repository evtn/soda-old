class Flex(Shape):
    draw_type = "image"
    
    def __init__(self, shapes, padding=None, axis="x", axis_size=None, space_around=False):
        self.shapes = shapes
        if padding is None and axis_size is None:
            raise ValueError("You must specify padding or axis_size for Flex")
        self.padding_ = padding
        self.axis = axis
        self.axis_size = axis_size
        self.k = 1
        self.space_around = space_around
    
    def size(self):
        size = [0, 0]
        axis = self.axis == "y"
        sizes = []
        for shape in self.shapes:
            s_size = shape.box_get()
            if s_size[1 - axis] > size[1 - axis]:
                size[1 - axis] = s_size[1 - axis]
            size[axis] += s_size[axis]
        return size
    
    def box_get(self):
        size = self.size()
        axis = self.axis == "y"
        if self.axis_size is None:
            size[axis] += self.padding_ * (len(self.shapes) - 1)
        else:
            size[axis] = self.axis_size
        return [s * self.k for s in size]
    
    @property 
    def padding(self):
        if self.axis_size is None:
            return self.padding_ * self.k
        return self.k * (self.axis_size - self.size()[self.axis == "y"]) / (len(self.shapes) - 1 + 2 * self.space_around)
    
    def render(self, draw, position):
        draw_ = ImageDraw.Draw(draw)
        padding = self.padding
        axis_position = padding * self.space_around
        for i, shape in enumerate(self.shapes):
            size = shape.box_get()
            s_position = position + Point(
                *[round(self.k * axis_position), round(self.k * (self.size()[self.axis != "y"] - size[self.axis != "y"]) / 2)][::(-1) ** (self.axis == "y")]
            )
            shape.resized(self.k).render(
                draw if shape.draw_type == "image" else draw_,
                s_position
            )
            axis_position += padding + size[self.axis == "y"]
    
    def resized(self, k):
        nf = Flex(self.shapes, self.padding, self.axis)
        nf.k = k
        return nf