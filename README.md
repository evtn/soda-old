# soda
## Contents
+ [Quickstart](#quickstart)
    + [Requirements](#requirements)
    + [Basics](#basics)
    + [Building a GIF](#building-a-gif)
    + [Positioning](#positioning)
+ [Basic Reference](#basic-reference)
    + [Objects system](#objects-system)
    + [Canvas](#canvas)
    + [Shape](#shape)
    + [Color](#color)
    + [Dot](#dot)
    + [Template](#template)
+ [Built-in Shapes](#built-in-shapes)
    + [Polygon](#polygon)
        + [Rectangle](#rectangle)
    + [Ellipse](#ellipse)
        + [Pieslice](#pieslice)
    + [Text](#text)
    + [MaskShape](#maskshape)
    + [FitBox](#fitbox)
    + [SodaImage](#sodaimage)

## Quickstart

### Requirements
Soda runs on Python3, using `Pillow` for rendering and `imageio` for GIFs (optional)

### Basics
The main object of Soda environment is canvas, an object that contains shapes and renders to an image:
```python
import soda

# let's create our canvas
my_first_canvas = soda.Canvas(size=(1000, 1000), # size is a tuple/list with two elements: width and height.
	                          color="green") # color can be either an (r, g, b) tuple, or a hex color, or even a CSS color (PIL.ImageColor)

# if one argument is given for Rectangle, soda assumes it's both width and height
square = soda.Rectangle(500, color="#fff")

# we need to put our square on the canvas.
my_first_canvas.put(square, position=(250, 250))

# then we can save our canvas and look at this ugly color scheme that we've chose (._.)
my_first_canvas.save("super_picture.png")
```
Canvas can be rendered and saved as an image at any point of your code, and it still would be a canvas.
At this point, it doesn't make any sense - why we need these shapes and canvas?
The answer is simplicity. You don't have to handle some unnecessary aspects of a picture, and you can create tons of different pictures with a few lines of code.

Despite the fact that Soda is intended for creating images, its main feature is dynamics. 
So, let's make a better example with GIF animation:

### Building a GIF
Imagine that you want to make an animation of 1600 squares randomly changing color. Pretty strange example, but here you are:    
```python
import soda
multiplier = 5
# let's create our canvas again
canvas = soda.Canvas(size=(42 * multiplier, 42 * multiplier),
	                 color="#fff") # no more green, okay?

squares = []
for i in range(1600):
    squares.append(soda.Rectangle(multiplier, color="#4680c2", position=(multiplier, multiplier))) # local position - square would have an additional offset
    canvas.put(squares[-1], position=((i % 40) * multiplier,
	                                  (i // 40) * multiplier)) # calculating the position according to the index

renders = []

for i in range(100):
    for j in range(len(squares)):
        squares[j].color_set(soda.hsl()) # if there's no arguments, hsl() places random values
    renders.append(canvas.render())
soda.build_gif(renders, framerate=30)

```
### Positioning
You've probably seen some `position` argument before on this page. Seems intuitive, but what does this argument do in Rectangle?    
Soda has levels of position: You can put an ellipse on canvas on (200, 200), and then set the position of this ellipse itself to (120, 90). The final position would be (320, 290)    

____

## Reference

### Objects system
There are 4 main object types:
+ Canvas
+ Shape
+ Dot
+ Color
+ Template

____

### Canvas
#### Arguments:    
`size`  size of the canvas in pixels as tuple of (x, y) or as an integer (would be converted to a tuple) *default: (1000, 1000)*    
`color`  background color of canvas (check [Color](#color)). *default: "white"*    
`mode`  mode of the picture (check [Pillow Image Modes](pillow.readthedocs.io/en/stable/handbook/concepts.html#concept-modes)) *default: "RGB"*    
`background`  picture to use as canvas. if value equals "color", no picture would be used *default: "color"*    

#### Methods
`put(obj: Shape, position=(0, 0), index=None)`    
Puts a shape to the canvas. If index is specified, would insert the shape on that index.   
*returns: None*     

`pop(index)`    
Removes a shape with chosen index.    
*returns: removed Shape*    

`move(index, position)`    
Moves a shape with chosen index to a specified position.    
*returns: None*    

`render()`    
Renders an image of the canvas.    
*returns: PIL.Image.Image*    

`save(file, extension=None)`    
Saves an image of the canvas, equivalent to `.render().save(file, extension)`    
*returns: None*    

`get_corners() and get_center()`    
*returns: list of Dot, containing corners of the canvas*; *returns: Dot of canvas center*    

____

### Shape
This is the default Shape reference, for built-in shapes check [Built-in Shapes](#built-in-shapes)    
#### Methods    
Shapes have to implement a few common methods:    

`render(draw, position)`    
Renders itself using `draw` on specified position    
*returns: None*    

`resized(k)`    
Returns a copy of itself, multiplied in size by `k`    
*returns: Shape*    

`box_get()`    
Returns a tuple with shape size in pixels: (width, height).    
*returns: tuple(width, height)*    

Next block contains methods fully-implemented in Shape class:

`color_set(color)`    
Sets a color of the shape. `color` can be either a Color object or any type of color notation the [Color.parse](#parse-method) accepts    
*returns: None*    

`color_get()`    
Returns a color of the shape    
*returns: Color*    

____

### Color
Defines color.    

#### Attributes    

`change(color)`    
Changes its color to specified    
*returns: None*    

`color`    
A tuple of (r, g, b) values (each one from 0 to 255)    

#### parse method    
`Color.parse(col, mode="RGBA")`    
Parses the color (from a list/tuple or from a string)    
Accepts:    
+ Strings:    
    + hex: `#fff`, `#103515`    
    + css: `white`    
    + hsl: `hsl(360, 82%, 60%)`    
+ RGB Tuple:    
	+ rgb: (`240`, `100`, `10`)    
	+ rgba: (`255`, `70`, `12`, `45`)    

*returns: rgb(a) tuple*    

____

### Dot    
Defines an abstract dot on any canvas   
*dot-like object* is a tuple or list of 2 integers, or the Dot itself

#### Arguments    
`x, y` - dot position    

#### Methods    
`move(x=None, y=None)`    
Moves a dot to another position. If some parameter isn't specified, it would stay the same.    

____

### Template    
Defines a template to create similiar shapes    

#### Arguments    
`o_class`  desired object class, i.e. Ellipse    
`arg_names`  tuple/list containing names of arguments as they would be passed    
`**params`  static default params passed to the shape constructor    

#### Methods    
`create(*args, **params)`    
Creates a shape with specified args, default params and passed params.    
Priority of arguments (from high to low): params - default params - args    
*returns: shape instance*    

____

## Built-in Shapes
Soda has 6 types of unique built-in shapes.    

### Polygon    
The most used shape is definitely a polygon.    

Polygon constructor takes two arguments:    
+ `dots` - tuple/list of dot-like objects    
+ `color` - see [Color notation](#parse-method). *default: "black"*    

Polygon shares default Shape methods and defines a `to_list()` method (*returns: list of dots*)    

#### Rectangle    
Rectangle is a wrapper class of Polygon.    

Rectangle constructor takes four arguments:    
+ `width` - width of the rectangle in pixels    
+ `height` - height in pixels *default: passed width*    
+ `color` - see [Color notation](#parse-method). *default: "black"*    
+ `position` - dot-like object    

Rectangle has unique `set_size(width, height=None)` method, that changes its size (*returns: None*)    

____
This part is still not documented. You might wait a few days.

### Ellipse

#### Pieslice

### Text

### MaskShape

### FitBox

### SodaImage
