from PIL import ImageColor, ImageFont, Image as PImage, ImageDraw, ImageFilter
import random
import io
from math import sin, cos, pi
from os import path
exists = path.exists
try:
    import imageio
except ImportError:
    pass

script_path = path.dirname(path.abspath(__file__)) + "/"
modules = []

class Utils:
    @staticmethod
    def all_of(iterable, vtype):
        iterator = range(len(iterable)) if type(iterable) in [list, tuple] else iterable
        return not any(not isinstance(iterable[elem], vtype) for elem in iterator)

    @staticmethod
    def default(passed, default):
        return default if passed is None else passed

    @staticmethod
    def deg_to_rad(angle):
        return angle * pi / 180


def fit(box_size, shape_size):
    return min([box_size[0] / shape_size[0], box_size[1] / shape_size[1]])


def hsl(h=None, s=None, l=None):
    args = [h, s, l]
    argsmax = [360, 100, 100]

    def getval(x, maxx):
        if type(x) in [int, float]:
            return x
        return random.randint(*[int(x) for x in (x or [0, maxx])]) % (maxx + 1)

    args = [getval(args[i], argsmax[i]) for i in range(3)]
    return Color.parse("hsl({}, {}%, {}%)".format(*args))


def mask_resize(shape, mask):
    mask_ = PImage.new("L", shape.size)
    k = fit(shape.size, mask.size)
    mask = mask.resize(
        (int(mask.size[0] * k), int(mask.size[1] * k)), resample=PImage.LANCZOS)
    m_position = [0, 0]
    for i in range(2):
        if mask.size[i] != shape.size[i]:
            m_position[i] = (shape.size[i] - mask.size[i]) // 2
    mask_.paste(mask, m_position)
    return mask_


def get_point(pointy):
    if isinstance(pointy, Point):
        return pointy
    if isinstance(pointy, (tuple, list)):
        return Point(*pointy)


class Color:
    def __init__(self, color):
        self.change(color)

    def change(self, color):
        color = Color.parse(color)
        if len(color) == 4:
            self.red, self.green, self.blue, self.opacity = color
        else:
            self.red, self.green, self.blue, self.opacity = color, 255

    @staticmethod
    def parse(col):
        if isinstance(col, Color):
            return col.color
        return tuple(col[:4] if type(col) != str else ImageColor.getrgb(col) + (255,))

    @property
    def hexval(self):
        return "#" + "".join([("0" + hex(x)[2:])[-2:] for x in self.color])

    @property
    def color(self):
        return self.red, self.green, self.blue, self.opacity

    def __getattr__(self, attr):
        return Color(attr)

    def __getitem__(self, item):
        return Color(item)

    def __str__(self):
        return "soda.Color(): r{}g{}b{}a{} ({})".format(*self.color, self.hexval)


class Shape:
    draw_type = "shape"
    color = None

    def color_set(self, color):
        if isinstance(color, Color):
            self.color = color
        else:
            self.color = Color(color)

    def color_get(self):
        return (self.color or Color("red")).color

    # next methods must be implemented in any shape

    def box_get(self):
        # returns size of shape's bounding box: (width, height)
        return (0, 1)

    def render(self, draw, position):
        # renders shape on the canvas
        pass

    def __str__(self):
        # returns a string providing formal info on the shape
        return "soda." + self.__class__.__name__ + "() object"

    def resized(self, k):
        # returns a k times bigger shape
        return self


class Point(Shape):
    draw_type = "image"

    def __init__(self, x=None, y=None):
        self.x = self.y = 0
        self.move(x, y)

    def move(self, x=None, y=None):
        self.x = Utils.default(x, self.x)
        self.y = Utils.default(y, self.y)

    def __str__(self):
        return "soda.Point({}, {})".format(self.x, self.y)

    def __getitem__(self, item):
        return [self.x, self.y][item]

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)

    def __abs__(self):
        return (self.x ** 2 + self.y ** 2) ** 0.5

    def __mul__(self, other):
        if type(other) == Point:
            return Point(self.x * other.x, self.y * other.y)
        return Point(self.x * other, self.y * other)

    def box_get(self):
        return (1, 1)

    def resized(self, k):
        return Point(*self)

    def render(self, draw, position):
        draw.putpixel(*[round(position[i] + self[i]) for i in range(2)], color=self.color_get())

    def rotate(self, center, angle):
        angle = Utils.deg_to_rad(angle)
        x = cos(angle) * (self.x - center.x) - sin(angle) * (self.y - center.y) + center.x
        y = sin(angle) * (self.x - center.x) + cos(angle) * (self.y - center.y) + center.y
        return Point(x, y)


# points[, color]
class Polygon(Shape):
    def __init__(self, points, color=(0, 0, 0, 255)):
        self.color_set(color)
        self.points = tuple(get_point(point) for point in points)

    def to_list(self, pos):
        return [(point.x + pos.x, point.y + pos.y) for point in self.points]

    def render(self, draw, position):
        draw.polygon(self.to_list(position), fill=self.color_get())

    def box_get(self):
        xs, ys = sorted([point.x for point in self.points]), sorted([point.y for point in self.points])
        return xs[-1] - xs[0], ys[-1] - ys[0]

    def __str__(self):
        return "soda.Polygon({})".format("; ".join(["({}, {})".format(point.x, point.y) for point in self.points]))

    def resized(self, k):
        position = min([point.x for point in self.points]), min([point.y for point in self.points])
        points = []
        for point in self.points:
            points.append(Point((point.x - position[0]) * k + position[0],
                            (point.y - position[1]) * k + position[1]))
        return Polygon(points, self.color)

    def rotated(self, center, angle):
        center = get_point(center)
        return Polygon([point.rotate(center, angle) for point in self.points], self.color)

    def rotate(self, center, angle):
        self.points = self.rotated(center, angle).points


class RoundRect(Polygon):
    def __init__(self, width, height=None, radius=0, color=(0, 0, 0, 255), position=(0, 0)):
        self.size = [width, Utils.default(height, width)]
        self.color_set(color)
        self.radius = radius if type(radius) != int else [radius] * 4
        self.position = position

    def radius_limiter(self):
        for corner in range(4):
            s = self.radius[corner] + self.radius[(corner + 1) % 4]
            if s > self.size[corner % 2]:
                k = self.radius[corner] / s
                self.radius[corner] = self.size[corner % 2] * k
                self.radius[(corner + 1) % 4] = self.size[corner % 2] * (1 - k)

    def box_get(self):
        return self.construct()[-1].box_get()

    def construct(self):
        self.radius_limiter()
        shapes = []
        points = [0] * 8
        for corner in range(4):
            center = [0, 0]
            cond = bool(corner % 3), corner > 1
            for subcorner in range(2):
                d = [cond[subcorner] * self.size[subcorner],
                     (-1) ** cond[1 - subcorner] * self.radius[corner] + cond[1 - subcorner] * self.size[1 - subcorner]]
                d = d[::(-1) ** subcorner]
                points[corner * 2 + (corner % 2 != subcorner)] = Point(*d)
                center[1 - subcorner] = d[1 - subcorner] + self.position[1 - subcorner]
            shapes.append(Pieslice(center, self.radius[corner], color=self.color, start=90 * (1 - corner), stop=90 * (2 - corner)))
        for point in points:
            point.move(point.x + self.position[0], point.y + self.position[1])
        shapes.append(Polygon(points, self.color))
        return shapes

    def render(self, draw, position):
        for shape in self.construct():
            shape.render(draw, position)


# center, x_radius[, y_radius, color]
class Ellipse(Shape):
    def __init__(self, center, x_radius, y_radius=None, color=(0, 0, 0, 255)):
        self.radius_set(x_radius, y_radius)
        self.center = get_point(center)
        self.color_set(color)

    def to_list(self, pos):
        pos = Utils.default(pos, [0, 0])
        coords = [(self.center.x + pos.x - self.x_radius, self.center.y + pos.y - self.y_radius),
                  (self.center.x + pos.x + self.x_radius, self.center.y + pos.y + self.y_radius)]
        return coords

    def radius_set(self, x_radius, y_radius=None):
        self.x_radius = x_radius
        self.y_radius = Utils.default(y_radius, x_radius)

    def render(self, draw, position):
        draw.ellipse(self.to_list(position), fill=self.color_get())

    def box_get(self):
        return (self.x_radius * 2, self.y_radius * 2)

    def __str__(self):
        if self.x_radius == self.y_radius:
            return "soda.Ellipse(center: {}, radius: {})".format(self.center, self.x_radius)
        return "soda.Ellipse(center: {}, horizontal radius: {}, vertical radius: {})".format(self.center,
                                                                                             self.x_radius,
                                                                                             self.y_radius)

    def resized(self, k, **params):
        new_x = self.x_radius * k
        new_y = self.y_radius * k
        new_center = Point(self.center.x - (self.x_radius - new_x), self.center.y - (self.y_radius - new_y))
        return self.__class__(new_center, new_x, new_y, self.color, **params)


# center, x_radius[, y_radius, color, start, stop]
class Pieslice(Ellipse):
    def __init__(self, center, xrad, yrad=None, color=(0, 0, 0, 255), start=0, stop=360):
        super().__init__(center, xrad, yrad, color)
        self.start_set(start)
        self.stop_set(stop)

    def start_set(self, start):
        self.start = -start

    def stop_set(self, stop):
        self.stop = -stop

    def render(self, draw, position):
        draw.pieslice(self.to_list(position), self.stop, self.start, fill=self.color_get())

    def __str__(self):
        return super().__str__().replace("Ellipse", "Pieslice")

    def resized(self, k):
        return super().resized(k, start=-self.start, stop=-self.stop)
        

# text, font, size[, position, align, color]
class Text(Shape):
    def __init__(self, text, font, size=1000, position=Point(0, 0), align="cs", color=(0, 0, 0, 255)):
        self.text = text
        self.font_set(font, size)
        self.color_set(color)
        self.position = get_point(position)
        self.align = align

    def font_set(self, path, size):
        self.font = ImageFont.truetype(path, size)
        self.font_ = [path, size]

    def size_set(self, size):
        self.font_set(self.font_[0], size)

    def render(self, draw, position):
        position = get_point(position)
        position = [position.x + self.position.x, position.y + self.position.y]
        draw.multiline_text(self.corners_get(position)[0],
                            text=self.text,
                            font=self.font,
                            fill=self.color_get(),
                            align={"c": "center", "s": "left", "e": "right"}[self.align[0]])

    def corners_get(self, position=(0, 0)):
        size = self.box_get()
        corner = [0, 0]
        for i in range(2):
            if self.align[i] == "c":
                corner[i] = position[i] - (size[i] // 2)
            elif self.align[i] == "s":
                corner[i] = position[i]
            elif self.align[i] == "e":
                corner[i] = position[i] - size[i]
        return [corner, [corner[0] + size[0], corner[1] + size[1]]]

    def box_get(self):
        return self.font.getsize_multiline(self.text)

    def resized(self, k):
        return Text(self.text, self.font_[0], int(self.font_[1] * k), self.position, self.align, self.color)


# mask, color[, position, size]
class MaskShape(Shape):
    def __init__(self, mask, color, position=(0, 0), size=None):
        self.mask = None
        self.mask_set(mask)
        self.color_set(color)
        self.position = get_point(position)
        self.size = None
        if size is not None:
            self.size = tuple(size)

    def render(self, draw, position):
        position = get_point(position)
        position = [position.x + self.position.x, position.y + self.position.y]
        mask = self.mask_get()
        if self.size is not None and mask.size != self.size:
            mask = mask_resize(self, mask)
        draw.bitmap(position, mask, fill=self.color_get())

    def mask_set(self, mask):
        self.mask = SodaImage(mask)

    def mask_get(self):
        return self.mask.get("L")

    def box_get(self):
        return Utils.default(self.size, self.mask.size)

    def __str__(self):
        size = Utils.default(self.size, self.mask.size)
        return "soda.MaskShape(in ({}, {}) with {}x{} size)".format(self.position.x,
                                                                      self.position.y,
                                                                      size[0], size[1])

    def resized(self, k):
        size = self.size
        if not self.size:
            size = self.mask.size
        return MaskShape(self.mask, self.color, self.position, (size[0] * k, size[1] * k))


# image[, position, size, mask]
class SodaImage(Shape):
    draw_type = "image"
    def __init__(self, image, position=(0, 0), size=None, mask=None):
        self.mask = SodaImage(mask) if mask is not None else None
        self.size = tuple(size) if size is not None else None
        self.set(image)
        self.position = get_point(position)

    def get(self, mode=None, orig=False):
        image = self.image.render() if isinstance(self.image, Canvas) else self.image.copy()
        if image.size != self.size and not orig:
            image = self.crop(self.size, image)
        if mode is None or mode == image.mode:
            return image
        return image.convert(mode)

    def set(self, image):
        its = lambda x: isinstance(image, x)
        if its(SodaImage):
            self.image = image.image
        elif its(str):
            self.image = PImage.open(image)
        elif its(PImage.Image):
            self.image = image.copy()
        elif its(Canvas):
            self.image = image
        elif its(bytes):
            bio = io.BytesIO()
            bio.write(image)
            bio.seek(0)
            self.image = PImage.open(bio)
        else:
            raise TypeError("invalid image")
        if self.size is None:
            self.size = self.image.size
        self.size = tuple(self.size)

    def resized(self, k, image=None, fitbox=True):
        image = image or self.get()
        res = image.resize(tuple(int(image.size[i] * k) for i in range(2)), resample=PImage.LANCZOS)
        if fitbox:
            return SodaImage(res)
        return res

    def render(self, draw, position):
        if self.mask is not None:
            mask = self.mask.get("L")
            if mask.size != self.image.size:
                mask = mask_resize(self.image, mask)
        else:
            mask = None
        position = tuple([position.x + self.position.x, position.y + self.position.y])
        draw.paste(self.get(), position, mask=mask)

    def crop(self, size, image=None):
        image = image or self.get(orig=True)
        if type(size) == int:
            size = (size, size)
        k = fit(image.size, size)
        image = self.resized(1/k, image, fitbox=False)
        offset = [(image.size[i] - size[i]) // 2 for i in range(2)]
        return image.crop(offset + [size[i] + offset[i] for i in range(2)])

    def square_get(self, size=None):
        return self.crop(Utils.default(size, min(self.size)))

    def box_get(self):
        return self.get().size
        

# o_class, arg_names, **params
class Template:
    def __init__(self, o_class, arg_names, **params):
        self.params = params
        self.o_class = o_class
        self.arg_names = arg_names

    def create(self, *args, **params):
        for arg_i in range(len(self.arg_names)):
            key = self.arg_names[arg_i]
            value = args[arg_i]
            if arg_i in range(len(args)):
                if key not in params:
                    params[key] = value
            else:
                break
        return self.o_class(**{**self.params, **params})

    def __call__(self, *args, **params):
        return self.create(*args, **params)


# width[, height, color, position]
class Rectangle(Polygon):
    def __init__(self, width, height=None, color=(0, 0, 0, 255), position=(0, 0)):
        height = Utils.default(height, width)
        points = [Point(position[0] + width * (i in [1, 2]),
                    position[1] + height * (i > 1)) for i in range(4)]
        super().__init__(points, color)

    def size_set(self, width, height=None):
        height = Utils.default(height, width)
        self.__init__(height, width, self.color, (self.points[0].x, self.points[0].y))

    def __str__(self):
        return super().__str__().replace("Polygon", "Rectangle")


# shape, box[, position]
class FitBox(Shape):
    def __init__(self, shape: Shape, box, position=Point(0, 0)):
        self.debug = False
        self.initial = shape
        self.position = get_point(position)
        self.color_set("red")
        if type(box) in (tuple, list):
            is_int = sum(isinstance(box[i], int) for i in range(len(box)))
            if is_int:
                if len(box) == 1:
                    self.box = box[0], box[0]
                elif len(box) > 1:
                    self.box = box[0], box[1]
            elif len(box) >= 3:
                self.box = Polygon(tuple(Point(*point) for point in box)).box_get()
        else:
            self.box = box, box
        self.box = tuple(box)

    def __str__(self):
        return "soda.FitBox{}".format(self.box)

    def render(self, draw, position):
        shape = self.shape_get()
        position = Point(position.x + self.position.x, position.y + self.position.y)
        if self.debug:
            if type(self.initial) == Text:
                shape.text = "{}x{}".format(*self.box)
            draw.rectangle(((position.x, position.y), (position.x + self.box[0], position.y + self.box[1])),
                           fill=self.color_get())

        shape.render(draw, position)

    def resized(self, k):
        return FitBox(self.initial, tuple(self.box[i] // k for i in range(len(self.box))))

    def shape_get(self):
        return self.initial.resized(fit(self.box, self.initial.box_get()))

    def box_get(self):
        return box


class Canvas:
    def __init__(self, size=(1000, 1000), color="white", mode="RGBA", background=None):
        self.color = Color(color)
        self.objects = []
        self.mode = mode
        if type(size) in [int, float]:
            size = (size, size)
        self.size = size
        self.background = background

    def put(self, obj: Shape, position=None, index=None, label=None):
        position = get_point(Utils.default(position, [0, 0]))
        obj_ = {"object": obj, "position": position, "label": Utils.default(label, "obj{}".format(random.randint(1, 10000)))}
        if index is None:
            self.objects.append(obj_)
        else:
            self.objects.insert(index, obj_)

    def pop(self, index):
        return self.objects.pop(index)

    def move(self, index, position):
        self.objects[index]["position"] = Point(*position)

    def render(self):
        if self.background is None:
            image = PImage.new(self.mode, tuple(self.size), self.color.color)
        else:
            image = PImage.new(self.mode, tuple(self.background.size), self.color.color)
        self.size = image.size
        draw = ImageDraw.Draw(image)
        objects = self.objects
        if self.background:
            objects = [{"object": SodaImage(self.background), "position": Point(0, 0)}] + objects
        for obj in objects:
            d = draw if obj["object"].draw_type != "image" else image
            obj["object"].render(d, obj["position"])
        return image

    def save(self, file, extension="png"):
        self.render().save(file, extension)

    def __rshift__(self, file):
        self.save(file)

    @property
    def corners(self):
        return [Point(point[0], point[1]) for point in [(0, 0),
                                                (self.size[0], 0),
                                                (self.size[0], self.size[1]),
                                                (0, self.size[1])]]

    @property
    def center(self):
        return Point(self.size[0] // 2, self.size[1] // 2)

    @property
    def gif(self):
        return GIF(self)

    def to_bytes(self, extension="png"):
        bio = io.BytesIO()
        self.save(bio, extension)
        bio.seek(0)
        return bio.read()
    

class GIF:
    def __init__(self, canvas=None):
        self.images = []
        self.canvas = canvas

    def __call__(self, image=None):
        image = image or self.canvas.render()
        bio = io.BytesIO()
        image.save(bio, "png")
        bio.seek(0)
        self.images.append(imageio.imread(bio))

    def __rshift__(self, args):
        if type(args) == str:
            name = args
            framerate = 60
        elif not args:
            letter_set = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890"
            name = "anim-{}".format("".join([random.choice(letter_set) for i in range(10)]))
        else:
            name, framerate = args
        imageio.mimsave(name.strip(".gif") + ".gif", self.images, duration=1 / framerate)


def random_point(canvas):
    return Point(
        random.randint(0, canvas.size[0] - 1),
        random.randint(0, canvas.size[1] - 1)
    )


Dot = Point

def connect(names, force=False):
    results = {}
    if type(names) == str:
        names = names.replace(" ", "").split(",")
    for name in names:
        name_ = script_path + "soda-{}.py".format(name)
        if name in modules and not force:
            result = 0
        elif exists(name_):
            if name in modules:
                modules.remove(name)
            with open(name_, 'rb') as file:
                exec(compile(file.read(), name_, 'exec'), globals())
            result = 1
            modules.append(name)
        else:
            result = -1
        results[name] = result
    return results