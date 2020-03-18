class Flex(Shape):
    draw_type = "image"
    
    def __init__(self, shapes, padding=0, axis="x", space_around=False):
        self.shapes = shapes
        self.padding = padding
        self.axis = axis
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
        size[axis] += self.padding_ * (len(self.shapes) - 1)
        return [s * self.k for s in size]
    
    def render(self, draw, position):
        draw_ = ImageDraw.Draw(draw)
        axis_position = self.padding * self.space_around
        axis = self.axis == "y"

        for i, shape in enumerate(self.shapes):
            size = shape.box_get()
            s_position = position + Point(
                *[round(self.k * axis_position), round(self.k * (self.size()[1 - axis] - size[1 - axis]) / 2)][::(-1) ** axis]
            )
            shape.resized(self.k).render(
                Utils.draw_get(shape, [draw, draw_]),
                s_position
            )
            axis_position += padding + size[axis]
    
    def resized(self, k):
        nf = Flex(self.shapes, self.padding, self.axis)
        nf.k = k
        return nf


class Row(Shape):
    draw_type = "image"

    def __init__(self, shapes, size=None, axis="x", space_around=False):
        self.shapes = shapes
        self.axis = axis
        self.size = size
        self.k = 1
        self.space_around = space_around
    
    def size_(self):
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
        return [s * self.k for s in self.size]
    
    @property 
    def padding(self):
        quantity = (len(self.shapes) - 1 + 2 * self.space_around) or 2
        return self.k * (self.size[self.axis == "y"] - self.size_()[self.axis == "y"]) / quantity
    
    def render(self, draw, position):
        draw_ = ImageDraw.Draw(draw)
        padding = self.padding
        axis_position = padding * (self.space_around or len(self.shapes) == 1)
        axis = self.axis == "y"

        for i, shape in enumerate(self.shapes):
            size = shape.box_get()
            s_position = position + Point(
                *[round(self.k * axis_position), round(self.k * (self.size_()[1 - axis] - size[1 - axis]) / 2)][::(-1) ** axis]
            )
            shape.resized(self.k).render(
                Utils.draw_get(shape, [draw, draw_]),
                s_position
            )
            axis_position += padding + size[axis]


class Padding(Shape):
    draw_type = "image"

    def __init__(self, shape, padding):
        self.shape = shape
        self.padding_set(padding)

    def padding_set(self, padding):
        keys = ["top", "right", "bottom", "left"]
        if type(padding) == int:
            self.padding = {k: padding for k in keys}
        if type(padding) == list:
            if len(padding) == 2:
                self.padding = {keys[i]: padding[i % 2] for i in range(len(keys))}
            elif len(padding) == 3:
                self.padding = {keys[i]: padding[i - 2 * (i > 2)] for i in range(len(keys))}
            elif len(padding) == 4:
                self.padding = {keys[i]: padding[i] for i in range(len(keys))}
        if type(padding) == dict:
            self.padding = {k: padding.get(k, 0) for k in keys}

    def render(self, draw, position):
        shape = self.shape
        shape.render(
            Utils.draw_get(shape, [draw, ImageDraw.Draw(draw)]),
            position + Point(
                self.padding["left"],
                self.padding["top"]
            )
        )

    def box_get(self):
        shape_size = self.shape.box_get()
        width = (shape_size[0] + self.padding["left"] + self.padding["right"])
        height = (shape_size[1] + self.padding["top"] + self.padding["bottom"])
        return [width, height]

    def resized(self, k):
        size = self.box_get()
        shape_size = self.shape.box_get()
        new_size = [s * k for s in size]
        new_size[0] -= (self.padding["left"] + self.padding["right"])
        new_size[1] -= (self.padding["top"] + self.padding["bottom"])
        nk = min([new_size[i] / shape_size[i] for i in range(2)])
        return Padding(self.shape.resized(nk), self.padding)


class Cell(Shape):
    def __init__(self, shape, width=1, height=1):
        self.shape = shape
        self.width = width
        self.height = height

    def render(self, draw, position, size):
        FitBox(
            self.shape,
            (self.width * size[0], self.height * size[1]),
            align="cc"
        ).render(draw, position)

class Grid(Shape):
    draw_type = "image"
    def __init__(self, cells, size, dimensions):
        self.cells = cells
        self.size = size
        self.dimensions = dimensions

    @property
    def cell_size(self):
        return self.size[0] / self.dimensions[0], self.size[1] / self.dimensions[1]

    def render(self, draw, position):
        draw_ = ImageDraw.Draw(draw)
        cell_size = self.cell_size
        for x, y in self.cells:
            if x > self.dimensions[0] or y > self.dimensions[1]:
                continue
            cell = self.cells[x, y]
            if type(cell) != Cell:
                cell = Cell(cell)
            cell.render(
                draw,
                position + Point(cell_size[0], cell_size[1]) * Point(x, y),
                cell_size
            )

    @staticmethod
    def to_dict(cells):
        result = {}
        for x in range(len(cells)):
            for y in range(len(cells[x])):
                if cells[x][y]:
                    result[x, y] = cells[x][y]
        return result

    def box_get(self):
        return self.size

    def resized(self, k):
        return Grid(self.cells, [s * k for s in self.size], self.dimensions)


def equals(a, b):
    for k in a:
        if a[k] != b[k]:
            return False
    return True





