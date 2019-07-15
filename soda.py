from PIL import ImageColor, ImageFont, Image, ImageDraw
import random
import io
try:
    import imageio
except ImportError:
    print("Loading without GIF-builder...")


gk = 2


def all_of(iterable, vtype):
    return not any(not isinstance(iterable[i], vtype) for i in (range(len(iterable)) if type(iterable) in [list, tuple] else iterable))


def get_default(to_check, default):
    return default if to_check is None else to_check


def hsl(h=None, s=None, l=None):
    h = (h, h) if type(h) in [int, float] else (0, 360) if h is None else h
    s = (s, s) if type(s) in [int, float] else (0, 100) if s is None else s
    l = (l, l) if type(l) in [int, float] else (0, 100) if l is None else l
    h = random.randint(*[int(x) for x in h]) % 361
    s = random.randint(*[int(x) for x in s]) % 101
    l = random.randint(*[int(x) for x in l]) % 101
    return Color.parse("hsl({}, {}%, {}%)".format(h, s, l))


def fit(box_size, shape_size):
    return min([box_size[0] / shape_size[0], box_size[1] / shape_size[1]])


def mask_resize(shape, mask):
    mask_ = Image.new("L", shape.size)
    k = fit(shape.size, mask.size)
    mask = mask.resize(
        (int(mask.size[0] * k), int(mask.size[1] * k)), resample=Image.LANCZOS)
    m_position = [0, 0]
    for i in range(2):
        if mask.size[i] != shape.size[i]:
            m_position[i] = (shape.size[i] - mask.size[i]) // 2
    mask_.paste(mask, m_position)
    return mask_


def get_dot(dot_like):
    if isinstance(dot_like, Dot):
        return dot_like
    if isinstance(dot_like, (tuple, list)):
        return Dot(*dot_like)


class Dot:
    def __init__(self, x, y):
        self.x = self.y = 0
        self.move(x, y)

    def move(self, x=None, y=None):
        self.x = get_default(x, self.x)
        self.y = get_default(y, self.y)

    def __str__(self):
        return "soda.Dot({}, {})".format(self.x, self.y)

    def __getitem__(self, item):
        return self.x if not item else self.y


class Color:
    def __init__(self, color):
        self.change(color)

    def change(self, color):
        self.color = Color.parse(color)

    @staticmethod
    def parse(col, mode="RGBA"):
        if isinstance(col, Color):
            return col.color
        return tuple(col[:4 if mode == "RGBA" else 3] if type(col) != str else ImageColor.getrgb(col) + ((255,) if mode == "RGBA" else tuple()))


class Shape:
    def color_set(self, color):
        if isinstance(color, Color):
            self.color = color
        else:
            self.color = Color(color)

    def color_get(self):
        return self.color.color

    def box_get(self):
        # returns left upper and right bottom corners of shape's bounding box: [(x1, y1), (x2, y2)]
        return [(0, 0), (1, 1)]

    def render(self, draw, position):
        # renders shape on the canvas
        pass

    def __str__(self):
        return "Some soda.Shape"

    def resized(self, k):
        return self.__class__()


# dots[, color]
class Polygon(Shape):
    def __init__(self, dots, color=(0, 0, 0, 255)):
        self.color_set(color)
        self.dots = tuple(get_dot(dot) for dot in dots)

    def to_list(self, pos):
        return [((dot.x + pos.x) * gk, (dot.y + pos.y) * gk) for dot in self.dots]

    def render(self, draw, position):
        draw.polygon(self.to_list(position), fill=self.color_get())

    def box_get(self):
        xs, ys = sorted([dot.x for dot in self.dots]), sorted([dot.y for dot in self.dots])
        return xs[-1] - xs[0], ys[-1] - ys[0]

    def __str__(self):
        return "soda.Polygon({})".format("; ".join(["({}, {})".format(dot.x, dot.y) for dot in self.dots]))

    def resized(self, k):
        position = min([dot.x for dot in self.dots]), min([dot.y for dot in self.dots])
        dots = []
        for dot in self.dots:
            dots.append(Dot((dot.x - position[0]) * k + position[0],
                            (dot.y - position[1]) * k + position[1]))
        return Polygon(dots, self.color)


class RoundRect(Polygon):
    def __init__(self, width, height=None, radius=0, color=(0, 0, 0, 255), position=(0, 0)):
        self.size = [width, height]
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

    def construct(self):
        self.radius_limiter()
        shapes = []
        dots = [0] * 8
        for corner in range(4):
            center = [0, 0]
            cond = bool(corner % 3), corner > 1
            for subcorner in range(2):
                d = [cond[subcorner] * self.size[subcorner],
                     (-1) ** cond[1 - subcorner] * self.radius[corner] + cond[1 - subcorner] * self.size[1 - subcorner]]
                d = d[::(-1) ** subcorner]
                dots[corner * 2 + (corner % 2 != subcorner)] = Dot(*d)
                center[1 - subcorner] = d[1 - subcorner] + self.position[1 - subcorner]
            shapes.append(Pieslice(center, self.radius[corner], color=self.color, start=90 * (1 - corner), stop=90 * (2 - corner)))
        for dot in dots:
            dot.move(dot.x + self.position[0], dot.y + self.position[1])
        shapes.append(Polygon(dots, self.color))
        return shapes

    def render(self, draw, position):
        for shape in self.construct():
            shape.render(draw, position)


# center, x_radius[, y_radius, color]
class Ellipse(Shape):
    def __init__(self, center, x_radius, y_radius=None, color=(0, 0, 0, 255)):
        self.radius_set(x_radius, y_radius)
        self.center = get_dot(center)
        self.color_set(color)

    def to_list(self, pos):
        pos = get_default(pos, [0, 0])
        coords = [(self.center.x + pos.x - self.x_radius, self.center.y + pos.y - self.y_radius),
                  (self.center.x + pos.x + self.x_radius, self.center.y + pos.y + self.y_radius)]
        print(coords, [tuple(i * gk for i in el) for el in coords])
        return [tuple(i * gk for i in el) for el in coords]

    def radius_set(self, x_radius, y_radius=None):
        self.x_radius = x_radius
        self.y_radius = get_default(y_radius, x_radius)

    def render(self, draw, position):
        draw.ellipse(self.to_list(position), fill=self.color_get())

    def box_get(self):
        return [(self.center.x - self.x_radius, self.center.y + self.y_radius * 2),
                (self.center.x +- self.x_radius, self.center.y - self.y_radius * 2)]

    def __str__(self):
        if self.x_radius == self.y_radius:
            return "soda.Ellipse(center: {}, radius: {})".format(self.center, self.x_radius)
        return "soda.Ellipse(center: {}, horizontal radius: {}, vertical radius: {})".format(self.center,
                                                                                             self.x_radius,
                                                                                             self.y_radius)

    def resized(self, k, **params):
        new_x = self.x_radius * k
        new_y = self.y_radius * k
        new_center = Dot(self.center.x - (self.x_radius - new_x), self.center.y - (self.y_radius - new_y))
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
    def __init__(self, text, font, size=1000, position=Dot(0, 0), align="cs", color=(0, 0, 0, 255)):
        self.text = text
        self.font_set(font, size * gk)
        self.color_set(color)
        self.position = get_dot(position)
        self.align = align

    def font_set(self, path, size):
        self.font = ImageFont.truetype(path, size)
        self.font_ = [path, size]

    def size_set(self, size):
        self.font_set(self.font_[0], size * gk)

    def render(self, draw, position):
        position = get_dot(position)
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
        return tuple(s // gk for s in self.font.getsize_multiline(self.text))

    def resized(self, k):
        return Text(self.text, self.font_[0], int(self.font_[1] * k), self.position, self.align, self.color)


# mask, color[, position, size]
class MaskShape(Shape):
    def __init__(self, mask, color, position=(0, 0), size=None):
        self.mask = None
        self.mask_set(mask)
        self.color_set(color)
        self.position = get_dot(position)
        self.size = None
        if size is not None:
            self.size = tuple(size)

    def render(self, draw, position):
        position = get_dot(position)
        position = [(position.x + self.position.x) * gk, (position.y + self.position.y) * gk]
        mask = self.mask_get()
        if self.size is not None and mask.size != self.size:
            mask = mask_resize(self, mask)
        mask.resize(tuple(s * gk for s in mask.size))
        draw.bitmap(position, mask, fill=self.color_get())

    def mask_set(self, mask):
        self.mask = SodaImage(mask)

    def mask_get(self):
        return self.mask.get("L")

    def box_get(self):
        return get_default(self.size, self.mask.size)

    def __str__(self):
        size = get_default(self.size, self.mask.size)
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
    def __init__(self, image, position=(0, 0), size=None, mask=None):
        self.mask = SodaImage(mask) if mask is not None else None
        self.size = tuple(size) if size is not None else None
        self.set(image)
        self.position = get_dot(position)

    def get(self, mode=None, orig=False):
        image = self.image.render() if isinstance(self.image, Canvas) else self.image.copy()
        if image.size != self.size and not orig:
            image = self.crop(self.size, image)
        if mode is None or mode == image.mode:
            return image
        return image.convert(mode)

    def set(self, image):
        if isinstance(image, SodaImage):
            self.image = image.image
        elif isinstance(image, str):
            self.image = Image.open(image)
        elif isinstance(image, Image.Image):
            self.image = image.copy()
        elif isinstance(image, Canvas):
            self.image = image
        else:
            raise TypeError("invalid image")
        if self.size is None:
            self.size = self.image.size
        self.size = tuple([self.size[i] * gk for i in range(2)])        

    def resized(self, k, image=None, fitbox=True):
        image = image or self.get(orig=True)
        res = image.resize(tuple(int(image.size[i] * k) for i in range(2)), resample=Image.LANCZOS)
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
        return self.crop(get_default(size, min(self.size)))


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
        height = get_default(height, width)
        dots = [Dot(position[0] + width * (i in [1, 2]),
                    position[1] + height * (i > 1)) for i in range(4)]
        super().__init__(dots, color)

    def size_set(self, width, height=None):
        height = get_default(height, width)
        self.__init__(height, width, self.color, (self.dots[0].x, self.dots[0].y))

    def __str__(self):
        return super().__str__().replace("Polygon", "Rectangle")


# shape, box[, position]
class FitBox(Shape):
    def __init__(self, shape: Shape, box, position=Dot(0, 0)):
        self.debug = False
        self.initial = shape
        self.position = get_dot(position)
        self.color_set("red")
        if type(box) in (tuple, list):
            is_int = sum(isinstance(box[i], int) for i in range(len(box)))
            if is_int:
                if len(box) == 1:
                    self.box = box[0], box[0]
                elif len(box) > 1:
                    self.box = box[0], box[1]
            elif len(box) >= 3:
                self.box = Polygon(tuple(Dot(*dot) for dot in box)).box_get()
        else:
            self.box = box, box
        self.box = tuple([b * gk for b in box])

    def __str__(self):
        return "soda.FitBox{}".format(self.box)

    def render(self, draw, position):
        shape = self.shape_get()
        position = Dot((position.x + self.position.x) * gk, (position.y + self.position.y) * gk)
        if self.debug:
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
    def __init__(self, size=(1000, 1000), color="white", mode="RGB", background=None):
        self.color = Color(color)
        self.objects = []
        self.mode = mode
        if type(size) == int:
            size = (size, size)
        self.size = size
        self.background = background

    def put(self, obj: Shape, position=None, index=None, label=None):
        position = get_dot(get_default(position, [0, 0]))
        obj_ = {"object": obj, "position": position, "label": get_default(label, "obj{}".format(random.randint(1, 10000)))}
        if index is None:
            self.objects.append(obj_)
        else:
            self.objects.insert(index, obj_)

    def pop(self, index):
        return self.objects.pop(index)

    def move(self, index, position):
        self.objects[index]["position"] = Dot(*position)

    def render(self):
        if self.background is None:
            image = Image.new(self.mode, tuple([size * gk for size in self.size]), self.color.color)
        else:
            image = SodaImage(self.background).get()
            image = image.resize(tuple(s * gk for s in image.size))
        self.size = image.size
        draw = ImageDraw.Draw(image)
        for obj in self.objects:
            d = draw if not isinstance(obj["object"], SodaImage) else image
            obj["object"].render(d, obj["position"])
        return image.resize(tuple(s // gk for s in self.size), resample=Image.LANCZOS)

    def save(self, file, extension="png"):
        self.render().save(file, extension)

    def corners_get(self):
        return [Dot(dot[0], dot[1]) for dot in [(0, 0),
                                                (self.size[0], 0),
                                                (self.size[0], self.size[1]),
                                                (0, self.size[1])]]

    def center_get(self):
        return Dot(self.size[0] // 2, self.size[1] // 2)


class GIF:
    def __init__(self, canvas=None):
        self.images = []
        self.canvas = canvas

    def add(self, image=None):
        image = image or self.canvas.render()
        bio = io.BytesIO()
        image.save(bio, "png")
        bio.seek(0)
        self.images.append(imageio.imread(bio))

    def save(self, name=None, framerate=60):
        letter_set = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890"
        path = name or "anim-{}".format("".join([random.choice(letter_set) for i in range(10)]))
        imageio.mimsave(path + (".gif" if not path.endswith(".gif") else ""), self.images, duration=1 / framerate)


def random_dot(canvas):
    return Dot(
        random.randint(0, canvas.size[0] - 1),
        random.randint(0, canvas.size[1] - 1)
    )


