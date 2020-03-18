class Star(soda.Polygon):
    def __init__(self, peaks, radius, k, color="black"):
        self.peaks, self.radius, self.k = peaks, radius, k
        self.dots = []
        self.color_set(color)
    def render(self, draw, position):
        self.dots = []
        base_angle = pi / self.peaks
        for i in range(self.peaks):
            base = 2 * i * base_angle
            self.dots.append(soda.Dot(x=self.radius * cos(base),
                                      y=self.radius * sin(base)))
            self.dots.append(soda.Dot(x=self.radius * cos(base + base_angle) * self.k,
                                      y=self.radius * sin(base + base_angle) * self.k))
        super().render(draw, position)
