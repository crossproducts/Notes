<h1>Udemy: The Complete Full-Stack Web Development Bootcamp</h1>

Boilerplate
    !<tab>
    needs to be .html file

CSS
    In-line
    <h1 style=“color:coral”>Hello World</h1>
    Internal
    <head> <style> h1{ background:blue; } </style> </head>
    External
    <link rel=“stylesheet” href=“style.css”/>
    Class Selector
    .html file: <… class=“class-name”>
    .css file: .class-name{ color:red }
    ID Selector
    .html file: <… id=“id-name”>
    .css file: #id -name{ color:red }
    Attribute Selector
    .html file: …
    .css file: HTML_ELEMENT[ATTRIBUTE]{ color:red}
    Or .css file: HTML_ELEMENT[ATTRIBUTE=false]{ color:red}
    Universal Selector
    .html file: …
    .css file: *{ color:red}
    Font Size
    1px
    1pt
    1em
    1rem
    Named Font Sizes
    Font Weight
    Font Family
    Box Model
    1. Padding
    2. Border
    3. Margin 
    Content Division Element
    <div> CONTENT </div>
    CSS Inheritance 

    Position 
    Position in the file
    Specificity
    Element
    Class
    Attribute
    ID
    Type
    External
    Internal
    In-Line
    Importance
    Use !important to override the order
    Combining Selectors
    Chaining
    Positioning
        Static: Default positioning 
        Relative: Position relative to default (supposed to be) position 
        Absolute: 
            Position relative to nearest positioned ancestor
            or Top Left corner of page
        Fixed: Position relative to top left corner of browser window
    Display Property
        Block: Takes the full width of page
        Inline: Elements will be on the same line, if there is space
        Inline-Block: 
        None: Hide element (button, etc.)
    Float
        Floating element with text wrapped around element
    Clear
        Remove need to wrap around
    Responsive Mediw
        Media Queries
            @media
        CSS Grid
            2D
        CSS Flexbox
            1D
        External Frameworks (Bootstrap)
